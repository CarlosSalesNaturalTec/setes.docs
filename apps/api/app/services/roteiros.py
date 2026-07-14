"""Serviço de roteiros de tramitação (D8) — versionamento por `vigente`."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import Roteiro


def obter_roteiro_vigente(db: Session, tipo_processo_id: uuid.UUID) -> Roteiro | None:
    """Único ponto de leitura do roteiro vigente de um tipo de processo.

    Nenhum outro lugar do código deve fazer `SELECT ... FROM roteiro WHERE
    vigente` diretamente (D8) — o Épico 2 grava `processo.roteiro_id` a partir
    do valor retornado aqui no momento da criação do processo, e mantém essa
    referência mesmo que o roteiro seja substituído depois (US 8.2 Cen.2).
    """
    return (
        db.query(Roteiro)
        .filter(Roteiro.tipo_processo_id == tipo_processo_id, Roteiro.vigente.is_(True))
        .one_or_none()
    )
