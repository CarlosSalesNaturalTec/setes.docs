"""create notificacao — notificação interna (sino), fan-out por linha

Revision ID: 0008_create_notificacao
Revises: 0007_restauracao_documento
Create Date: 2026-07-16

Épico 5 (US 5.1, 5.3, 5.4, design.md — Migration Plan passo 1). Cria a
tabela `notificacao` (fan-out por linha, D2): uma linha por (destinatário,
evento), com snapshot mínimo de render e estado lido/não-lido por linha.
Índices: `(usuario_id, lida_em)` para contador/lista, `(processo_id,
usuario_id, tipo, prazo_referencia)` para o guard de idempotência do alerta
de prazo (D3), `(lida_em)` para o expurgo diário.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_create_notificacao"
down_revision = "0007_restauracao_documento"
branch_labels = None
depends_on = None

# Enum definido uma vez, reaproveitado na coluna com create_type=False (mesmo
# padrão de 0002_identidade_estrutura_organizacional).
tipo_notificacao = postgresql.ENUM(
    "novo_processo", "concluido", "alerta_prazo", name="tipo_notificacao"
)


def upgrade() -> None:
    tipo_notificacao.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notificacao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"), nullable=False
        ),
        sa.Column(
            "processo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("processo.id"), nullable=False
        ),
        sa.Column(
            "unidade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("unidade.id"), nullable=False
        ),
        sa.Column("unidade_nome", sa.String(200), nullable=False),
        sa.Column(
            "unidade_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=True,
        ),
        sa.Column("unidade_origem_nome", sa.String(200), nullable=True),
        sa.Column(
            "tipo", postgresql.ENUM(name="tipo_notificacao", create_type=False), nullable=False
        ),
        sa.Column("numero_processo", sa.String(20), nullable=False),
        sa.Column("assunto", sa.String(500), nullable=False),
        sa.Column("prazo_referencia", sa.Date(), nullable=True),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_index("ix_notificacao_usuario_lida_em", "notificacao", ["usuario_id", "lida_em"])
    op.create_index(
        "ix_notificacao_prazo_guard",
        "notificacao",
        ["processo_id", "usuario_id", "tipo", "prazo_referencia"],
    )
    op.create_index("ix_notificacao_lida_em", "notificacao", ["lida_em"])


def downgrade() -> None:
    op.drop_index("ix_notificacao_lida_em", table_name="notificacao")
    op.drop_index("ix_notificacao_prazo_guard", table_name="notificacao")
    op.drop_index("ix_notificacao_usuario_lida_em", table_name="notificacao")
    op.drop_table("notificacao")
    tipo_notificacao.drop(op.get_bind(), checkfirst=True)
