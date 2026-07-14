"""Rate limiting (D6) — `slowapi`, 10 req/min/IP, aplicado nas rotas públicas
de autenticação (`/auth/login`, `/auth/recuperar-senha`, `/auth/primeiro-acesso`).

Limitação assumida (D6, Riscos): contador em memória do processo, não
compartilhado entre réplicas Cloud Run — camada complementar ao bloqueio por
conta (D5), que é a defesa primária e vive no Postgres.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

RATE_LIMIT_AUTH_PUBLICO = "10/minute"
