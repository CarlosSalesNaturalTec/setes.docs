"""dias antecedencia alerta — parâmetro de janela do alerta de prazo (US 8.5)

Revision ID: 0009_dias_antecedencia_alerta
Revises: 0008_create_notificacao
Create Date: 2026-07-16

Épico 5 (US 5.4/8.5, design.md D4 — Migration Plan passo 2). Adiciona
`sistema_config.dias_antecedencia_alerta_prazo` com `DEFAULT 2`; o
`server_default` já faz o backfill da linha singleton id=1 existente.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_dias_antecedencia_alerta"
down_revision = "0008_create_notificacao"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sistema_config",
        sa.Column(
            "dias_antecedencia_alerta_prazo", sa.Integer(), nullable=False, server_default="2"
        ),
    )


def downgrade() -> None:
    op.drop_column("sistema_config", "dias_antecedencia_alerta_prazo")
