"""Endpoints de processo e workflow (Épico 2).

Criação (US 2.1), Kanban (US 2.3/2.8), busca (US 2.7), detalhe (US 1.4 Cen.2),
histórico (US 2.4), despacho (US 2.2) e devolução (US 2.2b). A autorização por
unidade reutiliza `require_acesso_unidade` (D6) — toda rejeição grava
`log_seguranca`.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import (
    LogSeguranca,
    Notificacao,
    PerfilUsuario,
    Processo,
    TipoEventoLog,
    TipoNotificacao,
    Unidade,
    Usuario,
)
from app.db.session import get_db
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.schemas.processo import (
    CardProcessoResponse,
    CriarProcessoRequest,
    DespacharRequest,
    DevolverRequest,
    EventoHistoricoResponse,
    HistoricoResponse,
    KanbanResponse,
    ProcessoResponse,
)
from app.security.autorizacao import (
    get_current_user,
    registrar_acesso_negado,
    require_acesso_unidade,
    require_perfil,
    tem_acesso_a_unidade,
)
from app.services import processo as processo_service
from app.services import processo_consulta
from app.services import sigilo as sigilo_service

router = APIRouter(prefix="/processos", tags=["processos"])

_require_servidor = require_perfil(PerfilUsuario.SERVIDOR)

MSG_PROCESSO_NAO_ENCONTRADO = "Processo não encontrado."
MSG_ACESSO_NEGADO_PROCESSO = (
    "Acesso negado — você não tem permissão para visualizar este processo"
)
MSG_ACESSO_RESTRITO_SIGILO = "Acesso restrito — solicite autorização ao Administrador"
MSG_KANBAN_VAZIO_SERVIDOR = "Nenhum processo encontrado nesta unidade"
MSG_KANBAN_VAZIO_GESTOR = "Nenhum processo encontrado nas unidades gerenciadas"
MSG_BUSCA_VAZIA = "Nenhum processo encontrado para os filtros informados"


def _carregar_processo(db: Session, processo_id: uuid.UUID) -> Processo:
    processo = db.get(Processo, processo_id)
    if processo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_PROCESSO_NAO_ENCONTRADO
        )
    return processo


def _exigir_acesso_ao_processo(
    db: Session, *, usuario: Usuario, processo: Processo, request: Request
) -> None:
    """Nega acesso a processo de unidade fora do escopo, gravando log (US 1.4 Cen.2).

    A permissão de auditoria (`usuario.pode_auditar`, Épico 9 US 9.1) é um
    caminho de autorização paralelo à visibilidade por unidade (D1): libera o
    acesso a qualquer processo, inclusive sigiloso, e registra o acesso
    destravado em `log_seguranca` (`acesso_auditoria`, D3) — mas só quando a
    permissão é o que de fato viabiliza o acesso, não quando o usuário já
    teria acesso pela regra de unidade.
    """
    tem_acesso_unidade = tem_acesso_a_unidade(
        db, usuario=usuario, unidade_id=processo.unidade_atual_id
    )
    if usuario.pode_auditar:
        if not tem_acesso_unidade:
            db.add(
                LogSeguranca(
                    usuario_id=usuario.id,
                    tipo_evento=TipoEventoLog.ACESSO_AUDITORIA,
                    contexto={"rota": request.url.path, "processo_id": str(processo.id)},
                )
            )
            db.commit()
        return

    if tem_acesso_unidade:
        return

    if processo.sigiloso:
        registrar_acesso_negado(
            db,
            usuario=usuario,
            rota=request.url.path,
            contexto={"processo_id": str(processo.id), "unidade": str(processo.unidade_atual_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=MSG_ACESSO_RESTRITO_SIGILO
        )

    registrar_acesso_negado(
        db,
        usuario=usuario,
        rota=request.url.path,
        contexto={"processo_id": str(processo.id), "unidade": str(processo.unidade_atual_id)},
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail=MSG_ACESSO_NEGADO_PROCESSO
    )


@router.post("", response_model=ProcessoResponse, status_code=status.HTTP_201_CREATED)
def criar_processo(
    payload: CriarProcessoRequest,
    servidor: Annotated[Usuario, Depends(_require_servidor)],
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoResponse:
    """US 2.1 — Servidor cria processo na própria unidade."""
    processo = processo_service.criar_processo(db, criador=servidor, payload=payload)
    return ProcessoResponse.de(processo)


@router.get("", response_model=KanbanResponse)
def listar_kanban(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    filtro_unidade: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> KanbanResponse:
    """US 2.3/2.8 — Kanban da unidade (Servidor) ou consolidado (Gestor)."""
    itens, total = processo_consulta.listar_kanban(
        db, usuario=usuario, filtro_unidade=filtro_unidade, page=page, page_size=page_size
    )
    hoje = date.today()
    cards = [CardProcessoResponse.de(p, hoje=hoje) for p in itens]
    mensagem = None
    if total == 0:
        mensagem = (
            MSG_KANBAN_VAZIO_GESTOR
            if usuario.perfil == PerfilUsuario.GESTOR
            else MSG_KANBAN_VAZIO_SERVIDOR
        )
    return KanbanResponse(
        items=cards, total=total, page=page, page_size=page_size, mensagem_vazio=mensagem
    )


@router.get("/busca", response_model=KanbanResponse)
def buscar_processos(
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    numero: str | None = Query(default=None),
    assunto: str | None = Query(default=None),
    data_inicial: date | None = Query(default=None),
    data_final: date | None = Query(default=None),
) -> KanbanResponse:
    """US 2.7 — busca interna restrita ao escopo de unidade."""
    itens = processo_consulta.buscar(
        db,
        usuario=usuario,
        numero=numero,
        assunto=assunto,
        data_inicial=data_inicial,
        data_final=data_final,
    )
    hoje = date.today()
    cards = [CardProcessoResponse.de(p, hoje=hoje) for p in itens]
    mensagem = MSG_BUSCA_VAZIA if not cards else None
    return KanbanResponse(
        items=cards, total=len(cards), page=1, page_size=len(cards), mensagem_vazio=mensagem
    )


@router.get("/{processo_id}", response_model=ProcessoResponse)
def detalhe_processo(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoResponse:
    """US 1.4 Cen.2 — detalhe por unidade; acesso fora do escopo é negado e logado."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    return ProcessoResponse.de(processo)


@router.get("/{processo_id}/historico", response_model=HistoricoResponse)
def historico_processo(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> HistoricoResponse:
    """US 2.4 — linha do tempo imutável; vazia para processo recém-criado."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    eventos = processo_consulta.historico(db, processo.id)
    return HistoricoResponse(
        processo_id=str(processo.id),
        criado_em=processo.criado_em,
        eventos=[EventoHistoricoResponse.de(e) for e in eventos],
        mensagem_vazio=None if eventos else "Nenhuma movimentação registrada",
    )


def _enfileirar_emails_novo_processo(
    db: Session, *, notificacoes: list[Notificacao], processo: Processo, settings: Settings
) -> None:
    """US 5.2 Cen.1 — best-effort, após o commit da transação de despacho (D1)."""
    if not notificacoes:
        return
    unidade_origem = (
        db.get(Unidade, notificacoes[0].unidade_origem_id)
        if notificacoes[0].unidade_origem_id
        else None
    )
    link = f"{settings.frontend_base_url}/processos/{processo.id}"
    config = config_from_settings(settings)
    for notificacao in notificacoes:
        destinatario = db.get(Usuario, notificacao.usuario_id)
        if destinatario is None:
            continue
        origem_txt = f", vindo da unidade {unidade_origem.nome}" if unidade_origem else ""
        enqueue_email_seguro(
            EmailMessage(
                to=destinatario.email,
                subject=f"Novo processo recebido — {processo.numero}",
                body=(
                    f"O processo {processo.numero} — {processo.assunto} foi despachado para a "
                    f"sua unidade{origem_txt}. Acesse: {link}"
                ),
            ),
            event_id=f"novo-processo:{notificacao.id}",
            config=config,
        )


@router.post("/{processo_id}/despachar", response_model=ProcessoResponse)
def despachar_processo(
    processo_id: uuid.UUID,
    payload: DespacharRequest,
    request: Request,
    servidor: Annotated[Usuario, Depends(_require_servidor)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProcessoResponse:
    """US 2.2 — despacho para a próxima unidade; na última, conclusão confirmada."""
    processo = _carregar_processo(db, processo_id)
    require_acesso_unidade(
        db, usuario=servidor, unidade_id=processo.unidade_atual_id, rota=request.url.path
    )
    processo, notificacoes = processo_service.despachar(
        db, processo=processo, responsavel=servidor, confirmar=payload.confirmar
    )
    novo_processo = [n for n in notificacoes if n.tipo == TipoNotificacao.NOVO_PROCESSO]
    _enfileirar_emails_novo_processo(
        db, notificacoes=novo_processo, processo=processo, settings=settings
    )
    return ProcessoResponse.de(processo)


@router.post("/{processo_id}/devolver", response_model=ProcessoResponse)
def devolver_processo(
    processo_id: uuid.UUID,
    payload: DevolverRequest,
    request: Request,
    servidor: Annotated[Usuario, Depends(_require_servidor)],
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoResponse:
    """US 2.2b — devolução para a unidade anterior, com motivo obrigatório."""
    processo = _carregar_processo(db, processo_id)
    require_acesso_unidade(
        db, usuario=servidor, unidade_id=processo.unidade_atual_id, rota=request.url.path
    )
    processo = processo_service.devolver(
        db, processo=processo, responsavel=servidor, payload=payload
    )
    return ProcessoResponse.de(processo)


@router.post("/{processo_id}/sigilo", response_model=ProcessoResponse)
def marcar_sigilo(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoResponse:
    """US 2.6 Cen.1/1b — marca sigilo; idempotente (D4)."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    processo = sigilo_service.marcar(db, processo=processo, responsavel=usuario)
    return ProcessoResponse.de(processo)


@router.delete("/{processo_id}/sigilo", response_model=ProcessoResponse)
def remover_sigilo(
    processo_id: uuid.UUID,
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoResponse:
    """US 2.6 Cen.2 — remove sigilo; idempotente (D4)."""
    processo = _carregar_processo(db, processo_id)
    _exigir_acesso_ao_processo(db, usuario=usuario, processo=processo, request=request)
    processo = sigilo_service.remover(db, processo=processo, responsavel=usuario)
    return ProcessoResponse.de(processo)
