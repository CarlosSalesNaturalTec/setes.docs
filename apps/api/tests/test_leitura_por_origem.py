"""Testes de leitura do detalhe/histórico/documentos pela unidade de origem
(change visibilidade-processos-origem, task 3.2 — obrigatório: dados
pessoais/histórico de tramitação, com cenários explícitos de acesso negado).
US 1.4 (revisada), design D5."""

from __future__ import annotations

from app.db.models import LogSeguranca, TipoEventoLog
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"


def _processo_despachado(client, db):
    """COFIN cria e despacha para AJUR; devolve (cofin_token, ajur_token, proc, cofin, ajur)."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="origem-cofin@ex.com")
    token_cofin = login(client, "origem-cofin@ex.com")
    proc = client.post(
        "/processos",
        json={"assunto": "Leitura origem", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token_cofin),
    ).json()
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=ajur.id, email="destino-ajur@ex.com")
    token_ajur = login(client, "destino-ajur@ex.com")
    return token_cofin, token_ajur, proc, cofin, ajur


def _logs_negados(db):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


def test_leitura_do_detalhe_historico_e_documentos_por_origem_ok(client, db):
    token_cofin, token_ajur, proc, _cofin, _ajur = _processo_despachado(client, db)
    client.post(
        f"/processos/{proc['id']}/documentos",
        headers=auth(token_ajur),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    )

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_cofin))
    assert detalhe.status_code == 200, detalhe.text

    historico = client.get(f"/processos/{proc['id']}/historico", headers=auth(token_cofin))
    assert historico.status_code == 200, historico.text
    assert len(historico.json()["eventos"]) == 1

    documentos = client.get(f"/processos/{proc['id']}/documentos", headers=auth(token_cofin))
    assert documentos.status_code == 200, documentos.text
    assert len(documentos.json()["items"]) == 1


def test_escrita_por_origem_negada_despachar_devolver_sigilo_documentos(client, db):
    token_cofin, token_ajur, proc, _cofin, _ajur = _processo_despachado(client, db)
    anexo = client.post(
        f"/processos/{proc['id']}/documentos",
        headers=auth(token_ajur),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    ).json()

    despachar = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))
    assert despachar.status_code == 403

    devolver = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "correcao_dados"},
        headers=auth(token_cofin),
    )
    assert devolver.status_code == 403

    sigilo = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_cofin))
    assert sigilo.status_code == 403

    anexar = client.post(
        f"/processos/{proc['id']}/documentos",
        headers=auth(token_cofin),
        files={"arquivo": ("outro.pdf", PDF, "application/pdf")},
    )
    assert anexar.status_code == 403

    remover = client.delete(
        f"/processos/{proc['id']}/documentos/{anexo['id']}", headers=auth(token_cofin)
    )
    assert remover.status_code == 403

    assert len(_logs_negados(db)) == 5


def test_leitura_por_origem_de_sigiloso_negada(client, db):
    token_cofin, token_ajur, proc, _cofin, _ajur = _processo_despachado(client, db)
    marcar = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_ajur))
    assert marcar.status_code == 200, marcar.text

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_cofin))
    assert detalhe.status_code == 403
    assert "Acesso restrito" in detalhe.json()["detail"]

    assert len(_logs_negados(db)) == 1


def test_leitura_por_unidade_sem_vinculo_algum_negada(client, db):
    _token_cofin, _token_ajur, proc, _cofin, _ajur = _processo_despachado(client, db)
    dirad = unidade(db, "DIRAD")
    usuario(db, unidade_id=dirad.id, email="estranho@ex.com")
    token_dirad = login(client, "estranho@ex.com")

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_dirad))
    assert detalhe.status_code == 403
    assert "Acesso negado" in detalhe.json()["detail"]

    assert len(_logs_negados(db)) == 1
