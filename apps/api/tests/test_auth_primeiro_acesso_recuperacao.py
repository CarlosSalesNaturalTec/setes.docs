"""Teste de /auth/primeiro-acesso, /auth/recuperar-senha, /auth/redefinir-senha
(task 5.6 — obrigatório, toca dado pessoal: senha, e-mail)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import PerfilUsuario, StatusUsuario, TipoTokenAutenticacao, Usuario
from app.security.senha import hash_senha
from app.services.tokens import gerar_token

EMAIL = "usuario@example.com"


def _criar_usuario_pendente(db) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=EMAIL,
        senha_hash=hash_senha("placeholder-nao-usavel"),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.PENDENTE_PRIMEIRO_ACESSO,
    )
    db.add(usuario)
    db.commit()
    return usuario


def _criar_usuario_ativo(db, *, senha="SenhaAntiga1") -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=EMAIL,
        senha_hash=hash_senha(senha),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    return usuario


# --- primeiro acesso -----------------------------------------------------


def test_primeiro_acesso_com_link_valido_e_senha_forte_autentica(client, db):
    usuario = _criar_usuario_pendente(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    resp = client.post(f"/auth/primeiro-acesso/{gerado.valor}", json={"senha": "SenhaForte1"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["token"]  # já autenticado
    db.refresh(usuario)
    assert usuario.status == StatusUsuario.ATIVO


def test_primeiro_acesso_com_senha_fraca_e_rejeitado(client, db):
    usuario = _criar_usuario_pendente(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    resp = client.post(f"/auth/primeiro-acesso/{gerado.valor}", json={"senha": "fraca"})

    assert resp.status_code == 422
    db.refresh(usuario)
    assert usuario.status == StatusUsuario.PENDENTE_PRIMEIRO_ACESSO


def test_primeiro_acesso_com_link_expirado_e_rejeitado(client, db):
    usuario = _criar_usuario_pendente(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    from app.db.models import TokenAutenticacao

    registro = db.query(TokenAutenticacao).filter(TokenAutenticacao.id == gerado.token_id).one()
    registro.expira_em = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    resp = client.post(f"/auth/primeiro-acesso/{gerado.valor}", json={"senha": "SenhaForte1"})

    assert resp.status_code == 422
    assert "expirado" in resp.json()["detail"].lower()
    db.refresh(usuario)
    assert usuario.status == StatusUsuario.PENDENTE_PRIMEIRO_ACESSO


def test_primeiro_acesso_com_link_ja_usado_e_rejeitado(client, db):
    usuario = _criar_usuario_pendente(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    primeira = client.post(f"/auth/primeiro-acesso/{gerado.valor}", json={"senha": "SenhaForte1"})
    assert primeira.status_code == 200

    segunda = client.post(f"/auth/primeiro-acesso/{gerado.valor}", json={"senha": "OutraSenha1"})
    assert segunda.status_code == 422
    assert "utilizado" in segunda.json()["detail"].lower()


# --- recuperação de senha --------------------------------------------------


def test_recuperar_senha_com_email_cadastrado_enfileira_email(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.auth.enqueue_email_seguro",
        lambda message, *, event_id, config: chamadas.append(event_id) or True,
    )
    _criar_usuario_ativo(db)

    resp = client.post("/auth/recuperar-senha", json={"email": EMAIL})

    assert resp.status_code == 200
    assert "cadastrado" in resp.json()["mensagem"].lower()
    assert len(chamadas) == 1
    assert chamadas[0].startswith("recuperacao-senha:")


def test_recuperar_senha_com_email_nao_cadastrado_nao_enfileira_email(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.auth.enqueue_email_seguro",
        lambda *a, **k: chamadas.append(1) or True,
    )

    resp = client.post("/auth/recuperar-senha", json={"email": "naoexiste@example.com"})

    assert resp.status_code == 200
    assert chamadas == []


def test_recuperacao_durante_bloqueio_desbloqueia_a_conta(client, db):
    usuario = _criar_usuario_ativo(db)
    usuario.tentativas_login_falhas = 3
    usuario.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.RECUPERACAO_SENHA)
    db.commit()

    resp = client.post(f"/auth/redefinir-senha/{gerado.valor}", json={"senha": "SenhaNova1"})

    assert resp.status_code == 200
    db.refresh(usuario)
    assert usuario.tentativas_login_falhas == 0
    assert usuario.bloqueado_ate is None

    login_resp = client.post("/auth/login", json={"email": EMAIL, "senha": "SenhaNova1"})
    assert login_resp.status_code == 200
