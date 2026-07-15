"""Máquina de estados do processo (D4).

Status é máquina de estados explícita, nunca campo de texto livre. As
transições válidas neste change são apenas as movidas por ação explícita
(despacho/conclusão); `→ arquivado` NÃO é alcançável aqui (rotina do Change
B). Qualquer transição fora da tabela levanta `TransicaoInvalida`.
"""

from __future__ import annotations

from app.db.models import StatusProcesso

# Transições permitidas (origem → destinos válidos). `arquivado` não é destino
# de nenhuma transição neste change (workflow-tramitacao/spec — escopo).
_TRANSICOES: dict[StatusProcesso, set[StatusProcesso]] = {
    StatusProcesso.ABERTO: {StatusProcesso.EM_TRAMITACAO, StatusProcesso.CONCLUIDO},
    StatusProcesso.EM_TRAMITACAO: {StatusProcesso.EM_TRAMITACAO, StatusProcesso.CONCLUIDO},
    StatusProcesso.CONCLUIDO: set(),
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
