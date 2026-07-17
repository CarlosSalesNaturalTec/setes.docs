"""Schemas de autenticação — login, sessão, primeiro acesso, recuperação/troca
de senha (seções 4, 5, 6 de tasks.md)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UsuarioResumo(BaseModel):
    id: str
    nome: str
    email: str
    perfil: str
    status: str
    # Épico 9 — o frontend usa para exibir/ocultar a rota de relatório de
    # auditoria (US 9.2); ortogonal ao perfil (D1, auditoria-e-relatorios).
    pode_auditar: bool

    @classmethod
    def de(cls, usuario) -> "UsuarioResumo":  # usuario: app.db.models.Usuario
        return cls(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email,
            perfil=usuario.perfil.value,
            status=usuario.status.value,
            pode_auditar=usuario.pode_auditar,
        )


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class LoginResponse(BaseModel):
    token: str
    exp: datetime
    usuario: UsuarioResumo


class MeResponse(BaseModel):
    usuario: UsuarioResumo
    exp: datetime


class MensagemResponse(BaseModel):
    mensagem: str


class PrimeiroAcessoRequest(BaseModel):
    senha: str


class RecuperarSenhaRequest(BaseModel):
    email: EmailStr


class RedefinirSenhaRequest(BaseModel):
    senha: str


class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=1)
