"""Consulta pública de processo — sem autenticação (Épico 7, US 7.1/7.2).

Nenhuma dependência de sessão/JWT: acessível ao Cidadão. Sigilosos e números
inexistentes produzem a mesma resposta 404 (D2) — não revela existência.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rate_limit import RATE_LIMIT_CONSULTA_PUBLICA, limiter
from app.schemas.consulta_publica import PesquisaPublicaResponse, ProcessoPublicoResponse
from app.services import consulta_publica as consulta_publica_service

router = APIRouter(prefix="/publico", tags=["consulta-publica"])

MSG_PROCESSO_NAO_ENCONTRADO = "Nenhum processo encontrado com o número informado"
MSG_PESQUISA_VAZIA = "Nenhum processo encontrado para os filtros informados"


@router.get("/processos/{numero:path}", response_model=ProcessoPublicoResponse)
@limiter.limit(RATE_LIMIT_CONSULTA_PUBLICA)
def consultar_processo(
    request: Request,
    numero: str,
    db: Annotated[Session, Depends(get_db)],
) -> ProcessoPublicoResponse:
    """US 7.1 — consulta por número exato; sigiloso = "não encontrado" (Cen.4)."""
    resultado = consulta_publica_service.consultar_por_numero(db, numero)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_PROCESSO_NAO_ENCONTRADO
        )
    return resultado


@router.get("/processos", response_model=PesquisaPublicaResponse)
@limiter.limit(RATE_LIMIT_CONSULTA_PUBLICA)
def pesquisar_processos(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    assunto: str | None = Query(default=None),
    tipo_processo: str | None = Query(default=None),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
) -> PesquisaPublicaResponse:
    """US 7.2 — pesquisa paginada (20/página); sigilosos sempre excluídos."""
    itens, total = consulta_publica_service.pesquisar(
        db,
        assunto=assunto,
        tipo_processo=tipo_processo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pagina=pagina,
    )
    return PesquisaPublicaResponse(
        items=itens,
        total=total,
        page=pagina,
        mensagem_vazio=None if itens else MSG_PESQUISA_VAZIA,
    )
