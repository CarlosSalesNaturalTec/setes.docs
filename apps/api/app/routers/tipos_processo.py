"""Tipos de processo (seção 9 de tasks.md) — US 8.2.

Change tramitacao-manual: as rotas de roteiro (`PUT .../roteiro`) e os campos
de configuração de fluxo foram removidos — tipo de processo permanece só como
classificação, sem determinar o destino da tramitação.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, TipoProcesso, Usuario
from app.db.session import get_db
from app.schemas.tipos_processo import (
    CriarTipoProcessoRequest,
    TipoProcessoResponse,
    TipoProcessoUpdate,
)
from app.security.autorizacao import get_current_user, require_perfil

router = APIRouter(prefix="/tipos-processo", tags=["tipos-processo"])

MSG_NOME_DUPLICADO = "Já existe um tipo de processo com este nome"
MSG_TIPO_NAO_ENCONTRADO = "Tipo de processo não encontrado."

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


def _response(tipo: TipoProcesso) -> TipoProcessoResponse:
    return TipoProcessoResponse(
        id=str(tipo.id),
        nome=tipo.nome,
        ativo=tipo.ativo,
        prazo_anonimizacao_anos=tipo.prazo_anonimizacao_anos,
    )


@router.get("", response_model=list[TipoProcessoResponse])
def listar_tipos_processo(
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TipoProcessoResponse]:
    """Catálogo de tipos de processo — leitura aberta a qualquer usuário
    autenticado (Servidor precisa listar o catálogo para criar processo —
    US 2.1); cadastro/edição permanecem admin-only (`_require_admin` abaixo)."""
    tipos = db.query(TipoProcesso).order_by(TipoProcesso.nome).all()
    return [_response(tipo) for tipo in tipos]


@router.post("", response_model=TipoProcessoResponse, status_code=status.HTTP_201_CREATED)
def criar_tipo_processo(
    payload: CriarTipoProcessoRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> TipoProcessoResponse:
    if db.query(TipoProcesso).filter(TipoProcesso.nome == payload.nome).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_NOME_DUPLICADO)

    tipo = TipoProcesso(nome=payload.nome, ativo=True)
    db.add(tipo)
    db.commit()
    db.refresh(tipo)

    return _response(tipo)


@router.patch("/{tipo_processo_id}", response_model=TipoProcessoResponse)
def atualizar_tipo_processo(
    tipo_processo_id: uuid.UUID,
    payload: TipoProcessoUpdate,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> TipoProcessoResponse:
    """US 10.3 Cen.2/3 — configura o prazo de anonimização LGPD (Admin-only);
    não retroativo (aplica-se só à avaliação seguinte da rotina/atendimento)."""
    tipo = db.get(TipoProcesso, tipo_processo_id)
    if tipo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_TIPO_NAO_ENCONTRADO)

    tipo.prazo_anonimizacao_anos = payload.prazo_anonimizacao_anos
    db.commit()
    db.refresh(tipo)

    return _response(tipo)
