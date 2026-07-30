"""usuario — setor_id e campos complementares de cadastro

Revision ID: 0021_usuario_setor_e_campos
Revises: 0020_setor
Create Date: 2026-07-30

Change setores-e-cadastro-usuario (design.md D1, D2, D4, D7). `setor_id` é
nullable no schema: a obrigatoriedade é do perfil Servidor e depende da coluna
`perfil`, portanto é validada na aplicação (D2), não por CHECK condicional.
`chefia_direta` é texto livre, sem FK — a chefia pode ser externa ao sistema
(D4). `telefone`/`cargo`/`chefia_direta` são dados pessoais de servidor, fora
da consulta pública.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0021_usuario_setor_e_campos"
down_revision = "0020_setor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuario", sa.Column("setor_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key("fk_usuario_setor_id", "usuario", "setor", ["setor_id"], ["id"])
    op.create_index("ix_usuario_setor_id", "usuario", ["setor_id"])
    op.add_column("usuario", sa.Column("telefone", sa.String(30), nullable=True))
    op.add_column("usuario", sa.Column("cargo", sa.String(200), nullable=True))
    op.add_column("usuario", sa.Column("chefia_direta", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "chefia_direta")
    op.drop_column("usuario", "cargo")
    op.drop_column("usuario", "telefone")
    op.drop_index("ix_usuario_setor_id", table_name="usuario")
    op.drop_constraint("fk_usuario_setor_id", "usuario", type_="foreignkey")
    op.drop_column("usuario", "setor_id")
