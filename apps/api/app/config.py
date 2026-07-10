"""Configuração do serviço, lida de variáveis de ambiente.

Os segredos (`db-password`, `jwt-signing-key`, `sendgrid-api-key`) são injetados
pelo Cloud Run como variáveis de ambiente apontando para o Secret Manager (D4).
"""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

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

    # Banco ---------------------------------------------------------------------
    # `db_password` vem do secret `db-password` (só a senha, task 3.3); as demais
    # peças são env vars simples. A URL completa é montada em `database_url`.
    db_host: str = Field(default="", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="app", alias="DB_USER")
    db_name: str = Field(default="setes", alias="DB_NAME")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=0, alias="DB_MAX_OVERFLOW")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # E-mail SaaS -------------------------------------------------------------
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    email_from: str = Field(default="no-reply@setes.docs", alias="EMAIL_FROM")

    # Auth --------------------------------------------------------------------
    jwt_signing_key: str = Field(default="", alias="JWT_SIGNING_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
