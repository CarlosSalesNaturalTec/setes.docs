"""Setores da unidade — CRUD, unicidade de sigla, guardas de desativação e
acesso negado (task 2.5 do change setores-e-cadastro-usuario; obrigatório:
o vínculo servidor↔setor é dado pessoal de servidor)."""

from __future__ import annotations

from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    Setor,
    StatusUsuario,
    TipoEventoLog,
    Unidade,
    Usuario,
)
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


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


def _usuario(db, *, perfil, email="u@example.com", unidade_id=None, setor_id=None, status=StatusUsuario.ATIVO) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=email,
        senha_hash=hash_senha(SENHA),
        perfil=perfil,
        status=status,
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
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    return _login(client, "admin@example.com")


def _logs_acesso_negado(db) -> list[LogSeguranca]:
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


# --- CRUD -------------------------------------------------------------------


def test_admin_cadastra_setor_na_unidade(client, db):
    unidade = _unidade(db)
    token = _admin_token(client, db)

    resp = client.post(
        f"/unidades/{unidade.id}/setores",
        json={"nome": "Gabinete", "sigla": "GAB"},
        headers=_auth(token),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ativo"] is True
    assert body["unidade_id"] == str(unidade.id)

    listagem = client.get(f"/unidades/{unidade.id}/setores", headers=_auth(token))
    assert [s["sigla"] for s in listagem.json()] == ["GAB"]


def test_admin_edita_setor(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

    resp = client.patch(
        f"/setores/{setor.id}", json={"nome": "Gabinete do Coordenador"}, headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["nome"] == "Gabinete do Coordenador"
    assert resp.json()["sigla"] == "GAB"


def test_listagem_apenas_ativos_omite_setor_inativo(client, db):
    unidade = _unidade(db)
    _setor(db, unidade, nome="Gabinete", sigla="GAB")
    _setor(db, unidade, nome="Protocolo", sigla="PROT", ativo=False)
    token = _admin_token(client, db)

    todos = client.get(f"/unidades/{unidade.id}/setores", headers=_auth(token)).json()
    ativos = client.get(
        f"/unidades/{unidade.id}/setores", params={"apenas_ativos": True}, headers=_auth(token)
    ).json()

    assert len(todos) == 2
    assert [s["sigla"] for s in ativos] == ["GAB"]


def test_nao_existe_endpoint_de_exclusao_de_setor(client, db):
    """Setor nunca é excluído (D3) — só desativado."""
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

    resp = client.delete(f"/setores/{setor.id}", headers=_auth(token))

    assert resp.status_code == 405
    assert db.get(Setor, setor.id) is not None


# --- Unicidade de sigla (D1) ------------------------------------------------


def test_sigla_duplicada_na_mesma_unidade_e_rejeitada(client, db):
    unidade = _unidade(db)
    _setor(db, unidade, nome="Gabinete", sigla="GAB")
    token = _admin_token(client, db)

    resp = client.post(
        f"/unidades/{unidade.id}/setores",
        json={"nome": "Gabinete Adjunto", "sigla": "GAB"},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert "GAB" in resp.json()["detail"]
    assert db.query(Setor).filter(Setor.unidade_id == unidade.id).count() == 1


def test_mesma_sigla_em_unidades_diferentes_e_aceita(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    _setor(db, cofin, nome="Gabinete", sigla="GAB")
    token = _admin_token(client, db)

    resp = client.post(
        f"/unidades/{ajur.id}/setores", json={"nome": "Gabinete", "sigla": "GAB"}, headers=_auth(token)
    )

    assert resp.status_code == 201, resp.text
    assert db.query(Setor).filter(Setor.sigla == "GAB").count() == 2


def test_edicao_para_sigla_ja_existente_na_unidade_e_rejeitada(client, db):
    unidade = _unidade(db)
    _setor(db, unidade, nome="Gabinete", sigla="GAB")
    protocolo = _setor(db, unidade, nome="Protocolo", sigla="PROT")
    token = _admin_token(client, db)

    resp = client.patch(f"/setores/{protocolo.id}", json={"sigla": "GAB"}, headers=_auth(token))

    assert resp.status_code == 422
    db.refresh(protocolo)
    assert protocolo.sigla == "PROT"


def test_edicao_mantendo_a_propria_sigla_e_aceita(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade, nome="Gabinete", sigla="GAB")
    token = _admin_token(client, db)

    resp = client.patch(
        f"/setores/{setor.id}", json={"nome": "Gabinete", "sigla": "GAB"}, headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text


# --- Desativação e cascata (D3) ---------------------------------------------


def test_desativacao_bloqueada_com_servidores_ativos_vinculados(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)
    for i in range(3):
        _usuario(
            db,
            perfil=PerfilUsuario.SERVIDOR,
            email=f"s{i}@example.com",
            unidade_id=unidade.id,
            setor_id=setor.id,
        )

    resp = client.post(f"/setores/{setor.id}/desativar", headers=_auth(token))

    assert resp.status_code == 422
    assert "3 servidor" in resp.json()["detail"]
    db.refresh(setor)
    assert setor.ativo is True


def test_desativacao_liberada_quando_servidor_vinculado_esta_inativo(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)
    _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="inativo@example.com",
        unidade_id=unidade.id,
        setor_id=setor.id,
        status=StatusUsuario.INATIVO,
    )

    resp = client.post(f"/setores/{setor.id}/desativar", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["ativo"] is False


def test_reativar_setor_e_explicito_e_idempotente(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade, ativo=False)
    token = _admin_token(client, db)

    assert client.post(f"/setores/{setor.id}/reativar", headers=_auth(token)).json()["ativo"] is True
    assert client.post(f"/setores/{setor.id}/reativar", headers=_auth(token)).json()["ativo"] is True


def test_desativar_unidade_cascateia_para_os_setores(client, db):
    unidade = _unidade(db)
    gabinete = _setor(db, unidade, nome="Gabinete", sigla="GAB")
    protocolo = _setor(db, unidade, nome="Protocolo", sigla="PROT")
    token = _admin_token(client, db)

    resp = client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    db.refresh(gabinete)
    db.refresh(protocolo)
    assert gabinete.ativo is False
    assert protocolo.ativo is False


def test_desativar_unidade_desvincula_unidade_e_setor_do_servidor(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)
    servidor = _usuario(
        db,
        perfil=PerfilUsuario.SERVIDOR,
        email="s@example.com",
        unidade_id=unidade.id,
        setor_id=setor.id,
    )

    assert client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token)).status_code == 200

    db.refresh(servidor)
    assert servidor.unidade_id is None
    assert servidor.setor_id is None  # invariante setor↔unidade (D2) preservada


def test_reativar_unidade_nao_reativa_setores(client, db):
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    token = _admin_token(client, db)

    client.post(f"/unidades/{unidade.id}/desativar", headers=_auth(token))
    resp = client.post(f"/unidades/{unidade.id}/reativar", headers=_auth(token))

    assert resp.status_code == 200
    assert resp.json()["ativo"] is True
    db.refresh(setor)
    assert setor.ativo is False  # reativação de setor é explícita, item a item (D3)


def test_setor_inexistente_retorna_404(client, db):
    token = _admin_token(client, db)
    inexistente = "00000000-0000-0000-0000-000000000000"

    assert client.patch(f"/setores/{inexistente}", json={"nome": "X"}, headers=_auth(token)).status_code == 404
    assert client.post(f"/setores/{inexistente}/desativar", headers=_auth(token)).status_code == 404
    assert client.post(f"/setores/{inexistente}/reativar", headers=_auth(token)).status_code == 404


# --- Acesso negado (obrigatório) --------------------------------------------


def test_gestor_recebe_403_nas_rotas_de_escrita_de_setor(client, db):
    """Change tramitacao-manual (design.md — fluxo de Reatribuição): a
    listagem (GET) passou a ser aberta a qualquer autenticado, para a
    cascata unidade→setor→servidor da tela de Tramitação; só as rotas de
    escrita continuam admin-only."""
    unidade = _unidade(db)
    setor = _setor(db, unidade)
    gestor = _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    token = _login(client, "gestor@example.com")

    assert client.get(f"/unidades/{unidade.id}/setores", headers=_auth(token)).status_code == 200
    assert client.post(
        f"/unidades/{unidade.id}/setores", json={"nome": "X", "sigla": "X"}, headers=_auth(token)
    ).status_code == 403
    assert client.patch(f"/setores/{setor.id}", json={"nome": "X"}, headers=_auth(token)).status_code == 403
    assert client.post(f"/setores/{setor.id}/desativar", headers=_auth(token)).status_code == 403
    assert client.post(f"/setores/{setor.id}/reativar", headers=_auth(token)).status_code == 403

    db.refresh(setor)
    assert setor.ativo is True and setor.nome == "Gabinete"  # nada foi alterado
    logs = _logs_acesso_negado(db)
    assert len(logs) == 4
    assert all(log.usuario_id == gestor.id for log in logs)


def test_servidor_recebe_403_nas_rotas_de_escrita_de_setor(client, db):
    """Ver docstring de `test_gestor_recebe_403_nas_rotas_de_escrita_de_setor`."""
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

    assert client.get(f"/unidades/{unidade.id}/setores", headers=_auth(token)).status_code == 200
    assert client.post(
        f"/unidades/{unidade.id}/setores", json={"nome": "X", "sigla": "X"}, headers=_auth(token)
    ).status_code == 403
    assert client.patch(f"/setores/{setor.id}", json={"nome": "X"}, headers=_auth(token)).status_code == 403
    assert client.post(f"/setores/{setor.id}/desativar", headers=_auth(token)).status_code == 403
    assert client.post(f"/setores/{setor.id}/reativar", headers=_auth(token)).status_code == 403

    db.refresh(setor)
    assert setor.ativo is True and setor.nome == "Gabinete"
    logs = _logs_acesso_negado(db)
    assert len(logs) == 4
    assert all(log.usuario_id == servidor.id for log in logs)
