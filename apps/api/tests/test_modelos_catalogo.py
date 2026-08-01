"""Catálogo de modelos de documento — CRUD, desativação e acesso negado (task
3.4, obrigatório). Change modelos-de-documento; specs/modelos-documento."""

from __future__ import annotations

from app.db.models import Documento, LogSeguranca, ModeloDocumento, PerfilUsuario, TipoEventoLog
from tests.helpers_processo import (
    auth,
    login,
    servidor_com_setor,
    tipo_processo,
    unidade,
    usuario,
)

CONTEUDO = "<p><b>Requerimento</b> de [NOME DO SOLICITANTE]</p>"


def _admin(db, email="admin@example.com"):
    return usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email=email)


def _payload(**overrides):
    body = {
        "nome": "Requerimento padrão",
        "categoria": "Pessoal",
        "tipo": "requerimento",
        "descricao": "Modelo padrão de requerimento",
        "conteudo": CONTEUDO,
    }
    body.update(overrides)
    return body


def _logs_acesso_negado(db):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


# --- CRUD (US: Cadastro de modelo) -------------------------------------------


def test_admin_cadastra_modelo(client, db):
    admin = _admin(db)
    token = login(client, admin.email)

    resp = client.post("/modelos", json=_payload(), headers=auth(token))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["nome"] == "Requerimento padrão"
    assert body["categoria"] == "Pessoal"
    assert body["tipo"] == "requerimento"
    assert body["ativo"] is True
    assert body["criado_por_id"] == str(admin.id)
    assert "<b>Requerimento</b>" in body["conteudo"]


def test_modelo_criado_consta_no_catalogo_ativo(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    client.post("/modelos", json=_payload(), headers=auth(token))

    resp = client.get("/modelos", params={"ativo": True}, headers=auth(token))

    assert resp.status_code == 200
    assert [m["nome"] for m in resp.json()] == ["Requerimento padrão"]


def test_admin_edita_modelo(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token)).json()

    resp = client.patch(
        f"/modelos/{modelo['id']}",
        json={"nome": "Requerimento revisado"},
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["nome"] == "Requerimento revisado"
    assert resp.json()["categoria"] == "Pessoal"  # demais campos preservados


def test_conteudo_e_sanitizado_na_gravacao(client, db):
    admin = _admin(db)
    token = login(client, admin.email)

    resp = client.post(
        "/modelos",
        json=_payload(conteudo="<p>Ok</p><script>alert(1)</script>"),
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert "<script" not in resp.json()["conteudo"]
    assert "<p>Ok</p>" in resp.json()["conteudo"]


# --- Desativação/reativação (US: Modelo desativado sai do catálogo) ---------


def test_modelo_desativado_sai_do_catalogo_de_escolha(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token)).json()

    resp = client.post(f"/modelos/{modelo['id']}/desativar", headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["ativo"] is False
    catalogo_ativo = client.get("/modelos", params={"ativo": True}, headers=auth(token)).json()
    assert catalogo_ativo == []
    # Continua visível na listagem administrativa completa.
    catalogo_completo = client.get("/modelos", headers=auth(token)).json()
    assert [m["id"] for m in catalogo_completo] == [modelo["id"]]


def test_desativacao_preserva_documentos_ja_gerados(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    modelo_db = ModeloDocumento(
        nome="Requerimento padrão",
        categoria="Pessoal",
        tipo="requerimento",
        conteudo=CONTEUDO,
        ativo=True,
        criado_por_id=admin.id,
    )
    db.add(modelo_db)
    db.commit()

    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    token_criador = login(client, criador.email)
    proc = client.post(
        "/processos",
        json={"assunto": "Doc", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token_criador),
    ).json()
    documento_gerado = Documento(
        processo_id=proc["id"],
        nome_original="requerimento.pdf",
        nome_exibicao="requerimento.pdf",
        objeto_chave="x/y",
        tipo_conteudo="application/pdf",
        tamanho_bytes=10,
        hash_sha256="a" * 64,
        anexado_por_id=criador.id,
        modelo_id=modelo_db.id,
    )
    db.add(documento_gerado)
    db.commit()

    resp = client.post(f"/modelos/{modelo_db.id}/desativar", headers=auth(token))
    assert resp.status_code == 200

    db.refresh(documento_gerado)
    assert documento_gerado.modelo_id == modelo_db.id
    assert documento_gerado.removido_em is None
    resp_lista = client.get(f"/processos/{proc['id']}/documentos", headers=auth(token_criador))
    assert [d["id"] for d in resp_lista.json()["items"]] == [str(documento_gerado.id)]


def test_modelo_reativado_volta_ao_catalogo(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token)).json()
    client.post(f"/modelos/{modelo['id']}/desativar", headers=auth(token))

    resp = client.post(f"/modelos/{modelo['id']}/reativar", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["ativo"] is True
    catalogo_ativo = client.get("/modelos", params={"ativo": True}, headers=auth(token)).json()
    assert [m["id"] for m in catalogo_ativo] == [modelo["id"]]


# --- Sem exclusão física ------------------------------------------------------


def test_nenhuma_rota_de_exclusao_existe(client, db):
    admin = _admin(db)
    token = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token)).json()

    resp = client.delete(f"/modelos/{modelo['id']}", headers=auth(token))

    assert resp.status_code == 405  # método não suportado — rota não existe


# --- Leitura por Servidor (US: Leitura do catálogo por Servidor) ------------


def test_servidor_le_catalogo_de_modelos_ativos(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    client.post("/modelos", json=_payload(), headers=auth(token_admin))

    cofin = unidade(db, "COFIN")
    servidor, _setor = servidor_com_setor(db, cofin, email="servidor@example.com")
    token_servidor = login(client, servidor.email)

    resp = client.get("/modelos", params={"ativo": True}, headers=auth(token_servidor))

    assert resp.status_code == 200
    assert len(resp.json()) == 1


# --- Acesso negado (US: Escrita no catálogo por não-Administrador) ----------


def test_servidor_recebe_403_ao_criar_modelo(client, db):
    cofin = unidade(db, "COFIN")
    servidor, _setor = servidor_com_setor(db, cofin, email="servidor2@example.com")
    token = login(client, servidor.email)

    resp = client.post("/modelos", json=_payload(), headers=auth(token))

    assert resp.status_code == 403
    assert db.query(ModeloDocumento).count() == 0
    assert len(_logs_acesso_negado(db)) == 1


def test_gestor_recebe_403_ao_editar_modelo(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token_admin)).json()

    gestor = usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor@example.com")
    token_gestor = login(client, gestor.email)

    resp = client.patch(
        f"/modelos/{modelo['id']}", json={"nome": "Outro"}, headers=auth(token_gestor)
    )

    assert resp.status_code == 403
    assert len(_logs_acesso_negado(db)) == 1


def test_gestor_recebe_403_ao_desativar_modelo(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token_admin)).json()

    gestor = usuario(db, perfil=PerfilUsuario.GESTOR, email="gestor2@example.com")
    token_gestor = login(client, gestor.email)

    resp = client.post(f"/modelos/{modelo['id']}/desativar", headers=auth(token_gestor))

    assert resp.status_code == 403
    assert len(_logs_acesso_negado(db)) == 1


def test_servidor_recebe_403_ao_reativar_modelo(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = client.post("/modelos", json=_payload(), headers=auth(token_admin)).json()
    client.post(f"/modelos/{modelo['id']}/desativar", headers=auth(token_admin))

    cofin = unidade(db, "COFIN")
    servidor, _setor = servidor_com_setor(db, cofin, email="servidor3@example.com")
    token_servidor = login(client, servidor.email)

    resp = client.post(f"/modelos/{modelo['id']}/reativar", headers=auth(token_servidor))

    assert resp.status_code == 403
    assert len(_logs_acesso_negado(db)) == 1
