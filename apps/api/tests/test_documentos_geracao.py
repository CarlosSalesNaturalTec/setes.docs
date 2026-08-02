"""Geração de documento de processo a partir de modelo (task 4.4, obrigatório
— dados pessoais e documentos). Change modelos-de-documento;
specs/modelos-documento e specs/gestao-documental."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import Documento, LogSeguranca, PerfilUsuario, TipoEventoLog
from app.services import documento as documento_service
from app.services.storage import FilesystemStorage
from tests.helpers_processo import auth, gestor_de, login, servidor_com_setor, tipo_processo, unidade

CONTEUDO_COM_DADOS_PESSOAIS = (
    "<p><b>Requerimento</b></p><p>Nome: João da Silva, CPF: 529.982.247-25</p>"
)


def _admin(db, email="admin@example.com"):
    from tests.helpers_processo import usuario

    return usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email=email)


def _modelo_ativo(client, token_admin):
    resp = client.post(
        "/modelos",
        json={
            "nome": "Requerimento padrão",
            "categoria": "Pessoal",
            "tipo": "requerimento",
            "conteudo": CONTEUDO_COM_DADOS_PESSOAIS,
        },
        headers=auth(token_admin),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _processo_aberto(client, db, *, nome_unidade="COFIN"):
    cofin = unidade(db, nome_unidade)
    tipo = tipo_processo(db)
    criador, _setor = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Doc", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"], token, criador, cofin


def _logs_acesso_negado(db):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


def test_documento_gerado_aparece_na_lista_e_e_baixavel(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tipo_conteudo"] == "application/pdf"
    assert body["nome_exibicao"] == "Requerimento padrão.pdf"
    assert body["modelo_id"] == modelo["id"]

    resp_lista = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert [d["id"] for d in resp_lista.json()["items"]] == [body["id"]]

    resp_download = client.get(
        f"/processos/{proc_id}/documentos/{body['id']}/download", headers=auth(token)
    )
    assert resp_download.status_code == 200
    assert resp_download.content.startswith(b"%PDF")


def test_html_malicioso_e_sanitizado_antes_de_gerar(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={
            "modelo_id": modelo["id"],
            "conteudo": "<p>Ok</p><script>alert(1)</script>",
        },
        headers=auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["tipo_conteudo"] == "application/pdf"


def test_modelo_inativo_nao_pode_originar_documento(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    client.post(f"/modelos/{modelo['id']}/desativar", headers=auth(token_admin))
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token),
    )

    assert resp.status_code == 422
    assert db.query(Documento).filter(Documento.processo_id == proc_id).count() == 0


def test_modelo_inexistente_e_404(client, db):
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": "00000000-0000-0000-0000-000000000000", "conteudo": "<p>x</p>"},
        headers=auth(token),
    )

    assert resp.status_code == 404


def test_soft_delete_e_restauracao_do_documento_gerado(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)
    doc = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token),
    ).json()

    resp_remover = client.delete(f"/processos/{proc_id}/documentos/{doc['id']}", headers=auth(token))
    assert resp_remover.status_code == 200, resp_remover.text
    assert client.get(f"/processos/{proc_id}/documentos", headers=auth(token)).json()["items"] == []

    resp_removidos = client.get("/admin/documentos-removidos", headers=auth(token_admin))
    assert doc["id"] in [d["id"] for d in resp_removidos.json()["items"]]

    resp_restaurar = client.post(
        f"/admin/documentos-removidos/{doc['id']}/restaurar", headers=auth(token_admin)
    )
    assert resp_restaurar.status_code == 200, resp_restaurar.text
    resp_lista = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert [d["id"] for d in resp_lista.json()["items"]] == [doc["id"]]


def test_purga_remove_documento_gerado_do_bucket(client, db, tmp_path, settings, monkeypatch):
    monkeypatch.setattr(settings, "documentos_storage_local_dir", str(tmp_path))
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, token, _criador, _cofin = _processo_aberto(client, db)
    doc = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token),
    ).json()
    documento_db = db.get(Documento, doc["id"])
    agora = datetime.now(timezone.utc)
    documento_db.removido_em = agora - timedelta(days=31)
    documento_db.purgar_em = agora - timedelta(days=1)
    documento_db.removido_por_id = documento_db.anexado_por_id
    db.commit()

    total = documento_service.purgar_documentos_vencidos(
        db, agora=agora, storage=FilesystemStorage(tmp_path)
    )

    assert total == 1
    assert db.get(Documento, doc["id"]) is None
    assert not (tmp_path / documento_db.objeto_chave).exists()


def test_documento_gerado_nao_vaza_para_consulta_publica(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, token, criador, _cofin = _processo_aberto(client, db)
    client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token),
    )
    processo = client.get(f"/processos/{proc_id}", headers=auth(token)).json()

    resp = client.get(f"/publico/processos/{processo['numero']}")

    assert resp.status_code == 200, resp.text
    corpo = resp.text
    assert "João da Silva" not in corpo
    assert "529.982.247-25" not in corpo
    # Schema público não tem nenhum campo de documento/anexo (D1, schemas/
    # consulta_publica.py) — vazamento impossível por omissão de campo.
    assert set(resp.json().keys()) == {
        "numero", "assunto", "tipo_processo", "status", "unidade_atual",
        "criado_em", "interessados", "historico",
    }


def test_gerar_documento_em_processo_de_outra_unidade_e_acesso_negado(client, db):
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, _token_cofin, _criador, cofin = _processo_aberto(client, db, nome_unidade="COFIN2")

    ajur = unidade(db, "AJUR2")
    servidor_ajur, _setor = servidor_com_setor(db, ajur, email=f"servidor-{ajur.id}@ex.com")
    token_ajur = login(client, servidor_ajur.email)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token_ajur),
    )

    assert resp.status_code == 403
    assert db.query(Documento).filter(Documento.processo_id == proc_id).count() == 0
    assert len(_logs_acesso_negado(db)) == 1


def test_gestor_de_ambas_unidades_pode_gerar_documento(client, db):
    """Confirma que a checagem reusa `_exigir_acesso_ao_processo` (mesma regra
    de unidade dos demais endpoints de escrita), sem alteração em autorizacao.py."""
    admin = _admin(db)
    token_admin = login(client, admin.email)
    modelo = _modelo_ativo(client, token_admin)
    proc_id, _token, _criador, cofin = _processo_aberto(client, db, nome_unidade="COFIN3")

    gestor = gestor_de(db, cofin, email=f"gestor-{cofin.id}@ex.com")
    token_gestor = login(client, gestor.email)

    resp = client.post(
        f"/processos/{proc_id}/documentos/gerar",
        json={"modelo_id": modelo["id"], "conteudo": CONTEUDO_COM_DADOS_PESSOAIS},
        headers=auth(token_gestor),
    )

    assert resp.status_code == 201, resp.text
