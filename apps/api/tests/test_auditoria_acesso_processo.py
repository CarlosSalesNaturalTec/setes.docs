"""Acesso irrestrito de auditoria a processo (US 9.1, task 2.5 — obrigatório:
toca `log_seguranca` e dado pessoal). Cobre D1/D2/D3 de
`openspec/changes/auditoria-e-relatorios/design.md`."""

from __future__ import annotations

from app.db.models import LogSeguranca, TipoEventoLog
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"


def _processo_de_outra_unidade(client, db, *, sigiloso: bool = False):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    dono = usuario(db, unidade_id=cofin.id, email=f"dono-{cofin.id}@ex.com")
    token_dono = login(client, dono.email)
    proc_id = client.post(
        "/processos",
        json={"assunto": "Auditoria", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token_dono),
    ).json()["id"]
    client.post(
        f"/processos/{proc_id}/documentos",
        headers=auth(token_dono),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    )
    if sigiloso:
        resp = client.post(f"/processos/{proc_id}/sigilo", headers=auth(token_dono))
        assert resp.status_code == 200, resp.text
    return proc_id, cofin


def _logs(db, tipo_evento: TipoEventoLog):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == tipo_evento).all()


def test_auditor_le_processo_historico_e_documentos_de_outra_unidade(client, db):
    proc_id, _cofin = _processo_de_outra_unidade(client, db)
    ajur = unidade(db, "AJUR")
    auditor = usuario(db, unidade_id=ajur.id, email=f"auditor-{ajur.id}@ex.com")
    auditor.pode_auditar = True
    db.commit()
    token = login(client, auditor.email)

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))
    assert resp.status_code == 200, resp.text

    resp_historico = client.get(f"/processos/{proc_id}/historico", headers=auth(token))
    assert resp_historico.status_code == 200, resp_historico.text

    resp_docs = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert resp_docs.status_code == 200, resp_docs.text
    assert len(resp_docs.json()["items"]) == 1


def test_auditor_le_processo_sigiloso_de_outra_unidade(client, db):
    proc_id, _cofin = _processo_de_outra_unidade(client, db, sigiloso=True)
    ajur = unidade(db, "AJUR")
    auditor = usuario(db, unidade_id=ajur.id, email=f"auditor2-{ajur.id}@ex.com")
    auditor.pode_auditar = True
    db.commit()
    token = login(client, auditor.email)

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["sigiloso"] is True


def test_nao_auditor_em_sigiloso_fora_do_escopo_recebe_mensagem_especifica(client, db):
    proc_id, _cofin = _processo_de_outra_unidade(client, db, sigiloso=True)
    ajur = unidade(db, "AJUR")
    intruso = usuario(db, unidade_id=ajur.id, email=f"intruso-{ajur.id}@ex.com")
    token = login(client, intruso.email)

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Acesso restrito — solicite autorização ao Administrador"
    assert len(_logs(db, TipoEventoLog.ACESSO_NEGADO)) >= 1


def test_nao_auditor_em_processo_comum_fora_do_escopo_recebe_mensagem_generica(client, db):
    proc_id, _cofin = _processo_de_outra_unidade(client, db, sigiloso=False)
    ajur = unidade(db, "AJUR")
    intruso = usuario(db, unidade_id=ajur.id, email=f"intruso2-{ajur.id}@ex.com")
    token = login(client, intruso.email)

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))

    assert resp.status_code == 403
    assert resp.json()["detail"] == (
        "Acesso negado — você não tem permissão para visualizar este processo"
    )
    assert len(_logs(db, TipoEventoLog.ACESSO_NEGADO)) >= 1


def test_acesso_de_auditoria_fora_da_unidade_e_registrado(client, db):
    proc_id, _cofin = _processo_de_outra_unidade(client, db)
    ajur = unidade(db, "AJUR")
    auditor = usuario(db, unidade_id=ajur.id, email=f"auditor3-{ajur.id}@ex.com")
    auditor.pode_auditar = True
    db.commit()
    token = login(client, auditor.email)

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))
    assert resp.status_code == 200

    logs = _logs(db, TipoEventoLog.ACESSO_AUDITORIA)
    assert len(logs) == 1
    assert logs[0].usuario_id == auditor.id
    assert logs[0].contexto["processo_id"] == proc_id


def test_leitura_na_propria_unidade_nao_gera_evento_de_auditoria(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    auditor = usuario(db, unidade_id=cofin.id, email=f"auditor4-{cofin.id}@ex.com")
    auditor.pode_auditar = True
    db.commit()
    token = login(client, auditor.email)
    proc_id = client.post(
        "/processos",
        json={"assunto": "PropriaUnidade", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    ).json()["id"]

    resp = client.get(f"/processos/{proc_id}", headers=auth(token))
    assert resp.status_code == 200

    assert len(_logs(db, TipoEventoLog.ACESSO_AUDITORIA)) == 0
