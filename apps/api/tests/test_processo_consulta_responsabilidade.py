"""Teste de `contar_processos_sob_responsabilidade` (task 2.2 — obrigatório,
toca histórico de tramitação; guarda da desativação de usuário, US 8.4).

Change tramitacao-manual: a "responsabilidade" agora é o responsável corrente
denormalizado no processo (`servidor_atual_id`), não mais reconstruído a
partir do último evento de despacho (ver docstring de
`contar_processos_sob_responsabilidade` em `app/services/processo_consulta.py`).
Os testes abaixo movem `servidor_atual_id`/`setor_atual_id` explicitamente
(como faria uma tramitação real) e registram o evento correspondente em
`tramitacao`, mantendo o histórico exercitado."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.db.models import StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services.processo_consulta import contar_processos_sob_responsabilidade
from tests.helpers_processo import processo_ativo, processo_concluido, servidor_com_setor, tipo_processo, unidade


def _mover_responsabilidade(db, *, processo, destino, setor_destino):
    """Simula uma tramitação: move `servidor_atual_id`/`setor_atual_id` do
    processo para `destino` e registra o evento imutável correspondente."""
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.ENVIO,
            unidade_origem_id=processo.unidade_atual_id,
            unidade_destino_id=processo.unidade_atual_id,
            setor_origem_id=processo.setor_atual_id,
            setor_destino_id=setor_destino.id,
            servidor_origem_id=processo.servidor_atual_id,
            servidor_destino_id=destino.id,
            responsavel_id=processo.servidor_atual_id,
            status_resultante=processo.status,
        )
    )
    processo.setor_atual_id = setor_destino.id
    processo.servidor_atual_id = destino.id
    db.commit()


def test_ultimo_responsavel_de_processo_em_andamento_conta(db):
    cofin = unidade(db, "COFIN")
    criador, _setor_criador = servidor_com_setor(db, cofin)
    responsavel, setor_responsavel = servidor_com_setor(
        db, cofin, nome_setor="Análise", email="responsavel@ex.com"
    )
    tipo = tipo_processo(db)

    processo = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10)
    )
    _mover_responsabilidade(db, processo=processo, destino=responsavel, setor_destino=setor_responsavel)

    assert contar_processos_sob_responsabilidade(db, responsavel) == 1
    assert contar_processos_sob_responsabilidade(db, criador) == 0


def test_criador_sem_tramitacao_conta(db):
    cofin = unidade(db, "COFIN")
    criador, _setor_criador = servidor_com_setor(db, cofin)
    tipo = tipo_processo(db)

    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10))

    assert contar_processos_sob_responsabilidade(db, criador) == 1


def test_processo_concluido_ou_arquivado_nao_conta(db):
    cofin = unidade(db, "COFIN")
    criador, _setor_criador = servidor_com_setor(db, cofin)
    tipo = tipo_processo(db)

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
    criador, _setor_criador = servidor_com_setor(db, cofin)
    primeiro_responsavel, setor_primeiro = servidor_com_setor(
        db, cofin, nome_setor="Análise", email="primeiro@ex.com"
    )
    responsavel_atual, setor_atual = servidor_com_setor(
        db, cofin, nome_setor="Financeiro", email="atual@ex.com"
    )
    tipo = tipo_processo(db)

    processo = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today() + timedelta(days=10)
    )
    _mover_responsabilidade(
        db, processo=processo, destino=primeiro_responsavel, setor_destino=setor_primeiro
    )
    _mover_responsabilidade(
        db, processo=processo, destino=responsavel_atual, setor_destino=setor_atual
    )

    assert contar_processos_sob_responsabilidade(db, primeiro_responsavel) == 0
    assert contar_processos_sob_responsabilidade(db, responsavel_atual) == 1
