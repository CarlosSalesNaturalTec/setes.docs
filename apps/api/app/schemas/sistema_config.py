"""Schemas do parâmetro de configuração do sistema (fatia mínima da US 8.5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SistemaConfigResponse(BaseModel):
    prazo_arquivamento_dias: int = Field(examples=[30])


class AtualizarSistemaConfigRequest(BaseModel):
    prazo_arquivamento_dias: int = Field(examples=[60])
