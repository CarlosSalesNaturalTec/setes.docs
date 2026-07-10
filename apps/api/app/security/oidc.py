"""Verificação de token OIDC do Google para os endpoints internos.

O Cloud Tasks invoca `/internal/tasks/*` anexando um token OIDC assinado pelo
Google, cujo `email` é o da `sa-tasks-invoker`. Este módulo é a dependência
FastAPI que rejeita qualquer chamada sem um token válido dessa identidade
(spec fila-notificacoes — "Acesso negado — chamada sem token OIDC").

A verificação é feita contra as chaves públicas do Google (JWKS). Em teste,
`verify_google_oidc` é sobreposta por um fake — ver tests/conftest.py.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError

from app.config import Settings, get_settings

_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}

# Cache simples do JWKS (as chaves do Google giram com pouca frequência).
_jwks_cache: dict | None = None


def _fetch_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        import httpx

        resp = httpx.get(_GOOGLE_JWKS_URL, timeout=5.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def verify_google_oidc(token: str, audience: str) -> dict:
    """Valida assinatura, issuer e audience do token OIDC do Google.

    Retorna as claims. Levanta JWTError se inválido.
    """
    jwks = _fetch_jwks()
    return jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        audience=audience,
        issuer=list(_GOOGLE_ISSUERS),
    )


def require_tasks_invoker(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> dict:
    """Dependência: exige token OIDC válido emitido para a `sa-tasks-invoker`."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token OIDC ausente.",
        )
    token = authorization.split(" ", 1)[1].strip()

    try:
        claims = verify_google_oidc(token, audience=settings.oidc_audience)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token OIDC inválido.",
        ) from exc

    email = claims.get("email")
    email_verified = claims.get("email_verified", False)
    if not email_verified or email != settings.tasks_invoker_sa_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Identidade não autorizada para o endpoint interno.",
        )
    return claims
