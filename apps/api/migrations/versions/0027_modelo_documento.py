"""modelo_documento — catálogo de modelos e proveniência em documento

Revision ID: 0027_modelo_documento
Revises: 0026_ix_tramitacao_servidores
Create Date: 2026-08-01

Change modelos-de-documento (design.md D1, D6, D7, D8). Cria o enum
`tipo_modelo_documento` e a tabela `modelo_documento` (catálogo do
Administrador, D7); acresce `documento.modelo_id` (FK nullable, D6) — nulo
para anexos enviados por upload, preenchido para documentos gerados a partir
de um modelo (proveniência auditável). Nenhuma tabela de anexo antiga é
alterada além da nova coluna.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0027_modelo_documento"
down_revision = "0026_ix_tramitacao_servidores"
branch_labels = None
depends_on = None

_TIPO_MODELO_DOCUMENTO = postgresql.ENUM(
    "requerimento",
    "oficio",
    "memorando",
    "despacho",
    "parecer",
    "nota_tecnica",
    "relatorio",
    "ata",
    "contrato",
    "outro",
    name="tipo_modelo_documento",
)


def upgrade() -> None:
    _TIPO_MODELO_DOCUMENTO.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "modelo_documento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(200), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM(
                "requerimento",
                "oficio",
                "memorando",
                "despacho",
                "parecer",
                "nota_tecnica",
                "relatorio",
                "ata",
                "contrato",
                "outro",
                name="tipo_modelo_documento",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(500), nullable=True),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "criado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.add_column(
        "documento",
        sa.Column(
            "modelo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modelo_documento.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("documento", "modelo_id")
    op.drop_table("modelo_documento")
    _TIPO_MODELO_DOCUMENTO.drop(op.get_bind(), checkfirst=True)
