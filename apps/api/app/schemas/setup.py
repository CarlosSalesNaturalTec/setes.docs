"""Schemas de inicialização do sistema (US 8.0)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SetupAdministrador(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str


class SetupUnidade(BaseModel):
    nome: str = Field(min_length=1)
    sigla: str = Field(min_length=1, max_length=20)


class SetupRequest(BaseModel):
    administrador: SetupAdministrador
    unidade: SetupUnidade


class SetupResponse(BaseModel):
    usuario_id: str
    unidade_id: str


class SetupStatusResponse(BaseModel):
    inicializado: bool
