"""Teste de POST /tipos-processo e PUT /tipos-processo/{id}/roteiro (task 9.5)."""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Unidade, Usuario
from app.security.senha import hash_senha

SENHA = "SenhaForte1"


def _unidade(db, nome) -> Unidade:
    unidade = Unidade(nome=nome, sigla=nome[:3].upper(), ativo=True)
    db.add(unidade)
    db.commit()
    return unidade


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


def test_criacao_de_tipo_processo_com_roteiro_ordenado(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    dirad = _unidade(db, "DIRAD")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/tipos-processo",
        json={"nome": "Licitação", "unidade_ids": [str(cofin.id), str(ajur.id), str(dirad.id)]},
        headers=_auth(token),
    )

    assert resp.status_code == 201
    body = resp.json()
    etapas = body["roteiro"]["etapas"]
    assert [e["ordem"] for e in etapas] == [1, 2, 3]
    assert [e["unidade_id"] for e in etapas] == [str(cofin.id), str(ajur.id), str(dirad.id)]
    assert body["roteiro"]["vigente"] is True


def test_roteiro_vazio_e_rejeitado(client, db):
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/tipos-processo", json={"nome": "Licitação", "unidade_ids": []}, headers=_auth(token)
    )

    assert resp.status_code == 422
    assert "ao menos uma unidade" in resp.json()["detail"]


def test_nome_duplicado_e_rejeitado(client, db):
    cofin = _unidade(db, "COFIN")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    primeiro = client.post(
        "/tipos-processo", json={"nome": "Licitação", "unidade_ids": [str(cofin.id)]}, headers=_auth(token)
    )
    assert primeiro.status_code == 201

    segundo = client.post(
        "/tipos-processo", json={"nome": "Licitação", "unidade_ids": [str(cofin.id)]}, headers=_auth(token)
    )
    assert segundo.status_code == 422
    assert "já existe um tipo de processo" in segundo.json()["detail"].lower()


def test_alteracao_de_roteiro_preserva_versao_vigente_no_momento_da_criacao_do_processo(client, db):
    """US 8.2 Cen.2: um 'processo' (mock, tabela não existe neste change) criado
    sob o roteiro v1 continua referenciando v1 mesmo depois que o Administrador
    edita o roteiro do tipo de processo (v2 vira a nova vigente)."""
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    dirad = _unidade(db, "DIRAD")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    criado = client.post(
        "/tipos-processo",
        json={"nome": "Licitação", "unidade_ids": [str(cofin.id), str(ajur.id)]},
        headers=_auth(token),
    ).json()
    tipo_id = criado["id"]

    # "processo" mock criado agora, referenciando o roteiro vigente no momento (v1)
    processo_mock_roteiro_id = criado["roteiro"]["id"]

    atualizado = client.put(
        f"/tipos-processo/{tipo_id}/roteiro",
        json={"unidade_ids": [str(ajur.id), str(dirad.id), str(cofin.id)]},
        headers=_auth(token),
    ).json()

    assert atualizado["id"] != processo_mock_roteiro_id  # nova versão (v2)
    assert atualizado["vigente"] is True

    from app.db.models import Roteiro

    v1 = db.get(Roteiro, __import__("uuid").UUID(processo_mock_roteiro_id))
    assert v1.vigente is False  # v1 congelada, não vigente
    assert [e.ordem for e in sorted(v1.etapas, key=lambda e: e.ordem)] == [1, 2]  # etapas de v1 intocadas
    assert str(v1.etapas[0].unidade_id) == str(cofin.id)  # "processo" mock ainda enxerga o roteiro original


def test_unidade_inativa_no_roteiro_e_rejeitada_na_criacao(client, db):
    cofin = _unidade(db, "COFIN")
    cofin.ativo = False
    db.commit()
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/tipos-processo",
        json={"nome": "Licitação", "unidade_ids": [str(cofin.id)]},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert resp.json()["detail"] == "Unidade inválida no roteiro."
    from app.db.models import TipoProcesso

    assert db.query(TipoProcesso).filter(TipoProcesso.nome == "Licitação").first() is None


def test_unidade_inativa_no_roteiro_e_rejeitada_no_versionamento(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    criado = client.post(
        "/tipos-processo",
        json={"nome": "Licitação", "unidade_ids": [str(cofin.id)]},
        headers=_auth(token),
    ).json()
    tipo_id = criado["id"]
    roteiro_vigente_id = criado["roteiro"]["id"]

    ajur.ativo = False
    db.commit()

    resp = client.put(
        f"/tipos-processo/{tipo_id}/roteiro",
        json={"unidade_ids": [str(cofin.id), str(ajur.id)]},
        headers=_auth(token),
    )

    assert resp.status_code == 422
    assert resp.json()["detail"] == "Unidade inválida no roteiro."

    from app.db.models import Roteiro

    vigente = db.get(Roteiro, __import__("uuid").UUID(roteiro_vigente_id))
    assert vigente.vigente is True


def test_roteiro_so_com_unidades_ativas_tem_sucesso(client, db):
    cofin = _unidade(db, "COFIN")
    ajur = _unidade(db, "AJUR")
    _usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    token = _login(client, "admin@example.com")

    resp = client.post(
        "/tipos-processo",
        json={"nome": "Licitação", "unidade_ids": [str(cofin.id), str(ajur.id)]},
        headers=_auth(token),
    )

    assert resp.status_code == 201


def test_acesso_negado_para_gestor_e_servidor(client, db):
    cofin = _unidade(db, "COFIN")
    _usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    _usuario(db, perfil=PerfilUsuario.SERVIDOR, email="srv@example.com")
    gestor_token = _login(client, "gestor@example.com")
    servidor_token = _login(client, "srv@example.com")

    for token in (gestor_token, servidor_token):
        resp = client.post(
            "/tipos-processo",
            json={"nome": "X", "unidade_ids": [str(cofin.id)]},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    from app.db.models import LogSeguranca, TipoEventoLog

    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) == 2
