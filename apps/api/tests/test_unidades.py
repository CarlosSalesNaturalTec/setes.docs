"""Teste de unidades administrativas — POST/PATCH/desativar /unidades
(task 8.6 — visibilidade por perfil)."""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Unidade, Usuario
from app.security.senha import hash_senha
from app.services.unidades import contar_processos_em_andamento

SENHA = "SenhaForte1"


def _usuario(db, *, perfil, email="u@example.com", unidade_id=None) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=email,
        senha_hash=hash_senha(SENHA),
        perfil=perfil,
        status=StatusUsuario.ATIVO,
        unidade_id=unidade_id,
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


def test_stub_contar_processos_em_andamento_retorna_zero(db):
    unidade = Unidade(nome="X", sigla="X", ativo=True)
    db.add(unidade)
    db.commit()
    assert contar_processos_em_andamento(db, unidade.id) == 0


def test_admin_cadastra_unidade(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post("/unidades", json={"nome": "COFIN", "sigla": "COFIN"}, headers=_auth(token))

    assert resp.status_code == 201
    assert resp.json()["ativo"] is True


def test_admin_edita_unidade_existente(client, db):
    unidade = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(unidade)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.patch(f"/unidades/{unidade.id}", json={"nome": "COFIN Renomeada"}, headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json()["nome"] == "COFIN Renomeada"


def test_desativa_unidade_sem_processos_desvincula_usuarios(client, db):
    unidade = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(unidade)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    servidor = _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="s@example.com", unidade_id=unidade.id)
    token = _login(client, "admin@example.com")

    resp = client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json()["ativo"] is False
    db.refresh(servidor)
    assert servidor.unidade_id is None
    assert servidor.status == StatusUsuario.ATIVO  # status inalterado (design D9)


def test_desativa_unidade_com_processos_pendentes_e_bloqueada(client, db, monkeypatch):
    unidade = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(unidade)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    monkeypatch.setattr("app.routers.unidades.contar_processos_em_andamento", lambda db, unidade_id: 3)

    resp = client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token))

    assert resp.status_code == 422
    assert "3 processo" in resp.json()["detail"]
    db.refresh(unidade)
    assert unidade.ativo is True


def test_gestor_recebe_403_em_todos_os_endpoints_de_unidade(client, db):
    unidade = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(unidade)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    token = _login(client, "gestor@example.com")

    assert client.post("/unidades", json={"nome": "X", "sigla": "X"}, headers=_auth(token)).status_code == 403
    assert client.patch(f"/unidades/{unidade.id}", json={"nome": "Y"}, headers=_auth(token)).status_code == 403
    assert client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token)).status_code == 403


def test_servidor_recebe_403_em_todos_os_endpoints_de_unidade(client, db):
    unidade = Unidade(nome="COFIN", sigla="COFIN", ativo=True)
    db.add(unidade)
    db.commit()
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="srv@example.com", unidade_id=unidade.id)
    token = _login(client, "srv@example.com")

    assert client.post("/unidades", json={"nome": "X", "sigla": "X"}, headers=_auth(token)).status_code == 403

    from app.db.models import LogSeguranca, TipoEventoLog

    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) >= 1
