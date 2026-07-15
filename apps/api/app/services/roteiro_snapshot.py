"""Navegação sobre o roteiro-snapshot de um processo (D2, D3).

Um processo fixa `roteiro_id` na criação (snapshot do `Roteiro` vigente, ver
`services/roteiros.obter_roteiro_vigente`). Estas funções resolvem as etapas
ordenadas desse snapshot e a posição pelo índice `ordem_atual`.

`ordem_atual` é um **índice posicional 0-based** na lista ordenada de etapas do
snapshot (task 3.2 / D3), independente dos valores de `roteiro_etapa.ordem` (que
o cadastro de roteiro numera a partir de 1). Despacho é `ordem_atual + 1`;
devolução é `ordem_atual - 1`. Nenhuma etapa é duplicada — a leitura é sempre do
`roteiro_etapa` original.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import RoteiroEtapa

_MSG_SEM_ROTEIRO = (
    "Este tipo de processo não possui roteiro de tramitação configurado. "
    "Entre em contato com o Administrador."
)


class RoteiroInvalido(Exception):
    """Tipo de processo sem roteiro vigente ou com roteiro de zero etapas (US 2.1 Cen.3c)."""


def etapas_do_roteiro(db: Session, roteiro_id: uuid.UUID) -> list[RoteiroEtapa]:
    """Etapas do roteiro-snapshot, ordenadas por `ordem`. Levanta se vazio (Cen.3c)."""
    etapas = (
        db.query(RoteiroEtapa)
        .filter(RoteiroEtapa.roteiro_id == roteiro_id)
        .order_by(RoteiroEtapa.ordem)
        .all()
    )
    if not etapas:
        raise RoteiroInvalido(_MSG_SEM_ROTEIRO)
    return etapas


def validar_roteiro_para_criacao(roteiro, etapas: list[RoteiroEtapa]) -> None:
    """Rejeita criação quando não há roteiro vigente ou o roteiro tem zero etapas
    (US 2.1 Cen.3c). A mensagem é a exata do PRD."""
    if roteiro is None or not etapas:
        raise RoteiroInvalido(_MSG_SEM_ROTEIRO)


def etapa_atual(etapas: list[RoteiroEtapa], ordem_atual: int) -> RoteiroEtapa:
    return etapas[ordem_atual]


def is_primeira(etapas: list[RoteiroEtapa], ordem_atual: int) -> bool:
    return ordem_atual <= 0


def is_ultima(etapas: list[RoteiroEtapa], ordem_atual: int) -> bool:
    return ordem_atual >= len(etapas) - 1


def proxima_etapa(etapas: list[RoteiroEtapa], ordem_atual: int) -> RoteiroEtapa | None:
    """Etapa imediatamente seguinte, ou None se já na última (despacho vira conclusão)."""
    if ordem_atual + 1 < len(etapas):
        return etapas[ordem_atual + 1]
    return None


def etapa_anterior(etapas: list[RoteiroEtapa], ordem_atual: int) -> RoteiroEtapa | None:
    """Etapa imediatamente anterior, ou None se já na primeira (devolução bloqueada)."""
    if ordem_atual - 1 >= 0:
        return etapas[ordem_atual - 1]
    return None
