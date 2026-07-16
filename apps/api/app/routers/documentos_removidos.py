"""Área administrativa "Documentos Removidos" (change `restauracao-documento`,
US 8.7). Listagem cross-unidade dos documentos em período de retenção e a ação
de restaurá-los, restritas ao Administrador (D5) — não usa a autorização por
unidade de `routers/documentos.py` (o Admin tem acesso irrestrito). A
restauração é a operação inversa do soft-delete de `gestao-documental`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Documento, PerfilUsuario, Usuario
from app.db.session import get_db
from app.schemas.documento import (
    DocumentoRemovidoResponse,
    DocumentoResponse,
    DocumentosRemovidosListResponse,
)
from app.security.autorizacao import require_perfil
from app.services import documento as documento_service

router = APIRouter(prefix="/admin/documentos-removidos", tags=["documentos-removidos"])

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)

MSG_DOCUMENTO_NAO_ENCONTRADO = documento_service.MSG_DOCUMENTO_NAO_ENCONTRADO


@router.get("", response_model=DocumentosRemovidosListResponse)
def listar_documentos_removidos(
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentosRemovidosListResponse:
    """US 8.7 Cen.2/3 — lista os documentos em retenção (não os já purgados),
    de qualquer unidade, com processo de origem, data de remoção e responsável."""
    documentos = documento_service.listar_removidos_em_retencao(
        db, agora=datetime.now(timezone.utc)
    )
    return DocumentosRemovidosListResponse(
        items=[DocumentoRemovidoResponse.de(d) for d in documentos]
    )


@router.post("/{documento_id}/restaurar", response_model=DocumentoResponse)
def restaurar_documento(
    documento_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentoResponse:
    """US 8.7 Cen.1/2 — restaura um documento em retenção; 404 se já purgado ou
    inexistente (a purga faz DELETE, então "purgado" é naturalmente 404, D2)."""
    documento = db.get(Documento, documento_id)
    if documento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_DOCUMENTO_NAO_ENCONTRADO
        )
    documento = documento_service.restaurar(db, documento=documento, admin=admin)
    return DocumentoResponse.de(documento)
