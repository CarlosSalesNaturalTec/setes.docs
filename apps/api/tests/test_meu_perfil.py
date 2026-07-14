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
