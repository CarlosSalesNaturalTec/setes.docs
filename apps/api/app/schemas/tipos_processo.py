"""Schemas de tipos de processo e roteiros (seção 9 de tasks.md)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EtapaRoteiroResponse(BaseModel):
    unidade_id: str
    ordem: int


class RoteiroResponse(BaseModel):
    id: str
    vigente: bool
    etapas: list[EtapaRoteiroResponse]


class TipoProcessoResponse(BaseModel):
    id: str
    nome: str
    ativo: bool
    roteiro: RoteiroResponse
    # US 10.3 Cen.2 (Épico 10) — prazo legal de anonimização LGPD, em anos.
    prazo_anonimizacao_anos: int


class CriarTipoProcessoRequest(BaseModel):
    nome: str = Field(min_length=1)
    # Sequência de IDs de unidade, na ordem de tramitação (COFIN -> AJUR -> DIRAD).
    unidade_ids: list[str] = Field(default_factory=list)


class AtualizarRoteiroRequest(BaseModel):
    unidade_ids: list[str] = Field(default_factory=list)


class TipoProcessoUpdate(BaseModel):
    """US 10.3 Cen.2/3 — só o prazo de anonimização é editável por esta rota
    (nome/roteiro têm rotas próprias). Inteiro positivo (Cen.3)."""

    prazo_anonimizacao_anos: int = Field(gt=0)
