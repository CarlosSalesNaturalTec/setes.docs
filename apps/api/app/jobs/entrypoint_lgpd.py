"""Entrypoint do Cloud Run Job `job-anonimizacao-lgpd` (US 10.3, D4).

Mesmo padrão de `app.jobs.entrypoint`: abre sessão, executa a rotina, loga o
total processado, fecha a sessão. Executável via:

    uv run python -m app.jobs.entrypoint_lgpd
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.db.session import get_session_factory
from app.services.anonimizacao_lgpd import processar_anonimizacao_automatica

logger = logging.getLogger("setes.jobs.anonimizacao_lgpd")


def run() -> int:
    logger.info("job-anonimizacao-lgpd: início")
    agora = datetime.now(timezone.utc)
    session = get_session_factory()()
    try:
        total = processar_anonimizacao_automatica(session, agora=agora)
        logger.info("job-anonimizacao-lgpd: anonimizacao_automatica total=%s", total)
    finally:
        session.close()
    logger.info("job-anonimizacao-lgpd: fim")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    raise SystemExit(run())
