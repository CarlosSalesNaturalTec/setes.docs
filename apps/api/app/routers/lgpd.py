"""Canal público de solicitação LGPD e fila administrativa (Épico 10 — US
10.1/10.2). O endpoint público não tem dependência de sessão/JWT (acessível
ao Cidadão), sob o mesmo rate limiting de `consulta_publica`. As rotas
administrativas são Admin-only (US 10.2 Cen. Acesso negado)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import PerfilUsuario, Processo, Usuario
from app.db.session import get_db
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.rate_limit import RATE_LIMIT_CONSULTA_PUBLICA, limiter
from app.schemas.lgpd import (
    RejeitarSolicitacaoLgpdRequest,
    SolicitacaoLgpdCriadaResponse,
    SolicitacaoLgpdResponse,
    SolicitacoesLgpdListResponse,
)
from app.security.autorizacao import require_perfil
from app.services import solicitacao_lgpd as solicitacao_lgpd_service
from app.services.storage import get_lgpd_storage

router = APIRouter(tags=["lgpd"])

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


def _processo_numero(db: Session, processo_id: uuid.UUID) -> str:
    processo = db.get(Processo, processo_id)
    return processo.numero if processo else ""


def _enfileirar_email_confirmacao(settings: Settings, *, protocolo: str, email: str) -> None:
    enqueue_email_seguro(
        EmailMessage(
            to=email,
            subject=f"Solicitação LGPD registrada — {protocolo}",
            body=(
                f"Solicitação registrada com sucesso. Protocolo: {protocolo}. "
                "Você receberá a resposta no e-mail informado em até 15 dias."
            ),
        ),
        event_id=f"lgpd-confirmacao:{protocolo}",
        config=config_from_settings(settings),
    )


def _enfileirar_email_atendida(settings: Settings, *, protocolo: str, email: str) -> None:
    enqueue_email_seguro(
        EmailMessage(
            to=email,
            subject=f"Solicitação LGPD atendida — {protocolo}",
            body=f"Sua solicitação LGPD (protocolo {protocolo}) foi atendida e concluída.",
        ),
        event_id=f"lgpd-atendida:{protocolo}",
        config=config_from_settings(settings),
    )


def _enfileirar_email_rejeitada(settings: Settings, *, protocolo: str, email: str, justificativa: str) -> None:
    enqueue_email_seguro(
        EmailMessage(
            to=email,
            subject=f"Solicitação LGPD rejeitada — {protocolo}",
            body=(
                f"Sua solicitação LGPD (protocolo {protocolo}) foi rejeitada. "
                f"Justificativa: {justificativa}"
            ),
        ),
        event_id=f"lgpd-rejeitada:{protocolo}",
        config=config_from_settings(settings),
    )


@router.post(
    "/publico/lgpd/solicitacoes",
    response_model=SolicitacaoLgpdCriadaResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(RATE_LIMIT_CONSULTA_PUBLICA)
async def criar_solicitacao(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    arquivo: Annotated[UploadFile, File()],
    numero_processo: Annotated[str, Form()] = "",
    nome: Annotated[str, Form()] = "",
    cpf: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    tipo: Annotated[str, Form()] = "",
) -> SolicitacaoLgpdCriadaResponse:
    """US 10.1 Cen.1/2/3/3b/4 — registra a solicitação e enfileira a confirmação."""
    conteudo = await arquivo.read()
    solicitacao = solicitacao_lgpd_service.criar_solicitacao(
        db,
        storage=get_lgpd_storage(settings),
        numero_processo=numero_processo,
        nome=nome,
        cpf=cpf,
        email=email,
        tipo=tipo,
        nome_arquivo=arquivo.filename or "documento",
        conteudo=conteudo,
    )
    _enfileirar_email_confirmacao(
        settings, protocolo=solicitacao.protocolo, email=solicitacao.email_solicitante
    )
    return SolicitacaoLgpdCriadaResponse(protocolo=solicitacao.protocolo)


@router.get("/lgpd/solicitacoes", response_model=SolicitacoesLgpdListResponse)
def listar_solicitacoes(
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
    status_filtro: str | None = Query(default=None, alias="status"),
) -> SolicitacoesLgpdListResponse:
    """US 10.2 Cen.1 — fila administrativa, com filtro opcional por status."""
    solicitacoes = solicitacao_lgpd_service.listar(db, status_filtro=status_filtro)
    return SolicitacoesLgpdListResponse(
        items=[
            SolicitacaoLgpdResponse.de(s, processo_numero=_processo_numero(db, s.processo_id))
            for s in solicitacoes
        ]
    )


@router.post("/lgpd/solicitacoes/{solicitacao_id}/atender", response_model=SolicitacaoLgpdResponse)
def atender_solicitacao(
    solicitacao_id: uuid.UUID,
    admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SolicitacaoLgpdResponse:
    """US 10.2 Cen.2 — anonimiza os interessados do processo indicado."""
    solicitacao = solicitacao_lgpd_service.obter(db, solicitacao_id)
    solicitacao = solicitacao_lgpd_service.atender(
        db, solicitacao=solicitacao, admin=admin, agora=datetime.now(timezone.utc)
    )
    _enfileirar_email_atendida(
        settings, protocolo=solicitacao.protocolo, email=solicitacao.email_solicitante
    )
    return SolicitacaoLgpdResponse.de(
        solicitacao, processo_numero=_processo_numero(db, solicitacao.processo_id)
    )


@router.post("/lgpd/solicitacoes/{solicitacao_id}/rejeitar", response_model=SolicitacaoLgpdResponse)
def rejeitar_solicitacao(
    solicitacao_id: uuid.UUID,
    payload: RejeitarSolicitacaoLgpdRequest,
    admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SolicitacaoLgpdResponse:
    """US 10.2 Cen.3/3b — exige justificativa não vazia."""
    solicitacao = solicitacao_lgpd_service.obter(db, solicitacao_id)
    solicitacao = solicitacao_lgpd_service.rejeitar(
        db,
        solicitacao=solicitacao,
        admin=admin,
        justificativa=payload.justificativa,
        agora=datetime.now(timezone.utc),
    )
    _enfileirar_email_rejeitada(
        settings,
        protocolo=solicitacao.protocolo,
        email=solicitacao.email_solicitante,
        justificativa=payload.justificativa,
    )
    return SolicitacaoLgpdResponse.de(
        solicitacao, processo_numero=_processo_numero(db, solicitacao.processo_id)
    )
