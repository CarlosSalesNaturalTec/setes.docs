"""Endpoints de desenvolvimento/E2E — nunca habilitados em produção.

- `GET /internal/dev/emails` (Settings.dev_email_inbox): lê o link de primeiro
  acesso/recuperação de senha sem um provedor de e-mail real.
- `POST /internal/dev/reset` (Settings.dev_db_reset): trunca as tabelas de
  negócio e reseeda `sistema_config`, dando "banco limpo" à suíte Playwright
  (task 12.x) sem depender de acesso direto ao Postgres a partir do Node.

Cada endpoint responde 404 quando sua flag correspondente está desligada —
nenhuma delas é setada pelo Cloud Run/Secret Manager em produção.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.db.dev_reset import resetar_banco
from app.db.session import get_engine
from app.email.queue import dev_inbox_listar
from app.schemas.dev_inbox import DevEmailItem

router = APIRouter(prefix="/internal/dev", tags=["dev"])


@router.get("/emails", response_model=list[DevEmailItem])
def listar_emails(
    settings: Annotated[Settings, Depends(get_settings)],
    to: str | None = None,
) -> list[DevEmailItem]:
    if not settings.dev_email_inbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return [DevEmailItem(**item) for item in dev_inbox_listar(to=to)]


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def resetar(settings: Annotated[Settings, Depends(get_settings)]) -> None:
    if not settings.dev_db_reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    resetar_banco(get_engine())
