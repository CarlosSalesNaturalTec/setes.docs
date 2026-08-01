"""Schemas do catálogo de modelos de documento (change modelos-de-documento).

`tipo` é restrito ao enum de domínio (design.md D7); `categoria` é texto livre,
como o cliente especificou.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TipoModeloDocumentoLiteral = Literal[
    "requerimento",
    "oficio",
    "memorando",
    "despacho",
    "parecer",
    "nota_tecnica",
    "relatorio",
    "ata",
    "contrato",
    "outro",
]


class ModeloResponse(BaseModel):
    id: str
    nome: str
    categoria: str
    tipo: TipoModeloDocumentoLiteral
    descricao: str | None
    conteudo: str
    ativo: bool
    criado_por_id: str
    criado_em: datetime

    @classmethod
    def de(cls, modelo) -> "ModeloResponse":  # modelo: app.db.models.ModeloDocumento
        return cls(
            id=str(modelo.id),
            nome=modelo.nome,
            categoria=modelo.categoria,
            tipo=modelo.tipo.value,
            descricao=modelo.descricao,
            conteudo=modelo.conteudo,
            ativo=modelo.ativo,
            criado_por_id=str(modelo.criado_por_id),
            criado_em=modelo.criado_em,
        )


class CriarModeloRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    categoria: str = Field(min_length=1, max_length=200)
    tipo: TipoModeloDocumentoLiteral
    descricao: str | None = Field(default=None, max_length=500)
    conteudo: str = Field(min_length=1)


class EditarModeloRequest(BaseModel):
    nome: str | None = Field(default=None, max_length=200)
    categoria: str | None = Field(default=None, max_length=200)
    tipo: TipoModeloDocumentoLiteral | None = None
    descricao: str | None = Field(default=None, max_length=500)
    conteudo: str | None = Field(default=None, min_length=1)
