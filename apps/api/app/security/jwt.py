"""Emissão/validação de JWT HS256 (D1), assinado com `Settings.jwt_signing_key`
(segredo `jwt-signing-key` provisionado no bootstrap, D4).

Claims: `sub` (usuario_id), `jti` (identificador da sessão em `sessao`), `exp`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from jose import jwt
from jose.exceptions import JWTError

ALGORITHM = "HS256"


class TokenInvalido(Exception):
    """Assinatura inválida ou token expirado."""


def criar_jwt(*, usuario_id: uuid.UUID, jti: uuid.UUID, expira_em: datetime, chave: str) -> str:
    claims = {"sub": str(usuario_id), "jti": str(jti), "exp": expira_em}
    return jwt.encode(claims, chave, algorithm=ALGORITHM)


def decodificar_jwt(token: str, *, chave: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, chave, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise TokenInvalido(str(exc)) from exc
