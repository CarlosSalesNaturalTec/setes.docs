"""Endpoints de dev/E2E (Settings.dev_email_inbox / dev_db_reset) — usados
pelos testes Playwright para ler o link de primeiro acesso/recuperação de
senha e para garantir banco limpo antes da suíte (task 12.x), sem depender de
um provedor de e-mail real nem de acesso direto ao Postgres a partir do Node.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import main
from app.config import Settings, get_settings
from app.db.models import Unidade
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, dev_inbox_limpar, enqueue_email


@pytest.fixture(autouse=True)
def _limpar_inbox():
    dev_inbox_limpar()
    yield
    dev_inbox_limpar()


def test_endpoint_retorna_404_quando_desabilitado(client):
    resp = client.get("/internal/dev/emails")
    assert resp.status_code == 404


def test_enqueue_email_com_dev_inbox_nao_chama_cloud_tasks_real():
    settings = Settings(DEV_EMAIL_INBOX=True)
    config = config_from_settings(settings)
    message = EmailMessage(to="user@example.com", subject="Assunto", body="Corpo com link")

    nome = enqueue_email(message, event_id="primeiro-acesso:abc", config=config)

    assert nome == "dev-inbox/tasks/primeiro-acesso-abc"


def test_endpoint_lista_e_filtra_por_destinatario():
    settings = Settings(DEV_EMAIL_INBOX=True)
    main.app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(main.app) as c:
            config = config_from_settings(settings)
            enqueue_email(
                EmailMessage(to="a@example.com", subject="s1", body="link-a"),
                event_id="primeiro-acesso:a",
                config=config,
            )
            enqueue_email(
                EmailMessage(to="b@example.com", subject="s2", body="link-b"),
                event_id="primeiro-acesso:b",
                config=config,
            )

            resp_todos = c.get("/internal/dev/emails")
            assert resp_todos.status_code == 200
            assert len(resp_todos.json()) == 2

            resp_filtrado = c.get("/internal/dev/emails", params={"to": "a@example.com"})
            assert resp_filtrado.status_code == 200
            corpos = resp_filtrado.json()
            assert len(corpos) == 1
            assert corpos[0]["body"] == "link-a"
    finally:
        main.app.dependency_overrides.clear()


def test_reset_retorna_404_quando_desabilitado(client):
    resp = client.post("/internal/dev/reset")
    assert resp.status_code == 404


def test_reset_trunca_tabelas_e_reseeda_sistema_config(db):
    db.add(Unidade(nome="Unidade a apagar", sigla="UAA", ativo=True))
    db.commit()
    db.execute(text("UPDATE sistema_config SET inicializado = true WHERE id = 1"))
    db.commit()

    settings = Settings(DEV_DB_RESET=True)
    main.app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(main.app) as c:
            resp = c.post("/internal/dev/reset")
            assert resp.status_code == 204
    finally:
        main.app.dependency_overrides.clear()

    assert db.execute(text("SELECT count(*) FROM unidade")).scalar() == 0
    assert db.execute(text("SELECT inicializado FROM sistema_config WHERE id = 1")).scalar() is False


def test_reset_rate_limit_retorna_404_quando_desabilitado(client):
    """Sem a flag, o contador de rate limit (D6) não é zerável de fora."""
    resp = client.post("/internal/dev/reset-rate-limit")
    assert resp.status_code == 404


def test_reset_rate_limit_libera_novas_tentativas_de_login(db):
    """Com a flag, o contador zera e o 11º login volta a ser processado."""
    settings = Settings(DEV_RATE_LIMIT_RESET=True)
    main.app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(main.app) as c:
            credenciais = {"email": "inexistente@example.com", "senha": "SenhaQualquer1"}
            # O limite é 10/min/IP: a 11ª tentativa é barrada com 429.
            for _ in range(10):
                assert c.post("/auth/login", json=credenciais).status_code == 401
            assert c.post("/auth/login", json=credenciais).status_code == 429

            assert c.post("/internal/dev/reset-rate-limit").status_code == 204

            assert c.post("/auth/login", json=credenciais).status_code == 401
    finally:
        main.app.dependency_overrides.clear()
