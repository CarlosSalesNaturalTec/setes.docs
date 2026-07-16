"""Endpoints de notificação interna (sino), Épico 5 — US 5.1 Cen.2/3.

Toda operação escopa por `usuario_id = current_user` (D6, design.md
`notificacoes-e-alertas`) — ler ou marcar notificação de outro usuário é
acesso negado, registrado no padrão de `autorizacao`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Notificacao, Usuario
from app.db.session import get_db
from app.schemas.notificacao import (
    ContadorNotificacoesResponse,
    ListaNotificacoesResponse,
    MarcarTodasLidasResponse,
    NotificacaoResponse,
)
from app.security.autorizacao import get_current_user, registrar_acesso_negado
from app.services.notificacao import RETENCAO_LIDAS_DIAS

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])

MSG_NAO_ENCONTRADA = "Notificação não encontrada."
MSG_ACESSO_NEGADO = "Acesso negado — esta notificação não pertence a você"
MSG_LISTA_VAZIA = "Nenhuma notificação encontrada"


def _carregar_notificacao(db: Session, notificacao_id: uuid.UUID) -> Notificacao:
    notificacao = db.get(Notificacao, notificacao_id)
    if notificacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_NAO_ENCONTRADA)
    return notificacao


def _exigir_propria(
    db: Session, *, usuario: Usuario, notificacao: Notificacao, request: Request
) -> None:
    """US 5.1 "Acesso negado" — só o destinatário lê/marca a própria notificação."""
    if notificacao.usuario_id != usuario.id:
        registrar_acesso_negado(
            db,
            usuario=usuario,
            rota=request.url.path,
            contexto={"notificacao_id": str(notificacao.id)},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_ACESSO_NEGADO)


@router.get("", response_model=ListaNotificacoesResponse)
def listar_notificacoes(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ListaNotificacoesResponse:
    """US 5.1 Cen.4/4b — lidas ficam visíveis por 30 dias; não lidas, sempre."""
    limite = datetime.now(timezone.utc) - timedelta(days=RETENCAO_LIDAS_DIAS)
    itens = db.scalars(
        select(Notificacao)
        .where(Notificacao.usuario_id == usuario.id)
        .where((Notificacao.lida_em.is_(None)) | (Notificacao.lida_em >= limite))
        .order_by(Notificacao.criado_em.desc())
    ).all()
    return ListaNotificacoesResponse(
        items=[NotificacaoResponse.de(n) for n in itens],
        mensagem_vazio=None if itens else MSG_LISTA_VAZIA,
    )


@router.get("/contador", response_model=ContadorNotificacoesResponse)
def contador_notificacoes(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContadorNotificacoesResponse:
    """US 5.1 Cen.2/3 — só as não lidas do próprio usuário."""
    total = (
        db.query(Notificacao)
        .filter(Notificacao.usuario_id == usuario.id, Notificacao.lida_em.is_(None))
        .count()
    )
    return ContadorNotificacoesResponse(nao_lidas=total)


@router.post("/{notificacao_id}/ler", response_model=NotificacaoResponse)
def marcar_como_lida(
    notificacao_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificacaoResponse:
    """US 5.1 Cen.2 — marca uma notificação como lida; o contador decrementa."""
    notificacao = _carregar_notificacao(db, notificacao_id)
    _exigir_propria(db, usuario=usuario, notificacao=notificacao, request=request)
    if notificacao.lida_em is None:
        notificacao.lida_em = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notificacao)
    return NotificacaoResponse.de(notificacao)


@router.post("/marcar-todas-lidas", response_model=MarcarTodasLidasResponse)
def marcar_todas_como_lidas(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MarcarTodasLidasResponse:
    """US 5.1 Cen.2 — marca todas as próprias notificações não lidas; contador zera."""
    agora = datetime.now(timezone.utc)
    total = (
        db.query(Notificacao)
        .filter(Notificacao.usuario_id == usuario.id, Notificacao.lida_em.is_(None))
        .update({Notificacao.lida_em: agora}, synchronize_session=False)
    )
    db.commit()
    return MarcarTodasLidasResponse(marcadas=total)
