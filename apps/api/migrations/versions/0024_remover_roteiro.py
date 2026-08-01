"""remover roteiro — processo.roteiro_id/ordem_atual, tabelas roteiro/roteiro_etapa

Revision ID: 0024_remover_roteiro
Revises: 0023_tramitacao_setor_servidor_mensagem
Create Date: 2026-07-31

Change tramitacao-manual (design.md — Why, D1). O cliente rejeitou a
tramitação automática por roteiro; o destino passa a ser escolhido
explicitamente em cada ação (`0022`/`0023`). Remove `processo.roteiro_id` e
`processo.ordem_atual`, depois as tabelas `roteiro_etapa` e `roteiro` (nessa
ordem, pela FK). O downgrade recria as tabelas vazias — não restaura dados: a
base em avaliação contém apenas dados de teste (decisão do cliente).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0024_remover_roteiro"
down_revision = "0023_tramitacao_setor_servidor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("processo_roteiro_id_fkey", "processo", type_="foreignkey")
    op.drop_column("processo", "roteiro_id")
    op.drop_column("processo", "ordem_atual")

    op.drop_table("roteiro_etapa")
    op.drop_table("roteiro")


def downgrade() -> None:
    op.create_table(
        "roteiro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tipo_processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tipo_processo.id"),
            nullable=False,
        ),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "roteiro_etapa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "roteiro_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roteiro.id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=False,
        ),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.UniqueConstraint("roteiro_id", "ordem", name="uq_roteiro_etapa_ordem"),
    )

    op.add_column("processo", sa.Column("ordem_atual", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "processo", sa.Column("roteiro_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key("processo_roteiro_id_fkey", "processo", "roteiro", ["roteiro_id"], ["id"])
