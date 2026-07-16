"""Endpoint do relatório consolidado de auditoria (Épico 9, US 9.2).

Restrito a usuário com `pode_auditar = true` (D6) — `require_pode_auditar`
não é `require_perfil`, a permissão é ortogonal ao perfil. Filtros de
período/unidade/tipo (D5); agregações reaproveitam o padrão de cálculo do
dashboard, em escopo global (D4). Sem exportação — relatório em tela.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import Usuario
from app.db.session import get_db
from app.schemas.relatorio_auditoria import ProcessoRelatorioItem, RelatorioAuditoriaResponse
from app.security.autorizacao import require_pode_auditar
from app.services import relatorio_auditoria as relatorio_service

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

MSG_RELATORIO_VAZIO = "Nenhum dado encontrado para os filtros informados"


@router.get("/relatorio", response_model=RelatorioAuditoriaResponse)
def obter_relatorio(
    auditor: Annotated[Usuario, Depends(require_pode_auditar)],
    db: Annotated[Session, Depends(get_db)],
    inicio: date | None = Query(default=None),
    fim: date | None = Query(default=None),
    unidade_id: uuid.UUID | None = Query(default=None),
    tipo_processo_id: uuid.UUID | None = Query(default=None),
) -> RelatorioAuditoriaResponse:
    """US 9.2 Cen.1/Cen.2 — relatório consolidado em tela, sem exportação."""
    total, tempo_medio, processos = relatorio_service.gerar_relatorio(
        db,
        inicio=inicio,
        fim=fim,
        unidade_id=unidade_id,
        tipo_processo_id=tipo_processo_id,
    )
    return RelatorioAuditoriaResponse(
        total_processos=total,
        tempo_medio_tramitacao_dias=tempo_medio,
        items=[ProcessoRelatorioItem.de(p) for p in processos],
        mensagem_vazio=MSG_RELATORIO_VAZIO if total == 0 else None,
    )
