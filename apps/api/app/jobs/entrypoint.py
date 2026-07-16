"""Entrypoint do Cloud Run Job `job-manutencao-diaria` (US 2.5, Épico 3, Épico 5).

Executa os passos de arquivamento automático, purga física de documentos,
verificação de prazos (alerta interno + e-mail) e expurgo de notificações
lidas sobre o estado atual do banco. O contrato de idempotência (seleção por
estado, retomada sem duplicar efeito) já está provado em memória por
`app.jobs.manutencao_diaria` e `tests/test_idempotencia.py`; aqui ele passa a
operar sobre o banco real. Executável via:

    uv run python -m app.jobs.entrypoint
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.config import get_settings
from app.db.session import get_session_factory
from app.services.arquivamento import arquivar_vencidos
from app.services.documento import purgar_documentos_vencidos
from app.services.notificacao import expurgar_notificacoes_lidas
from app.services.prazo import verificar_prazos
from app.services.storage import get_storage

logger = logging.getLogger("setes.jobs.manutencao_diaria")


def run() -> int:
    logger.info("job-manutencao-diaria: início")
    agora = datetime.now(timezone.utc)
    settings = get_settings()
    session = get_session_factory()()
    try:
        total_arquivados = arquivar_vencidos(session, agora=agora)
        logger.info("job-manutencao-diaria: arquivamento_automatico total=%s", total_arquivados)

        storage = get_storage(settings)
        total_purgados = purgar_documentos_vencidos(session, agora=agora, storage=storage)
        logger.info("job-manutencao-diaria: purga_documentos total=%s", total_purgados)

        total_alertas = verificar_prazos(session, agora=agora, settings=settings)
        logger.info("job-manutencao-diaria: alerta_prazo total=%s", total_alertas)

        total_expurgados = expurgar_notificacoes_lidas(session, agora=agora)
        logger.info("job-manutencao-diaria: expurgo_notificacoes total=%s", total_expurgados)
    finally:
        session.close()
    logger.info("job-manutencao-diaria: fim")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    raise SystemExit(run())
