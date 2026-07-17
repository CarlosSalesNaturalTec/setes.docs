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

    # Cloud Tasks — fila `emails` provisionada no bootstrap (D10).
    cloud_tasks_location: str = Field(default="southamerica-east1", alias="CLOUD_TASKS_LOCATION")
    cloud_tasks_queue: str = Field(default="emails", alias="CLOUD_TASKS_QUEUE")

    # URL do frontend Next.js — usada para montar os links enviados por e-mail
    # (primeiro acesso, recuperação de senha, reset por Administrador).
    frontend_base_url: str = Field(default="http://localhost:3000", alias="FRONTEND_BASE_URL")

    # Dev/E2E only: quando habilitado, enqueue_email (D10) não chama o Cloud
    # Tasks real — grava a mensagem numa caixa de entrada em memória, exposta
    # via GET /internal/dev/emails. Nunca deve ser habilitado em produção
    # (não é setado pelo Cloud Run/Secret Manager); usado pelos testes
    # Playwright para obter o link de primeiro acesso/recuperação de senha
    # sem depender de um provedor de e-mail real.
    dev_email_inbox: bool = Field(default=False, alias="DEV_EMAIL_INBOX")

    # Dev/E2E only: habilita POST /internal/dev/reset, que trunca as tabelas
    # de negócio e reseeda `sistema_config` (mesmo reset usado pela fixture
    # `db` do pytest). Roda antes da suíte Playwright (task 12.x) para
    # garantir "banco limpo" entre execuções. Nunca setado em produção.
    dev_db_reset: bool = Field(default=False, alias="DEV_DB_RESET")

    # Cloud Storage (Épico 3, D4) — bucket `${project_id}-documentos`
    # (provisionado no bootstrap). Em produção, `documentos_storage_local` fica
    # `False` e o backend real (google-cloud-storage, ADC via SA do Cloud Run)
    # é usado; em dev/pytest/E2E, o backend local (filesystem) evita depender
    # do GCP, mesmo padrão dev/prod de `email/provider.py`.
    documentos_bucket: str = Field(default="", alias="DOCUMENTOS_BUCKET")
    documentos_storage_local: bool = Field(default=True, alias="DOCUMENTOS_STORAGE_LOCAL")
    documentos_storage_local_dir: str = Field(
        default="/tmp/setes-documentos", alias="DOCUMENTOS_STORAGE_LOCAL_DIR"
    )

    # Cloud Storage (Épico 10, D6) — bucket dedicado `${project_id}-lgpd-solicitacoes`
    # para o documento de identificação anexado ao canal público de solicitação
    # LGPD; mesmo padrão dev/prod local-vs-GCS de `documentos_bucket` acima.
    lgpd_solicitacoes_bucket: str = Field(default="", alias="LGPD_SOLICITACOES_BUCKET")
    lgpd_solicitacoes_storage_local_dir: str = Field(
        default="/tmp/setes-lgpd-solicitacoes", alias="LGPD_SOLICITACOES_STORAGE_LOCAL_DIR"
    )

    # CORS — o frontend chama a API a partir de uma origem diferente (dev:
    # localhost:3000 -> localhost:8000; prod: domínios distintos no Cloud Run).
    cors_allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ALLOWED_ORIGINS"
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
