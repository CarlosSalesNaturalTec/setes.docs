"""Teste de POST /tipos-processo e PATCH /tipos-processo/{id} (task 9.5).

Change tramitacao-manual: roteiro foi removido do tipo de processo — o CRUD
que resta é nome (criação) e prazo de anonimização LGPD (PATCH).
"""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Usuario
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


def test_criacao_de_tipo_processo(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post("/tipos-processo", json={"nome": "Licitação"}, headers=_auth(token))

    assert resp.status_code == 201
    body = resp.json()
    assert body["nome"] == "Licitação"
    assert body["ativo"] is True
    assert "roteiro" not in body


def test_nome_duplicado_e_rejeitado(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    primeiro = client.post("/tipos-processo", json={"nome": "Licitação"}, headers=_auth(token))
    assert primeiro.status_code == 201

    segundo = client.post("/tipos-processo", json={"nome": "Licitação"}, headers=_auth(token))
    assert segundo.status_code == 422
    assert "já existe um tipo de processo" in segundo.json()["detail"].lower()


def test_atualiza_prazo_anonimizacao(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    criado = client.post("/tipos-processo", json={"nome": "Licitação"}, headers=_auth(token)).json()

    resp = client.patch(
        f"/tipos-processo/{criado['id']}",
        json={"prazo_anonimizacao_anos": 10},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["prazo_anonimizacao_anos"] == 10


def test_acesso_negado_para_gestor_e_servidor(client, db):
    _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="srv@example.com")
    gestor_token = _login(client, "gestor@example.com")
    servidor_token = _login(client, "srv@example.com")

    for token in (gestor_token, servidor_token):
        resp = client.post("/tipos-processo", json={"nome": "X"}, headers=_auth(token))
        assert resp.status_code == 403

    from app.db.models import LogSeguranca, TipoEventoLog

    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) == 2
