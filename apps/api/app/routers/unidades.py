"""Unidades administrativas (seção 8 de tasks.md) — US 8.1."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Unidade, Usuario
from app.db.session import get_db
from app.schemas.unidades import CadastroUnidadeRequest, EditarUnidadeRequest, UnidadeResponse
from app.security.autorizacao import get_current_user, require_perfil
from app.services.unidades import contar_processos_em_andamento

router = APIRouter(prefix="/unidades", tags=["unidades"])

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


@router.get("", response_model=list[UnidadeResponse])
def listar_unidades(
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UnidadeResponse]:
    """Catálogo de unidades (nome/sigla/ativo) — qualquer usuário autenticado
    pode listar: dado não sensível, usado pelos formulários de cadastro/CRUD
    (Administrador/Gestor) e para o Servidor resolver o nome da unidade de
    destino após despachar/devolver um processo (ver openspec/changes/
    corrigir-feedback-despacho-devolucao). Cadastro/edição/desativação
    continuam restritos ao Administrador (`_require_admin`, capability
    `unidades-administrativas`)."""
    unidades = db.query(Unidade).order_by(Unidade.nome).all()
    return [UnidadeResponse.de(u) for u in unidades]


@router.post("", response_model=UnidadeResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_unidade(
    payload: CadastroUnidadeRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UnidadeResponse:
    gestor_id = uuid.UUID(payload.gestor_responsavel_id) if payload.gestor_responsavel_id else None
    if gestor_id is not None and db.get(Usuario, gestor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Gestor responsável não encontrado."
        )

    unidade = Unidade(nome=payload.nome, sigla=payload.sigla, ativo=True, gestor_responsavel_id=gestor_id)
    db.add(unidade)
    db.commit()
    return UnidadeResponse.de(unidade)


@router.patch("/{unidade_id}", response_model=UnidadeResponse)
def editar_unidade(
    unidade_id: uuid.UUID,
    payload: EditarUnidadeRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UnidadeResponse:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    if payload.nome is not None:
        unidade.nome = payload.nome
    if payload.sigla is not None:
        unidade.sigla = payload.sigla
    if payload.gestor_responsavel_id is not None:
        gestor_id = uuid.UUID(payload.gestor_responsavel_id)
        if db.get(Usuario, gestor_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Gestor responsável não encontrado."
            )
        unidade.gestor_responsavel_id = gestor_id

    db.commit()
    return UnidadeResponse.de(unidade)


@router.post("/{unidade_id}/desativar", response_model=UnidadeResponse)
def desativar_unidade(
    unidade_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UnidadeResponse:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    pendentes = contar_processos_em_andamento(db, unidade_id)
    if pendentes > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Esta unidade possui {pendentes} processo(s) em andamento. Para desativá-la, "
                "primeiro redistribua ou conclua todos os processos pendentes."
            ),
        )

    unidade.ativo = False
    db.query(Usuario).filter(Usuario.unidade_id == unidade_id).update({"unidade_id": None})
    db.commit()

    return UnidadeResponse.de(unidade)


@router.post("/{unidade_id}/reativar", response_model=UnidadeResponse)
def reativar_unidade(
    unidade_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UnidadeResponse:
    """US 8.1 — reativa (idempotente); não repovoa `Usuario.unidade_id` dos
    servidores desvinculados na desativação (revínculo permanece manual)."""
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    unidade.ativo = True
    db.commit()

    return UnidadeResponse.de(unidade)
