"""Agregação do relatório consolidado de auditoria (Épico 9, US 9.2, D4/D5).

Reusa o padrão de cálculo de `services/dashboard.py` (média de dias corridos
criação→conclusão, contagem por unidade/status), mas com janela e recorte de
status próprios do relatório — não as funções do dashboard tal como estão
(D4: `total_ativos` só conta Aberto/Em Tramitação; `tempo_medio_tramitacao_dias`
usa janela fixa de 12 meses).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.db.models import Processo, StatusProcesso


def gerar_relatorio(
    db: Session,
    *,
    inicio: date | None = None,
    fim: date | None = None,
    unidade_id: uuid.UUID | None = None,
    tipo_processo_id: uuid.UUID | None = None,
) -> tuple[int, float | None, list[Processo]]:
    """Total de processos no período (D5), tempo médio de tramitação dos
    concluídos no período (dias corridos `concluido_em - criado_em`, `None`
    sem concluídos) e a lista de processos com status e unidade atual."""
    query = db.query(Processo)
    if inicio is not None:
        query = query.filter(Processo.criado_em >= inicio)
    if fim is not None:
        # Inclui o dia final inteiro (criado_em é timestamp).
        query = query.filter(Processo.criado_em <= datetime.combine(fim, time.max))
    if unidade_id is not None:
        query = query.filter(Processo.unidade_atual_id == unidade_id)
    if tipo_processo_id is not None:
        query = query.filter(Processo.tipo_processo_id == tipo_processo_id)

    processos = query.order_by(Processo.criado_em.desc()).all()

    concluidos = [
        p for p in processos if p.status == StatusProcesso.CONCLUIDO and p.concluido_em is not None
    ]
    tempo_medio: float | None = None
    if concluidos:
        dias = [(p.concluido_em.date() - p.criado_em.date()).days for p in concluidos]
        tempo_medio = sum(dias) / len(dias)

    return len(processos), tempo_medio, processos
