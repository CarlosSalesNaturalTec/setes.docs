"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings, get_settings
from app.security import oidc


@pytest.fixture
def settings() -> Settings:
    return Settings(
        TASKS_INVOKER_SA_EMAIL="sa-tasks-invoker@proj.iam.gserviceaccount.com",
        OIDC_AUDIENCE="https://api.example.run.app",
        SENDGRID_API_KEY="",  # vazio: força EmailDeliveryError no caminho de falha
    )


@pytest.fixture
def client(settings: Settings):
    main.app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture
def fake_valid_oidc(monkeypatch, settings: Settings):
    """Substitui a verificação real do JWKS do Google por um fake que aceita
    um token 'válido' emitido para a sa-tasks-invoker."""

    def _verify(token: str, audience: str) -> dict:
        if token != "valid-token" or audience != settings.oidc_audience:
            from jose.exceptions import JWTError

            raise JWTError("token inválido no fake")
        return {
            "email": settings.tasks_invoker_sa_email,
            "email_verified": True,
            "aud": audience,
        }

    monkeypatch.setattr(oidc, "verify_google_oidc", _verify)
