"""Testes de leitura do detalhe/histórico/documentos pela unidade de origem
(change visibilidade-processos-origem, task 3.2 — obrigatório: dados
pessoais/histórico de tramitação, com cenários explícitos de acesso negado).
US 1.4 (revisada), design D5."""

from __future__ import annotations

from app.db.models import LogSeguranca, TipoEventoLog
from tests.helpers_processo import auth, enviar_para, login, servidor_com_setor, tipo_processo, unidade

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"


def _processo_enviado(client, db):
    """COFIN cria e envia para AJUR; devolve (cofin_token, ajur_token, proc, cofin, ajur)."""
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="origem-cofin@ex.com")
    token_cofin = login(client, "origem-cofin@ex.com")
    proc = client.post(
        "/processos",
        json={"assunto": "Leitura origem", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token_cofin),
    ).json()
    _resp, _dest, _s = enviar_para(
        client, db, processo_id=proc["id"], token_origem=token_cofin, unidade_destino=ajur,
        email_destino="destino-ajur@ex.com",
    )

    token_ajur = login(client, "destino-ajur@ex.com")
    return token_cofin, token_ajur, proc, cofin, ajur


def _logs_negados(db):
    return db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()


def test_leitura_do_detalhe_historico_e_documentos_por_origem_ok(client, db):
    token_cofin, token_ajur, proc, _cofin, _ajur = _processo_enviado(client, db)
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


def test_escrita_por_origem_negada_enviar_devolver_sigilo_documentos(client, db):
    token_cofin, token_ajur, proc, _cofin, ajur = _processo_enviado(client, db)
    anexo = client.post(
        f"/processos/{proc['id']}/documentos",
        headers=auth(token_ajur),
        files={"arquivo": ("parecer.pdf", PDF, "application/pdf")},
    ).json()

    # Autorização por unidade (require_acesso_unidade) roda antes de validar o
    # payload — valores fictícios bastam para provar que a rejeição por
    # origem acontece antes de qualquer validação de destino.
    enviar = client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(ajur.id),
            "setor_destino_id": str(ajur.id),
            "servidor_destino_id": str(ajur.id),
        },
        headers=auth(token_cofin),
    )
    assert enviar.status_code == 403

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
    token_cofin, token_ajur, proc, _cofin, _ajur = _processo_enviado(client, db)
    marcar = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_ajur))
    assert marcar.status_code == 200, marcar.text

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_cofin))
    assert detalhe.status_code == 403
    assert "Acesso restrito" in detalhe.json()["detail"]

    assert len(_logs_negados(db)) == 1


def test_leitura_por_unidade_sem_vinculo_algum_negada(client, db):
    _token_cofin, _token_ajur, proc, _cofin, _ajur = _processo_enviado(client, db)
    dirad = unidade(db, "DIRAD")
    from tests.helpers_processo import usuario

    usuario(db, unidade_id=dirad.id, email="estranho@ex.com")
    token_dirad = login(client, "estranho@ex.com")

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_dirad))
    assert detalhe.status_code == 403
    assert "Acesso negado" in detalhe.json()["detail"]

    assert len(_logs_negados(db)) == 1
