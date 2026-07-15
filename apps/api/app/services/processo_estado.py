"""Máquina de estados do processo (D4).

Status é máquina de estados explícita, nunca campo de texto livre. As
transições movidas por ação explícita são despacho/conclusão; `concluido →
arquivado` é a única transição realizada pela rotina automática de
arquivamento (change arquivamento-automatico), nunca por ação de usuário.
Qualquer transição fora da tabela levanta `TransicaoInvalida`.
"""

from __future__ import annotations

from app.db.models import StatusProcesso

# Transições permitidas (origem → destinos válidos). `concluido → arquivado`
# é alcançada apenas por `services/arquivamento.py` (rotina automática).
_TRANSICOES: dict[StatusProcesso, set[StatusProcesso]] = {
    StatusProcesso.ABERTO: {StatusProcesso.EM_TRAMITACAO, StatusProcesso.CONCLUIDO},
    StatusProcesso.EM_TRAMITACAO: {StatusProcesso.EM_TRAMITACAO, StatusProcesso.CONCLUIDO},
    StatusProcesso.CONCLUIDO: {StatusProcesso.ARQUIVADO},
    StatusProcesso.ARQUIVADO: set(),
}


class TransicaoInvalida(Exception):
    """Tentativa de transição de status fora da máquina de estados (D4)."""


def validar_transicao(origem: StatusProcesso, destino: StatusProcesso) -> None:
    """Levanta `TransicaoInvalida` se `origem → destino` não é permitida."""
    if destino not in _TRANSICOES.get(origem, set()):
        raise TransicaoInvalida(
            f"Transição de status inválida: {origem.value} → {destino.value}"
        )
