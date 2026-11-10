"""PKI descartável e PDFs assinados para testes de verificação de assinatura.

Change assinatura-verificacao-fundacao (design.md D8, tasks 2.1/2.2). Gera, só
com `cryptography` e pyHanko, uma hierarquia de teste no formato ICP-Brasil
(raiz → AC intermediária → signatário com `otherName` 2.16.76.1.3.1 contendo
CPF fictício), uma TSA de teste, a LCR da AC intermediária e os PDFs de cada
veredito. **Prova o fluxo, não prova conformidade ICP-Brasil** (estudo-tecnico.md
§8): a raiz gerada aqui nunca é âncora em produção.

Usos:
- pytest: `from scripts.pki_teste import gerar_pki` (tudo em memória, offline).
- Playwright: `uv run python scripts/pki_teste.py --saida DIR --porta 8765`
  grava raiz/LCR/PDFs em DIR e serve DIR por HTTP local (a LCR dos certificados
  de teste aponta para esse servidor) até ser encerrado.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import io
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from asn1crypto import keys as asn1_keys
from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from fpdf import FPDF
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers, timestamps
from pyhanko_certvalidator.registry import SimpleCertificateStore

OID_ICP_PF = "2.16.76.1.3.1"  # dados de pessoa física (nascimento + CPF + …)
CPF_TESTE = "12345678909"
NOME_TESTE = "MARIA DE TESTE DA SILVA"
PORTA_PADRAO = 8765


@dataclass
class Par:
    cert: x509.Certificate
    chave: rsa.RSAPrivateKey

    @property
    def asn1(self) -> asn1_x509.Certificate:
        return asn1_x509.Certificate.load(self.cert.public_bytes(serialization.Encoding.DER))

    @property
    def pem(self) -> bytes:
        return self.cert.public_bytes(serialization.Encoding.PEM)


@dataclass
class PkiTeste:
    raiz: Par
    ac: Par
    signatario: Par
    revogado: Par
    expira_logo: Par
    sem_cpf: Par
    tsa: Par
    lcr: bytes
    url_lcr: str
    agora: datetime
    # Hierarquia paralela, nunca confiável — simula assinatura gov.br/privada.
    raiz_estranha: Par
    signatario_estranho: Par
    extras: dict[str, bytes] = field(default_factory=dict)


def _chave() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _nome(cn: str, ou: str = "Teste") -> x509.Name:
    return x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ICP-Teste"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ou),
            x509.NameAttribute(NameOID.COMMON_NAME, cn),
        ]
    )


def _octet_string(conteudo: bytes) -> bytes:
    assert len(conteudo) < 128
    return b"\x04" + bytes([len(conteudo)]) + conteudo


def _emitir(
    *,
    sujeito: x509.Name,
    chave: rsa.RSAPrivateKey,
    emissor: Par | None,
    inicio: datetime,
    fim: datetime,
    ac: bool,
    url_lcr: str | None,
    cpf: str | None = None,
    eku: list | None = None,
) -> Par:
    chave_emissora = emissor.chave if emissor else chave
    nome_emissor = emissor.cert.subject if emissor else sujeito
    b = (
        x509.CertificateBuilder()
        .subject_name(sujeito)
        .issuer_name(nome_emissor)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(inicio)
        .not_valid_after(fim)
        .add_extension(x509.BasicConstraints(ca=ac, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(chave.public_key()), critical=False)
    )
    if emissor:
        b = b.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(emissor.chave.public_key()),
            critical=False,
        )
    if ac:
        b = b.add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=True, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
    else:
        b = b.add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=True, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
    if eku:
        b = b.add_extension(x509.ExtendedKeyUsage(eku), critical=True)
    if url_lcr:
        b = b.add_extension(
            x509.CRLDistributionPoints(
                [x509.DistributionPoint([x509.UniformResourceIdentifier(url_lcr)], None, None, None)]
            ),
            critical=False,
        )
    if cpf:
        valor = ("01011980" + cpf + "0" * 11 + "0" * 15 + "SSPBA").encode("ascii")
        b = b.add_extension(
            x509.SubjectAlternativeName(
                [x509.OtherName(x509.ObjectIdentifier(OID_ICP_PF), _octet_string(valor))]
            ),
            critical=False,
        )
    return Par(b.sign(chave_emissora, hashes.SHA256()), chave)


@functools.lru_cache(maxsize=4)
def gerar_pki(url_lcr: str = f"http://127.0.0.1:{PORTA_PADRAO}/ac-teste.crl") -> PkiTeste:
    """Gera a hierarquia inteira (≈1 s). Cacheada por URL: os certificados são
    imutáveis e regenerá-los a cada teste só custaria tempo."""
    agora = datetime.now(UTC).replace(microsecond=0)
    inicio = agora - timedelta(days=30)
    raiz = _emitir(
        sujeito=_nome("AC Raiz de Teste do Despapelize"), chave=_chave(), emissor=None,
        inicio=inicio, fim=agora + timedelta(days=3650), ac=True, url_lcr=None,
    )
    ac = _emitir(
        sujeito=_nome("AC Intermediaria de Teste"), chave=_chave(), emissor=raiz,
        inicio=inicio, fim=agora + timedelta(days=1825), ac=True, url_lcr=None,
    )

    def folha(cn: str, *, fim: datetime | None = None, cpf: str | None = CPF_TESTE) -> Par:
        return _emitir(
            sujeito=_nome(f"{cn}:{cpf}" if cpf else cn), chave=_chave(), emissor=ac,
            inicio=inicio, fim=fim or agora + timedelta(days=365), ac=False,
            url_lcr=url_lcr, cpf=cpf,
        )

    signatario = folha(NOME_TESTE)
    revogado = folha("JOAO REVOGADO DE TESTE", cpf="98765432100")
    expira_logo = folha("ANA EXPIRA LOGO", fim=agora + timedelta(days=2), cpf="11144477735")
    sem_cpf = folha("PESSOA SEM CPF", cpf=None)
    tsa = _emitir(
        sujeito=_nome("ACT de Teste"), chave=_chave(), emissor=ac, inicio=inicio,
        fim=agora + timedelta(days=1825), ac=False, url_lcr=url_lcr,
        eku=[ExtendedKeyUsageOID.TIME_STAMPING],
    )

    lcr = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ac.cert.subject)
        .last_update(agora - timedelta(hours=1))
        .next_update(agora + timedelta(days=60))
        .add_revoked_certificate(
            x509.RevokedCertificateBuilder()
            .serial_number(revogado.cert.serial_number)
            .revocation_date(agora - timedelta(hours=2))
            .build()
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ac.chave.public_key()),
            critical=False,
        )
        .add_extension(x509.CRLNumber(1), critical=False)
        .sign(ac.chave, hashes.SHA256())
        .public_bytes(serialization.Encoding.DER)
    )

    raiz_estranha = _emitir(
        sujeito=_nome("AC Raiz Estranha", ou="Fora"), chave=_chave(), emissor=None,
        inicio=inicio, fim=agora + timedelta(days=3650), ac=True, url_lcr=None,
    )
    signatario_estranho = _emitir(
        sujeito=_nome("FORNECEDOR EXTERNO", ou="Fora"), chave=_chave(), emissor=raiz_estranha,
        inicio=inicio, fim=agora + timedelta(days=365), ac=False, url_lcr=None,
    )
    return PkiTeste(
        raiz=raiz, ac=ac, signatario=signatario, revogado=revogado, expira_logo=expira_logo,
        sem_cpf=sem_cpf, tsa=tsa, lcr=lcr, url_lcr=url_lcr, agora=agora,
        raiz_estranha=raiz_estranha, signatario_estranho=signatario_estranho,
    )


# --- PDFs --------------------------------------------------------------------


def pdf_simples(texto: str = "Documento de teste") -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, texto)
    return bytes(pdf.output())


def _signer(pki: PkiTeste, par: Par, cadeia: list[Par]) -> signers.SimpleSigner:
    chave = asn1_keys.PrivateKeyInfo.load(
        par.chave.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return signers.SimpleSigner(
        signing_cert=par.asn1,
        signing_key=chave,
        cert_registry=SimpleCertificateStore.from_certs([c.asn1 for c in cadeia]),
    )


def assinar(
    pki: PkiTeste,
    conteudo: bytes,
    *,
    par: Par | None = None,
    cadeia: list[Par] | None = None,
    carimbo: bool = False,
    campo: str = "Assinatura1",
) -> bytes:
    """Assina (revisão incremental) o PDF com o par dado, opcionalmente com
    carimbo de tempo da TSA de teste."""
    par = par or pki.signatario
    cadeia = cadeia if cadeia is not None else [pki.ac, pki.raiz]
    timestamper = None
    if carimbo:
        timestamper = timestamps.DummyTimeStamper(
            tsa_cert=pki.tsa.asn1,
            tsa_key=asn1_keys.PrivateKeyInfo.load(
                pki.tsa.chave.private_bytes(
                    serialization.Encoding.DER,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            ),
            certs_to_embed=SimpleCertificateStore.from_certs([pki.ac.asn1, pki.raiz.asn1]),
        )
    saida = io.BytesIO()
    signers.sign_pdf(
        IncrementalPdfFileWriter(io.BytesIO(conteudo)),
        signers.PdfSignatureMetadata(field_name=campo),
        signer=_signer(pki, par, cadeia),
        timestamper=timestamper,
        output=saida,
    )
    return saida.getvalue()


def adulterar(assinado: bytes) -> bytes:
    """Troca um byte do conteúdo coberto pela assinatura (o texto da página)."""
    alvo = b"Documento"
    i = assinado.find(alvo)
    if i < 0:  # conteúdo comprimido: troca um byte no meio do primeiro stream
        i = assinado.find(b"stream") + 20
    return assinado[:i] + bytes([assinado[i] ^ 0x01]) + assinado[i + 1 :]


def acrescentar_revisao(assinado: bytes) -> bytes:
    """Revisão incremental depois da assinatura: um campo de assinatura vazio
    novo (modificação que a assinatura anterior não cobre)."""
    w = IncrementalPdfFileWriter(io.BytesIO(assinado))
    fields.append_signature_field(
        w, fields.SigFieldSpec(sig_field_name="CampoPosterior", on_page=0, box=(10, 10, 60, 40))
    )
    saida = io.BytesIO()
    w.write(saida)
    return saida.getvalue()


def pdf_criptografado() -> bytes:
    from pyhanko.pdf_utils.crypt import StandardSecurityHandler
    from pyhanko.pdf_utils.writer import copy_into_new_writer
    from pyhanko.pdf_utils.reader import PdfFileReader

    w = copy_into_new_writer(PdfFileReader(io.BytesIO(pdf_simples())))
    w.security_handler = StandardSecurityHandler.build_from_pw("senha-secreta")
    w._assign_security_handler(w.security_handler)
    saida = io.BytesIO()
    w.write(saida)
    return saida.getvalue()


def pdfs_e2e(pki: PkiTeste) -> dict[str, bytes]:
    """Os arquivos usados pelo spec Playwright 20-verificacao-assinatura."""
    valido = assinar(pki, pdf_simples("Contrato assinado de teste"))
    return {
        "assinado-valido.pdf": valido,
        "assinado-adulterado.pdf": adulterar(valido),
        "sem-assinatura.pdf": pdf_simples("Documento sem assinatura"),
    }


# --- servidor para o Playwright -----------------------------------------------


def _gravar(pki: PkiTeste, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "raiz-teste.pem").write_bytes(pki.raiz.pem)
    (saida / "ac-teste.crl").write_bytes(pki.lcr)
    for nome, conteudo in pdfs_e2e(pki).items():
        (saida / nome).write_bytes(conteudo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--porta", type=int, default=PORTA_PADRAO)
    args = parser.parse_args()
    pki = gerar_pki(f"http://127.0.0.1:{args.porta}/ac-teste.crl")
    _gravar(pki, args.saida)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.saida))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.porta), handler) as srv:
        print(f"PKI de teste em {args.saida}, servida em http://127.0.0.1:{args.porta}/", flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
