"""Endpoints de documentos (Épico 3, fatia A — US 3.1, 3.2).

Upload multipart, listagem, visualização inline/streaming, download e remoção
(soft-delete). Reusa `_carregar_processo` de `routers/processos.py`. Leitura
usa `_exigir_leitura_ao_processo` (libera auditor, US 9.1); escrita (anexar/
remover) usa `_exigir_acesso_ao_processo`, estrito por unidade — a permissão
de auditoria é somente leitura e não concede escrita. Toda rejeição grava
`log_seguranca`.
"""

from __future__ import annotations

import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import Documento, Usuario
from app.db.session import get_db
from app.routers.processos import (
    _carregar_processo,
    _exigir_acesso_ao_processo,
    _exigir_leitura_ao_processo,
)
from app.schemas.documento import DocumentoResponse, DocumentosListResponse
from app.security.autorizacao import get_current_user
from app.services import documento as documento_service
from app.services.storage import get_storage

router = APIRouter(prefix="/processos/{processo_id}/documentos", tags=["documentos"])

# MIME que abrem inline (US 3.2 Cen.1); os demais (DOC/DOCX) disparam
# download automático mesmo no endpoint de "conteúdo" (US 3.2 Cen.3).
_MIME_INLINE = {"application/pdf", "image/jpeg", "image/png"}


def _content_disposition(disposicao: str, nome: str) -> str:
    """Nome de arquivo com acentuação (PT-BR) — RFC 5987 (`filename*`) além do
    `filename` simples, para navegadores que não decodificam o primeiro."""
    return f'{disposicao}; filename="{nome}"; filename*=UTF-8\'\'{quote(nome)}'


@router.post("", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def anexar_documento(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    arquivo: Annotated[UploadFile, File()],
) -> DocumentoResponse:
    """US 3.1 Cen.1/2/2b/5 — anexa um documento ao processo."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    conteudo = await arquivo.read()
    documento = documento_service.anexar(
        db,
        processo=processo,
        usuario=usuario,
        storage=get_storage(settings),
        nome_arquivo=arquivo.filename or "arquivo",
        conteudo=conteudo,
    )
    return DocumentoResponse.de(documento)


@router.get("", response_model=DocumentosListResponse)
def listar_documentos(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentosListResponse:
    """Lista os documentos visíveis do processo, autorizados por unidade."""
    processo = _carregar_processo(db, processo_id)
    _exigir_leitura_ao_processo(db, usuario=usuario, processo=processo, request=request)
    documentos = documento_service.listar(db, processo_id=processo.id)
    return DocumentosListResponse(items=[DocumentoResponse.de(d) for d in documentos])


def _disposicao(documento: Documento) -> str:
    return "inline" if documento.tipo_conteudo in _MIME_INLINE else "attachment"


@router.get("/{documento_id}/conteudo")
def conteudo_documento(
    processo_id: uuid.UUID,
    documento_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """US 3.2 Cen.1/3 — inline para PDF/imagem; attachment (com aviso do
    frontend) para DOC/DOCX. Streaming autenticado (D5) — nunca URL pública."""
    processo = _carregar_processo(db, processo_id)
    _exigir_leitura_ao_processo(db, usuario=usuario, processo=processo, request=request)
    documento = documento_service.obter_visivel(
        db, processo_id=processo.id, documento_id=documento_id
    )
    stream = get_storage(settings).abrir(documento.objeto_chave)
    return StreamingResponse(
        stream,
        media_type=documento.tipo_conteudo,
        headers={
            "Content-Disposition": _content_disposition(_disposicao(documento), documento.nome_exibicao)
        },
    )


@router.get("/{documento_id}/download")
def baixar_documento(
    processo_id: uuid.UUID,
    documento_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """US 3.2 Cen.2 — sempre `attachment`, mantendo formato e nome (D3: o
    nome de exibição já desduplicado é "o nome certo" a devolver)."""
    processo = _carregar_processo(db, processo_id)
    _exigir_leitura_ao_processo(db, usuario=usuario, processo=processo, request=request)
    documento = documento_service.obter_visivel(
        db, processo_id=processo.id, documento_id=documento_id
    )
    stream = get_storage(settings).abrir(documento.objeto_chave)
    return StreamingResponse(
        stream,
        media_type=documento.tipo_conteudo,
        headers={"Content-Disposition": _content_disposition("attachment", documento.nome_exibicao)},
    )


@router.delete("/{documento_id}", response_model=DocumentoResponse)
def remover_documento(
    processo_id: uuid.UUID,
    documento_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentoResponse:
    """US 3.1 Cen.3/4/4b/4c — soft-delete; bloqueia conforme a regra de custódia (D1)."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    documento = documento_service.obter_visivel(
        db, processo_id=processo.id, documento_id=documento_id
    )
    documento = documento_service.remover(db, processo=processo, documento=documento, usuario=usuario)
    return DocumentoResponse.de(documento)
