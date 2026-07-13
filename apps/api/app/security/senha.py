"""Hash de senha (D2 — bcrypt custo 12).

`hash_senha` inclui salt aleatório por chamada (bcrypt gera um salt novo a
cada hash) — duas chamadas para a mesma senha produzem hashes diferentes,
mas `verificar_senha` confirma ambas.
"""

from __future__ import annotations

import re
import secrets

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

MENSAGEM_COMPLEXIDADE = (
    "A senha deve ter no mínimo 8 caracteres, incluindo letras maiúsculas, "
    "minúsculas e números"
)


def hash_senha(senha: str) -> str:
    return _pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha, senha_hash)


def hash_senha_inutilizavel() -> str:
    """Hash de um valor aleatório — placeholder para contas sem senha utilizável
    ainda (cadastro pendente de primeiro acesso, senha invalidada por reset)."""
    return hash_senha(secrets.token_urlsafe(32))


def senha_atende_complexidade(senha: str) -> bool:
    """Mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número (PRD US 1.6 Cen.1b)."""
    return (
        len(senha) >= 8
        and re.search(r"[A-Z]", senha) is not None
        and re.search(r"[a-z]", senha) is not None
        and re.search(r"[0-9]", senha) is not None
    )
