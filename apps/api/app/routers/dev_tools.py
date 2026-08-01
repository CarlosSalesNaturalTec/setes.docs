"""Endpoints de desenvolvimento/E2E — nunca habilitados em produção.

- `GET /internal/dev/emails` (Settings.dev_email_inbox): lê o link de primeiro
  acesso/recuperação de senha sem um provedor de e-mail real.
- `POST /internal/dev/reset` (Settings.dev_db_reset): trunca as tabelas de
  negócio e reseeda `sistema_config`, dando "banco limpo" à suíte Playwright
  (task 12.x) sem depender de acesso direto ao Postgres a partir do Node.
- `POST /internal/dev/reset-rate-limit` (Settings.dev_rate_limit_reset): zera o
  contador em memória do rate limit de `/auth/*` (D6), que a suíte Playwright
  estouraria — são dezenas de logins do mesmo IP contra o limite de 10/min.
- `POST /internal/dev/arquivar-vencidos` (Settings.dev_db_reset): adianta a
  rotina diária de arquivamento (`services/arquivamento.py`), que em produção
  só roda via Cloud Scheduler + Cloud Run Job — sem isso, o cenário E2E do
  quadro pessoal (change kanban-por-servidor, task 7.2) não teria como
  alcançar o estado Arquivado sem esperar `dias_para_arquivamento` corridos.

Cada endpoint responde 404 quando sua flag correspondente está desligada —
nenhuma delas é setada pelo Cloud Run/Secret Manager em produção.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.dev_reset import resetar_banco
from app.db.session import get_db, get_engine
from app.email.queue import dev_inbox_listar
from app.rate_limit import limiter
from app.schemas.dev_inbox import DevEmailItem
from app.services.arquivamento import arquivar_vencidos

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


@router.post("/reset-rate-limit", status_code=status.HTTP_204_NO_CONTENT)
def resetar_rate_limit(settings: Annotated[Settings, Depends(get_settings)]) -> None:
    if not settings.dev_rate_limit_reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    limiter.reset()  # contador em memória do processo (D6)


@router.post("/arquivar-vencidos", status_code=status.HTTP_204_NO_CONTENT)
def forcar_arquivamento(
    settings: Annotated[Settings, Depends(get_settings)], db: Annotated[Session, Depends(get_db)]
) -> None:
    if not settings.dev_db_reset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    # `agora` bem à frente adianta qualquer `arquivar_em` já congelado na
    # conclusão (US 2.5 Cen.2, D1) — equivalente a rodar a Cloud Run Job hoje.
    arquivar_vencidos(db, agora=datetime.utcnow() + timedelta(days=3650))
