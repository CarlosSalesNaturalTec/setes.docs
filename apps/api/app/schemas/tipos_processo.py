"""Schemas de tipos de processo (seção 9 de tasks.md).

Change tramitacao-manual: os requisitos de roteiro (definição, versionamento,
validação) foram removidos — tipo de processo permanece só como classificação
(filtro de Kanban, dashboard, prazo de anonimização LGPD).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TipoProcessoResponse(BaseModel):
    id: str
    nome: str
    ativo: bool
    # US 10.3 Cen.2 (Épico 10) — prazo legal de anonimização LGPD, em anos.
    prazo_anonimizacao_anos: int


class CriarTipoProcessoRequest(BaseModel):
    nome: str = Field(min_length=1)


class TipoProcessoUpdate(BaseModel):
    """US 10.3 Cen.2/3 — só o prazo de anonimização é editável por esta rota
    (nome tem rota própria). Inteiro positivo (Cen.3)."""

    prazo_anonimizacao_anos: int = Field(gt=0)
