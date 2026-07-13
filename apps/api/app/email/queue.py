"""Enqueue de e-mail assíncrono (D10) — fila `emails` (Cloud Tasks).

O bootstrap só implementou o lado receptor (`POST /internal/tasks/email`,
OIDC-only, `maxAttempts=1`). Este módulo é o primeiro emissor: cria uma Cloud
Task cujo *nome* é derivado de `event_id` — dedup nativo do Cloud Tasks,
reenfileirar o mesmo `event_id` não duplica o envio (levanta `AlreadyExists`,
tratado aqui como sucesso).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from google.api_core.exceptions import AlreadyExists
from google.cloud import tasks_v2

from app.config import Settings
from app.email.provider import EmailMessage

logger = logging.getLogger("setes.api")


@dataclass(frozen=True)
class EnqueueConfig:
    project_id: str
    location: str
    queue: str
    target_url: str  # https://.../internal/tasks/email
    oidc_service_account_email: str


def config_from_settings(settings: Settings) -> EnqueueConfig:
    return EnqueueConfig(
        project_id=settings.gcp_project_id,
        location=settings.cloud_tasks_location,
        queue=settings.cloud_tasks_queue,
        target_url=f"{settings.oidc_audience}/internal/tasks/email",
        oidc_service_account_email=settings.tasks_invoker_sa_email,
    )


def _task_id(event_id: str) -> str:
    """Cloud Tasks só aceita `[A-Za-z0-9_-]` no nome da task."""
    return event_id.replace(":", "-")


def enqueue_email(
    message: EmailMessage,
    *,
    event_id: str,
    config: EnqueueConfig,
    client: tasks_v2.CloudTasksClient | None = None,
) -> str:
    """Cria a Cloud Task apontando para `/internal/tasks/email`. Retorna o nome da task."""
    client = client or tasks_v2.CloudTasksClient()
    queue_path = client.queue_path(config.project_id, config.location, config.queue)
    task_name = f"{queue_path}/tasks/{_task_id(event_id)}"

    body = json.dumps(
        {
            "to": message.to,
            "subject": message.subject,
            "body": message.body,
            "event_id": event_id,
        }
    ).encode()

    task = {
        "name": task_name,
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": config.target_url,
            "headers": {"Content-Type": "application/json"},
            "body": body,
            "oidc_token": {"service_account_email": config.oidc_service_account_email},
        },
    }

    try:
        client.create_task(request={"parent": queue_path, "task": task})
    except AlreadyExists:
        pass
    return task_name


def enqueue_email_seguro(
    message: EmailMessage,
    *,
    event_id: str,
    config: EnqueueConfig,
    client: tasks_v2.CloudTasksClient | None = None,
) -> bool:
    """`enqueue_email` sem propagar exceção — o fluxo de negócio já foi commitado
    quando o e-mail é enfileirado; uma falha no Cloud Tasks não deve reverter a
    operação principal (cadastro, login, etc.). Loga e retorna `False` em falha.
    """
    try:
        enqueue_email(message, event_id=event_id, config=config, client=client)
        return True
    except Exception:
        logger.exception("email.enqueue_falha event_id=%s to=%s", event_id, message.to)
        return False
