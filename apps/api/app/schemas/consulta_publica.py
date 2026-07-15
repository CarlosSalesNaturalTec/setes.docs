"""Schemas públicos da Consulta Pública (Épico 7, US 7.1/7.2).

Schemas dedicados e estruturalmente sem os campos sensíveis (D1): nenhum
campo de CPF/CNPJ (`InteressadoPublicoResponse` só tem `nome`) e nenhum
campo de servidor responsável (`MovimentacaoPublicaResponse` não tem
`responsavel_id`). Isso torna o vazamento impossível por omissão de campo,
em vez de depender de `exclude` num schema interno.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

PAGE_SIZE_PUBLICO = 20


class InteressadoPublicoResponse(BaseModel):
    nome: str


class MovimentacaoPublicaResponse(BaseModel):
    criado_em: datetime
    unidade_origem: str | None
    unidade_destino: str | None
    status_resultante: str


class ProcessoPublicoResponse(BaseModel):
    numero: str
    assunto: str
    tipo_processo: str
    status: str
    unidade_atual: str
    criado_em: datetime
    interessados: list[InteressadoPublicoResponse] = Field(default_factory=list)
    historico: list[MovimentacaoPublicaResponse] = Field(default_factory=list)


class ItemPesquisaPublicaResponse(BaseModel):
    numero: str
    assunto: str
    tipo_processo: str
    status: str
    unidade_atual: str
    criado_em: datetime


class PesquisaPublicaResponse(BaseModel):
    items: list[ItemPesquisaPublicaResponse]
    total: int
    page: int
    page_size: int = PAGE_SIZE_PUBLICO
    mensagem_vazio: str | None = None
