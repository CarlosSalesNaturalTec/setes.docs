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


class DocumentoRemovidoResponse(BaseModel):
    """Item da área administrativa "Documentos Removidos" (US 8.7): identifica o
    anexo em retenção com o processo de origem (número/assunto), a data de
    remoção e o responsável pela remoção."""

    id: str
    processo_id: str
    processo_numero: str
    processo_assunto: str
    nome_exibicao: str
    removido_em: datetime
    removido_por_id: str

    @classmethod
    def de(cls, documento) -> "DocumentoRemovidoResponse":
        return cls(
            id=str(documento.id),
            processo_id=str(documento.processo_id),
            processo_numero=documento.processo.numero,
            processo_assunto=documento.processo.assunto,
            nome_exibicao=documento.nome_exibicao,
            removido_em=documento.removido_em,
            removido_por_id=str(documento.removido_por_id),
        )


class DocumentosRemovidosListResponse(BaseModel):
    items: list[DocumentoRemovidoResponse] = Field(default_factory=list)
