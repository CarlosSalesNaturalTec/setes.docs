"""Schemas do relatório consolidado de auditoria (Épico 9, US 9.2).

A forma do payload espelha o cálculo de `services/relatorio_auditoria.py`
(D4/D5, design.md). `status` é a enum `StatusProcesso` — nunca texto livre.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import StatusProcesso


class ProcessoRelatorioItem(BaseModel):
    id: str
    numero: str
    assunto: str
    status: StatusProcesso
    unidade_atual_id: str
    tipo_processo_id: str
    criado_em: datetime
    concluido_em: datetime | None

    @classmethod
    def de(cls, processo) -> "ProcessoRelatorioItem":
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            status=processo.status,
            unidade_atual_id=str(processo.unidade_atual_id),
            tipo_processo_id=str(processo.tipo_processo_id),
            criado_em=processo.criado_em,
            concluido_em=processo.concluido_em,
        )


class RelatorioAuditoriaResponse(BaseModel):
    """US 9.2 Cen.1/Cen.2 — consolidado em tela, sem exportação."""

    total_processos: int
    tempo_medio_tramitacao_dias: float | None
    items: list[ProcessoRelatorioItem] = Field(default_factory=list)
    mensagem_vazio: str | None = None
