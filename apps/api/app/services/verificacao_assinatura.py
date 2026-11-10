"""Verificação de assinaturas digitais embutidas em PDF (Épico 4, US 4.2).

Change assinatura-verificacao-fundacao. Valida **localmente**, com pyHanko +
pyhanko-certvalidator (D3): integridade criptográfica, cobertura do arquivo,
cadeia até as âncoras ICP-Brasil versionadas (D5), revogação (LCR/OCSP em
hard-fail) e carimbo de tempo quando presente. Não valida política de
assinatura ICP-Brasil (LPA/DOC-ICP-15.03) — o veredito oficial é o do VALIDAR do
ITI, para onde a tela aponta (D7).

A verificação é **efêmera** (D4): o resultado — inclusive nome e CPF extraídos
do certificado, quase sempre de terceiros — vive só no valor devolvido. Nada é
gravado em banco, cache de resultado ou log; os loggers do pyHanko são
silenciados porque registram o CN do certificado (que, na ICP-Brasil, contém o
CPF) em todo erro de validação.
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import io
import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from pyhanko.pdf_utils.misc import PdfReadError
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.diff_analysis import ModificationLevel
from pyhanko.sign.validation.errors import SignatureValidationError
from pyhanko.sign.validation import async_validate_pdf_signature
from pyhanko.sign.validation.status import PdfSignatureStatus, SignatureCoverageLevel
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.fetchers.api import Fetchers
from pyhanko_certvalidator.fetchers.requests_fetchers import RequestsFetcherBackend
from pyhanko.sign.ades.report import AdESIndeterminate

from app.config import Settings
from app.schemas.verificacao_assinatura import (
    AssinaturaVerificada,
    OrigemDataAssinatura,
    ResultadoVerificacaoResponse,
    SituacaoVerificacao,
    VereditoAssinatura,
)

logger = logging.getLogger(__name__)

# Dados do signatário nunca vão para log (D4): pyHanko/certvalidator logam o
# CN do certificado — "NOME:CPF" na ICP-Brasil — com traceback a cada falha.
for _nome_logger in ("pyhanko", "pyhanko_certvalidator"):
    logging.getLogger(_nome_logger).setLevel(logging.CRITICAL + 1)

# --- Mensagens (spec verificacao-assinatura; PRD US 4.2) -----------------------

MSG_VALIDA = "Assinatura válida — documento íntegro"
MSG_SUFIXO_EXPIRADO = "Certificado expirado em {data}, mas válido na data da assinatura."
MSG_INVALIDA = "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado"
MSG_INCONCLUSIVA = (
    "Verificação inconclusiva — não foi possível confirmar agora a situação do certificado. "
    "Tente novamente mais tarde ou confira no verificador oficial do ITI."
)
MSG_INCONCLUSIVA_EXPIRADO = (
    "Verificação inconclusiva — o certificado expirou em {data} e o documento não tem "
    "carimbo de tempo que comprove a data da assinatura."
)
MSG_FORA_ICP_BRASIL = (
    "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil — "
    "não é uma assinatura qualificada."
)
MSG_ALTERADA_APOS = (
    "Assinatura válida, mas o documento recebeu alterações depois de assinado. "
    "As alterações posteriores não estão cobertas pela assinatura."
)
MSG_SEM_ASSINATURA = "Este documento não contém assinatura digital."
MSG_ILEGIVEL = (
    "Não foi possível ler as assinaturas deste documento. "
    "O arquivo pode estar corrompido ou protegido por senha."
)
MSG_VERIFICACAO_SOMENTE_PDF = "A verificação de assinatura está disponível apenas para documentos PDF."
MSG_AVISO_OFICIAL = (
    "Esta conferência é feita pelo Despapelize e não substitui o verificador oficial. "
    "Para o veredito oficial, envie o arquivo ao Verificador de Conformidade do ITI."
)
URL_VERIFICADOR_OFICIAL = "https://validar.iti.gov.br"

# Gravidade para o resumo do documento (D2): o pior veredito vence.
_GRAVIDADE = {
    VereditoAssinatura.VALIDA: 0,
    VereditoAssinatura.ALTERADA_APOS_ASSINATURA: 1,
    VereditoAssinatura.FORA_ICP_BRASIL: 2,
    VereditoAssinatura.INCONCLUSIVA: 3,
    VereditoAssinatura.INVALIDA: 4,
}

# Datas exibidas no horário de Brasília (D6). Offset fixo: o Brasil não tem
# horário de verão desde 2019, e evita depender de tzdata na imagem slim.
_BRT = timezone(timedelta(hours=-3), "BRT")

OID_ICP_PESSOA_FISICA = "2.16.76.1.3.1"

# Orçamento de rede (D3).
TIMEOUT_POR_REQUISICAO_S = 5
TETO_POR_VERIFICACAO_S = 15
# Cache de LCR/OCSP em memória do processo (dado público, não pessoal — D3/D4).
# TTL curto: o validador recusa LCR vencida, e um cache eterno prenderia a
# instância num veredito "inconclusiva" até o próximo restart.
TTL_CACHE_REVOGACAO_S = 3600


# --- Âncoras de confiança (D5) ------------------------------------------------

DIR_ANCORAS_ICP_BRASIL = Path(__file__).resolve().parent.parent / "trust" / "icp_brasil"


class AncorasIndisponiveis(Exception):
    """O conjunto de âncoras ICP-Brasil não confere com o manifesto (D5)."""


def _ler_certificado(dados: bytes) -> asn1_x509.Certificate:
    if dados.lstrip().startswith(b"-----BEGIN"):
        dados = x509.load_pem_x509_certificate(dados).public_bytes(serialization.Encoding.DER)
    return asn1_x509.Certificate.load(dados)


def carregar_ancoras_icp_brasil(diretorio: Path = DIR_ANCORAS_ICP_BRASIL) -> list[asn1_x509.Certificate]:
    """Lê as âncoras e confere cada uma contra o SHA-256 do `MANIFESTO.json`.
    Falha fechada (D5): qualquer arquivo ausente ou divergente invalida o
    conjunto inteiro — nunca devolve um subconjunto."""
    try:
        manifesto = json.loads((diretorio / "MANIFESTO.json").read_text(encoding="utf-8"))
        ancoras = []
        for item in manifesto["ancoras"]:
            dados = (diretorio / item["arquivo"]).read_bytes()
            if hashlib.sha256(dados).hexdigest() != item["sha256"]:
                raise AncorasIndisponiveis(f"hash divergente: {item['arquivo']}")
            ancoras.append(_ler_certificado(dados))
    except AncorasIndisponiveis:
        raise
    except (OSError, ValueError, KeyError) as exc:
        raise AncorasIndisponiveis(f"{type(exc).__name__}: {exc}") from exc
    if not ancoras:
        raise AncorasIndisponiveis("manifesto sem âncoras")
    return ancoras


@functools.lru_cache(maxsize=1)
def _ancoras_icp_brasil_em_cache() -> tuple[asn1_x509.Certificate, ...]:
    """Lazy na primeira verificação (estudo §7f): não pesa no cold start."""
    return tuple(carregar_ancoras_icp_brasil())


def ancoras_para(settings: Settings) -> list[asn1_x509.Certificate] | None:
    """Âncoras efetivas: ICP-Brasil (manifesto) + a âncora de teste, só com a
    flag dev/E2E (D8). `None` = âncoras indisponíveis → tudo inconclusivo."""
    try:
        ancoras = list(_ancoras_icp_brasil_em_cache())
    except AncorasIndisponiveis as exc:
        # Sem dado pessoal: só o motivo técnico (D4).
        logger.error("Âncoras ICP-Brasil indisponíveis — verificação inconclusiva: %s", exc)
        return None
    if settings.dev_trust_anchor_teste and settings.dev_trust_anchor_path:
        ancoras.append(_ler_certificado(Path(settings.dev_trust_anchor_path).read_bytes()))
    return ancoras


# --- Busca de revogação (D3) --------------------------------------------------

_lock_fetchers = threading.Lock()
_fetchers_cache: tuple[float, Fetchers] | None = None


def _fetchers_compartilhados() -> Fetchers:
    global _fetchers_cache
    with _lock_fetchers:
        agora = time.monotonic()
        if _fetchers_cache is None or agora - _fetchers_cache[0] > TTL_CACHE_REVOGACAO_S:
            backend = RequestsFetcherBackend(per_request_timeout=TIMEOUT_POR_REQUISICAO_S)
            _fetchers_cache = (agora, backend.get_fetchers())
        return _fetchers_cache[1]


def limpar_cache_revogacao() -> None:
    global _fetchers_cache
    with _lock_fetchers:
        _fetchers_cache = None


# --- Extração de dados do certificado (D6) ------------------------------------


def _cn(nome: x509.Name) -> str | None:
    attrs = nome.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    return str(attrs[0].value) if attrs else None


def _conteudo_der_texto(der: bytes) -> bytes | None:
    """Conteúdo de OCTET STRING / PrintableString / UTF8String / IA5String."""
    if len(der) < 2 or der[0] not in (0x04, 0x13, 0x0C, 0x16):
        return None
    tamanho, inicio = der[1], 2
    if tamanho & 0x80:
        n = tamanho & 0x7F
        tamanho, inicio = int.from_bytes(der[2 : 2 + n], "big"), 2 + n
    return der[inicio : inicio + tamanho]


def extrair_cpf(cert: x509.Certificate) -> str | None:
    """CPF do `otherName` ICP-Brasil 2.16.76.1.3.1: posições 9–19 do valor
    (as 8 primeiras são a data de nascimento) (D6)."""
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        return None
    for outro in san.get_values_for_type(x509.OtherName):
        if outro.type_id.dotted_string != OID_ICP_PESSOA_FISICA:
            continue
        conteudo = _conteudo_der_texto(outro.value)
        if conteudo is None:
            return None
        cpf = conteudo[8:19].decode("ascii", "ignore")
        return cpf if re.fullmatch(r"\d{11}", cpf) and cpf != "0" * 11 else None
    return None


def _nome_signatario(cert: x509.Certificate) -> str | None:
    cn = _cn(cert.subject)
    # Perfis ICP-Brasil usam "NOME:CPF" no CN — o sufixo não é parte do nome.
    return re.sub(r":\d{11,14}$", "", cn) if cn else None


def formatar_data(dt: datetime) -> str:
    return dt.astimezone(_BRT).strftime("%d/%m/%Y %H:%M")


# --- Classificação (D2) -------------------------------------------------------


@dataclass
class _Classificada:
    veredito: VereditoAssinatura
    mensagem: str
    data: datetime | None
    origem: OrigemDataAssinatura
    act: str | None
    expirado_em: datetime | None


def _carimbo_confiavel(status: PdfSignatureStatus) -> bool:
    ts = status.timestamp_validity
    return bool(ts and ts.intact and ts.valid and ts.trusted)


def _cobre_ate_o_fim(status: PdfSignatureStatus, *, ultima_cobre_tudo: bool, eh_ultima: bool) -> bool:
    """A assinatura cobre o arquivo — ou só lhe seguem outras assinaturas.

    Coassinar acrescenta uma revisão, então a 1ª assinatura de um PDF com duas
    nunca cobre `ENTIRE_FILE`; isso não é "alteração posterior". Só é quando a
    última assinatura não cobre o fim do arquivo, ou quando o que veio depois
    vai além de preenchimento de formulário/assinatura (anotações, páginas)."""
    if status.coverage == SignatureCoverageLevel.ENTIRE_FILE:
        return True
    if eh_ultima or not ultima_cobre_tudo:
        return False
    nivel = status.modification_level
    return nivel is not None and nivel <= ModificationLevel.FORM_FILLING


async def _classificar(
    sig,
    status: PdfSignatureStatus,
    *,
    contexto_em,
    ultima_cobre_tudo: bool,
    eh_ultima: bool,
    agora: datetime,
) -> _Classificada:
    """Ordem de avaliação fixa (D2) — a primeira regra que casa decide."""
    carimbo = _carimbo_confiavel(status)
    if carimbo:
        data, origem = status.timestamp_validity.timestamp, OrigemDataAssinatura.CARIMBO
        act = _cn(x509.load_der_x509_certificate(status.timestamp_validity.signing_cert.dump()).subject)
    else:
        data, origem, act = status.signer_reported_dt, OrigemDataAssinatura.DECLARADA, None

    def c(veredito, mensagem, expirado_em=None):
        return _Classificada(veredito, mensagem, data, origem, act, expirado_em)

    if not (status.intact and status.valid):
        return c(VereditoAssinatura.INVALIDA, MSG_INVALIDA)
    indicacao = status.trust_problem_indic
    if status.revoked or indicacao == AdESIndeterminate.REVOKED_NO_POE:
        return c(VereditoAssinatura.INVALIDA, MSG_INVALIDA)
    if indicacao == AdESIndeterminate.NO_CERTIFICATE_CHAIN_FOUND:
        return c(VereditoAssinatura.FORA_ICP_BRASIL, MSG_FORA_ICP_BRASIL)

    expirado_em = None
    if indicacao == AdESIndeterminate.OUT_OF_BOUNDS_NO_POE:
        not_after = status.signing_cert["tbs_certificate"]["validity"]["not_after"].native
        if not_after > agora:  # fora do prazo por outro motivo (ex.: ainda não válido)
            return c(VereditoAssinatura.INCONCLUSIVA, MSG_INCONCLUSIVA)
        data_exp = formatar_data(not_after).split(" ")[0]
        if not (carimbo and status.timestamp_validity.timestamp < not_after):
            return c(VereditoAssinatura.INCONCLUSIVA, MSG_INCONCLUSIVA_EXPIRADO.format(data=data_exp))
        # Revalida no momento comprovado pelo carimbo (US 4.2 Cen.3).
        status = await async_validate_pdf_signature(
            sig, contexto_em(status.timestamp_validity.timestamp)
        )
        if status.revoked or status.trust_problem_indic == AdESIndeterminate.REVOKED_NO_POE:
            return c(VereditoAssinatura.INVALIDA, MSG_INVALIDA)
        if not status.trusted:
            return c(VereditoAssinatura.INCONCLUSIVA, MSG_INCONCLUSIVA)
        expirado_em = not_after
        indicacao = None

    if indicacao is not None or not status.trusted:
        # Revogação indeterminável, cadeia com falha geral, restrição etc.
        return c(VereditoAssinatura.INCONCLUSIVA, MSG_INCONCLUSIVA)
    if not _cobre_ate_o_fim(status, ultima_cobre_tudo=ultima_cobre_tudo, eh_ultima=eh_ultima):
        return c(VereditoAssinatura.ALTERADA_APOS_ASSINATURA, MSG_ALTERADA_APOS, expirado_em)
    if expirado_em is not None:
        sufixo = MSG_SUFIXO_EXPIRADO.format(data=formatar_data(expirado_em).split(" ")[0])
        return c(VereditoAssinatura.VALIDA, f"{MSG_VALIDA}. {sufixo}", expirado_em)
    return c(VereditoAssinatura.VALIDA, MSG_VALIDA)


def _resumo_mensagem(veredito: VereditoAssinatura, assinaturas: list[AssinaturaVerificada]) -> str:
    return next(a.mensagem for a in assinaturas if a.veredito == veredito)


# --- Entrada pública ----------------------------------------------------------


def verificar_pdf(
    conteudo: bytes,
    *,
    documento_id: str,
    ancoras: list[asn1_x509.Certificate] | None,
    agora: datetime | None = None,
    crls: list[bytes] | None = None,
    ocsps: list[bytes] | None = None,
    permitir_busca: bool = True,
    fetchers: Fetchers | None = None,
    teto_segundos: float = TETO_POR_VERIFICACAO_S,
) -> ResultadoVerificacaoResponse:
    """Verifica todas as assinaturas do PDF. `crls`/`ocsps`/`permitir_busca`
    existem para os testes rodarem offline (D8); em produção a revogação é
    buscada online, com o orçamento de rede de D3."""
    return asyncio.run(
        _verificar_pdf(
            conteudo,
            documento_id=documento_id,
            ancoras=ancoras,
            agora=agora or datetime.now(UTC),
            crls=crls or [],
            ocsps=ocsps or [],
            permitir_busca=permitir_busca,
            fetchers=fetchers,
            teto_segundos=teto_segundos,
        )
    )


async def _verificar_pdf(
    conteudo: bytes,
    *,
    documento_id: str,
    ancoras,
    agora: datetime,
    crls,
    ocsps,
    permitir_busca: bool,
    fetchers: Fetchers | None,
    teto_segundos: float,
) -> ResultadoVerificacaoResponse:
    def resultado(situacao, resumo, mensagem, assinaturas):
        com_assinatura = situacao == SituacaoVerificacao.ASSINADO
        return ResultadoVerificacaoResponse(
            documento_id=documento_id,
            situacao=situacao,
            resumo=resumo,
            mensagem_resumo=mensagem,
            assinaturas=assinaturas,
            aviso_veredito_oficial=MSG_AVISO_OFICIAL if com_assinatura else None,
            url_verificador_oficial=URL_VERIFICADOR_OFICIAL if com_assinatura else None,
        )

    try:
        leitor = PdfFileReader(io.BytesIO(conteudo), strict=False)
        if leitor.encrypted:
            return resultado(SituacaoVerificacao.ILEGIVEL, None, MSG_ILEGIVEL, [])
        assinaturas_pdf = sorted(leitor.embedded_signatures, key=lambda s: s.signed_revision)
    except (PdfReadError, ValueError, KeyError, TypeError, IndexError) as exc:
        logger.info("PDF ilegível na verificação (documento %s): %s", documento_id, type(exc).__name__)
        return resultado(SituacaoVerificacao.ILEGIVEL, None, MSG_ILEGIVEL, [])
    if not assinaturas_pdf:
        return resultado(SituacaoVerificacao.SEM_ASSINATURA, None, MSG_SEM_ASSINATURA, [])

    if permitir_busca and fetchers is None:
        fetchers = _fetchers_compartilhados()

    def contexto_em(momento: datetime) -> ValidationContext:
        return ValidationContext(
            trust_roots=ancoras or [],
            moment=momento,
            crls=crls,
            ocsps=ocsps,
            allow_fetching=permitir_busca,
            fetchers=fetchers if permitir_busca else None,
            revocation_mode="hard-fail",
            retroactive_revinfo=True,
        )

    prazo = time.monotonic() + teto_segundos
    status_por_sig: list[PdfSignatureStatus | None] = []
    for sig in assinaturas_pdf:
        restante = prazo - time.monotonic()
        status = None
        if ancoras is not None and restante > 0:
            try:
                status = await asyncio.wait_for(
                    async_validate_pdf_signature(sig, contexto_em(agora)), timeout=restante
                )
            except TimeoutError:
                logger.warning("Verificação excedeu o orçamento de rede (documento %s)", documento_id)
            except (SignatureValidationError, ValueError, KeyError, TypeError) as exc:
                logger.info("Falha ao validar assinatura (documento %s): %s", documento_id, type(exc).__name__)
        status_por_sig.append(status)

    ultimo = status_por_sig[-1]
    ultima_cobre_tudo = bool(ultimo and ultimo.coverage == SignatureCoverageLevel.ENTIRE_FILE)

    assinaturas: list[AssinaturaVerificada] = []
    for ordem, (sig, status) in enumerate(zip(assinaturas_pdf, status_por_sig, strict=True), start=1):
        cert = x509.load_der_x509_certificate(sig.signer_cert.dump())
        if status is None:
            classificada = _Classificada(
                VereditoAssinatura.INCONCLUSIVA, MSG_INCONCLUSIVA, None,
                OrigemDataAssinatura.DECLARADA, None, None,
            )
            try:
                classificada.data = sig.self_reported_timestamp
            except (ValueError, KeyError, TypeError):
                pass
        else:
            classificada = await _classificar(
                sig, status, contexto_em=contexto_em, ultima_cobre_tudo=ultima_cobre_tudo,
                eh_ultima=ordem == len(assinaturas_pdf), agora=agora,
            )
        assinaturas.append(
            AssinaturaVerificada(
                ordem=ordem,
                veredito=classificada.veredito,
                mensagem=classificada.mensagem,
                signatario_nome=_nome_signatario(cert),
                signatario_cpf=extrair_cpf(cert),
                autoridade_certificadora=_cn(cert.issuer),
                data_assinatura=classificada.data,
                origem_data=classificada.origem,
                autoridade_carimbo=classificada.act,
                certificado_expirado_em=classificada.expirado_em,
            )
        )

    pior = max((a.veredito for a in assinaturas), key=_GRAVIDADE.__getitem__)
    return resultado(SituacaoVerificacao.ASSINADO, pior, _resumo_mensagem(pior, assinaturas), assinaturas)
