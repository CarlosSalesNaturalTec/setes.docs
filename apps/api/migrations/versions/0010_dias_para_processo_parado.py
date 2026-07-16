"""dias para processo parado — limiar do KPI "Processos Parados" (US 6.1/8.5)

Revision ID: 0010_dias_para_processo_parado
Revises: 0009_dias_antecedencia_alerta
Create Date: 2026-07-16

Épico 6 (US 6.1, US 8.5, design.md D1 — Migration Plan passo 1). Adiciona
`sistema_config.dias_para_processo_parado` com `DEFAULT 7`; o `server_default`
já faz o backfill da linha singleton id=1 existente.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_dias_para_processo_parado"
down_revision = "0009_dias_antecedencia_alerta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sistema_config",
        sa.Column("dias_para_processo_parado", sa.Integer(), nullable=False, server_default="7"),
    )


def downgrade() -> None:
    op.drop_column("sistema_config", "dias_para_processo_parado")
