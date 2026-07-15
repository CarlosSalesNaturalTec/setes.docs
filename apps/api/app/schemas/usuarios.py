"""Schemas de gestão de usuários (seção 7 de tasks.md)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    perfil: str
    status: str
    unidade_id: str | None

    @classmethod
    def de(cls, usuario) -> "UsuarioResponse":  # usuario: app.db.models.Usuario
        return cls(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email,
            perfil=usuario.perfil.value,
            status=usuario.status.value,
            unidade_id=str(usuario.unidade_id) if usuario.unidade_id else None,
        )


class CadastroUsuarioRequest(BaseModel):
    nome: str
    email: str
    perfil: Literal["servidor", "gestor", "administrador"]
    unidade_id: str | None = None


class TransferirUnidadeRequest(BaseModel):
    unidade_id: str


class UnidadesGeridasRequest(BaseModel):
    unidade_ids: list[str] = Field(min_length=1)


class ListaUsuariosResponse(BaseModel):
    items: list[UsuarioResponse]
    total: int
    page: int
    page_size: int


class MeuPerfilResponse(BaseModel):
    """US 1.5 — dados cadastrais + histórico de atuação. `processos` passa a
    listar os processos em que o usuário atuou (número, assunto, data e tipo de
    ação — US 1.5 Cen.1); `documentos_assinados` segue vazio até o Épico 3/4.
    As mensagens cobrem os estados vazios (Cen.2)."""

    usuario: UsuarioResponse
    processos: list[dict] = Field(default_factory=list)
    documentos_assinados: list[dict] = Field(default_factory=list)
    mensagem_processos: str = "Nenhum processo registrado"
    mensagem_documentos: str = "Nenhum documento assinado"
