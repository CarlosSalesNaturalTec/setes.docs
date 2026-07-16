"""Agregação de KPIs do dashboard do Gestor (Épico 6, US 6.1).

Fonte única das regras de cálculo (D3, design.md `dashboard-kpis-gestor`): o
router de KPIs e os routers de drill-down (`processos-ativos`,
`processos-parados`) chamam as mesmas funções daqui, para que a contagem do
KPI nunca divirja do tamanho da listagem detalhada.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    Processo,
    SistemaConfig,
    StatusProcesso,
    Tramitacao,
    Unidade,
    UnidadeGestor,
    Usuario,
)

DIAS_JANELA_TEMPO_MEDIO = 365


class EscopoNegado(Exception):
    """Sinaliza que `unidade_id` não pertence às unidades geridas do Gestor."""


def resolver_escopo_gestor(
    db: Session, *, gestor: Usuario, unidade_id: uuid.UUID | None
) -> list[uuid.UUID]:
    """Unidades do escopo do Gestor autenticado; `unidade_id` opcional restringe a uma delas.

    Levanta `EscopoNegado` se `unidade_id` não pertence às unidades geridas —
    o chamador (router) grava `log_seguranca` e responde 403 (D2).
    """
    geridas = [
        linha[0]
        for linha in db.query(UnidadeGestor.unidade_id)
        .filter(UnidadeGestor.gestor_id == gestor.id)
        .all()
    ]
    if unidade_id is not None:
        if unidade_id not in geridas:
            raise EscopoNegado()
        return [unidade_id]
    return geridas


def _query_ativos(db: Session, unidades: list[uuid.UUID]):
    return db.query(Processo).filter(
        Processo.unidade_atual_id.in_(unidades),
        Processo.status.in_([StatusProcesso.ABERTO, StatusProcesso.EM_TRAMITACAO]),
    )


def listar_ativos(db: Session, unidades: list[uuid.UUID]) -> list[Processo]:
    """Processos ativos (Aberto + Em Tramitação) do escopo — base do KPI e do drill-down."""
    if not unidades:
        return []
    return _query_ativos(db, unidades).order_by(Processo.prazo_em.asc(), Processo.numero.asc()).all()


def total_ativos(db: Session, unidades: list[uuid.UUID]) -> int:
    return len(listar_ativos(db, unidades))


def tempo_medio_tramitacao_dias(
    db: Session, unidades: list[uuid.UUID], *, hoje: date
) -> float | None:
    """Média em dias corridos (criação→conclusão) dos concluídos nos últimos 12 meses.

    `None` quando não há concluídos no período (US 6.1 Cen.2 — estado vazio).
    """
    if not unidades:
        return None
    limite = hoje - timedelta(days=DIAS_JANELA_TEMPO_MEDIO)
    concluidos = (
        db.query(Processo)
        .filter(
            Processo.unidade_atual_id.in_(unidades),
            Processo.status == StatusProcesso.CONCLUIDO,
            Processo.concluido_em.isnot(None),
            Processo.concluido_em >= limite,
        )
        .all()
    )
    if not concluidos:
        return None
    dias = [(p.concluido_em.date() - p.criado_em.date()).days for p in concluidos]
    return sum(dias) / len(dias)


def _ultima_movimentacao(db: Session, processo_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
    if not processo_ids:
        return {}
    linhas = (
        db.query(Tramitacao.processo_id, func.max(Tramitacao.criado_em))
        .filter(Tramitacao.processo_id.in_(processo_ids))
        .group_by(Tramitacao.processo_id)
        .all()
    )
    return {processo_id: ultima for processo_id, ultima in linhas}


def listar_parados(
    db: Session, unidades: list[uuid.UUID], *, dias_limiar: int, hoje: date
) -> list[tuple[Processo, int]]:
    """Ativos sem movimentação há mais que `dias_limiar` dias corridos.

    Processo sem nenhuma tramitação usa `processo.criado_em` como referência
    (D3). Retorna pares `(processo, dias_parados)`, ordenados do mais parado
    ao menos parado.
    """
    ativos = listar_ativos(db, unidades)
    if not ativos:
        return []
    ultimas = _ultima_movimentacao(db, [p.id for p in ativos])
    resultado: list[tuple[Processo, int]] = []
    for processo in ativos:
        referencia = ultimas.get(processo.id, processo.criado_em)
        dias_parados = (hoje - referencia.date()).days
        if dias_parados > dias_limiar:
            resultado.append((processo, dias_parados))
    resultado.sort(key=lambda item: item[1], reverse=True)
    return resultado


def total_parados(db: Session, unidades: list[uuid.UUID], *, dias_limiar: int, hoje: date) -> int:
    return len(listar_parados(db, unidades, dias_limiar=dias_limiar, hoje=hoje))


def produtividade_por_unidade(
    db: Session, unidades: list[uuid.UUID], *, hoje: date
) -> list[tuple[Unidade, int]]:
    """Processos concluídos no mês corrente, agrupados por unidade (D3)."""
    if not unidades:
        return []
    inicio_mes = hoje.replace(day=1)
    linhas = (
        db.query(Processo.unidade_atual_id, func.count(Processo.id))
        .filter(
            Processo.unidade_atual_id.in_(unidades),
            Processo.status == StatusProcesso.CONCLUIDO,
            Processo.concluido_em.isnot(None),
            Processo.concluido_em >= inicio_mes,
        )
        .group_by(Processo.unidade_atual_id)
        .all()
    )
    resultado: list[tuple[Unidade, int]] = []
    for unidade_id, quantidade in linhas:
        unidade = db.get(Unidade, unidade_id)
        resultado.append((unidade, quantidade))
    return resultado


def prazos_em_risco(
    db: Session, unidades: list[uuid.UUID], *, dias_antecedencia: int, hoje: date
) -> list[Processo]:
    """Ativos com prazo vencido ou a vencer dentro da janela de antecedência (D3)."""
    if not unidades:
        return []
    janela = hoje + timedelta(days=dias_antecedencia)
    return (
        _query_ativos(db, unidades)
        .filter(Processo.prazo_em <= janela)
        .order_by(Processo.prazo_em.asc(), Processo.numero.asc())
        .all()
    )


def dias_para_processo_parado(db: Session) -> int:
    config = db.get(SistemaConfig, 1)
    return config.dias_para_processo_parado


def dias_antecedencia_alerta_prazo(db: Session) -> int:
    config = db.get(SistemaConfig, 1)
    return config.dias_antecedencia_alerta_prazo
