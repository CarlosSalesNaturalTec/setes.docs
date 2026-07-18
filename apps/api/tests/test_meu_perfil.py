"""Teste de GET /usuarios/me/perfil (task 10.3 — obrigatório, toca dado pessoal)."""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Usuario
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


def test_perfil_sem_historico_retorna_estados_vazios(client, db):
    usuario = Usuario(
        nome="Fulano",
        email="fulano@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()

    login = client.post("/auth/login", json={"email": "fulano@example.com", "senha": SENHA})
    token = login.json()["token"]

    resp = client.get("/usuarios/me/perfil", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["usuario"]["email"] == "fulano@example.com"
    assert body["processos"] == []
    assert body["documentos_assinados"] == []
    assert body["mensagem_processos"] == "Nenhum processo registrado"
    assert body["mensagem_documentos"] == "Nenhum documento assinado"


def test_perfil_sem_autenticacao_e_rejeitado(client, db):
    resp = client.get("/usuarios/me/perfil")
    assert resp.status_code == 401


def test_nao_existe_rota_para_ver_perfil_de_terceiros(client, db):
    """US 1.5 Cen.2 / task 10.2 — não há `GET /usuarios/{id}/perfil`."""
    usuario = Usuario(
        nome="Fulano",
        email="fulano2@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()

    login = client.post("/auth/login", json={"email": "fulano2@example.com", "senha": SENHA})
    token = login.json()["token"]

    resp = client.get(
        f"/usuarios/{usuario.id}/perfil", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404


def _login(client, email: str) -> str:
    login = client.post("/auth/login", json={"email": email, "senha": SENHA})
    return login.json()["token"]


def test_atualizar_meu_perfil_altera_nome_com_sucesso(client, db):
    usuario = Usuario(
        nome="Maria Souza",
        email="maria@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    token = _login(client, "maria@example.com")

    resp = client.patch(
        "/usuarios/me/perfil",
        json={"nome": "Maria Souza Lima"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["usuario"]["nome"] == "Maria Souza Lima"
    assert body["usuario"]["email"] == "maria@example.com"
    assert body["usuario"]["perfil"] == "servidor"


def test_atualizar_meu_perfil_rejeita_nome_vazio_ou_so_espacos(client, db):
    usuario = Usuario(
        nome="Fulano",
        email="fulano3@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    token = _login(client, "fulano3@example.com")

    resp_vazio = client.patch(
        "/usuarios/me/perfil",
        json={"nome": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp_espacos = client.patch(
        "/usuarios/me/perfil",
        json={"nome": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp_vazio.status_code == 422
    assert resp_espacos.status_code == 422
    db.refresh(usuario)
    assert usuario.nome == "Fulano"


def test_atualizar_meu_perfil_rejeita_nome_acima_do_limite(client, db):
    usuario = Usuario(
        nome="Fulano",
        email="fulano4@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    token = _login(client, "fulano4@example.com")

    resp = client.patch(
        "/usuarios/me/perfil",
        json={"nome": "A" * 201},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 422
    db.refresh(usuario)
    assert usuario.nome == "Fulano"


def test_atualizar_meu_perfil_nao_afeta_email_nem_perfil(client, db):
    usuario = Usuario(
        nome="Fulano",
        email="fulano5@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=PerfilUsuario.GESTOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    token = _login(client, "fulano5@example.com")

    resp = client.patch(
        "/usuarios/me/perfil",
        json={"nome": "Novo Nome"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["usuario"]["email"] == "fulano5@example.com"
    assert body["usuario"]["perfil"] == "gestor"


def test_atualizar_meu_perfil_sem_sessao_e_rejeitado(client, db):
    resp = client.patch("/usuarios/me/perfil", json={"nome": "Qualquer"})
    assert resp.status_code == 401
