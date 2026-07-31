"""Consultas de leitura pública de processo (Épico 7, US 7.1/7.2).

Toda query aplica `sigiloso = false` diretamente no `WHERE` (D2): um processo
sigiloso e um número inexistente produzem o mesmo resultado vazio — não se
carrega o processo para só depois decidir ocultá-lo, o que evitaria uma
diferença de comportamento observável que revelasse a existência.
"""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.db.models import (
    Processo,
    TipoEventoTramitacao,
    TipoProcesso,
    Tramitacao,
    Unidade,
)
from app.schemas.consulta_publica import (
    PAGE_SIZE_PUBLICO,
    ItemPesquisaPublicaResponse,
    MovimentacaoPublicaResponse,
    ProcessoPublicoResponse,
    InteressadoPublicoResponse,
)

# D3 — eventos de movimentação; `marcar_sigilo`/`remover_sigilo` são internos
# e nunca aparecem no histórico público.
EVENTOS_MOVIMENTACAO = (
    TipoEventoTramitacao.ENVIO,
    TipoEventoTramitacao.DEVOLUCAO,
    TipoEventoTramitacao.CONCLUSAO,
    TipoEventoTramitacao.ARQUIVAMENTO_AUTOMATICO,
)


def _nome_unidade(db: Session, unidade_id) -> str | None:
    if unidade_id is None:
        return None
    unidade = db.get(Unidade, unidade_id)
    return unidade.sigla if unidade else None


def _nome_tipo_processo(db: Session, tipo_processo_id) -> str:
    tipo = db.get(TipoProcesso, tipo_processo_id)
    return tipo.nome if tipo else ""


def _historico_publico(db: Session, processo_id) -> list[MovimentacaoPublicaResponse]:
    eventos = (
        db.query(Tramitacao)
        .filter(
            Tramitacao.processo_id == processo_id,
            Tramitacao.tipo_evento.in_(EVENTOS_MOVIMENTACAO),
        )
        .order_by(Tramitacao.criado_em.asc())
        .all()
    )
    return [
        MovimentacaoPublicaResponse(
            criado_em=evento.criado_em,
            unidade_origem=_nome_unidade(db, evento.unidade_origem_id),
            unidade_destino=_nome_unidade(db, evento.unidade_destino_id),
            status_resultante=evento.status_resultante.value,
        )
        for evento in eventos
    ]


def montar_processo_publico(db: Session, processo: Processo) -> ProcessoPublicoResponse:
    return ProcessoPublicoResponse(
        numero=processo.numero,
        assunto=processo.assunto,
        tipo_processo=_nome_tipo_processo(db, processo.tipo_processo_id),
        status=processo.status.value,
        unidade_atual=_nome_unidade(db, processo.unidade_atual_id) or "",
        criado_em=processo.criado_em,
        interessados=[
            InteressadoPublicoResponse(nome=i.nome) for i in processo.interessados
        ],
        historico=_historico_publico(db, processo.id),
    )


def _montar_item_pesquisa(db: Session, processo: Processo) -> ItemPesquisaPublicaResponse:
    return ItemPesquisaPublicaResponse(
        numero=processo.numero,
        assunto=processo.assunto,
        tipo_processo=_nome_tipo_processo(db, processo.tipo_processo_id),
        status=processo.status.value,
        unidade_atual=_nome_unidade(db, processo.unidade_atual_id) or "",
        criado_em=processo.criado_em,
    )


def consultar_por_numero(db: Session, numero: str) -> ProcessoPublicoResponse | None:
    """US 7.1 — sigiloso e inexistente são indistinguíveis (D2, Cen.4)."""
    processo = (
        db.query(Processo)
        .filter(Processo.numero == numero, Processo.sigiloso.is_(False))
        .one_or_none()
    )
    if processo is None:
        return None
    return montar_processo_publico(db, processo)


def pesquisar(
    db: Session,
    *,
    assunto: str | None = None,
    tipo_processo: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    pagina: int = 1,
) -> tuple[list[ItemPesquisaPublicaResponse], int]:
    """US 7.2 — pesquisa paginada; sigilosos sempre excluídos (D2).

    `tipo_processo` filtra pelo **nome** do tipo (correspondência parcial), não
    pelo UUID interno — o cidadão não tem como conhecer o identificador, e não
    há endpoint público de catálogo de tipos neste change (proposal — apenas os
    dois endpoints de consulta são adicionados).
    """
    query = db.query(Processo).filter(Processo.sigiloso.is_(False))

    if assunto:
        query = query.filter(Processo.assunto.ilike(f"%{assunto}%"))
    if tipo_processo:
        ids_tipo = db.query(TipoProcesso.id).filter(TipoProcesso.nome.ilike(f"%{tipo_processo}%"))
        query = query.filter(Processo.tipo_processo_id.in_(ids_tipo))
    if data_inicio is not None:
        query = query.filter(Processo.criado_em >= data_inicio)
    if data_fim is not None:
        fim = datetime.combine(data_fim, time.max)
        query = query.filter(Processo.criado_em <= fim)

    total = query.count()
    itens = (
        query.order_by(Processo.criado_em.desc(), Processo.numero.desc())
        .offset((pagina - 1) * PAGE_SIZE_PUBLICO)
        .limit(PAGE_SIZE_PUBLICO)
        .all()
    )
    return [_montar_item_pesquisa(db, p) for p in itens], total
