"""Teste de POST /auth/login, /auth/logout, /auth/me (tasks 4.5, 4.6 — obrigatório,
credenciais/sessão são dado pessoal)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import PerfilUsuario, StatusUsuario, Usuario
from app.security.senha import hash_senha

EMAIL = "usuario@example.com"
SENHA = "SenhaForte1"


def _criar_usuario(db, *, status=StatusUsuario.ATIVO, senha=SENHA) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=EMAIL,
        senha_hash=hash_senha(senha),
        perfil=PerfilUsuario.SERVIDOR,
        status=status,
    )
    db.add(usuario)
    db.commit()
    return usuario


def test_login_com_credenciais_validas(client, db):
    _criar_usuario(db)

    resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resp.status_code == 200
    body = resp.json()
    assert body["token"]
    assert body["usuario"]["email"] == EMAIL


def test_login_com_senha_errada_e_rejeitado(client, db):
    _criar_usuario(db)

    resp = client.post("/auth/login", json={"email": EMAIL, "senha": "errada"})

    assert resp.status_code == 401


def test_bloqueio_apos_3_tentativas_incorretas_dispara_email(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.auth.enqueue_email_seguro",
        lambda message, *, event_id, config: chamadas.append(event_id) or True,
    )
    _criar_usuario(db)

    for _ in range(3):
        resp = client.post("/auth/login", json={"email": EMAIL, "senha": "errada"})
        assert resp.status_code == 401

    assert len(chamadas) == 1
    assert chamadas[0].startswith("alerta-bloqueio:")

    usuario = db.query(Usuario).filter(Usuario.email == EMAIL).one()
    assert usuario.bloqueado_ate is not None


def test_login_durante_bloqueio_nao_reseta_contador_mesmo_com_senha_correta(client, db):
    usuario = _criar_usuario(db)
    usuario.tentativas_login_falhas = 3
    usuario.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resp.status_code == 403
    db.refresh(usuario)
    assert usuario.tentativas_login_falhas == 3
    assert usuario.bloqueado_ate is not None


def test_desbloqueio_automatico_apos_30_minutos(client, db):
    usuario = _criar_usuario(db)
    usuario.tentativas_login_falhas = 3
    usuario.bloqueado_ate = datetime.now(timezone.utc) - timedelta(minutes=1)  # já expirou
    db.commit()

    resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resp.status_code == 200
    db.refresh(usuario)
    assert usuario.tentativas_login_falhas == 0
    assert usuario.bloqueado_ate is None


def test_login_com_conta_inativa_e_rejeitado_sem_email_nem_contador(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.auth.enqueue_email_seguro",
        lambda *a, **k: chamadas.append(1) or True,
    )
    usuario = _criar_usuario(db, status=StatusUsuario.INATIVO)

    resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})

    assert resp.status_code == 403
    assert "desativada" in resp.json()["detail"].lower()
    db.refresh(usuario)
    assert usuario.tentativas_login_falhas == 0
    assert chamadas == []


def test_logout_invalida_a_sessao(client, db):
    _criar_usuario(db)
    login_resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_resp = client.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401


def test_me_retorna_exp_atualizado(client, db):
    _criar_usuario(db)
    login_resp = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA})
    token = login_resp.json()["token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    assert resp.json()["exp"]
    assert resp.headers.get("x-renewed-token")


def test_sessoes_concorrentes_independentes_logout_nao_afeta_outra(client, db):
    """US 1.9 — dois logins (dispositivos diferentes) do mesmo usuário."""
    _criar_usuario(db)

    sessao_a = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA}).json()
    sessao_b = client.post("/auth/login", json={"email": EMAIL, "senha": SENHA}).json()

    client.post("/auth/logout", headers={"Authorization": f"Bearer {sessao_a['token']}"})

    resp_a = client.get("/auth/me", headers={"Authorization": f"Bearer {sessao_a['token']}"})
    resp_b = client.get("/auth/me", headers={"Authorization": f"Bearer {sessao_b['token']}"})

    assert resp_a.status_code == 401
    assert resp_b.status_code == 200
