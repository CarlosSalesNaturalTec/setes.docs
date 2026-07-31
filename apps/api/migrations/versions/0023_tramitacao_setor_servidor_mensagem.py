"""tramitacao — setor/servidor de origem e destino, mensagem; enums de ação e notificação

Revision ID: 0023_tramitacao_setor_servidor_mensagem
Revises: 0022_processo_setor_servidor_atual
Create Date: 2026-07-31

Change tramitacao-manual (design.md D7, D8, D10). Quatro FKs nullable (todas as
quatro) e `mensagem` text em `tramitacao` — nullable porque eventos ortogonais
ao status (sigilo, documento) não as preenchem, no mesmo padrão de
`unidade_origem_id`/`unidade_destino_id`. `ALTER TYPE ... RENAME VALUE` troca
`despacho` por `envio` (vocabulário da tela, D7); `ADD VALUE 'reatribuicao'`
para o novo tipo de evento. Dois valores novos em `tipo_notificacao` para o
fluxo de reatribuição (D8). `ADD VALUE`/`RENAME VALUE` não roda dentro de
bloco transacional — `COMMIT` explícito antes, no padrão de `0014_lgpd_enums`
e `0004_arquivamento_automatico`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0023_tramitacao_setor_servidor"  # alembic_version.version_num é varchar(32)
down_revision = "0022_processo_setor_servidor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tramitacao", sa.Column("setor_origem_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "tramitacao", sa.Column("setor_destino_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "tramitacao",
        sa.Column("servidor_origem_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "tramitacao",
        sa.Column("servidor_destino_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("tramitacao", sa.Column("mensagem", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_tramitacao_setor_origem_id", "tramitacao", "setor", ["setor_origem_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_tramitacao_setor_destino_id", "tramitacao", "setor", ["setor_destino_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_tramitacao_servidor_origem_id",
        "tramitacao",
        "usuario",
        ["servidor_origem_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_tramitacao_servidor_destino_id",
        "tramitacao",
        "usuario",
        ["servidor_destino_id"],
        ["id"],
    )

    # ALTER TYPE ... RENAME/ADD VALUE não roda dentro de transação — COMMIT
    # explícito antes (padrão de 0004/0014). O valor 'reatribuicao' adicionado
    # não pode ser removido no downgrade (Postgres não suporta DROP VALUE).
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_tramitacao RENAME VALUE 'despacho' TO 'envio'")
    op.execute("ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'reatribuicao'")
    op.execute("ALTER TYPE tipo_notificacao ADD VALUE IF NOT EXISTS 'reatribuido_para_voce'")
    op.execute("ALTER TYPE tipo_notificacao ADD VALUE IF NOT EXISTS 'destino_corrigido'")
    op.execute("COMMIT")


def downgrade() -> None:
    # Os valores adicionados em tipo_notificacao ficam órfãos (sem DROP VALUE
    # em Postgres) — inócuo, mesmo padrão de 0004/0014.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_tramitacao RENAME VALUE 'envio' TO 'despacho'")
    op.execute("COMMIT")

    op.drop_constraint("fk_tramitacao_servidor_destino_id", "tramitacao", type_="foreignkey")
    op.drop_constraint("fk_tramitacao_servidor_origem_id", "tramitacao", type_="foreignkey")
    op.drop_constraint("fk_tramitacao_setor_destino_id", "tramitacao", type_="foreignkey")
    op.drop_constraint("fk_tramitacao_setor_origem_id", "tramitacao", type_="foreignkey")

    op.drop_column("tramitacao", "mensagem")
    op.drop_column("tramitacao", "servidor_destino_id")
    op.drop_column("tramitacao", "servidor_origem_id")
    op.drop_column("tramitacao", "setor_destino_id")
    op.drop_column("tramitacao", "setor_origem_id")
