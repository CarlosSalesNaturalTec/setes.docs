"""processo_interessado.anonimizado_em — guard de idempotência da anonimização

Revision ID: 0017_interessado_anonimizado_em
Revises: 0016_prazo_anonimizacao
Create Date: 2026-07-17

Épico 10 (D2, design.md Migration Plan passo 5). `NULL` cobre todas as linhas
existentes — nada é anonimizado retroativamente pela migration em si, só pela
execução seguinte da rotina/atendimento manual.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_interessado_anonimizado_em"
down_revision = "0016_prazo_anonimizacao"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "processo_interessado",
        sa.Column("anonimizado_em", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("processo_interessado", "anonimizado_em")
