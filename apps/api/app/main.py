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

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings
from app.email.provider import EmailDeliveryError, EmailMessage, send_email
from app.rate_limit import MSG_RATE_LIMIT_CONSULTA_PUBLICA, limiter
from app.routers import (
    auth,
    consulta_publica,
    dashboard,
    dev_tools,
    documentos,
    documentos_removidos,
    notificacoes,
    processos,
    setup,
    sistema_config,
    tipos_processo,
    unidades,
    usuarios,
)
from app.schemas import AckResponse, EmailTaskPayload, HealthResponse
from app.security.oidc import require_tasks_invoker

# "Logs do Sistema" — em produção vai para Cloud Logging (stdout estruturado).
# Sem isso, logger.info/error não tem handler e é descartado silenciosamente
# (só o root logger de última instância pega WARNING+, então nem "email.falha"
# aparecia de forma confiável). Mesma config usada em app/jobs/entrypoint.py.
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("setes.api")

app = FastAPI(title="SETES.DOCS API", version="0.0.0")
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """D4 — rotas públicas de consulta devolvem a mensagem exata do PRD;
    as demais mantêm o corpo padrão do `slowapi`."""
    if request.url.path.startswith("/publico/"):
        response = JSONResponse(
            {"detail": MSG_RATE_LIMIT_CONSULTA_PUBLICA}, status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        return limiter._inject_headers(response, request.state.view_rate_limit)
    return _rate_limit_exceeded_handler(request, exc)


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allowed_origins,
    allow_credentials=False,  # sessão é via Bearer token (D1), não cookies
    allow_methods=["*"],
    allow_headers=["*"],
    # O frontend lê o JWT renovado (sliding window, D1) e o nome do arquivo
    # (Épico 3, D5 — streaming de documentos) nestes headers a cada chamada;
    # sem expor, o fetch() do browser não os enxerga (CORS só libera os
    # headers "simples" por padrão).
    expose_headers=["X-Renewed-Token", "Content-Disposition"],
)

app.include_router(setup.router)
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(unidades.router)
app.include_router(tipos_processo.router)
app.include_router(processos.router)
app.include_router(documentos.router)
app.include_router(documentos_removidos.router)
app.include_router(notificacoes.router)
app.include_router(sistema_config.router)
app.include_router(dashboard.router)
app.include_router(consulta_publica.router)
app.include_router(dev_tools.router)


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
