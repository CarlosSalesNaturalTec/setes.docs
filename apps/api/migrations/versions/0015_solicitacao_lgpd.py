"""solicitacao_lgpd — canal público de solicitação e fila administrativa

Revision ID: 0015_solicitacao_lgpd
Revises: 0014_lgpd_enums
Create Date: 2026-07-17

Épico 10 (US 10.1/10.2, design.md Migration Plan passo 3). `protocolo` único
(`LGPD/AAAA/NNNNNN`, D5); `processo_id` referencia o processo indicado pelo
titular; `documento_identificacao_chave` aponta para o bucket dedicado (D6,
não o bucket de documentos de processo).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0015_solicitacao_lgpd"
down_revision = "0014_lgpd_enums"
branch_labels = None
depends_on = None

_TIPO_SOLICITACAO_LGPD = postgresql.ENUM(
    "exclusao", "anonimizacao", name="tipo_solicitacao_lgpd", create_type=False
)
_STATUS_SOLICITACAO_LGPD = postgresql.ENUM(
    "pendente", "em_analise", "atendida", "rejeitada",
    name="status_solicitacao_lgpd", create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "solicitacao_lgpd",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("protocolo", sa.String(30), nullable=False),
        sa.Column(
            "processo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processo.id"), nullable=False
        ),
        sa.Column("nome_solicitante", sa.String(200), nullable=False),
        sa.Column("cpf_solicitante", sa.String(11), nullable=False),
        sa.Column("email_solicitante", sa.String(320), nullable=False),
        sa.Column("tipo", _TIPO_SOLICITACAO_LGPD, nullable=False),
        sa.Column(
            "status", _STATUS_SOLICITACAO_LGPD, nullable=False, server_default="pendente"
        ),
        sa.Column("documento_identificacao_chave", sa.String(500), nullable=False),
        sa.Column("justificativa_rejeicao", sa.Text(), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("atendido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "atendido_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=True,
        ),
    )
    op.create_unique_constraint("uq_solicitacao_lgpd_protocolo", "solicitacao_lgpd", ["protocolo"])


def downgrade() -> None:
    op.drop_table("solicitacao_lgpd")
