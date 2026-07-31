"""Testes obrigatórios da rotina automática trimestral de anonimização LGPD
(US 10.3, tasks 7.3/7.4/7.5) — dado pessoal e idempotência/retomada."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import LogSeguranca, ProcessoInteressado, StatusProcesso, TipoEventoLog
from app.services.anonimizacao_lgpd import processar_anonimizacao_automatica
from tests.helpers_processo import processo_concluido, servidor_com_setor, tipo_processo, unidade

AGORA = datetime(2026, 7, 15, 4, 0, 0, tzinfo=timezone.utc)


def _base(db, *, prazo_anos=5):
    cofin = unidade(db, "COFIN")
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    tipo = tipo_processo(db)
    tipo.prazo_anonimizacao_anos = prazo_anos
    db.commit()
    return cofin, criador, tipo


def _processo_arquivado(db, *, unidade, criador, tipo, arquivado_ha_dias):
    arquivar_em = AGORA - timedelta(days=arquivado_ha_dias)
    processo = processo_concluido(
        db,
        unidade=unidade,
        criador=criador,
        tipo=tipo,
        concluido_em=arquivar_em - timedelta(days=1),
        arquivar_em=arquivar_em,
        status=StatusProcesso.ARQUIVADO,
    )
    interessado = ProcessoInteressado(processo_id=processo.id, nome="Fulano de Tal", documento="52998224725")
    db.add(interessado)
    db.commit()
    db.refresh(interessado)
    return processo, interessado


def test_processo_vencido_e_anonimizado_dentro_do_prazo_nao(db):
    cofin, criador, tipo = _base(db, prazo_anos=5)
    vencido, interessado_vencido = _processo_arquivado(
        db, unidade=cofin, criador=criador, tipo=tipo, arquivado_ha_dias=5 * 365 + 10
    )
    dentro_prazo, interessado_dentro_prazo = _processo_arquivado(
        db, unidade=cofin, criador=criador, tipo=tipo, arquivado_ha_dias=30
    )

    total = processar_anonimizacao_automatica(db, agora=AGORA)

    assert total == 1
    db.refresh(interessado_vencido)
    assert interessado_vencido.nome == "Titular Anonimizado"
    assert interessado_vencido.anonimizado_em is not None

    db.refresh(interessado_dentro_prazo)
    assert interessado_dentro_prazo.nome == "Fulano de Tal"
    assert interessado_dentro_prazo.anonimizado_em is None

    db.refresh(vencido)
    assert vencido.status == StatusProcesso.ARQUIVADO
    db.refresh(dentro_prazo)
    assert dentro_prazo.status == StatusProcesso.ARQUIVADO


def test_reexecucao_sobre_mesmo_estado_nao_reprocessa(db):
    cofin, criador, tipo = _base(db, prazo_anos=5)
    processo, interessado = _processo_arquivado(
        db, unidade=cofin, criador=criador, tipo=tipo, arquivado_ha_dias=5 * 365 + 10
    )

    n1 = processar_anonimizacao_automatica(db, agora=AGORA)
    n2 = processar_anonimizacao_automatica(db, agora=AGORA + timedelta(days=1))

    assert n1 == 1
    assert n2 == 0
    eventos = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.INTERESSADO_ANONIMIZADO)
        .filter(LogSeguranca.contexto["processo_id"].astext == str(processo.id))
        .all()
    )
    assert len(eventos) == 1


def test_retomada_apos_indisponibilidade_anonimiza_todos_vencidos(db):
    cofin, criador, tipo = _base(db, prazo_anos=5)
    processos_e_interessados = [
        _processo_arquivado(db, unidade=cofin, criador=criador, tipo=tipo, arquivado_ha_dias=5 * 365 + d)
        for d in (5, 15, 25)
    ]

    total = processar_anonimizacao_automatica(db, agora=AGORA)

    assert total == 3
    for _processo, interessado in processos_e_interessados:
        db.refresh(interessado)
        assert interessado.nome == "Titular Anonimizado"
        assert interessado.anonimizado_em is not None

    eventos = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.INTERESSADO_ANONIMIZADO)
        .all()
    )
    assert len(eventos) == 3
