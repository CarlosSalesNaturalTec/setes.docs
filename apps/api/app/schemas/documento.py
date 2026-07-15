"""Schemas de documento (Épico 3, fatia A)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentoResponse(BaseModel):
    id: str
    processo_id: str
    nome_exibicao: str
    tipo_conteudo: str
    tamanho_bytes: int
    anexado_por_id: str
    anexado_em: datetime

    @classmethod
    def de(cls, documento) -> "DocumentoResponse":
        return cls(
            id=str(documento.id),
            processo_id=str(documento.processo_id),
            nome_exibicao=documento.nome_exibicao,
            tipo_conteudo=documento.tipo_conteudo,
            tamanho_bytes=documento.tamanho_bytes,
            anexado_por_id=str(documento.anexado_por_id),
            anexado_em=documento.anexado_em,
        )


class DocumentosListResponse(BaseModel):
    items: list[DocumentoResponse] = Field(default_factory=list)
