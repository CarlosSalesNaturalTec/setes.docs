"""Teste de gestão de usuários — POST/GET/PATCH/PUT /usuarios (task 7.6 —
obrigatório, toca dado pessoal: nome, e-mail, vínculo organizacional)."""

from __future__ import annotations

from app.db.models import PerfilUsuario, Setor, StatusUsuario, Unidade, UnidadeGestor, Usuario
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


def _unidade(db, nome="Unidade A", ativo=True) -> Unidade:
    unidade = Unidade(nome=nome, sigla=nome[:3].upper(), ativo=ativo)
    db.add(unidade)
    db.commit()
    return unidade


def _setor(db, unidade, *, nome="Gabinete", sigla="GAB") -> Setor:
    """Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2)."""
    setor = Setor(unidade_id=unidade.id, nome=nome, sigla=sigla, ativo=True)
    db.add(setor)
    db.commit()
    return setor


def _usuario(db, *, perfil, unidade_id=None, email="u@example.com", setor_id=None) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=email,
        senha_hash=hash_senha(SENHA),
        perfil=perfil,
        status=StatusUsuario.ATIVO,
        unidade_id=unidade_id,
        setor_id=setor_id,
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


# --- 7.1 / 7.2 — POST /usuarios --------------------------------------------


def test_admin_cadastra_servidor_com_sucesso(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.usuarios.enqueue_email_seguro",
        lambda message, *, event_id, config: chamadas.append(event_id) or True,
    )
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Novo Servidor",
            "email": "novo@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade.id),
            "setor_id": str(setor.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 201
    assert resp.json()["status"] == "pendente_primeiro_acesso"
    assert len(chamadas) == 1
    assert chamadas[0].startswith("primeiro-acesso:")


def test_cadastro_com_email_duplicado_e_rejeitado(client, db, monkeypatch):
    monkeypatch.setattr("app.routers.usuarios.enqueue_email_seguro", lambda *a, **k: True)
    unidade = _unidade(db)
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=unidade.id, email="existe@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/usuarios",
        json={"nome": "X", "email": "existe@example.com", "perfil": "servidor", "unidade_id": str(unidade.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "já cadastrado" in resp.json()["detail"].lower()


def test_cadastro_com_email_formato_invalido_e_rejeitado(client, db):
    unidade = _unidade(db)
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/usuarios",
        json={"nome": "X", "email": "joao", "perfil": "servidor", "unidade_id": str(unidade.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "formato" in resp.json()["detail"].lower()


def test_cadastro_com_nome_vazio_e_rejeitado(client, db):
    unidade = _unidade(db)
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/usuarios",
        json={"nome": "   ", "email": "x@example.com", "perfil": "servidor", "unidade_id": str(unidade.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "nome" in resp.json()["detail"].lower()


def test_cadastro_com_unidade_inexistente_ou_inativa_e_rejeitado(client, db):
    unidade_inativa = _unidade(db, "Inativa", ativo=False)
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/usuarios",
        json={
            "nome": "X",
            "email": "x@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade_inativa.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "unidade" in resp.json()["detail"].lower()


def test_gestor_cadastra_servidor_na_unidade_gerenciada(client, db, monkeypatch):
    monkeypatch.setattr("app.routers.usuarios.enqueue_email_seguro", lambda *a, **k: True)
    unidade = _unidade(db, "COFIN")
    setor = _setor(db, unidade)
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=unidade.id))
    db.commit()
    token = _login(client, "gestor@example.com")

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Servidor Novo",
            "email": "srv@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade.id),
            "setor_id": str(setor.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 201


def test_gestor_nao_cadastra_em_unidade_nao_gerenciada(client, db):
    unidade_cofin = _unidade(db, "COFIN")
    unidade_cogep = _unidade(db, "COGEP")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=unidade_cofin.id))
    db.commit()
    token = _login(client, "gestor@example.com")

    resp = client.post(
        "/usuarios",
        json={"nome": "X", "email": "x@example.com", "perfil": "servidor", "unidade_id": str(unidade_cogep.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 403
    assert "permissão" in resp.json()["detail"].lower()


def test_gestor_nao_pode_atribuir_perfil_privilegiado(client, db):
    unidade = _unidade(db, "COFIN")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=unidade.id))
    db.commit()
    token = _login(client, "gestor@example.com")

    resp = client.post(
        "/usuarios",
        json={"nome": "X", "email": "x@example.com", "perfil": "gestor", "unidade_id": str(unidade.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 403
    assert "administrador pode" in resp.json()["detail"].lower()


# --- 7.3 — PATCH /usuarios/{id}/unidade ------------------------------------


def test_transferencia_de_servidor_substitui_vinculo(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_cofin = _setor(db, cofin)
    setor_ajur = _setor(db, ajur, nome="Consultivo", sigla="CONS")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        unidade_id=cofin.id,
        setor_id=setor_cofin.id,
        email="joao@example.com",
    )
    token = _login(client, "admin@example.com")

    resp = client.patch(
        f"/usuarios/{servidor.id}/unidade",
        json={"unidade_id": str(ajur.id), "setor_id": str(setor_ajur.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 200
    db.refresh(servidor)
    assert servidor.unidade_id == ajur.id  # vínculo antigo removido, nunca há dois simultâneos
    assert servidor.setor_id == setor_ajur.id


# --- 7.4 — PUT /usuarios/{id}/unidades-geridas -----------------------------


def test_definir_unidades_geridas_de_gestor(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    dirad = _unidade(db, "DIRAD")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="maria@example.com")
    token = _login(client, "admin@example.com")

    resp = client.put(
        f"/usuarios/{gestor.id}/unidades-geridas",
        json={"unidade_ids": [str(cofin.id), str(ajur.id), str(dirad.id)]},
        headers=_auth(token),
    )

    assert resp.status_code == 200
    vinculos = db.query(UnidadeGestor).filter(UnidadeGestor.gestor_id == gestor.id).all()
    assert len(vinculos) == 3


def test_unidades_geridas_com_lista_vazia_e_rejeitada(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="maria@example.com")
    token = _login(client, "admin@example.com")

    resp = client.put(
        f"/usuarios/{gestor.id}/unidades-geridas", json={"unidade_ids": []}, headers=_auth(token)
    )

    assert resp.status_code == 422


# --- 7.5 — GET /usuarios ----------------------------------------------------


def test_admin_lista_todos_os_usuarios(client, db):
    cofin = _unidade(db, "COFIN")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id, email="s1@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id, email="s2@example.com")
    token = _login(client, "admin@example.com")

    resp = client.get("/usuarios", headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json()["total"] == 3  # admin + 2 servidores


def test_gestor_so_lista_usuarios_das_unidades_geridas(client, db):
    cofin = _unidade(db, "COFIN")
    cogep = _unidade(db, "COGEP")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=cofin.id))
    db.commit()
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id, email="s1@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cogep.id, email="s2@example.com")
    token = _login(client, "gestor@example.com")

    resp = client.get("/usuarios", headers=_auth(token))

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == "s1@example.com"
