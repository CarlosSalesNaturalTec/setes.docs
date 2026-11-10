"""Endpoint `GET …/documentos/{id}/verificacao` — change assinatura-verificacao-fundacao.

Regra de acesso de leitura (D1, G2) com "acesso negado" explícito, só PDF,
não persistência (D4, LGPD) e ausência de rota pública (G1). A LCR da PKI de
teste é servida por um HTTP local em porta aleatória — o endpoint usa o mesmo
caminho de busca online de produção, sem sair da máquina.
"""

from __future__ import annotations

import functools
import http.server
import logging
import threading

import pytest
from sqlalchemy import func, inspect, select, text

from app.config import Settings
from app.db.models import Documento, LogSeguranca, TipoEventoLog, Tramitacao
from app.services import verificacao_assinatura as va
from scripts import pki_teste as pt
from tests.helpers_processo import auth, enviar_para, login, servidor_com_setor, tipo_processo, unidade, usuario


@pytest.fixture(scope="module")
def servidor_lcr(tmp_path_factory):
    diretorio = tmp_path_factory.mktemp("lcr")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(diretorio))
    handler.log_message = lambda *_a, **_kw: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/ac-teste.crl"
    pki = pt.gerar_pki(url)
    (diretorio / "ac-teste.crl").write_bytes(pki.lcr)
    (diretorio / "raiz.pem").write_bytes(pki.raiz.pem)
    yield pki, diretorio / "raiz.pem"
    srv.shutdown()


@pytest.fixture
def settings(servidor_lcr) -> Settings:
    """Sobrepõe a fixture do conftest: liga a âncora de teste (D8)."""
    _pki, raiz = servidor_lcr
    va.limpar_cache_revogacao()
    return Settings(
        TASKS_INVOKER_SA_EMAIL="sa-tasks-invoker@proj.iam.gserviceaccount.com",
        OIDC_AUDIENCE="https://api.example.run.app",
        SENDGRID_API_KEY="",
        DEV_TRUST_ANCHOR_TESTE=True,
        DEV_TRUST_ANCHOR_PATH=str(raiz),
    )


@pytest.fixture
def pki(servidor_lcr):
    return servidor_lcr[0]


def _processo(client, db, sufixo="a"):
    cofin = unidade(db, f"COFIN-{sufixo}")
    tipo = tipo_processo(db, f"Tipo-{sufixo}")
    criador, _ = servidor_com_setor(db, cofin, email=f"dono-{sufixo}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Contrato", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"], token, cofin


def _anexar(client, token, proc_id, nome, conteudo, mime="application/pdf"):
    resp = client.post(
        f"/processos/{proc_id}/documentos", headers=auth(token), files={"arquivo": (nome, conteudo, mime)}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _verificar(client, token, proc_id, doc_id):
    return client.get(f"/processos/{proc_id}/documentos/{doc_id}/verificacao", headers=auth(token))


class _StorageEspiao:
    """Registra se o conteúdo foi lido — acesso negado não pode chegar ao storage."""

    def __init__(self, real):
        self.real, self.aberturas = real, 0

    def abrir(self, chave):
        self.aberturas += 1
        return self.real.abrir(chave)

    def __getattr__(self, nome):
        return getattr(self.real, nome)


@pytest.fixture
def espiao(monkeypatch):
    from app.routers import documentos as router

    original = router.get_storage
    espiao = None

    def fabrica(settings):
        nonlocal espiao
        espiao = espiao or _StorageEspiao(original(settings))
        return espiao

    monkeypatch.setattr(router, "get_storage", fabrica)
    return lambda: espiao.aberturas if espiao else 0


# --- caminho feliz e formatos ------------------------------------------------


def test_verifica_pdf_assinado_valido(client, db, pki):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "contrato.pdf", pt.assinar(pki, pt.pdf_simples()))

    resp = _verificar(client, token, proc_id, doc_id)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["situacao"] == "assinado"
    assert body["resumo"] == "valida"
    assert body["mensagem_resumo"] == "Assinatura válida — documento íntegro"
    a = body["assinaturas"][0]
    assert (a["signatario_nome"], a["signatario_cpf"]) == (pt.NOME_TESTE, pt.CPF_TESTE)
    assert body["url_verificador_oficial"] == "https://validar.iti.gov.br"


def test_verifica_pdf_adulterado_e_sem_assinatura(client, db, pki):
    proc_id, token, _ = _processo(client, db)
    adulterado = _anexar(client, token, proc_id, "a.pdf", pt.adulterar(pt.assinar(pki, pt.pdf_simples())))
    simples = _anexar(client, token, proc_id, "b.pdf", pt.pdf_simples())

    assert _verificar(client, token, proc_id, adulterado).json()["resumo"] == "invalida"
    body = _verificar(client, token, proc_id, simples).json()
    assert body["situacao"] == "sem_assinatura"
    assert body["mensagem_resumo"] == "Este documento não contém assinatura digital."


def test_documento_nao_pdf_e_rejeitado_sem_ler_o_storage(client, db, espiao):
    proc_id, token, _ = _processo(client, db)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    doc_id = _anexar(client, token, proc_id, "foto.png", png, "image/png")

    aberturas_antes = espiao()

    resp = _verificar(client, token, proc_id, doc_id)

    assert resp.status_code == 422
    assert resp.json()["detail"] == "A verificação de assinatura está disponível apenas para documentos PDF."
    assert espiao() == aberturas_antes  # conteúdo nem foi lido


def test_documento_removido_responde_404(client, db, pki):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "x.pdf", pt.pdf_simples())
    assert client.delete(f"/processos/{proc_id}/documentos/{doc_id}", headers=auth(token)).status_code == 200

    assert _verificar(client, token, proc_id, doc_id).status_code == 404


def test_sem_autenticacao_responde_401(client, db):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "x.pdf", pt.pdf_simples())

    resp = client.get(f"/processos/{proc_id}/documentos/{doc_id}/verificacao")

    assert resp.status_code == 401


# --- acesso negado explícito (regra vinculante) ------------------------------


def _logs(db, tipo):
    return db.scalars(select(LogSeguranca).where(LogSeguranca.tipo_evento == tipo)).all()


def test_servidor_de_outra_unidade_tem_acesso_negado_e_log(client, db, pki, espiao):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "c.pdf", pt.assinar(pki, pt.pdf_simples()))
    aberturas_antes = espiao()
    ajur = unidade(db, "AJUR-x")
    intruso = usuario(db, unidade_id=ajur.id, email="intruso-verif@ex.com")

    resp = _verificar(client, login(client, intruso.email), proc_id, doc_id)

    assert resp.status_code == 403
    assert _logs(db, TipoEventoLog.ACESSO_NEGADO)
    assert espiao() == aberturas_antes


def test_unidade_de_origem_com_processo_sigiloso_tem_acesso_negado(client, db, pki):
    proc_id, token_origem, _ = _processo(client, db, "orig")
    doc_id = _anexar(client, token_origem, proc_id, "c.pdf", pt.assinar(pki, pt.pdf_simples()))
    ajur = unidade(db, "AJUR-sig")
    resp, _dest, _s = enviar_para(
        client, db, processo_id=proc_id, token_origem=token_origem, unidade_destino=ajur,
        email_destino="destino-sig@ex.com",
    )
    assert resp.status_code == 200, resp.text
    token_destino = login(client, "destino-sig@ex.com")
    # Antes do sigilo a origem acompanha (lê) — e verifica.
    assert _verificar(client, token_origem, proc_id, doc_id).status_code == 200
    assert client.post(f"/processos/{proc_id}/sigilo", headers=auth(token_destino)).status_code == 200

    resp = _verificar(client, token_origem, proc_id, doc_id)

    assert resp.status_code == 403
    assert _logs(db, TipoEventoLog.ACESSO_NEGADO)


def test_auditor_de_outra_unidade_verifica_e_registra_acesso_auditoria(client, db, pki):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "c.pdf", pt.assinar(pki, pt.pdf_simples()))
    outra = unidade(db, "AUD-x")
    auditor = usuario(db, unidade_id=outra.id, email="auditor-verif@ex.com")
    auditor.pode_auditar = True
    db.commit()

    resp = _verificar(client, login(client, auditor.email), proc_id, doc_id)

    assert resp.status_code == 200
    assert resp.json()["resumo"] == "valida"
    assert _logs(db, TipoEventoLog.ACESSO_AUDITORIA)


# --- não persistência (D4, LGPD) ---------------------------------------------


def _contagens(db):
    tabelas = inspect(db.get_bind()).get_table_names()
    return {t: db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar_one() for t in tabelas}


def test_verificar_nao_grava_nada_nem_loga_o_signatario(client, db, pki, caplog):
    proc_id, token, _ = _processo(client, db)
    doc_id = _anexar(client, token, proc_id, "c.pdf", pt.assinar(pki, pt.pdf_simples()))
    antes_doc = db.get(Documento, doc_id)
    estado_doc = (antes_doc.hash_sha256, antes_doc.tamanho_bytes, antes_doc.objeto_chave)
    eventos_antes = db.scalar(select(func.count()).select_from(Tramitacao))
    db.expire_all()
    antes = _contagens(db)
    caplog.set_level(logging.DEBUG)

    assert _verificar(client, token, proc_id, doc_id).status_code == 200

    db.expire_all()
    assert _contagens(db) == antes
    assert db.scalar(select(func.count()).select_from(Tramitacao)) == eventos_antes
    depois_doc = db.get(Documento, doc_id)
    assert (depois_doc.hash_sha256, depois_doc.tamanho_bytes, depois_doc.objeto_chave) == estado_doc
    assert pt.CPF_TESTE not in caplog.text
    assert pt.NOME_TESTE not in caplog.text


# --- consulta pública não expõe assinaturas (G1) -----------------------------


def test_nenhuma_rota_publica_de_verificacao(client):
    schema = client.get("/openapi.json").json()
    publicas = {p: ops for p, ops in schema["paths"].items() if p.startswith("/publico")}
    assert publicas, "esperava rotas /publico/* no contrato"
    assert not any("verificacao" in p for p in publicas)
    refs = str(publicas)
    for nome in ("ResultadoVerificacao", "AssinaturaVerificada", "VereditoAssinatura"):
        assert nome not in refs
