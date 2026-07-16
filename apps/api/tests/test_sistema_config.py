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


def test_dias_antecedencia_alerta_prazo_padrao_e_2(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin2@example.com")
    token = login(client, admin.email)

    resp = client.get("/sistema-config", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["dias_antecedencia_alerta_prazo"] == 2


def test_admin_altera_dias_antecedencia_alerta_prazo_e_persiste(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin3@example.com")
    token = login(client, admin.email)

    resp = client.put(
        "/sistema-config", json={"dias_antecedencia_alerta_prazo": 5}, headers=auth(token)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["dias_antecedencia_alerta_prazo"] == 5
    # Não altera o outro parâmetro (campos independentes, D4).
    assert resp.json()["prazo_arquivamento_dias"] == 30

    resp_get = client.get("/sistema-config", headers=auth(token))
    assert resp_get.json()["dias_antecedencia_alerta_prazo"] == 5


def test_servidor_ou_gestor_nao_altera_dias_antecedencia_alerta_prazo(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor2@example.com")
    token = login(client, servidor.email)

    resp = client.put(
        "/sistema-config", json={"dias_antecedencia_alerta_prazo": 5}, headers=auth(token)
    )
    assert resp.status_code == 403

    gestor = usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor2@example.com")
    token_gestor = login(client, gestor.email)
    resp_gestor = client.put(
        "/sistema-config", json={"dias_antecedencia_alerta_prazo": 5}, headers=auth(token_gestor)
    )
    assert resp_gestor.status_code == 403


def test_dias_antecedencia_alerta_prazo_valor_invalido_e_rejeitado(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin4@example.com")
    token = login(client, admin.email)

    resp = client.put(
        "/sistema-config", json={"dias_antecedencia_alerta_prazo": 0}, headers=auth(token)
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "O valor deve ser um número inteiro positivo"


def test_dias_para_processo_parado_padrao_e_7(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin5@example.com")
    token = login(client, admin.email)

    resp = client.get("/sistema-config", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["dias_para_processo_parado"] == 7


def test_admin_altera_dias_para_processo_parado_e_persiste(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin6@example.com")
    token = login(client, admin.email)

    resp = client.put("/sistema-config", json={"dias_para_processo_parado": 10}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["dias_para_processo_parado"] == 10
    # Não altera os demais parâmetros (campos independentes, D4).
    assert resp.json()["prazo_arquivamento_dias"] == 30

    resp_get = client.get("/sistema-config", headers=auth(token))
    assert resp_get.json()["dias_para_processo_parado"] == 10


def test_dias_para_processo_parado_valor_invalido_e_rejeitado(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin7@example.com")
    token = login(client, admin.email)

    resp = client.put("/sistema-config", json={"dias_para_processo_parado": 0}, headers=auth(token))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "O valor deve ser um número inteiro positivo"


def test_servidor_ou_gestor_nao_altera_dias_para_processo_parado(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor3@example.com")
    token = login(client, servidor.email)

    resp = client.put(
        "/sistema-config", json={"dias_para_processo_parado": 10}, headers=auth(token)
    )
    assert resp.status_code == 403

    log = (
        db.query(LogSeguranca)
        .filter(
            LogSeguranca.usuario_id == servidor.id,
            LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO,
        )
        .first()
    )
    assert log is not None

    gestor = usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor3@example.com")
    token_gestor = login(client, gestor.email)
    resp_gestor = client.put(
        "/sistema-config", json={"dias_para_processo_parado": 10}, headers=auth(token_gestor)
    )
    assert resp_gestor.status_code == 403
