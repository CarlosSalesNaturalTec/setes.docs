"""Teste dos endpoints de listagem que sustentam os formulários do frontend
(GET /unidades, GET /tipos-processo, GET /usuarios/{id}/unidades-geridas)."""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Unidade, UnidadeGestor, Usuario
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


def _usuario(db, *, perfil, email) -> Usuario:
    usuario = Usuario(
        nome="Fulano", email=email, senha_hash=hash_senha(SENHA), perfil=perfil, status=StatusUsuario.ATIVO
    )
    db.add(usuario)
    db.commit()
    return usuario


def _login(client, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "senha": SENHA})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_listar_unidades(client, db):
    db.add_all([Unidade(nome="COFIN", sigla="COFIN", ativo=True), Unidade(nome="AJUR", sigla="AJUR", ativo=True)])
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.get("/unidades", headers=_auth(token))

    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_listar_tipos_processo_inclui_roteiro_vigente(client, db):
    cofin = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(cofin)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")
    client.post(
        "/tipos-processo", json={"nome": "Licitação", "unidade_ids": [str(cofin.id)]}, headers=_auth(token)
    )

    resp = client.get("/tipos-processo", headers=_auth(token))

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["nome"] == "Licitação"
    assert len(body[0]["roteiro"]["etapas"]) == 1


def test_obter_unidades_geridas(client, db):
    cofin = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(cofin)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=cofin.id))
    db.commit()
    token = _login(client, "admin@example.com")

    resp = client.get(f"/usuarios/{gestor.id}/unidades-geridas", headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json() == [str(cofin.id)]
