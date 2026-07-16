"""Teste de `contar_processos_sob_responsabilidade` (task 2.2 — obrigatório,
toca histórico de tramitação; guarda da desativação de usuário, US 8.4)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.db.models import StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services.processo_consulta import contar_processos_sob_responsabilidade
from tests.helpers_processo import processo_ativo, processo_concluido, tipo_com_roteiro, unidade, usuario


def _tramitacao(db, *, processo, responsavel, status_resultante):
    evento = Tramitacao(
        processo_id=processo.id,
        tipo_evento=TipoEventoTramitacao.DESPACHO,
        unidade_origem_id=processo.unidade_atual_id,
        unidade_destino_id=processo.unidade_atual_id,
        responsavel_id=responsavel.id,
        status_resultante=status_resultante,
    )
    db.add(evento)
    db.commit()
    return evento


def test_ultimo_responsavel_de_processo_em_andamento_conta(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, unidade_id=cofin.id)
    responsavel = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    processo = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10))
    _tramitacao(db, processo=processo, responsavel=responsavel, status_resultante=StatusProcesso.EM_TRAMITACAO)

    assert contar_processos_sob_responsabilidade(db, responsavel) == 1
    assert contar_processos_sob_responsabilidade(db, criador) == 0


def test_criador_sem_tramitacao_conta(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10))

    assert contar_processos_sob_responsabilidade(db, criador) == 1


def test_processo_concluido_ou_arquivado_nao_conta(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    agora = datetime.now(timezone.utc)
    processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=agora,
        arquivar_em=agora,
    )
    processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=agora,
        arquivar_em=agora,
        status=StatusProcesso.ARQUIVADO,
    )

    assert contar_processos_sob_responsabilidade(db, criador) == 0


def test_responsavel_antigo_que_ja_despachou_nao_conta(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, unidade_id=cofin.id)
    primeiro_responsavel = usuario(db, unidade_id=cofin.id)
    responsavel_atual = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    processo = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10))
    _tramitacao(db, processo=processo, responsavel=primeiro_responsavel, status_resultante=StatusProcesso.EM_TRAMITACAO)
    _tramitacao(db, processo=processo, responsavel=responsavel_atual, status_resultante=StatusProcesso.EM_TRAMITACAO)

    assert contar_processos_sob_responsabilidade(db, primeiro_responsavel) == 0
    assert contar_processos_sob_responsabilidade(db, responsavel_atual) == 1
