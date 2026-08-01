"""Teste do serviço de sigilo (task 2.2 — obrigatório: histórico de
tramitação imutável). US 2.6 Cen.1/2 e idempotência (D4)."""

from __future__ import annotations

from app.db.models import Processo, StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services import sigilo as sigilo_service
from tests.helpers_processo import auth, enviar_para, login, servidor_com_setor, tipo_processo, unidade


def _processo_em_tramitacao(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    criador, _setor = servidor_com_setor(db, cofin)
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Sigilo", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    processo_id = resp.json()["id"]
    enviar_para(client, db, processo_id=processo_id, token_origem=token, unidade_destino=ajur)
    processo = db.get(Processo, processo_id)
    db.refresh(processo)
    return processo, criador


def test_marcar_processo_nao_sigiloso_gera_um_evento(client, db):
    processo, responsavel = _processo_em_tramitacao(client, db)
    assert processo.status == StatusProcesso.EM_TRAMITACAO

    resultado = sigilo_service.marcar(db, processo=processo, responsavel=responsavel)

    assert resultado.sigiloso is True
    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).all()
    novos = [e for e in eventos if e.tipo_evento == TipoEventoTramitacao.MARCAR_SIGILO]
    assert len(novos) == 1
    evento = novos[0]
    assert evento.responsavel_id == responsavel.id
    assert evento.unidade_origem_id is None
    assert evento.unidade_destino_id is None
    assert evento.status_resultante == StatusProcesso.EM_TRAMITACAO
    # sigilo não altera o status do processo
    assert resultado.status == StatusProcesso.EM_TRAMITACAO


def test_marcar_processo_ja_sigiloso_e_no_op(client, db):
    processo, responsavel = _processo_em_tramitacao(client, db)
    sigilo_service.marcar(db, processo=processo, responsavel=responsavel)
    total_antes = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count()

    sigilo_service.marcar(db, processo=processo, responsavel=responsavel)

    assert processo.sigiloso is True
    assert (
        db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count() == total_antes
    )


def test_remover_processo_sigiloso_gera_um_evento(client, db):
    processo, responsavel = _processo_em_tramitacao(client, db)
    sigilo_service.marcar(db, processo=processo, responsavel=responsavel)

    resultado = sigilo_service.remover(db, processo=processo, responsavel=responsavel)

    assert resultado.sigiloso is False
    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).all()
    remocoes = [e for e in eventos if e.tipo_evento == TipoEventoTramitacao.REMOVER_SIGILO]
    assert len(remocoes) == 1
    assert remocoes[0].responsavel_id == responsavel.id
    assert remocoes[0].status_resultante == StatusProcesso.EM_TRAMITACAO


def test_remover_processo_nao_sigiloso_e_no_op(client, db):
    processo, responsavel = _processo_em_tramitacao(client, db)
    total_antes = db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count()

    sigilo_service.remover(db, processo=processo, responsavel=responsavel)

    assert processo.sigiloso is False
    assert (
        db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count() == total_antes
    )
