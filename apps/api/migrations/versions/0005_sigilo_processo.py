"""sigilo de processo — atributo booleano + eventos de histórico (US 2.6)

Revision ID: 0005_sigilo_processo
Revises: 0004_arquivamento_automat
Create Date: 2026-07-15

Fecha a última história pendente do Épico 2 (design.md — Migration Plan).
Adiciona os valores de enum dos eventos de sigilo e a coluna
`processo.sigiloso` (D1). Sigilo é ortogonal ao status — nenhuma alteração
na máquina de estados nem em `tramitacao`.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_sigilo_processo"
down_revision = "0004_arquivamento_automat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1 — enum (Migration Plan passo 1). Mesmo padrão de 0004: COMMIT antes e
    # depois do ADD VALUE, já que ele não pode rodar dentro da transação da
    # migration nem ser usado na mesma transação que o criou.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'marcar_sigilo'")
    op.execute("ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'remover_sigilo'")
    op.execute("COMMIT")

    # 2 — processo.sigiloso (Migration Plan passo 2); default mantém as linhas
    # existentes válidas (não-sigilosas), sem backfill.
    op.add_column(
        "processo",
        sa.Column("sigiloso", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("processo", "sigiloso")

    # Nota: os valores 'marcar_sigilo'/'remover_sigilo' adicionados ao enum
    # `tipo_evento_tramitacao` não são removidos — o Postgres não suporta DROP
    # VALUE em enum; downgrade os mantém (inócuo), mesmo padrão de 0004.
