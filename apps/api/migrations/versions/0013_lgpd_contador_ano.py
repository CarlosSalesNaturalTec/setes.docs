"""solicitacao_lgpd_contador_ano — contador atômico do protocolo LGPD

Revision ID: 0013_lgpd_contador_ano
Revises: 0012_acesso_auditoria
Create Date: 2026-07-17

Épico 10 (US 10.1, D5, design.md Migration Plan passo 1). Mesmo padrão de
`processo_contador_ano`: uma linha por ano, incrementada via upsert atômico na
mesma transação da criação da `solicitacao_lgpd`. Tabela separada de
`processo_contador_ano` — sequência semanticamente distinta (D5).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_lgpd_contador_ano"
down_revision = "0012_acesso_auditoria"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "solicitacao_lgpd_contador_ano",
        sa.Column("ano", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("ultimo_sequencial", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("solicitacao_lgpd_contador_ano")
