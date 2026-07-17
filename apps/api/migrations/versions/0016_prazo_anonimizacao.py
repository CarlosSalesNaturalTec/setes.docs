"""tipo_processo.prazo_anonimizacao_anos — prazo LGPD configurável por tipo

Revision ID: 0016_prazo_anonimizacao
Revises: 0015_solicitacao_lgpd
Create Date: 2026-07-17

US 10.3 Cen.2 (design.md Migration Plan passo 4). `DEFAULT 5` cobre os tipos
já cadastrados sem efeito retroativo de comportamento — só passa a valer a
partir da execução seguinte da rotina/atendimento (mesma regra de
`sistema_config`).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_prazo_anonimizacao"
down_revision = "0015_solicitacao_lgpd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tipo_processo",
        sa.Column("prazo_anonimizacao_anos", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("tipo_processo", "prazo_anonimizacao_anos")
