"""índice em processo.unidade_origem_id — acompanhamento por origem

Revision ID: 0019_ix_unidade_origem
Revises: 0018_evento_anonimizado
Create Date: 2026-07-22

Change visibilidade-processos-origem (design.md D7). `unidade_origem_id` passa
a ser filtro de toda montagem de Kanban/busca (D1) — sem mudança de dado.
"""

from __future__ import annotations

from alembic import op

revision = "0019_ix_unidade_origem"
down_revision = "0018_evento_anonimizado"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_processo_unidade_origem_id", "processo", ["unidade_origem_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_processo_unidade_origem_id", table_name="processo")
