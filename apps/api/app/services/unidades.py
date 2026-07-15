"""Serviços de unidade administrativa (seção 8 de tasks.md)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.services.processo_consulta import contar_em_andamento


def contar_processos_em_andamento(db: Session, unidade_id: uuid.UUID) -> int:
    """Quantos processos em andamento (Aberto/Em Tramitação) a unidade possui
    (US 8.1 Cen.3). Agora que a tabela `processo` existe, a contagem é efetiva
    (proposal — fecha a pendência de `unidades-administrativas`)."""
    return contar_em_andamento(db, unidade_id)
