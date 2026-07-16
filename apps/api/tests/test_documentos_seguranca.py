"""Testes obrigatórios de segurança (task 5.x): acesso negado por unidade,
evento imutável `remover_documento` no histórico, e rejeição de MIME
falsificado — histórico de tramitação e dado pessoal em anexo. US 3.1 Cen.2,
US 3.1 Cen.3, US 1.4 Cen.2, US 3.2 (acesso negado ao conteúdo)."""

from __future__ import annotations

from app.db.models import LogSeguranca, TipoEventoLog, TipoEventoTramitacao, Tramitacao
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"
EXE_DISFARCADO_DE_PDF = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 20


def _processo_com_documento(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id, email=f"dono-{cofin.id}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Seguranca", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    proc_id = resp.json()["id"]
    doc = client.post(
        f"/processos/{proc_id}/documentos",
        headers=auth(token),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    ).json()
    return proc_id, doc, token, criador


def _logs_acesso_negado(db):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


# --- 5.1 — acesso negado por unidade ----------------------------------------


def test_servidor_de_outra_unidade_nao_anexa_e_loga(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email=f"dono2-{cofin.id}@ex.com")
    intruso = usuario(db, unidade_id=ajur.id, email=f"intruso-{ajur.id}@ex.com")
    token_dono = login(client, f"dono2-{cofin.id}@ex.com")
    proc_id = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token_dono),
    ).json()["id"]

    token_intruso = login(client, intruso.email)
    resp = client.post(
        f"/processos/{proc_id}/documentos",
        headers=auth(token_intruso),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    )

    assert resp.status_code == 403
    assert "Acesso negado" in resp.json()["detail"]
    assert len(_logs_acesso_negado(db)) >= 1


def test_servidor_de_outra_unidade_nao_baixa_e_loga(client, db):
    proc_id, doc, _token, _criador = _processo_com_documento(client, db)
    ajur = unidade(db, "AJUR")
    intruso = usuario(db, unidade_id=ajur.id, email=f"intruso2-{ajur.id}@ex.com")
    token_intruso = login(client, intruso.email)

    resp = client.get(
        f"/processos/{proc_id}/documentos/{doc['id']}/download", headers=auth(token_intruso)
    )

    assert resp.status_code == 403
    assert len(_logs_acesso_negado(db)) >= 1


def test_servidor_de_outra_unidade_nao_remove_e_loga(client, db):
    proc_id, doc, _token, _criador = _processo_com_documento(client, db)
    ajur = unidade(db, "AJUR")
    intruso = usuario(db, unidade_id=ajur.id, email=f"intruso3-{ajur.id}@ex.com")
    token_intruso = login(client, intruso.email)

    resp = client.delete(
        f"/processos/{proc_id}/documentos/{doc['id']}", headers=auth(token_intruso)
    )

    assert resp.status_code == 403
    assert len(_logs_acesso_negado(db)) >= 1


# --- 5.2 — evento imutável `remover_documento` -------------------------------


def test_remocao_gera_evento_imutavel_no_historico(client, db):
    proc_id, doc, token, criador = _processo_com_documento(client, db)

    client.delete(f"/processos/{proc_id}/documentos/{doc['id']}", headers=auth(token))

    resp = client.get(f"/processos/{proc_id}/historico", headers=auth(token))
    assert resp.status_code == 200
    eventos = resp.json()["eventos"]
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento["tipo_evento"] == "remover_documento"
    assert evento["responsavel_id"] == str(criador.id)
    assert evento["unidade_origem_id"] is None
    assert evento["unidade_destino_id"] is None
    assert evento["status_resultante"] == "aberto"  # remoção não altera o status

    # Imutabilidade: só um INSERT gravado, sem update/delete disponível na API.
    total_no_banco = (
        db.query(Tramitacao)
        .filter(Tramitacao.processo_id == proc_id)
        .filter(Tramitacao.tipo_evento == TipoEventoTramitacao.REMOVER_DOCUMENTO)
        .count()
    )
    assert total_no_banco == 1


# --- 5.3 — MIME falsificado (nível API) --------------------------------------


def test_upload_com_mime_falsificado_e_rejeitado(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id, email=f"mimefake-{cofin.id}@ex.com")
    token = login(client, criador.email)
    proc_id = client.post(
        "/processos",
        json={"assunto": "MimeFake", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    ).json()["id"]

    resp = client.post(
        f"/processos/{proc_id}/documentos",
        headers=auth(token),
        files={"arquivo": ("disfarcado.pdf", EXE_DISFARCADO_DE_PDF, "application/pdf")},
    )

    assert resp.status_code == 422
    assert "Formato de arquivo não permitido" in resp.json()["detail"]
    resp_lista = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert resp_lista.json()["items"] == []
