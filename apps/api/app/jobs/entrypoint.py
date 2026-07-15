"""Entrypoint do Cloud Run Job `job-manutencao-diaria` (US 2.5).

Executa o passo de arquivamento automático sobre o estado atual do banco. O
contrato de idempotência (seleção por estado, retomada sem duplicar efeito)
já está provado em memória por `app.jobs.manutencao_diaria` e
`tests/test_idempotencia.py`; aqui ele passa a operar sobre o banco real.
Demais passos do job (alerta de prazo, purga de anexos, expurgo de
notificações) permanecem fora de escopo — o job acreta passos nos próximos
changes. Executável via:

    uv run python -m app.jobs.entrypoint
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.db.session import get_session_factory
from app.services.arquivamento import arquivar_vencidos

logger = logging.getLogger("setes.jobs.manutencao_diaria")


def run() -> int:
    logger.info("job-manutencao-diaria: início")
    agora = datetime.now(timezone.utc)
    session = get_session_factory()()
    try:
        total = arquivar_vencidos(session, agora=agora)
        logger.info("job-manutencao-diaria: arquivamento_automatico total=%s", total)
    finally:
        session.close()
    logger.info("job-manutencao-diaria: fim")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    raise SystemExit(run())
