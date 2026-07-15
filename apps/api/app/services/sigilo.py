"""Marcar/remover sigilo de processo (US 2.6 Cen.1/1b/2).

Sigilo é atributo de visibilidade ortogonal ao status — nunca transiciona a
máquina de estados. Idempotente (D4): se o processo já está no estado-alvo,
é um no-op sem novo evento no histórico imutável.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Processo, TipoEventoTramitacao, Tramitacao, Usuario


def marcar(db: Session, *, processo: Processo, responsavel: Usuario) -> Processo:
    if processo.sigiloso:
        return processo
    processo.sigiloso = True
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.MARCAR_SIGILO,
            unidade_origem_id=None,
            unidade_destino_id=None,
            responsavel_id=responsavel.id,
            status_resultante=processo.status,
        )
    )
    db.commit()
    db.refresh(processo)
    return processo


def remover(db: Session, *, processo: Processo, responsavel: Usuario) -> Processo:
    if not processo.sigiloso:
        return processo
    processo.sigiloso = False
    db.add(
        Tramitacao(
            processo_id=processo.id,
            tipo_evento=TipoEventoTramitacao.REMOVER_SIGILO,
            unidade_origem_id=None,
            unidade_destino_id=None,
            responsavel_id=responsavel.id,
            status_resultante=processo.status,
        )
    )
    db.commit()
    db.refresh(processo)
    return processo
