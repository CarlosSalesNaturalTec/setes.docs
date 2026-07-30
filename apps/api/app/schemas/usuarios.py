"""Schemas de gestão de usuários (seção 7 de tasks.md)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    perfil: str
    status: str
    unidade_id: str | None
    # Segundo nível da estrutura organizacional (D1); obrigatório só para
    # Servidor (D2). `telefone`/`cargo`/`chefia_direta` são dados pessoais de
    # servidor — nunca expostos na consulta pública.
    setor_id: str | None = None
    telefone: str | None = None
    cargo: str | None = None
    chefia_direta: str | None = None
    pode_auditar: bool

    @classmethod
    def de(cls, usuario) -> "UsuarioResponse":  # usuario: app.db.models.Usuario
        return cls(
            id=str(usuario.id),
            nome=usuario.nome,
            email=usuario.email,
            perfil=usuario.perfil.value,
            status=usuario.status.value,
            unidade_id=str(usuario.unidade_id) if usuario.unidade_id else None,
            setor_id=str(usuario.setor_id) if usuario.setor_id else None,
            telefone=usuario.telefone,
            cargo=usuario.cargo,
            chefia_direta=usuario.chefia_direta,
            pode_auditar=usuario.pode_auditar,
        )


class CadastroUsuarioRequest(BaseModel):
    nome: str
    email: str
    perfil: Literal["servidor", "gestor", "administrador"]
    unidade_id: str | None = None
    setor_id: str | None = None
    telefone: str | None = Field(default=None, max_length=30)
    cargo: str | None = Field(default=None, max_length=200)
    # Texto livre: a chefia pode ser pessoa externa ao sistema (D4).
    chefia_direta: str | None = Field(default=None, max_length=200)


class AtualizarMeuPerfilRequest(BaseModel):
    """US 1.5 — auto-serviço do próprio nome (task 2.1) e dos dados funcionais
    de contato. `setor_id` é aceito porque Setor não é fronteira de permissão
    (design.md Non-Goals) e continua validado contra a unidade do usuário (D2);
    e-mail, perfil e unidade seguem sob gestão exclusiva do Administrador."""

    nome: str = Field(min_length=1, max_length=200)
    setor_id: str | None = None
    telefone: str | None = Field(default=None, max_length=30)
    cargo: str | None = Field(default=None, max_length=200)
    chefia_direta: str | None = Field(default=None, max_length=200)

    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Nome é obrigatório")
        return v


class TransferirUnidadeRequest(BaseModel):
    unidade_id: str
    # Omitido = mantém o setor atual, que a validação (D2) então rejeita por
    # pertencer à unidade antiga — transferir exige escolher setor da nova.
    setor_id: str | None = None


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
    # Nomes desnormalizados só para exibição: as rotas de catálogo de setor são
    # restritas ao Administrador (task 2.4), então o próprio Servidor não teria
    # como resolver o nome do seu setor a partir do id.
    unidade_nome: str | None = None
    setor_nome: str | None = None
    processos: list[dict] = Field(default_factory=list)
    documentos_assinados: list[dict] = Field(default_factory=list)
    mensagem_processos: str = "Nenhum processo registrado"
    mensagem_documentos: str = "Nenhum documento assinado"
