"""Schemas do parâmetro de configuração do sistema (fatia mínima da US 8.5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SistemaConfigResponse(BaseModel):
    prazo_arquivamento_dias: int = Field(examples=[30])
    dias_antecedencia_alerta_prazo: int = Field(examples=[2])
    dias_para_processo_parado: int = Field(examples=[7])


class AtualizarSistemaConfigRequest(BaseModel):
    # Campos independentes — cada um é atualizado só quando informado (D4,
    # design.md `notificacoes-e-alertas`); omitir mantém o valor vigente.
    prazo_arquivamento_dias: int | None = Field(default=None, examples=[60])
    dias_antecedencia_alerta_prazo: int | None = Field(default=None, examples=[5])
    dias_para_processo_parado: int | None = Field(default=None, examples=[10])
