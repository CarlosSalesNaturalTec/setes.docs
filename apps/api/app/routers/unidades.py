"""Unidades administrativas (seção 8 de tasks.md) — US 8.1."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Unidade, Usuario
from app.db.session import get_db
from app.schemas.unidades import (
    CadastrarSetorRequest,
    CadastroUnidadeRequest,
    EditarSetorRequest,
    EditarUnidadeRequest,
    SetorResponse,
    UnidadeResponse,
)
from app.security.autorizacao import get_current_user, require_perfil
from app.services import unidades as servico
from app.services.unidades import contar_processos_em_andamento

router = APIRouter(prefix="/unidades", tags=["unidades"])
# Setor é recurso próprio (D1) — path raiz `/setores/{id}` para editar/ativar,
# enquanto a criação/listagem vive sob a unidade dona.
router_setores = APIRouter(prefix="/setores", tags=["unidades"])

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
    # Desvincula também o setor: a invariante `setor.unidade_id ==
    # usuario.unidade_id` (D2) não sobreviveria a um servidor sem unidade e
    # com setor da unidade desativada.
    db.query(Usuario).filter(Usuario.unidade_id == unidade_id).update(
        {"unidade_id": None, "setor_id": None}
    )
    # Cascata de contenção: desativar a unidade desativa seus setores (D3).
    servico.desativar_setores_da_unidade(db, unidade_id)
    db.commit()

    return UnidadeResponse.de(unidade)


@router.post("/{unidade_id}/reativar", response_model=UnidadeResponse)
def reativar_unidade(
    unidade_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UnidadeResponse:
    """US 8.1 — reativa (idempotente); não repovoa `Usuario.unidade_id` dos
    servidores desvinculados na desativação (revínculo permanece manual) e
    **não** reativa os setores desativados em cascata: a reativação de cada
    setor é ação administrativa explícita (D3)."""
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    unidade.ativo = True
    db.commit()

    return UnidadeResponse.de(unidade)


# --- Setores da unidade (D1, D3) --------------------------------------------


@router.get("/{unidade_id}/setores", response_model=list[SetorResponse])
def listar_setores(
    unidade_id: uuid.UUID,
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    apenas_ativos: bool = False,
) -> list[SetorResponse]:
    """Setores da unidade. Aberto a qualquer usuário autenticado (change
    tramitacao-manual, design.md — fluxo de Reatribuição): a cascata
    unidade→setor→servidor da tela de Tramitação precisa que o Servidor
    resolva os setores da própria unidade, não só o Administrador. Cadastro/
    edição/desativação de setor continuam admin-only (rotas abaixo)."""
    setores = servico.listar_setores(db, unidade_id, apenas_ativos=apenas_ativos)
    return [SetorResponse.de(s) for s in setores]


@router.post(
    "/{unidade_id}/setores", response_model=SetorResponse, status_code=status.HTTP_201_CREATED
)
def cadastrar_setor(
    unidade_id: uuid.UUID,
    payload: CadastrarSetorRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SetorResponse:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    setor = servico.cadastrar_setor(
        db, unidade_id=unidade_id, nome=payload.nome, sigla=payload.sigla
    )
    return SetorResponse.de(setor)


@router_setores.patch("/{setor_id}", response_model=SetorResponse)
def editar_setor(
    setor_id: uuid.UUID,
    payload: EditarSetorRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SetorResponse:
    setor = servico.editar_setor(db, setor_id=setor_id, nome=payload.nome, sigla=payload.sigla)
    return SetorResponse.de(setor)


@router_setores.post("/{setor_id}/desativar", response_model=SetorResponse)
def desativar_setor(
    setor_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SetorResponse:
    """Nunca exclui — só desativa (D3), e apenas se nenhum Servidor ativo
    estiver vinculado."""
    return SetorResponse.de(servico.desativar_setor(db, setor_id))


@router_setores.post("/{setor_id}/reativar", response_model=SetorResponse)
def reativar_setor(
    setor_id: uuid.UUID,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SetorResponse:
    return SetorResponse.de(servico.reativar_setor(db, setor_id))
