"""gestao documental — tabela documento, índices parciais, evento remover_documento

Revision ID: 0006_gestao_documental
Revises: 0005_sigilo_processo
Create Date: 2026-07-15

Épico 3, fatia A (design.md — Migration Plan). Cria a entidade `documento`
(anexos de processo, D2/D3) e acresce o valor `remover_documento` ao enum
`tipo_evento_tramitacao` (histórico imutável, D6). Estado de soft-delete é
derivado (`removido_em IS NULL` = visível) — sem coluna de status textual.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_gestao_documental"
down_revision = "0005_sigilo_processo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1 — enum (Migration Plan passo 3). ALTER TYPE ... ADD VALUE não pode
    # rodar dentro de bloco transacional; mesmo padrão de 0004/0005.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'remover_documento'")
    op.execute("COMMIT")

    # 2 — documento (Migration Plan passo 1)
    op.create_table(
        "documento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("processo.id"),
            nullable=False,
        ),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("nome_exibicao", sa.String(255), nullable=False),
        sa.Column("objeto_chave", sa.String(500), nullable=False),
        sa.Column("tipo_conteudo", sa.String(100), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger, nullable=False),
        sa.Column("hash_sha256", sa.CHAR(64), nullable=False),
        sa.Column(
            "anexado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column(
            "anexado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("removido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "removido_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=True,
        ),
        sa.Column("purgar_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_documento_objeto_chave", "documento", ["objeto_chave"])
    op.create_check_constraint(
        "ck_documento_tamanho_positivo", "documento", "tamanho_bytes > 0"
    )

    # 3 — índices parciais (Migration Plan passo 2)
    op.create_index(
        "ix_documento_processo_visivel",
        "documento",
        ["processo_id"],
        postgresql_where=sa.text("removido_em IS NULL"),
    )
    op.create_index(
        "ix_documento_purga",
        "documento",
        ["purgar_em"],
        postgresql_where=sa.text("removido_em IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_documento_purga", table_name="documento")
    op.drop_index("ix_documento_processo_visivel", table_name="documento")
    op.drop_table("documento")

    # Nota: o valor 'remover_documento' adicionado ao enum
    # `tipo_evento_tramitacao` não é removido — o Postgres não suporta DROP
    # VALUE em enum; downgrade o mantém (inócuo), mesmo padrão de 0004/0005.
