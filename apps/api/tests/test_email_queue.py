"""Teste de app/email/queue.py (task 2.8) — nome de task determinístico a
partir do event_id (dedup nativo do Cloud Tasks)."""

from __future__ import annotations

from app.email.provider import EmailMessage
from app.email.queue import EnqueueConfig, enqueue_email


class _FakeCloudTasksClient:
    def __init__(self) -> None:
        self.created: list[dict] = []

    def queue_path(self, project: str, location: str, queue: str) -> str:
        return f"projects/{project}/locations/{location}/queues/{queue}"

    def create_task(self, request: dict):
        self.created.append(request)

        class _Resp:
            name = request["task"]["name"]

        return _Resp()


def _config() -> EnqueueConfig:
    return EnqueueConfig(
        project_id="proj",
        location="southamerica-east1",
        queue="emails",
        target_url="https://api.example.run.app/internal/tasks/email",
        oidc_service_account_email="sa-tasks-invoker@proj.iam.gserviceaccount.com",
    )


def test_nome_da_task_e_deterministico_a_partir_do_event_id():
    client = _FakeCloudTasksClient()
    message = EmailMessage(to="user@example.com", subject="Assunto", body="Corpo")

    nome1 = enqueue_email(message, event_id="primeiro-acesso:abc123", config=_config(), client=client)
    nome2 = enqueue_email(message, event_id="primeiro-acesso:abc123", config=_config(), client=client)

    assert nome1 == nome2
    assert nome1 == (
        "projects/proj/locations/southamerica-east1/queues/emails/tasks/primeiro-acesso-abc123"
    )


def test_task_criada_aponta_para_endpoint_interno_com_oidc():
    client = _FakeCloudTasksClient()
    message = EmailMessage(to="user@example.com", subject="Assunto", body="Corpo")

    enqueue_email(message, event_id="recuperacao-senha:xyz", config=_config(), client=client)

    task = client.created[0]["task"]
    assert task["http_request"]["url"] == "https://api.example.run.app/internal/tasks/email"
    assert (
        task["http_request"]["oidc_token"]["service_account_email"]
        == "sa-tasks-invoker@proj.iam.gserviceaccount.com"
    )
