"""Schemas de unidades administrativas (seção 8 de tasks.md)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UnidadeResponse(BaseModel):
    id: str
    nome: str
    sigla: str
    ativo: bool
    gestor_responsavel_id: str | None

    @classmethod
    def de(cls, unidade) -> "UnidadeResponse":  # unidade: app.db.models.Unidade
        return cls(
            id=str(unidade.id),
            nome=unidade.nome,
            sigla=unidade.sigla,
            ativo=unidade.ativo,
            gestor_responsavel_id=(
                str(unidade.gestor_responsavel_id) if unidade.gestor_responsavel_id else None
            ),
        )


class CadastroUnidadeRequest(BaseModel):
    nome: str = Field(min_length=1)
    sigla: str = Field(min_length=1, max_length=20)
    gestor_responsavel_id: str | None = None


class EditarUnidadeRequest(BaseModel):
    nome: str | None = None
    sigla: str | None = None
    gestor_responsavel_id: str | None = None
