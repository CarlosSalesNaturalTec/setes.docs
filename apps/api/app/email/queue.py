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
    # `aud` a assinar no token OIDC. DEVE bater com o que o endpoint interno
    # valida (Settings.oidc_audience — a URL base do serviço, SEM o path). Se
    # `audience` for omitido no oidc_token, o Cloud Tasks assina com a URL do
    # alvo (target_url, COM o path) e a validação falha com 401. Ver
    # security/oidc.py:require_tasks_invoker.
    oidc_audience: str
    # Dev/E2E only (Settings.dev_email_inbox) — ver `_DEV_INBOX` abaixo.
    dev_inbox: bool = False


def config_from_settings(settings: Settings) -> EnqueueConfig:
    return EnqueueConfig(
        project_id=settings.gcp_project_id,
        location=settings.cloud_tasks_location,
        queue=settings.cloud_tasks_queue,
        target_url=f"{settings.oidc_audience}/internal/tasks/email",
        oidc_service_account_email=settings.tasks_invoker_sa_email,
        oidc_audience=settings.oidc_audience,
        dev_inbox=settings.dev_email_inbox,
    )


def _task_id(event_id: str) -> str:
    """Cloud Tasks só aceita `[A-Za-z0-9_-]` no nome da task."""
    return event_id.replace(":", "-")


# Caixa de entrada de desenvolvimento (Settings.dev_email_inbox) — usada pelos
# testes Playwright para ler o link de primeiro acesso/recuperação de senha
# sem um provedor de e-mail real nem credenciais do Cloud Tasks localmente.
# Processo único (uvicorn --reload roda num só worker em dev); não precisa de
# sincronização entre processos.
_DEV_INBOX: list[dict] = []


def _dev_inbox_registrar(message: EmailMessage, *, event_id: str) -> None:
    _DEV_INBOX.append(
        {"to": message.to, "subject": message.subject, "body": message.body, "event_id": event_id}
    )


def dev_inbox_listar(*, to: str | None = None) -> list[dict]:
    if to is None:
        return list(_DEV_INBOX)
    return [item for item in _DEV_INBOX if item["to"] == to]


def dev_inbox_limpar() -> None:
    _DEV_INBOX.clear()


def enqueue_email(
    message: EmailMessage,
    *,
    event_id: str,
    config: EnqueueConfig,
    client: tasks_v2.CloudTasksClient | None = None,
) -> str:
    """Cria a Cloud Task apontando para `/internal/tasks/email`. Retorna o nome da task."""
    task_id = _task_id(event_id)

    if config.dev_inbox:
        _dev_inbox_registrar(message, event_id=event_id)
        return f"dev-inbox/tasks/{task_id}"

    client = client or tasks_v2.CloudTasksClient()
    queue_path = client.queue_path(config.project_id, config.location, config.queue)
    task_name = f"{queue_path}/tasks/{task_id}"

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
            "oidc_token": {
                "service_account_email": config.oidc_service_account_email,
                "audience": config.oidc_audience,
            },
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
