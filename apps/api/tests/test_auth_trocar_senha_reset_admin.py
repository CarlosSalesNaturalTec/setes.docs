"""Teste de POST /auth/trocar-senha e POST /admin/usuarios/{id}/resetar-senha
(task 6.3 — obrigatório, dado pessoal e log de auditoria)."""

from __future__ import annotations

from app.db.models import LogSeguranca, PerfilUsuario, StatusUsuario, TipoEventoLog, Usuario
from app.security.senha import hash_senha

SENHA_ATUAL = "SenhaAtual1"


def _criar_usuario(db, *, perfil=PerfilUsuario.SERVIDOR, status=StatusUsuario.ATIVO, email="u@example.com") -> Usuario:
    usuario = Usuario(
        nome="Fulano", email=email, senha_hash=hash_senha(SENHA_ATUAL), perfil=perfil, status=status
    )
    db.add(usuario)
    db.commit()
    return usuario


def _login(client, email: str, senha: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "senha": senha})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


# --- trocar senha (US 1.7) -------------------------------------------------


def test_trocar_senha_com_sucesso(client, db):
    _criar_usuario(db)
    token = _login(client, "u@example.com", SENHA_ATUAL)

    resp = client.post(
        "/auth/trocar-senha",
        json={"senha_atual": SENHA_ATUAL, "nova_senha": "SenhaNova1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    novo_login = client.post("/auth/login", json={"email": "u@example.com", "senha": "SenhaNova1"})
    assert novo_login.status_code == 200


def test_trocar_senha_com_senha_atual_incorreta_e_rejeitada(client, db):
    _criar_usuario(db)
    token = _login(client, "u@example.com", SENHA_ATUAL)

    resp = client.post(
        "/auth/trocar-senha",
        json={"senha_atual": "errada", "nova_senha": "SenhaNova1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422
    assert "incorreta" in resp.json()["detail"].lower()


def test_trocar_senha_repetida_do_historico_e_rejeitada(client, db):
    _criar_usuario(db)
    token = _login(client, "u@example.com", SENHA_ATUAL)
    headers = {"Authorization": f"Bearer {token}"}

    # troca 1x com sucesso (SENHA_ATUAL -> SenhaNova1)
    r1 = client.post(
        "/auth/trocar-senha",
        json={"senha_atual": SENHA_ATUAL, "nova_senha": "SenhaNova1"},
        headers=headers,
    )
    assert r1.status_code == 200

    # tenta voltar para a senha original (que já está no histórico)
    r2 = client.post(
        "/auth/trocar-senha",
        json={"senha_atual": "SenhaNova1", "nova_senha": SENHA_ATUAL},
        headers=headers,
    )
    assert r2.status_code == 422
    assert "6 senhas" in r2.json()["detail"]


# --- reset por Administrador (US 1.10) -------------------------------------


def test_admin_reseta_senha_de_usuario_ativo_grava_log(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.usuarios.enqueue_email_seguro",
        lambda message, *, event_id, config: chamadas.append(event_id) or True,
    )
    admin = _criar_usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = _criar_usuario(db, email="alvo@example.com")
    admin_token = _login(client, "admin@example.com", SENHA_ATUAL)

    resp = client.post(
        f"/admin/usuarios/{alvo.id}/resetar-senha",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 200
    assert len(chamadas) == 1
    assert chamadas[0].startswith("reset-admin:")

    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.RESET_SENHA_ADMIN)
        .all()
    )
    assert len(logs) == 1
    assert logs[0].usuario_id == alvo.id
    assert logs[0].contexto["administrador_id"] == str(admin.id)

    # senha antiga não funciona mais
    velho_login = client.post("/auth/login", json={"email": "alvo@example.com", "senha": SENHA_ATUAL})
    assert velho_login.status_code == 401


def test_admin_reseta_senha_de_usuario_inativo_e_rejeitado_sem_email(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.usuarios.enqueue_email_seguro",
        lambda *a, **k: chamadas.append(1) or True,
    )
    _criar_usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin2@example.com")
    alvo = _criar_usuario(db, status=StatusUsuario.INATIVO, email="inativo@example.com")
    admin_token = _login(client, "admin2@example.com", SENHA_ATUAL)

    resp = client.post(
        f"/admin/usuarios/{alvo.id}/resetar-senha",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert resp.status_code == 422
    assert "inativo" in resp.json()["detail"].lower()
    assert chamadas == []


def test_gestor_nao_pode_resetar_senha_de_usuario(client, db):
    _criar_usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    alvo = _criar_usuario(db, email="alvo2@example.com")
    gestor_token = _login(client, "gestor@example.com", SENHA_ATUAL)

    resp = client.post(
        f"/admin/usuarios/{alvo.id}/resetar-senha",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )

    assert resp.status_code == 403
