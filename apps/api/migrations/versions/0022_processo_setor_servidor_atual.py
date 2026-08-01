"""processo — setor_atual_id e servidor_atual_id (responsável corrente)

Revision ID: 0022_processo_setor_servidor_atual
Revises: 0021_usuario_setor_e_campos
Create Date: 2026-07-31

Change tramitacao-manual (design.md D1, D10). O processo passa a registrar
diretamente o setor e o servidor atualmente responsáveis, em vez de derivá-los
do roteiro. Backfill: `servidor_atual_id = criado_por_id` e `setor_atual_id` =
setor do criador — o processo nasce (e, para os já existentes, permanece)
atribuído a quem o criou. `SET NOT NULL` só depois do backfill.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0022_processo_setor_servidor"  # alembic_version.version_num é varchar(32)
down_revision = "0021_usuario_setor_e_campos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "processo", sa.Column("setor_atual_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "processo", sa.Column("servidor_atual_id", postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Backfill: servidor_atual = criador; setor_atual = setor do criador no
    # momento da migration (pode ser NULL se o criador não tiver setor vinculado).
    op.execute(
        "UPDATE processo SET servidor_atual_id = criado_por_id"
    )
    op.execute(
        """
        UPDATE processo
        SET setor_atual_id = usuario.setor_id
        FROM usuario
        WHERE usuario.id = processo.criado_por_id
        """
    )

    op.create_foreign_key(
        "fk_processo_setor_atual_id", "processo", "setor", ["setor_atual_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_processo_servidor_atual_id", "processo", "usuario", ["servidor_atual_id"], ["id"]
    )
    op.create_index("ix_processo_setor_atual_id", "processo", ["setor_atual_id"])
    op.create_index("ix_processo_servidor_atual_id", "processo", ["servidor_atual_id"])

    op.alter_column("processo", "servidor_atual_id", nullable=False)
    op.alter_column("processo", "setor_atual_id", nullable=False)


def downgrade() -> None:
    op.alter_column("processo", "setor_atual_id", nullable=True)
    op.alter_column("processo", "servidor_atual_id", nullable=True)
    op.drop_index("ix_processo_servidor_atual_id", table_name="processo")
    op.drop_index("ix_processo_setor_atual_id", table_name="processo")
    op.drop_constraint("fk_processo_servidor_atual_id", "processo", type_="foreignkey")
    op.drop_constraint("fk_processo_setor_atual_id", "processo", type_="foreignkey")
    op.drop_column("processo", "servidor_atual_id")
    op.drop_column("processo", "setor_atual_id")
