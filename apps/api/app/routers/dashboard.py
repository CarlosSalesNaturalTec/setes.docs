"""Endpoints do dashboard de KPIs do Gestor (Épico 6, US 6.1).

Restrito ao perfil Gestor, escopado às unidades geridas (`unidade_gestor`),
com filtro opcional por uma unidade gerida. O helper de escopo (D2) é
compartilhado pelo endpoint de KPIs e pelos dois drill-downs — toda rejeição
grava `log_seguranca`.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Usuario
from app.db.session import get_db
from app.schemas.dashboard import (
    ContagensPorStatusResponse,
    DashboardKpisResponse,
    DistribuicaoItem,
    DistribuicoesResponse,
    PrazoRiscoItem,
    ProcessoAtivoItem,
    ProcessoParadoItem,
    ProcessosAtivosResponse,
    ProcessosParadosResponse,
    ProdutividadeUnidadeItem,
)
from app.security.autorizacao import registrar_acesso_negado, require_perfil
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_require_gestor = require_perfil(PerfilUsuario.GESTOR)

MSG_ACESSO_NEGADO_UNIDADE = "Acesso negado a esta unidade."


def _resolver_escopo_ou_negar(
    db: Session, *, gestor: Usuario, unidade_id: uuid.UUID | None, request: Request
) -> list[uuid.UUID]:
    try:
        return dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=unidade_id)
    except dashboard_service.EscopoNegado as exc:
        registrar_acesso_negado(
            db,
            usuario=gestor,
            rota=request.url.path,
            contexto={"unidade_solicitada": str(unidade_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=MSG_ACESSO_NEGADO_UNIDADE
        ) from exc


@router.get("/kpis", response_model=DashboardKpisResponse)
def obter_kpis(
    request: Request,
    gestor: Annotated[Usuario, Depends(_require_gestor)],
    db: Annotated[Session, Depends(get_db)],
    unidade_id: uuid.UUID | None = Query(default=None),
) -> DashboardKpisResponse:
    """US 6.1 Cen.1/Cen.2/Cen.3 — KPIs consolidados (ou de uma unidade) do escopo do Gestor."""
    unidades = _resolver_escopo_ou_negar(db, gestor=gestor, unidade_id=unidade_id, request=request)
    hoje = date.today()

    limiar_parado = dashboard_service.dias_para_processo_parado(db)
    antecedencia_prazo = dashboard_service.dias_antecedencia_alerta_prazo(db)

    parados = dashboard_service.listar_parados(db, unidades, dias_limiar=limiar_parado, hoje=hoje)
    produtividade = dashboard_service.produtividade_por_unidade(db, unidades, hoje=hoje)
    em_risco = dashboard_service.prazos_em_risco(
        db, unidades, dias_antecedencia=antecedencia_prazo, hoje=hoje
    )

    return DashboardKpisResponse(
        total_processos_ativos=dashboard_service.total_ativos(db, unidades),
        tempo_medio_tramitacao_dias=dashboard_service.tempo_medio_tramitacao_dias(
            db, unidades, hoje=hoje
        ),
        total_processos_parados=len(parados),
        produtividade_por_unidade=[
            ProdutividadeUnidadeItem(
                unidade_id=str(unidade_obj.id), unidade_nome=unidade_obj.nome, quantidade=quantidade
            )
            for unidade_obj, quantidade in produtividade
        ],
        prazos_em_risco=[PrazoRiscoItem.de(p, hoje=hoje) for p in em_risco],
    )


@router.get("/contagens", response_model=ContagensPorStatusResponse)
def obter_contagens_por_status(
    request: Request,
    gestor: Annotated[Usuario, Depends(_require_gestor)],
    db: Annotated[Session, Depends(get_db)],
    unidade_id: uuid.UUID | None = Query(default=None),
) -> ContagensPorStatusResponse:
    """Cards de contagem por status do dashboard (design D8, change
    kanban-por-servidor) — Total, Abertos, Em Tramitação, Concluídos e
    Arquivados, no escopo de unidades geridas (ou de uma unidade filtrada)."""
    unidades = _resolver_escopo_ou_negar(db, gestor=gestor, unidade_id=unidade_id, request=request)
    return ContagensPorStatusResponse(**dashboard_service.contagens_por_status(db, unidades))


@router.get("/processos-ativos", response_model=ProcessosAtivosResponse)
def obter_processos_ativos(
    request: Request,
    gestor: Annotated[Usuario, Depends(_require_gestor)],
    db: Annotated[Session, Depends(get_db)],
    unidade_id: uuid.UUID | None = Query(default=None),
) -> ProcessosAtivosResponse:
    """US 6.1 Cen.5 — drill-down do KPI "Total de Processos Ativos"."""
    unidades = _resolver_escopo_ou_negar(db, gestor=gestor, unidade_id=unidade_id, request=request)
    hoje = date.today()
    itens = dashboard_service.listar_ativos(db, unidades)
    return ProcessosAtivosResponse(
        items=[ProcessoAtivoItem.de(p, hoje=hoje) for p in itens], total=len(itens)
    )


@router.get("/processos-parados", response_model=ProcessosParadosResponse)
def obter_processos_parados(
    request: Request,
    gestor: Annotated[Usuario, Depends(_require_gestor)],
    db: Annotated[Session, Depends(get_db)],
    unidade_id: uuid.UUID | None = Query(default=None),
) -> ProcessosParadosResponse:
    """US 6.1 Cen.4 — drill-down do KPI "Processos Parados"."""
    unidades = _resolver_escopo_ou_negar(db, gestor=gestor, unidade_id=unidade_id, request=request)
    hoje = date.today()
    limiar_parado = dashboard_service.dias_para_processo_parado(db)
    itens = dashboard_service.listar_parados(db, unidades, dias_limiar=limiar_parado, hoje=hoje)
    return ProcessosParadosResponse(
        items=[ProcessoParadoItem.de(p, dias_parados=dias) for p, dias in itens], total=len(itens)
    )


@router.get("/distribuicoes", response_model=DistribuicoesResponse)
def obter_distribuicoes(
    request: Request,
    gestor: Annotated[Usuario, Depends(_require_gestor)],
    db: Annotated[Session, Depends(get_db)],
    unidade_id: uuid.UUID | None = Query(default=None),
) -> DistribuicoesResponse:
    """US 6.2 — distribuição de processos ativos por unidade, por tipo e por usuário."""
    unidades = _resolver_escopo_ou_negar(db, gestor=gestor, unidade_id=unidade_id, request=request)
    return DistribuicoesResponse(
        por_unidade=[
            DistribuicaoItem(rotulo=rotulo, quantidade=quantidade)
            for rotulo, quantidade in dashboard_service.distribuicao_por_unidade(db, unidades)
        ],
        por_tipo=[
            DistribuicaoItem(rotulo=rotulo, quantidade=quantidade)
            for rotulo, quantidade in dashboard_service.distribuicao_por_tipo(db, unidades)
        ],
        por_usuario=[
            DistribuicaoItem(rotulo=rotulo, quantidade=quantidade)
            for rotulo, quantidade in dashboard_service.distribuicao_por_usuario(db, unidades)
        ],
    )
