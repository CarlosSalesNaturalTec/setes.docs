"""Entrypoint placeholder do Cloud Run Job `job-manutencao-diaria` (task 8.1).

A lógica de negócio real (arquivamento, purga, alertas) vem em changes futuros.
Aqui apenas demonstra a estrutura de execução idempotente. Executável via:

    uv run python -m app.jobs.entrypoint
"""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger("setes.jobs.manutencao_diaria")


def run() -> int:
    # Placeholder: em produção, abre sessão via IP privado, seleciona por estado
    # atual e transiciona sob guard (ver app.jobs.manutencao_diaria).
    logger.info("job-manutencao-diaria: início (placeholder de bootstrap)")
    logger.info("job-manutencao-diaria: nenhum passo de negócio implementado ainda")
    logger.info("job-manutencao-diaria: fim")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    raise SystemExit(run())
