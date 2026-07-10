"""baseline — sem tabela de negócio; habilita extensões de base

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-09

Baseline do bootstrap: NÃO cria tabela de negócio (processo, unidade, etc.).
Apenas habilita extensões que os changes de negócio usarão (ex.: pgcrypto para
o identificador anonimizado irreversível da US 10.3). Idempotente via IF NOT EXISTS.
"""

from __future__ import annotations

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
