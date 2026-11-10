"""Serviço de verificação de assinatura — change assinatura-verificacao-fundacao.

Um teste por veredito (D2), extração de dados (D6), orçamento de rede (D3),
âncoras com falha fechada (D5) e âncora de teste só com a flag (D8). Tudo
offline: PKI descartável de `scripts/pki_teste.py`, LCR pré-carregada,
`permitir_busca=False`. **Prova o fluxo, não conformidade ICP-Brasil.**
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import UTC, datetime, timedelta

import pytest

from app.config import Settings
from app.schemas.verificacao_assinatura import OrigemDataAssinatura, SituacaoVerificacao
from app.schemas.verificacao_assinatura import VereditoAssinatura as V
from app.services import verificacao_assinatura as va
from scripts import pki_teste as pt


@pytest.fixture(scope="module")
def pki():
    return pt.gerar_pki()


def _verificar(pki, pdf, *, agora=None, crls=None, ancoras="teste", **kw):
    if ancoras == "teste":
        ancoras = [pki.raiz.asn1]
    return va.verificar_pdf(
        pdf,
        documento_id="doc-teste",
        ancoras=ancoras,
        agora=agora,
        crls=[pki.lcr] if crls is None else crls,
        permitir_busca=False,
        **kw,
    )


# --- vereditos (D2) -----------------------------------------------------------


def test_assinatura_valida_e_documento_integro(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples()))

    assert r.situacao == SituacaoVerificacao.ASSINADO
    assert r.resumo == V.VALIDA
    [a] = r.assinaturas
    assert a.veredito == V.VALIDA
    assert a.mensagem == "Assinatura válida — documento íntegro"
    assert a.signatario_nome == pt.NOME_TESTE
    assert a.signatario_cpf == pt.CPF_TESTE
    assert a.autoridade_certificadora == "AC Intermediaria de Teste"
    assert a.origem_data == OrigemDataAssinatura.DECLARADA
    assert a.data_assinatura is not None
    assert r.url_verificador_oficial == "https://validar.iti.gov.br"
    assert r.aviso_veredito_oficial == va.MSG_AVISO_OFICIAL


def test_documento_adulterado_e_invalido(pki):
    r = _verificar(pki, pt.adulterar(pt.assinar(pki, pt.pdf_simples())))

    assert r.resumo == V.INVALIDA
    assert r.assinaturas[0].mensagem == (
        "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado"
    )


def test_certificado_revogado_e_invalido(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples(), par=pki.revogado))

    assert r.resumo == V.INVALIDA
    assert r.assinaturas[0].signatario_cpf == "98765432100"


def test_cadeia_fora_da_icp_brasil(pki):
    pdf = pt.assinar(pki, pt.pdf_simples(), par=pki.signatario_estranho, cadeia=[pki.raiz_estranha])

    r = _verificar(pki, pdf)

    assert r.resumo == V.FORA_ICP_BRASIL
    a = r.assinaturas[0]
    assert a.mensagem == (
        "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil — "
        "não é uma assinatura qualificada."
    )
    assert a.signatario_nome == "FORNECEDOR EXTERNO"
    assert a.autoridade_certificadora == "AC Raiz Estranha"


def test_revogacao_indisponivel_e_inconclusiva_nunca_valida(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples()), crls=[])

    assert r.resumo == V.INCONCLUSIVA
    assert r.assinaturas[0].mensagem.startswith("Verificação inconclusiva — não foi possível")


def test_lcr_vencida_e_inconclusiva(pki):
    # Depois do next_update da LCR (60 dias), ela não serve mais como prova.
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples()), agora=pki.agora + timedelta(days=90))

    assert r.resumo == V.INCONCLUSIVA


def test_ancoras_indisponiveis_tornam_tudo_inconclusivo(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples()), ancoras=None)

    assert r.resumo == V.INCONCLUSIVA
    assert r.assinaturas[0].signatario_nome == pt.NOME_TESTE  # dados ainda exibidos


def test_alteracao_posterior_a_assinatura(pki):
    r = _verificar(pki, pt.acrescentar_revisao(pt.assinar(pki, pt.pdf_simples())))

    assert r.resumo == V.ALTERADA_APOS_ASSINATURA
    assert r.assinaturas[0].mensagem == va.MSG_ALTERADA_APOS


def test_coassinatura_nao_e_alteracao_posterior(pki):
    uma = pt.assinar(pki, pt.pdf_simples())
    duas = pt.assinar(pki, uma, par=pki.sem_cpf, campo="Assinatura2")

    r = _verificar(pki, duas)

    assert [a.veredito for a in r.assinaturas] == [V.VALIDA, V.VALIDA]
    assert [a.ordem for a in r.assinaturas] == [1, 2]


def test_duas_assinaturas_resumo_e_a_pior(pki):
    uma = pt.assinar(pki, pt.pdf_simples())
    duas = pt.assinar(pki, uma, par=pki.revogado, campo="Assinatura2")

    r = _verificar(pki, duas)

    assert [a.veredito for a in r.assinaturas] == [V.VALIDA, V.INVALIDA]
    assert r.resumo == V.INVALIDA
    assert r.mensagem_resumo == va.MSG_INVALIDA


# --- data, carimbo e expiração (D6, US 4.2 Cen.3) ----------------------------


def test_carimbo_de_tempo_define_a_data(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples(), carimbo=True))

    a = r.assinaturas[0]
    assert a.veredito == V.VALIDA
    assert a.origem_data == OrigemDataAssinatura.CARIMBO
    assert a.autoridade_carimbo == "ACT de Teste"


def test_expirado_com_carimbo_anterior_e_valido_na_data(pki):
    pdf = pt.assinar(pki, pt.pdf_simples(), par=pki.expira_logo, carimbo=True)

    r = _verificar(pki, pdf, agora=pki.agora + timedelta(days=10))

    a = r.assinaturas[0]
    assert a.veredito == V.VALIDA
    data = va.formatar_data(pki.expira_logo.cert.not_valid_after_utc).split(" ")[0]
    assert a.mensagem == (
        f"Assinatura válida — documento íntegro. Certificado expirado em {data}, "
        "mas válido na data da assinatura."
    )
    assert a.certificado_expirado_em is not None


def test_expirado_sem_carimbo_e_inconclusivo(pki):
    pdf = pt.assinar(pki, pt.pdf_simples(), par=pki.expira_logo)

    r = _verificar(pki, pdf, agora=pki.agora + timedelta(days=10))

    a = r.assinaturas[0]
    assert a.veredito == V.INCONCLUSIVA
    data = va.formatar_data(pki.expira_logo.cert.not_valid_after_utc).split(" ")[0]
    assert a.mensagem == (
        f"Verificação inconclusiva — o certificado expirou em {data} e o documento não tem "
        "carimbo de tempo que comprove a data da assinatura."
    )


def test_certificado_sem_cpf(pki):
    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples(), par=pki.sem_cpf))

    assert r.assinaturas[0].signatario_cpf is None
    assert r.assinaturas[0].signatario_nome == "PESSOA SEM CPF"


def test_data_formatada_no_horario_de_brasilia():
    assert va.formatar_data(datetime(2026, 11, 10, 2, 30, tzinfo=UTC)) == "09/11/2026 23:30"


# --- sem assinatura / ilegível (D2) ------------------------------------------


def test_pdf_sem_assinatura(pki):
    r = _verificar(pki, pt.pdf_simples())

    assert r.situacao == SituacaoVerificacao.SEM_ASSINATURA
    assert r.mensagem_resumo == "Este documento não contém assinatura digital."
    assert r.assinaturas == []
    assert r.resumo is None
    assert r.url_verificador_oficial is None


@pytest.mark.parametrize("pdf", [b"%PDF-1.4\nlixo sem estrutura", None], ids=["corrompido", "senha"])
def test_pdf_ilegivel(pki, pdf):
    r = _verificar(pki, pdf or pt.pdf_criptografado())

    assert r.situacao == SituacaoVerificacao.ILEGIVEL
    assert r.mensagem_resumo == va.MSG_ILEGIVEL
    assert r.assinaturas == []


# --- orçamento de rede (D3) --------------------------------------------------


def test_teto_de_tempo_resulta_em_inconclusiva(pki, monkeypatch):
    async def lento(*_a, **_kw):
        import asyncio

        await asyncio.sleep(5)

    monkeypatch.setattr(va, "async_validate_pdf_signature", lento)
    inicio = time.monotonic()

    r = _verificar(pki, pt.assinar(pki, pt.pdf_simples()), teto_segundos=0.5)

    assert time.monotonic() - inicio < 3
    assert r.resumo == V.INCONCLUSIVA


def test_cache_de_revogacao_e_reutilizado_e_expira(monkeypatch):
    va.limpar_cache_revogacao()
    f1 = va._fetchers_compartilhados()
    assert va._fetchers_compartilhados() is f1
    relogio = time.monotonic() + va.TTL_CACHE_REVOGACAO_S + 1
    monkeypatch.setattr(va.time, "monotonic", lambda: relogio)
    assert va._fetchers_compartilhados() is not f1
    va.limpar_cache_revogacao()


# --- LGPD: nada do signatário em log (D4) ------------------------------------


def test_nenhum_log_contem_cpf_ou_nome(pki, caplog):
    caplog.set_level(logging.DEBUG)
    pdfs = [
        pt.assinar(pki, pt.pdf_simples(), par=pki.revogado),
        pt.assinar(pki, pt.pdf_simples()),
    ]
    for pdf in pdfs:
        _verificar(pki, pdf, crls=[])
        _verificar(pki, pdf)

    texto = caplog.text
    for dado in (pt.CPF_TESTE, "98765432100", pt.NOME_TESTE, "JOAO REVOGADO"):
        assert dado not in texto


# --- âncoras (D5, D8) --------------------------------------------------------


def test_ancoras_icp_brasil_carregam_integras():
    ancoras = va.carregar_ancoras_icp_brasil()

    nomes = {a.subject.native["common_name"] for a in ancoras}
    assert "Autoridade Certificadora Raiz Brasileira v5" in nomes
    assert len(ancoras) == len(json.loads((va.DIR_ANCORAS_ICP_BRASIL / "MANIFESTO.json").read_text())["ancoras"])
    assert not any("Governo Federal" in n for n in nomes)


def _copia_ancoras(tmp_path):
    destino = tmp_path / "icp"
    shutil.copytree(va.DIR_ANCORAS_ICP_BRASIL, destino)
    return destino


def test_ancora_adulterada_invalida_o_conjunto_inteiro(tmp_path):
    d = _copia_ancoras(tmp_path)
    alvo = d / "ICP-Brasilv5.crt"
    alvo.write_bytes(alvo.read_bytes().replace(b"A", b"B", 1))

    with pytest.raises(va.AncorasIndisponiveis):
        va.carregar_ancoras_icp_brasil(d)


def test_ancora_faltando_invalida_o_conjunto_inteiro(tmp_path):
    d = _copia_ancoras(tmp_path)
    (d / "ICP-Brasilv10.crt").unlink()

    with pytest.raises(va.AncorasIndisponiveis):
        va.carregar_ancoras_icp_brasil(d)


def test_nenhuma_ancora_vence_em_menos_de_180_dias():
    """Rotação de AC Raiz não pode ser descoberta em produção (D5)."""
    manifesto = json.loads((va.DIR_ANCORAS_ICP_BRASIL / "MANIFESTO.json").read_text())
    limite = datetime.now(UTC) + timedelta(days=180)
    vencendo = [
        a["arquivo"] for a in manifesto["ancoras"] if datetime.fromisoformat(a["not_after"]) < limite
    ]
    assert vencendo == [], f"Âncoras a menos de 180 dias do vencimento: {vencendo} — rotacionar."


def test_ancora_de_teste_ignorada_sem_a_flag(pki, tmp_path):
    pem = tmp_path / "raiz.pem"
    pem.write_bytes(pki.raiz.pem)
    sem_flag = Settings(DEV_TRUST_ANCHOR_TESTE=False, DEV_TRUST_ANCHOR_PATH=str(pem))
    com_flag = Settings(DEV_TRUST_ANCHOR_TESTE=True, DEV_TRUST_ANCHOR_PATH=str(pem))

    ancoras_sem = va.ancoras_para(sem_flag)
    ancoras_com = va.ancoras_para(com_flag)

    assert pki.raiz.asn1.sha256 not in {a.sha256 for a in ancoras_sem}
    assert len(ancoras_com) == len(ancoras_sem) + 1
    pdf = pt.assinar(pki, pt.pdf_simples())
    assert _verificar(pki, pdf, ancoras=ancoras_sem).resumo == V.FORA_ICP_BRASIL
    assert _verificar(pki, pdf, ancoras=ancoras_com).resumo == V.VALIDA


def test_ancoras_indisponiveis_logam_erro_sem_dado_pessoal(monkeypatch, caplog):
    def falha():
        raise va.AncorasIndisponiveis("hash divergente: ICP-Brasilv5.crt")

    monkeypatch.setattr(va, "_ancoras_icp_brasil_em_cache", falha)
    with caplog.at_level(logging.ERROR, logger=va.__name__):
        assert va.ancoras_para(Settings()) is None
    assert "Âncoras ICP-Brasil indisponíveis" in caplog.text
