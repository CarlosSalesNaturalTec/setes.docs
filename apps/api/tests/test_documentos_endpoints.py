"""Teste dos endpoints de documentos (task 4.x). US 3.1 Cen.1, US 3.2 Cen.1/2/3."""

from __future__ import annotations

from app.db.models import Documento
from tests.helpers_processo import auth, enviar_para, gestor_de, login, servidor_com_setor, tipo_processo, unidade

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"
DOCX = b"PK\x03\x04" + b"\x00" * 20


def _processo_aberto(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    criador, _setor = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Doc", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    proc_id = resp.json()["id"]
    return proc_id, token, criador, cofin, ajur


def _anexar(client, token, proc_id, nome, conteudo, content_type):
    return client.post(
        f"/processos/{proc_id}/documentos",
        headers=auth(token),
        files={"arquivo": (nome, conteudo, content_type)},
    )


def test_upload_retorna_metadados_e_aparece_na_lista(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)

    resp = _anexar(client, token, proc_id, "parecer.pdf", PDF, "application/pdf")

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["nome_exibicao"] == "parecer.pdf"
    assert body["tipo_conteudo"] == "application/pdf"
    assert body["tamanho_bytes"] == len(PDF)

    resp_lista = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert resp_lista.status_code == 200
    assert [d["id"] for d in resp_lista.json()["items"]] == [body["id"]]


def test_listar_retorna_so_visiveis(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)
    d1 = _anexar(client, token, proc_id, "a.pdf", PDF, "application/pdf").json()
    _anexar(client, token, proc_id, "b.docx", DOCX, "application/vnd...").json()
    d2 = client.get(f"/processos/{proc_id}/documentos", headers=auth(token)).json()["items"][1]

    client.delete(f"/processos/{proc_id}/documentos/{d2['id']}", headers=auth(token))

    resp = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert [d["id"] for d in resp.json()["items"]] == [d1["id"]]


def test_conteudo_pdf_e_servido_inline(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)
    doc = _anexar(client, token, proc_id, "parecer.pdf", PDF, "application/pdf").json()

    resp = client.get(f"/processos/{proc_id}/documentos/{doc['id']}/conteudo", headers=auth(token))

    assert resp.status_code == 200
    assert resp.content == PDF
    assert resp.headers["content-disposition"].startswith("inline")
    assert "parecer.pdf" in resp.headers["content-disposition"]


def test_conteudo_docx_dispara_attachment(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)
    doc = _anexar(client, token, proc_id, "oficio.docx", DOCX, "application/vnd...").json()

    resp = client.get(f"/processos/{proc_id}/documentos/{doc['id']}/conteudo", headers=auth(token))

    assert resp.status_code == 200
    assert resp.headers["content-disposition"].startswith("attachment")


def test_download_mantem_formato_e_nome(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)
    doc = _anexar(client, token, proc_id, "parecer.pdf", PDF, "application/pdf").json()

    resp = client.get(f"/processos/{proc_id}/documentos/{doc['id']}/download", headers=auth(token))

    assert resp.status_code == 200
    assert resp.content == PDF
    assert resp.headers["content-disposition"].startswith("attachment")
    assert "parecer.pdf" in resp.headers["content-disposition"]


def test_remover_com_processo_aberto(client, db):
    proc_id, token, _criador, _cofin, _ajur = _processo_aberto(client, db)
    doc = _anexar(client, token, proc_id, "parecer.pdf", PDF, "application/pdf").json()

    resp = client.delete(f"/processos/{proc_id}/documentos/{doc['id']}", headers=auth(token))

    assert resp.status_code == 200, resp.text
    resp_lista = client.get(f"/processos/{proc_id}/documentos", headers=auth(token))
    assert resp_lista.json()["items"] == []


def test_remover_bloqueado_apos_envio(client, db):
    """US 3.1 Cen.4 — um Gestor de ambas as unidades mantém acesso ao processo
    mesmo após o envio, e é bloqueado pela regra de custódia (409), não por
    acesso negado (403)."""
    proc_id, token, _criador, cofin, ajur = _processo_aberto(client, db)
    doc = _anexar(client, token, proc_id, "parecer.pdf", PDF, "application/pdf").json()
    enviar_para(client, db, processo_id=proc_id, token_origem=token, unidade_destino=ajur)

    gestor = gestor_de(db, cofin, ajur, email=f"gestor-{cofin.id}@ex.com")
    token_gestor = login(client, gestor.email)

    resp = client.delete(f"/processos/{proc_id}/documentos/{doc['id']}", headers=auth(token_gestor))

    assert resp.status_code == 409
    assert "já foi despachado" in resp.json()["detail"]
    doc_db = db.get(Documento, doc["id"])
    assert doc_db.removido_em is None
