"""Serviços de unidade administrativa (seção 8 de tasks.md)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session


def contar_processos_em_andamento(db: Session, unidade_id: uuid.UUID) -> int:
    """Quantos processos em andamento a unidade possui (US 8.1 Cen.3).

    TODO(épico-2): substituir por contagem real de `processo.status` quando a
    tabela `processo` existir. Até lá, retorna 0 — o único valor correto
    possível, já que nenhum processo existe no sistema neste change (D9).
    """
    return 0
