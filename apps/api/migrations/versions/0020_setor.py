"""setor — segundo nível da estrutura organizacional (1:N com unidade)

Revision ID: 0020_setor
Revises: 0019_ix_unidade_origem
Create Date: 2026-07-30

Change setores-e-cadastro-usuario (design.md D1, D7). Sigla única *dentro* da
unidade (`uq_setor_unidade_sigla`) — a mesma sigla pode existir em unidades
diferentes. Setor nunca é excluído, apenas desativado (`ativo`), porque o
histórico imutável de tramitação passa a referenciá-lo.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0020_setor"
down_revision = "0019_ix_unidade_origem"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "setor",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unidade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("sigla", sa.String(20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_setor_unidade_id", "setor", ["unidade_id"])
    op.create_unique_constraint("uq_setor_unidade_sigla", "setor", ["unidade_id", "sigla"])


def downgrade() -> None:
    op.drop_table("setor")
