"""Consultas de leitura de processo: Kanban, busca, histórico, atuação (D6).

Todo escopo de unidade é derivado da primitiva de autorização existente
(`tem_acesso_a_unidade`): Servidor vê só a própria unidade; Gestor, as unidades
geridas; Administrador, todas. Nenhuma consulta retorna processo fora do escopo.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import (
    PerfilUsuario,
    Processo,
    Tramitacao,
    UnidadeGestor,
    Usuario,
)


def unidades_visiveis(db: Session, usuario: Usuario) -> list[uuid.UUID] | None:
    """IDs de unidade que o usuário enxerga no Kanban/busca.

    `None` significa "todas" (Administrador). Servidor: a própria; Gestor: as
    geridas (lista possivelmente vazia).
    """
    if usuario.perfil == PerfilUsuario.ADMINISTRADOR:
        return None
    if usuario.perfil == PerfilUsuario.SERVIDOR:
        return [usuario.unidade_id] if usuario.unidade_id else []
    if usuario.perfil == PerfilUsuario.GESTOR:
        linhas = (
            db.query(UnidadeGestor.unidade_id)
            .filter(UnidadeGestor.gestor_id == usuario.id)
            .all()
        )
        return [linha[0] for linha in linhas]
    return []


def listar_kanban(
    db: Session,
    *,
    usuario: Usuario,
    filtro_unidade: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Processo], int]:
    """Cards do Kanban no escopo do usuário, ordenados por prazo (vencido primeiro)."""
    escopo = unidades_visiveis(db, usuario)
    query = db.query(Processo)
    if escopo is not None:
        if not escopo:
            return [], 0
        query = query.filter(Processo.unidade_atual_id.in_(escopo))
    if filtro_unidade is not None:
        # Só filtra dentro do escopo já autorizado — nunca amplia o acesso.
        if escopo is not None and filtro_unidade not in escopo:
            return [], 0
        query = query.filter(Processo.unidade_atual_id == filtro_unidade)

    total = query.count()
    itens = (
        query.order_by(Processo.prazo_em.asc(), Processo.numero.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return itens, total


def buscar(
    db: Session,
    *,
    usuario: Usuario,
    numero: str | None = None,
    assunto: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> list[Processo]:
    """Busca interna restrita ao escopo de unidade (US 2.7)."""
    escopo = unidades_visiveis(db, usuario)
    query = db.query(Processo)
    if escopo is not None:
        if not escopo:
            return []
        query = query.filter(Processo.unidade_atual_id.in_(escopo))

    if numero:
        query = query.filter(Processo.numero == numero)
    if assunto:
        query = query.filter(Processo.assunto.ilike(f"%{assunto}%"))
    if data_inicial is not None:
        query = query.filter(Processo.criado_em >= data_inicial)
    if data_final is not None:
        # Inclui o dia final inteiro (criado_em é timestamp).
        from datetime import datetime, time

        fim = datetime.combine(data_final, time.max)
        query = query.filter(Processo.criado_em <= fim)

    return query.order_by(Processo.prazo_em.asc(), Processo.numero.asc()).all()


def historico(db: Session, processo_id: uuid.UUID) -> list[Tramitacao]:
    """Linha do tempo do processo, em ordem cronológica (US 2.4)."""
    return (
        db.query(Tramitacao)
        .filter(Tramitacao.processo_id == processo_id)
        .order_by(Tramitacao.criado_em.asc())
        .all()
    )


def processos_atuados(db: Session, usuario: Usuario) -> list[dict]:
    """Processos em que o usuário atuou — criação OU tramitação (US 1.5 Cen.1).

    Visível independentemente da unidade atual do processo: o histórico de
    atuação acompanha o usuário mesmo após transferência (US 1.4 Cen.3).
    """
    ids_atuados = (
        db.query(Tramitacao.processo_id)
        .filter(Tramitacao.responsavel_id == usuario.id)
        .subquery()
    )
    processos = (
        db.query(Processo)
        .filter(
            or_(
                Processo.criado_por_id == usuario.id,
                Processo.id.in_(db.query(ids_atuados.c.processo_id)),
            )
        )
        .all()
    )

    itens: list[dict] = []
    for processo in processos:
        eventos = (
            db.query(Tramitacao)
            .filter(
                Tramitacao.processo_id == processo.id,
                Tramitacao.responsavel_id == usuario.id,
            )
            .order_by(Tramitacao.criado_em.desc())
            .all()
        )
        if eventos:
            ultimo = eventos[0]
            itens.append(
                {
                    "processo_id": str(processo.id),
                    "numero": processo.numero,
                    "assunto": processo.assunto,
                    "data_acao": ultimo.criado_em,
                    "tipo_acao": ultimo.tipo_evento.value,
                }
            )
        else:
            # Atuou apenas criando (ainda sem tramitação).
            itens.append(
                {
                    "processo_id": str(processo.id),
                    "numero": processo.numero,
                    "assunto": processo.assunto,
                    "data_acao": processo.criado_em,
                    "tipo_acao": "criacao",
                }
            )

    itens.sort(key=lambda i: i["data_acao"], reverse=True)
    return itens


def contar_em_andamento(db: Session, unidade_id: uuid.UUID) -> int:
    """Processos em andamento (Aberto/Em Tramitação) atualmente na unidade (US 8.1 Cen.3)."""
    from app.db.models import StatusProcesso

    return (
        db.query(Processo)
        .filter(
            Processo.unidade_atual_id == unidade_id,
            Processo.status.in_([StatusProcesso.ABERTO, StatusProcesso.EM_TRAMITACAO]),
        )
        .count()
    )
