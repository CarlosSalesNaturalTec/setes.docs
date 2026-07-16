"""Parâmetro de prazo de arquivamento (fatia mínima da US 8.5) — admin-only."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, SistemaConfig, Usuario
from app.db.session import get_db
from app.schemas.sistema_config import AtualizarSistemaConfigRequest, SistemaConfigResponse
from app.security.autorizacao import require_perfil

router = APIRouter(prefix="/sistema-config", tags=["sistema-config"])

MSG_VALOR_INVALIDO = "O valor deve ser um número inteiro positivo"

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


def _response(config: SistemaConfig) -> SistemaConfigResponse:
    return SistemaConfigResponse(
        prazo_arquivamento_dias=config.prazo_arquivamento_dias,
        dias_antecedencia_alerta_prazo=config.dias_antecedencia_alerta_prazo,
    )


@router.get("", response_model=SistemaConfigResponse)
def obter_sistema_config(
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SistemaConfigResponse:
    config = db.get(SistemaConfig, 1)
    return _response(config)


@router.put("", response_model=SistemaConfigResponse)
def atualizar_sistema_config(
    payload: AtualizarSistemaConfigRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> SistemaConfigResponse:
    """US 8.5 Cen.1/3 — só afeta conclusões futuras (o congelamento em
    `services/processo.py` já garante a não-retroatividade). US 5.4/8.5 — o
    parâmetro de antecedência de alerta é lido em runtime pela rotina diária
    (D4, design.md `notificacoes-e-alertas`); cada campo só é alterado se
    informado no payload."""
    config = db.get(SistemaConfig, 1)

    if payload.prazo_arquivamento_dias is not None:
        if payload.prazo_arquivamento_dias < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_VALOR_INVALIDO
            )
        config.prazo_arquivamento_dias = payload.prazo_arquivamento_dias

    if payload.dias_antecedencia_alerta_prazo is not None:
        if payload.dias_antecedencia_alerta_prazo < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_VALOR_INVALIDO
            )
        config.dias_antecedencia_alerta_prazo = payload.dias_antecedencia_alerta_prazo

    db.commit()
    return _response(config)
