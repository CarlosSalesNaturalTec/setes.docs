"""Consultas de leitura de processo: Kanban, busca, histórico, atuação (D6).

Kanban do **Servidor** é pessoal (change kanban-por-servidor, design D1):
responsável atual ∪ criador ∪ participante histórico da tramitação — não mais
por unidade. Kanban do **Gestor**/Administrador permanece por unidade (atual ∪
origem, change visibilidade-processos-origem D1), derivado da primitiva de
autorização existente (`tem_acesso_a_unidade`). A **busca** (`buscar`)
mantém o escopo por unidade para todos os perfis, inclusive Servidor — a
divergência entre quadro e busca é deliberada (design D6). Nenhuma consulta
retorna processo fora do escopo, e sigiloso fora da unidade atual do usuário
nunca aparece, mesmo para participante histórico (design D3).
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    PerfilUsuario,
    Processo,
    StatusProcesso,
    TipoEventoTramitacao,
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


def _filtro_escopo(escopo: list[uuid.UUID]):
    """Cláusula WHERE do escopo ampliado (design D1): unidade atual OU unidade
    de origem, com sigiloso restrito à unidade atual — nunca vazado por origem."""
    return or_(
        Processo.unidade_atual_id.in_(escopo),
        and_(Processo.unidade_origem_id.in_(escopo), Processo.sigiloso.is_(False)),
    )


def _unidade_no_escopo(unidade_id: uuid.UUID, escopo: list[uuid.UUID] | None) -> bool:
    """`None` (Administrador) enxerga qualquer unidade — sempre "no escopo"."""
    return escopo is None or unidade_id in escopo


def _escopo_pessoal_servidor(db: Session, usuario: Usuario):
    """Cláusula do escopo pessoal do Servidor no quadro (design D1, change
    kanban-por-servidor): responsável atual ∪ criador ∪ participante
    histórico — já foi detentor em algum evento de `tramitacao`
    (`servidor_origem_id`/`servidor_destino_id`). Usa detentores, não
    `responsavel_id`: quem apenas agiu sobre o processo sem tê-lo detido (ex.:
    Gestor que reatribuiu) não deve carregá-lo no quadro pessoal (D6 de
    `tramitacao-manual`).

    Sigilo (D3) permanece filtrado por unidade dentro do próprio escopo
    pessoal: processo sigiloso fora da unidade atual do usuário fica de fora,
    mesmo para quem já foi detentor.
    """
    detentor = (
        db.query(Tramitacao.id)
        .filter(
            Tramitacao.processo_id == Processo.id,
            or_(
                Tramitacao.servidor_origem_id == usuario.id,
                Tramitacao.servidor_destino_id == usuario.id,
            ),
        )
        .exists()
    )
    participacao = or_(
        Processo.servidor_atual_id == usuario.id,
        Processo.criado_por_id == usuario.id,
        detentor,
    )
    sem_sigilo_fora_da_unidade = or_(
        Processo.sigiloso.is_(False), Processo.unidade_atual_id == usuario.unidade_id
    )
    return and_(participacao, sem_sigilo_fora_da_unidade)


def listar_kanban(
    db: Session,
    *,
    usuario: Usuario,
    filtro_unidade: uuid.UUID | None = None,
    incluir_arquivados: bool = False,
    tipo_processo_id: uuid.UUID | None = None,
    assunto: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Processo], int]:
    """Cards do Kanban, ordenados por prazo (vencido primeiro).

    Escopo: Servidor vê o conjunto **pessoal** (D1); Gestor e Administrador
    mantêm o escopo por unidade (atual ∪ origem, D1 de
    `visibilidade-processos-origem`), inalterado. `incluir_arquivados=False`
    (default, D4) omite apenas Arquivado — Concluído é sempre exibido. Os
    filtros de tipo/assunto/data (D5) são aplicados **depois** do recorte de
    escopo, nunca ampliando o que o usuário pode ver.
    """
    query = db.query(Processo).options(
        joinedload(Processo.tipo_processo),
        joinedload(Processo.unidade_atual),
        joinedload(Processo.servidor_atual),
    )

    if usuario.perfil == PerfilUsuario.SERVIDOR:
        query = query.filter(_escopo_pessoal_servidor(db, usuario))
    else:
        escopo = unidades_visiveis(db, usuario)
        if escopo is not None:
            if not escopo:
                return [], 0
            query = query.filter(_filtro_escopo(escopo))
        if filtro_unidade is not None:
            # Só filtra dentro do escopo já autorizado — nunca amplia o acesso.
            if escopo is not None and filtro_unidade not in escopo:
                return [], 0
            query = query.filter(Processo.unidade_atual_id == filtro_unidade)

    if not incluir_arquivados:
        query = query.filter(Processo.status != StatusProcesso.ARQUIVADO)
    if tipo_processo_id is not None:
        query = query.filter(Processo.tipo_processo_id == tipo_processo_id)
    if assunto:
        query = query.filter(Processo.assunto.ilike(f"%{assunto}%"))
    if data_inicial is not None:
        query = query.filter(Processo.criado_em >= data_inicial)
    if data_final is not None:
        # Inclui o dia final inteiro (criado_em é timestamp).
        from datetime import datetime, time

        fim = datetime.combine(data_final, time.max)
        query = query.filter(Processo.criado_em <= fim)

    total = query.count()
    itens = (
        query.order_by(Processo.prazo_em.asc(), Processo.numero.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return itens, total


def atributos_contextuais(
    db: Session, *, usuario: Usuario, processos: list[Processo]
) -> dict[uuid.UUID, tuple[bool, bool, bool]]:
    """`somente_leitura`, `devolvido` e `acao_requerida` por processo (D2, D3
    de `visibilidade-processos-origem`; D2 de `kanban-por-servidor`).

    `somente_leitura` = unidade atual fora do escopo **por unidade**
    (sempre `False` para Administrador; para o Servidor, cuja unidade única é
    a própria, coincide com "unidade atual diferente da minha"). `devolvido` =
    último evento do histórico é `DEVOLUCAO` e o processo está na unidade do
    escopo. `acao_requerida` = sou o responsável atual (`servidor_atual_id`).
    Os três são independentes e calculados sem atalho, em lote (`DISTINCT ON`
    para os ids da página), sem N+1 e sem tocar em `tramitacao` além da
    consulta em lote (histórico imutável).
    """
    if not processos:
        return {}

    escopo = unidades_visiveis(db, usuario)
    ids = [p.id for p in processos]
    ultimos = (
        db.query(Tramitacao.processo_id, Tramitacao.tipo_evento)
        .filter(Tramitacao.processo_id.in_(ids))
        .distinct(Tramitacao.processo_id)
        .order_by(Tramitacao.processo_id, Tramitacao.criado_em.desc())
        .all()
    )
    ultimo_evento_por_processo = {linha.processo_id: linha.tipo_evento for linha in ultimos}

    resultado: dict[uuid.UUID, tuple[bool, bool, bool]] = {}
    for processo in processos:
        no_escopo = _unidade_no_escopo(processo.unidade_atual_id, escopo)
        somente_leitura = not no_escopo
        devolvido = (
            no_escopo
            and ultimo_evento_por_processo.get(processo.id) == TipoEventoTramitacao.DEVOLUCAO
        )
        acao_requerida = processo.servidor_atual_id == usuario.id
        resultado[processo.id] = (somente_leitura, devolvido, acao_requerida)
    return resultado


def buscar(
    db: Session,
    *,
    usuario: Usuario,
    numero: str | None = None,
    assunto: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
) -> list[Processo]:
    """Busca interna (US 2.7) — escopo por **unidade** (atual ∪ origem),
    igual para todos os perfis, inclusive Servidor.

    Diverge deliberadamente do escopo pessoal do quadro (design D6 de
    `kanban-por-servidor`): o quadro é a área de trabalho pessoal do
    servidor; a busca é investigativa e serve para localizar processos da
    unidade sob tratamento de colegas. Como a autorização por unidade não
    muda, a busca não revela nada que o usuário não pudesse já abrir por
    acesso direto — apenas facilita achar.
    """
    escopo = unidades_visiveis(db, usuario)
    query = db.query(Processo).options(
        joinedload(Processo.tipo_processo),
        joinedload(Processo.unidade_atual),
        joinedload(Processo.servidor_atual),
    )
    if escopo is not None:
        if not escopo:
            return []
        query = query.filter(_filtro_escopo(escopo))

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


def contar_processos_sob_responsabilidade(db: Session, usuario: Usuario) -> int:
    """Processos "parados com" o usuário, guarda da desativação (US 8.4, D2).

    Change tramitacao-manual (design.md — Risks/Trade-offs): conta por
    `servidor_atual_id`, o responsável corrente denormalizado no processo —
    mais preciso que a heurística anterior de "último responsável de
    tramitação" (que exigia reconstruir o histórico por processo).
    """
    from app.db.models import StatusProcesso

    em_andamento = [StatusProcesso.ABERTO, StatusProcesso.EM_TRAMITACAO]
    return (
        db.query(Processo)
        .filter(Processo.status.in_(em_andamento))
        .filter(Processo.servidor_atual_id == usuario.id)
        .count()
    )


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
