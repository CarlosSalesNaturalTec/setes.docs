"""Schemas do canal público de solicitação LGPD e da fila administrativa
(Épico 10 — US 10.1/10.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SolicitacaoLgpdCreate(BaseModel):
    """Corpo do formulário público (US 10.1) — o documento de identificação
    chega como `UploadFile` separado (multipart), não neste schema."""

    numero_processo: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    cpf: str = Field(min_length=1)
    email: EmailStr
    tipo: Literal["exclusao", "anonimizacao"]


class SolicitacaoLgpdCriadaResponse(BaseModel):
    protocolo: str


class SolicitacaoLgpdResponse(BaseModel):
    """Item da fila administrativa (US 10.2 Cen.1)."""

    id: str
    protocolo: str
    criado_em: datetime
    nome_solicitante: str
    processo_numero: str
    processo_id: str
    tipo: str
    status: str
    justificativa_rejeicao: str | None

    @classmethod
    def de(cls, solicitacao, *, processo_numero: str) -> "SolicitacaoLgpdResponse":
        return cls(
            id=str(solicitacao.id),
            protocolo=solicitacao.protocolo,
            criado_em=solicitacao.criado_em,
            nome_solicitante=solicitacao.nome_solicitante,
            processo_numero=processo_numero,
            processo_id=str(solicitacao.processo_id),
            tipo=solicitacao.tipo.value,
            status=solicitacao.status.value,
            justificativa_rejeicao=solicitacao.justificativa_rejeicao,
        )


class SolicitacoesLgpdListResponse(BaseModel):
    items: list[SolicitacaoLgpdResponse] = Field(default_factory=list)


class RejeitarSolicitacaoLgpdRequest(BaseModel):
    justificativa: str = Field(min_length=1)
