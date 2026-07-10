"""Configuração do serviço, lida de variáveis de ambiente.

Os segredos (`db-password`, `jwt-signing-key`, `sendgrid-api-key`) são injetados
pelo Cloud Run como variáveis de ambiente apontando para o Secret Manager (D4).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Identidade GCP / OIDC ---------------------------------------------------
    gcp_project_id: str = Field(default="", alias="GCP_PROJECT_ID")
    # E-mail (service account) autorizada a chamar os endpoints internos via OIDC.
    tasks_invoker_sa_email: str = Field(default="", alias="TASKS_INVOKER_SA_EMAIL")
    # Audience esperada no token OIDC (normalmente a URL do próprio serviço `api`).
    oidc_audience: str = Field(default="", alias="OIDC_AUDIENCE")

    # Banco -------------------------------------------------------------------
    database_url: str = Field(default="", alias="DATABASE_URL")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=0, alias="DB_MAX_OVERFLOW")

    # E-mail SaaS -------------------------------------------------------------
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    email_from: str = Field(default="no-reply@setes.docs", alias="EMAIL_FROM")

    # Auth --------------------------------------------------------------------
    jwt_signing_key: str = Field(default="", alias="JWT_SIGNING_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
