"""Rotina diária de verificação de prazos (Épico 5 — US 5.2 Cen.2, US 5.4).

Gera o alerta de prazo (notificação interna + e-mail) para cada processo ativo
cujo `prazo_em` está a vencer dentro da janela configurada
(`sistema_config.dias_antecedencia_alerta_prazo`, lida a cada execução — D4),
aos servidores da unidade atual. Idempotente por guard de existência (D3,
design.md `notificacoes-e-alertas`): só cria notificação/e-mail se não existir
alerta prévio para o mesmo `(processo_id, usuario_id, prazo_em vigente)` —
reexecutar sobre o mesmo estado não duplica; retomar após indisponibilidade
cobre a janela inteira. Se o processo for despachado (`prazo_em` muda), um novo
ciclo de alerta é válido — comportamento desejado. Commit por processo (D5):
uma falha a meio caminho preserva o progresso já feito, mesmo padrão de
`arquivar_vencidos`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import (
    Notificacao,
    Processo,
    SistemaConfig,
    StatusProcesso,
    TipoNotificacao,
    Unidade,
    Usuario,
)
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.services.notificacao import servidores_da_unidade


def _ja_alertado(
    db: Session, *, processo_id: uuid.UUID, usuario_id: uuid.UUID, prazo_referencia: date
) -> bool:
    return (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == processo_id,
            Notificacao.usuario_id == usuario_id,
            Notificacao.tipo == TipoNotificacao.ALERTA_PRAZO,
            Notificacao.prazo_referencia == prazo_referencia,
        )
        .first()
        is not None
    )


def _enfileirar_email_prazo(
    *, processo: Processo, servidor: Usuario, dias_restantes: int, settings: Settings
) -> None:
    enqueue_email_seguro(
        EmailMessage(
            to=servidor.email,
            subject=f"Prazo próximo — {processo.numero}",
            body=(
                f"O processo {processo.numero} — {processo.assunto} tem prazo em "
                f"{processo.prazo_em.isoformat()} ({dias_restantes} dia(s) restante(s))."
            ),
        ),
        event_id=f"prazo:{processo.id}:{processo.prazo_em.isoformat()}:{servidor.id}",
        config=config_from_settings(settings),
    )


def verificar_prazos(db: Session, *, agora: datetime, settings: Settings) -> int:
    """Gera o alerta de prazo (notificação + e-mail); retorna quantas notificações novas."""
    config = db.get(SistemaConfig, 1)
    hoje = agora.date()
    janela = hoje + timedelta(days=config.dias_antecedencia_alerta_prazo)

    processos = db.scalars(
        select(Processo)
        .where(Processo.status.in_([StatusProcesso.ABERTO, StatusProcesso.EM_TRAMITACAO]))
        .where(Processo.prazo_em <= janela)
    ).all()

    total = 0
    for processo in processos:
        unidade_atual = db.get(Unidade, processo.unidade_atual_id)
        novos: list[tuple[Notificacao, Usuario]] = []
        for servidor in servidores_da_unidade(db, processo.unidade_atual_id):
            if _ja_alertado(
                db,
                processo_id=processo.id,
                usuario_id=servidor.id,
                prazo_referencia=processo.prazo_em,
            ):
                continue
            notificacao = Notificacao(
                usuario_id=servidor.id,
                processo_id=processo.id,
                unidade_id=processo.unidade_atual_id,
                unidade_nome=unidade_atual.nome,
                tipo=TipoNotificacao.ALERTA_PRAZO,
                numero_processo=processo.numero,
                assunto=processo.assunto,
                prazo_referencia=processo.prazo_em,
            )
            db.add(notificacao)
            novos.append((notificacao, servidor))

        if not novos:
            continue

        db.commit()  # por processo (D5) — retomável a meio caminho
        total += len(novos)

        dias_restantes = (processo.prazo_em - hoje).days
        for _notificacao, servidor in novos:
            _enfileirar_email_prazo(
                processo=processo, servidor=servidor, dias_restantes=dias_restantes, settings=settings
            )

    return total
