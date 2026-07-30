"""Vínculo servidor↔setor, campos complementares de cadastro e filtro por nome
(task 3.4 do change setores-e-cadastro-usuario; obrigatório: telefone, cargo e
chefia direta são dados pessoais de servidor)."""

from __future__ import annotations

import pytest

from app.db.models import LogSeguranca, PerfilUsuario, Setor, StatusUsuario, TipoEventoLog, Unidade, Usuario
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


@pytest.fixture(autouse=True)
def _sem_envio_de_email(monkeypatch):
    monkeypatch.setattr("app.routers.usuarios.enqueue_email_seguro", lambda *a, **k: True)


def _unidade(db, nome="COFIN", ativo=True) -> Unidade:
    unidade = Unidade(nome=nome, sigla=nome[:5].upper(), ativo=ativo)
    db.add(unidade)
    db.commit()
    return unidade


def _setor(db, unidade, *, nome="Gabinete", sigla="GAB", ativo=True) -> Setor:
    setor = Setor(unidade_id=unidade.id, nome=nome, sigla=sigla, ativo=ativo)
    db.add(setor)
    db.commit()
    return setor


def _usuario(db, *, perfil, email="u@example.com", nome="Fulano", unidade_id=None, setor_id=None) -> Usuario:
    usuario = Usuario(
        nome=nome,
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


def _admin_token(client, db) -> str:
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com", nome="Admin Geral")
    return _login(client, "admin@example.com")


# --- Obrigatoriedade e coerência do setor (D2) ------------------------------


def test_cadastro_de_servidor_sem_setor_e_rejeitado(client, db):
    unidade = _unidade(db)
    token = _admin_token(client, db)

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Novo Servidor",
            "email": "novo@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "setor é obrigatório" in resp.json()["detail"].lower()
    assert db.query(Usuario).filter(Usuario.email == "novo@example.com").first() is None


def test_cadastro_de_servidor_com_setor_de_outra_unidade_e_rejeitado(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_ajur = _setor(db, ajur, nome="Consultivo", sigla="CONS")
    token = _admin_token(client, db)

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Novo Servidor",
            "email": "novo@example.com",
            "perfil": "servidor",
            "unidade_id": str(cofin.id),
            "setor_id": str(setor_ajur.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "não pertence à unidade" in resp.json()["detail"]
    assert db.query(Usuario).filter(Usuario.email == "novo@example.com").first() is None


def test_cadastro_de_servidor_com_setor_da_propria_unidade(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

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

    assert resp.status_code == 201, resp.text
    assert resp.json()["setor_id"] == str(setor.id)


def test_cadastro_de_servidor_com_setor_inativo_e_rejeitado(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade, ativo=False)
    token = _admin_token(client, db)

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

    assert resp.status_code == 422
    assert "inativo" in resp.json()["detail"].lower()


@pytest.mark.parametrize("perfil", ["gestor", "administrador"])
def test_gestor_e_administrador_sao_cadastrados_sem_setor(client, db, perfil):
    unidade = _unidade(db)
    token = _admin_token(client, db)

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Sem Setor",
            "email": f"{perfil}@example.com",
            "perfil": perfil,
            "unidade_id": str(unidade.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["setor_id"] is None


def test_transferencia_de_unidade_sem_trocar_o_setor_e_rejeitada(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_cofin = _setor(db, cofin, nome="Gabinete", sigla="GAB")
    token = _admin_token(client, db)
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="joao@example.com",
        unidade_id=cofin.id,
        setor_id=setor_cofin.id,
    )

    resp = client.patch(
        f"/usuarios/{servidor.id}/unidade", json={"unidade_id": str(ajur.id)}, headers=_auth(token)
    )

    assert resp.status_code == 422
    assert "não pertence à unidade" in resp.json()["detail"]
    db.refresh(servidor)
    assert servidor.unidade_id == cofin.id  # vínculo original inalterado
    assert servidor.setor_id == setor_cofin.id


def test_transferencia_de_unidade_com_setor_da_nova_unidade(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_cofin = _setor(db, cofin, nome="Gabinete", sigla="GAB")
    setor_ajur = _setor(db, ajur, nome="Consultivo", sigla="CONS")
    token = _admin_token(client, db)
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="joao@example.com",
        unidade_id=cofin.id,
        setor_id=setor_cofin.id,
    )

    resp = client.patch(
        f"/usuarios/{servidor.id}/unidade",
        json={"unidade_id": str(ajur.id), "setor_id": str(setor_ajur.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 200, resp.text
    db.refresh(servidor)
    assert servidor.unidade_id == ajur.id
    assert servidor.setor_id == setor_ajur.id


# --- Campos complementares (D4) ---------------------------------------------


def test_campos_complementares_persistidos_e_exibidos_em_meu_perfil(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Maria Silva",
            "email": "maria@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade.id),
            "setor_id": str(setor.id),
            "telefone": "(71) 99999-0000",
            "cargo": "Analista Administrativo",
            "chefia_direta": "Chefe Externo Sem Conta",
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text

    criada = db.query(Usuario).filter(Usuario.email == "maria@example.com").first()
    criada.senha_hash = hash_senha(SENHA)
    criada.status = StatusUsuario.ATIVO
    db.commit()

    perfil = client.get("/usuarios/me/perfil", headers=_auth(_login(client, "maria@example.com")))

    assert perfil.status_code == 200, perfil.text
    body = perfil.json()
    assert body["usuario"]["telefone"] == "(71) 99999-0000"
    assert body["usuario"]["cargo"] == "Analista Administrativo"
    # Chefia é texto livre — a pessoa não precisa existir como usuário (D4).
    assert body["usuario"]["chefia_direta"] == "Chefe Externo Sem Conta"
    assert body["unidade_nome"] == "COFIN"
    assert body["setor_nome"] == "Gabinete"


def test_campos_complementares_sao_opcionais_e_voltam_nulos(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

    resp = client.post(
        "/usuarios",
        json={
            "nome": "Sem Complementos",
            "email": "simples@example.com",
            "perfil": "servidor",
            "unidade_id": str(unidade.id),
            "setor_id": str(setor.id),
        },
        headers=_auth(token),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["telefone"] is None and body["cargo"] is None and body["chefia_direta"] is None


def test_meu_perfil_omite_setor_quando_usuario_nao_tem(client, db):
    _admin_token(client, db)
    token = _login(client, "admin@example.com")

    body = client.get("/usuarios/me/perfil", headers=_auth(token)).json()

    assert body["setor_nome"] is None
    assert body["unidade_nome"] is None


def test_atualizar_meu_perfil_grava_campos_funcionais(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="joao@example.com",
        nome="João",
        unidade_id=unidade.id,
        setor_id=setor.id,
    )
    token = _login(client, "joao@example.com")

    resp = client.patch(
        "/usuarios/me/perfil",
        json={
            "nome": "João Souza",
            "setor_id": str(setor.id),
            "telefone": "71 3333-4444",
            "cargo": "Técnico",
            "chefia_direta": "Ana Chefe",
        },
        headers=_auth(token),
    )

    assert resp.status_code == 200, resp.text
    db.refresh(servidor)
    assert servidor.nome == "João Souza"
    assert servidor.telefone == "71 3333-4444"
    assert servidor.cargo == "Técnico"
    assert servidor.chefia_direta == "Ana Chefe"


def test_servidor_nao_move_o_proprio_perfil_para_setor_de_outra_unidade(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_cofin = _setor(db, cofin, nome="Gabinete", sigla="GAB")
    setor_ajur = _setor(db, ajur, nome="Consultivo", sigla="CONS")
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="joao@example.com",
        unidade_id=cofin.id,
        setor_id=setor_cofin.id,
    )
    token = _login(client, "joao@example.com")

    resp = client.patch(
        "/usuarios/me/perfil",
        json={"nome": "João", "setor_id": str(setor_ajur.id)},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    db.refresh(servidor)
    assert servidor.setor_id == setor_cofin.id


# --- Filtro por nome (D5) ---------------------------------------------------


def test_filtro_por_fragmento_de_nome_e_case_insensitive(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)
    for nome, email in [("Maria Silva", "m1@example.com"), ("Mariana Costa", "m2@example.com"), ("João Souza", "j@example.com")]:
        _usuario(
            db,
            perfil=PerfilUsuario.SERVIDOR,
            email=email,
            nome=nome,
            unidade_id=unidade.id,
            setor_id=setor.id,
        )

    resp = client.get("/usuarios", params={"nome": "mari"}, headers=_auth(token))

    assert resp.status_code == 200
    body = resp.json()
    nomes = sorted(u["nome"] for u in body["items"])
    assert nomes == ["Maria Silva", "Mariana Costa"]
    assert body["total"] == 2


def test_filtro_vazio_restaura_a_listagem_completa(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)
    _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="m1@example.com",
        nome="Maria Silva",
        unidade_id=unidade.id,
        setor_id=setor.id,
    )

    assert client.get("/usuarios", headers=_auth(token)).json()["total"] == 2
    assert client.get("/usuarios", params={"nome": ""}, headers=_auth(token)).json()["total"] == 2


def test_filtro_por_nome_nao_amplia_o_escopo_do_gestor(client, db):
    """O filtro restringe dentro do escopo de autorização, nunca o amplia."""
    from app.db.models import UnidadeGestor

    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    setor_cofin = _setor(db, cofin, nome="Gabinete", sigla="GAB")
    setor_ajur = _setor(db, ajur, nome="Consultivo", sigla="CONS")
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com", nome="Gestor")
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=cofin.id))
    db.commit()
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="m1@example.com", nome="Maria Silva", unidade_id=cofin.id, setor_id=setor_cofin.id)
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="m2@example.com", nome="Mariana Costa", unidade_id=ajur.id, setor_id=setor_ajur.id)
    token = _login(client, "gestor@example.com")

    body = client.get("/usuarios", params={"nome": "mari"}, headers=_auth(token)).json()

    assert body["total"] == 1
    assert body["items"][0]["email"] == "m1@example.com"


def test_servidor_recebe_403_ao_listar_ou_cadastrar_usuarios(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="srv@example.com",
        unidade_id=unidade.id,
        setor_id=setor.id,
    )
    token = _login(client, "srv@example.com")

    assert client.get("/usuarios", params={"nome": "a"}, headers=_auth(token)).status_code == 403
    assert client.post(
        "/usuarios",
        json={"nome": "X", "email": "x@example.com", "perfil": "servidor", "unidade_id": str(unidade.id)},
        headers=_auth(token),
    ).status_code == 403

    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) == 2
    assert all(log.usuario_id == servidor.id for log in logs)
