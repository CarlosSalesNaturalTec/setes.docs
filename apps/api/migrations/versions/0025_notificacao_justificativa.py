"""notificacao — justificativa (reatribuição / destino corrigido)

Revision ID: 0025_notificacao_justificativa
Revises: 0024_remover_roteiro
Create Date: 2026-07-31

Change tramitacao-manual (design.md D8). `REATRIBUIDO_PARA_VOCE` exige exibir
a justificativa da reatribuição (notificacoes-internas spec); `DESTINO_CORRIGIDO`
usa o mesmo campo para descrever o novo destino. Nullable — os demais tipos de
notificação (`novo_processo`, `concluido`, `alerta_prazo`) não o preenchem.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0025_notificacao_justificativa"
down_revision = "0024_remover_roteiro"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notificacao", sa.Column("justificativa", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notificacao", "justificativa")
