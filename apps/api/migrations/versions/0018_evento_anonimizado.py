"""log_seguranca — evento interessado_anonimizado no enum tipo_evento_log

Revision ID: 0018_evento_anonimizado
Revises: 0017_interessado_anonimizado_em
Create Date: 2026-07-17

Épico 10 (D1, design.md Migration Plan passo 6). Nenhuma tabela/coluna nova:
apenas acresce o valor `interessado_anonimizado` ao enum `tipo_evento_log`,
usado tanto pelo atendimento manual quanto pela rotina automática.
"""

from __future__ import annotations

from alembic import op

revision = "0018_evento_anonimizado"
down_revision = "0017_interessado_anonimizado_em"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE não pode rodar dentro de bloco transacional;
    # mesmo padrão de 0004/0005/0006/0007.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'interessado_anonimizado'")
    op.execute("COMMIT")


def downgrade() -> None:
    # Nota: o valor 'interessado_anonimizado' adicionado ao enum
    # `tipo_evento_log` não é removido — o Postgres não suporta DROP VALUE em
    # enum; downgrade o mantém (inócuo), mesmo padrão de 0004/0005/0006/0007.
    pass
