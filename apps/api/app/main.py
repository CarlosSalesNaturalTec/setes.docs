"""Aplicação FastAPI do SETES.DOCS.

Rotas do bootstrap:
- GET  /health                — health check (Cloud Run / task 1.2, spec plataforma-gcp)
- POST /internal/tasks/email  — endpoint interno OIDC-only chamado pelo Cloud Tasks
                                (task 7.2, spec fila-notificacoes)
"""

from __future__ import annotations

import logging
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, status

from app.config import Settings, get_settings
from app.email.provider import EmailDeliveryError, EmailMessage, send_email
from app.schemas import AckResponse, EmailTaskPayload, HealthResponse
from app.security.oidc import require_tasks_invoker

# "Logs do Sistema" — em produção vai para Cloud Logging (stdout estruturado).
# Sem isso, logger.info/error não tem handler e é descartado silenciosamente
# (só o root logger de última instância pega WARNING+, então nem "email.falha"
# aparecia de forma confiável). Mesma config usada em app/jobs/entrypoint.py.
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("setes.api")

app = FastAPI(title="SETES.DOCS API", version="0.0.0")


@app.get("/health", response_model=HealthResponse, tags=["infra"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="api")


@app.post(
    "/internal/tasks/email",
    response_model=AckResponse,
    status_code=status.HTTP_200_OK,
    tags=["internal"],
)
def process_email_task(
    payload: EmailTaskPayload,
    _claims: Annotated[dict, Depends(require_tasks_invoker)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AckResponse:
    """Processa uma tarefa de e-mail entregue pelo Cloud Tasks.

    Contrato de falha (US 5.2 Cen.3): em QUALQUER falha de entrega, registra em
    log e retorna 200 (ACK). A fila usa maxAttempts=1, então não há redespacho.
    Nunca propaga exceção — isso faria o Cloud Tasks tratar como retryable.
    """
    try:
        send_email(
            EmailMessage(to=payload.to, subject=payload.subject, body=payload.body),
            api_key=settings.sendgrid_api_key,
            sender=settings.email_from,
        )
        logger.info("email.enviado event_id=%s to=%s", payload.event_id, payload.to)
    except EmailDeliveryError as exc:
        # Falha registrada; ACK mesmo assim para não redespachar.
        logger.error(
            "email.falha event_id=%s to=%s erro=%s",
            payload.event_id,
            payload.to,
            exc,
        )
    return AckResponse(status="acked")
