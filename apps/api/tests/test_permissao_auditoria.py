"""Teste de concessão/revogação da permissão de auditoria — POST/DELETE
/usuarios/{id}/permissao-auditoria (task 3.4 — obrigatório, toca `log_seguranca`)."""

from __future__ import annotations

from app.db.models import LogSeguranca, PerfilUsuario, TipoEventoLog
from tests.helpers_processo import auth, login, unidade, usuario


def test_admin_concede_permissao_de_auditoria(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "admin@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp.status_code == 200
    body = resp.json()
    assert body["pode_auditar"] is True
    assert body["perfil"] == "servidor"

    db.refresh(alvo)
    assert alvo.pode_auditar is True
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 1
    assert logs[0].tipo_evento == TipoEventoLog.PERMISSAO_AUDITORIA_CONCEDIDA
    assert logs[0].contexto["administrador_id"] == str(admin.id)


def test_concessao_idempotente_nao_duplica_log(client, db):
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "admin@example.com")

    resp1 = client.post(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))
    resp2 = client.post(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 1


def test_admin_revoga_permissao_de_auditoria(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    alvo.pode_auditar = True
    db.commit()
    token = login(client, "admin@example.com")

    resp = client.delete(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp.status_code == 200
    body = resp.json()
    assert body["pode_auditar"] is False
    assert body["perfil"] == "servidor"

    db.refresh(alvo)
    assert alvo.pode_auditar is False
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 1
    assert logs[0].tipo_evento == TipoEventoLog.PERMISSAO_AUDITORIA_REVOGADA
    assert logs[0].contexto["administrador_id"] == str(admin.id)


def test_revogacao_idempotente_nao_registra_log(client, db):
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "admin@example.com")

    resp = client.delete(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["pode_auditar"] is False
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 0


def test_servidor_ou_gestor_recebe_acesso_negado_ao_conceder(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "servidor@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp.status_code == 403
    db.refresh(alvo)
    assert alvo.pode_auditar is False
    logs = db.query(LogSeguranca).filter(
        LogSeguranca.usuario_id == servidor.id, LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO
    ).all()
    assert len(logs) == 1


def test_auditor_sem_perfil_admin_recebe_acesso_negado(client, db):
    unidade(db)
    auditor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="auditor@example.com")
    auditor.pode_auditar = True
    db.commit()
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "auditor@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/permissao-auditoria", headers=auth(token))

    assert resp.status_code == 403
    db.refresh(alvo)
    assert alvo.pode_auditar is False
