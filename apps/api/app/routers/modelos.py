"""Catálogo de modelos de documento (change modelos-de-documento).

CRUD restrito ao Administrador (`_require_admin`); a leitura do catálogo é
liberada a qualquer usuário autenticado — Servidor e Gestor precisam listar
os modelos ativos para escolher um na abertura de processo (US 2.1). Nenhuma
rota de exclusão física: um modelo é só desativado/reativado (D6).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, TipoModeloDocumento, Usuario
from app.db.session import get_db
from app.schemas.modelos import CriarModeloRequest, EditarModeloRequest, ModeloResponse
from app.security.autorizacao import get_current_user, require_perfil
from app.services import modelo_documento as servico

router = APIRouter(prefix="/modelos", tags=["modelos"])

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


@router.get("", response_model=list[ModeloResponse])
def listar_modelos(
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    ativo: bool | None = None,
) -> list[ModeloResponse]:
    """Catálogo de modelos — leitura aberta a qualquer usuário autenticado
    (Servidor/Gestor precisam escolher modelo na abertura de processo).
    `ativo=true` filtra só os selecionáveis; omitido lista todos (tela
    administrativa)."""
    modelos = servico.listar(db, apenas_ativos=bool(ativo))
    return [ModeloResponse.de(m) for m in modelos]


@router.get("/{modelo_id}", response_model=ModeloResponse)
def obter_modelo(
    modelo_id: uuid.UUID,
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ModeloResponse:
    return ModeloResponse.de(servico.obter(db, modelo_id))


@router.post("", response_model=ModeloResponse, status_code=status.HTTP_201_CREATED)
def criar_modelo(
    payload: CriarModeloRequest,
    admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ModeloResponse:
    modelo = servico.criar(
        db,
        nome=payload.nome,
        categoria=payload.categoria,
        tipo=TipoModeloDocumento(payload.tipo),
        descricao=payload.descricao,
        conteudo=payload.conteudo,
        criado_por=admin,
    )
    return ModeloResponse.de(modelo)


@router.patch("/{modelo_id}", response_model=ModeloResponse)
def editar_modelo(
    modelo_id: uuid.UUID,
    payload: EditarModeloRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ModeloResponse:
    modelo = servico.editar(
        db,
        modelo_id=modelo_id,
        nome=payload.nome,
        categoria=payload.categoria,
        tipo=TipoModeloDocumento(payload.tipo) if payload.tipo is not None else None,
        descricao=payload.descricao,
        conteudo=payload.conteudo,
    )
    return ModeloResponse.de(modelo)


@router.post("/{modelo_id}/desativar", response_model=ModeloResponse)
def desativar_modelo(
    modelo_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ModeloResponse:
    return ModeloResponse.de(servico.desativar(db, modelo_id))


@router.post("/{modelo_id}/reativar", response_model=ModeloResponse)
def reativar_modelo(
    modelo_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ModeloResponse:
    return ModeloResponse.de(servico.reativar(db, modelo_id))
