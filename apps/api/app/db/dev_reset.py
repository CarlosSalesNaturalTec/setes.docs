"""Reset de banco para desenvolvimento/E2E e testes automatizados.

Trunca as tabelas de negócio (nunca as de infraestrutura do Alembic) e
reseeda o singleton `sistema_config` como não inicializado — mesmo estado
usado pela fixture `db` do pytest (`tests/conftest.py`) e pelo endpoint de
dev `POST /internal/dev/reset` (Settings.dev_db_reset) consumido pelos
testes Playwright (task 12.x) antes de cada execução da suíte.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

TABELAS_NEGOCIO = (
    "tramitacao",
    "processo_interessado",
    "processo",
    "processo_contador_ano",
    "sessao",
    "token_autenticacao",
    "senha_historico",
    "log_seguranca",
    "tipo_processo",
    "unidade_gestor",
    "usuario",
    "setor",
    "unidade",
    "sistema_config",
    # Change modelos-de-documento (design.md D6) — `documento.modelo_id`
    # referencia esta tabela; TRUNCATE ... CASCADE resolve a ordem de
    # dependência automaticamente, então a posição na tupla é só organizativa.
    "modelo_documento",
)


def resetar_banco(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(TABELAS_NEGOCIO)} RESTART IDENTITY CASCADE"))
        conn.execute(text("INSERT INTO sistema_config (id, inicializado) VALUES (1, false)"))
