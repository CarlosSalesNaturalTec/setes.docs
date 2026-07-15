"""Testes de GET/PUT /sistema-config (task 3.3, US 8.5 — fatia mínima)."""

from __future__ import annotations

from app.db.models import LogSeguranca, PerfilUsuario, TipoEventoLog
from tests.helpers_processo import auth, login, usuario


def test_leitura_padrao_e_30_dias(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = login(client, admin.email)

    resp = client.get("/sistema-config", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["prazo_arquivamento_dias"] == 30


def test_escrita_valida_e_persistida(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = login(client, admin.email)

    resp = client.put("/sistema-config", json={"prazo_arquivamento_dias": 60}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["prazo_arquivamento_dias"] == 60

    resp_get = client.get("/sistema-config", headers=auth(token))
    assert resp_get.json()["prazo_arquivamento_dias"] == 60


def test_valor_zero_e_rejeitado(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = login(client, admin.email)

    resp = client.put("/sistema-config", json={"prazo_arquivamento_dias": 0}, headers=auth(token))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "O valor deve ser um número inteiro positivo"


def test_valor_negativo_e_rejeitado(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = login(client, admin.email)

    resp = client.put("/sistema-config", json={"prazo_arquivamento_dias": -5}, headers=auth(token))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "O valor deve ser um número inteiro positivo"


def test_servidor_recebe_acesso_negado_e_loga(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor@example.com")
    token = login(client, servidor.email)

    resp = client.put("/sistema-config", json={"prazo_arquivamento_dias": 60}, headers=auth(token))
    assert resp.status_code == 403

    log = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.usuario_id == servidor.id, LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO)
        .first()
    )
    assert log is not None


def test_gestor_recebe_acesso_negado(client, db):
    gestor = usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    token = login(client, gestor.email)

    resp = client.get("/sistema-config", headers=auth(token))
    assert resp.status_code == 403
