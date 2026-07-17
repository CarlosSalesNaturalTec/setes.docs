"""acesso auditoria — novo valor de tipo_evento_log para acesso destravado por auditoria

Revision ID: 0012_acesso_auditoria
Revises: 0011_permissao_auditoria
Create Date: 2026-07-16

Épico 9 (US 9.1, design.md Migrations Alembic). Adiciona o valor
`acesso_auditoria` ao enum `tipo_evento_log`, usado para registrar o acesso
de leitura que só a permissão de auditoria viabiliza (D3). Não altera
estrutura de tabela nem coluna.
"""

from __future__ import annotations

from alembic import op

revision = "0012_acesso_auditoria"
down_revision = "0011_permissao_auditoria"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE não pode rodar dentro de bloco transacional —
    # mesmo padrão de 0011/0004/0003 (COMMIT antes do ADD VALUE).
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'acesso_auditoria'")
    op.execute("COMMIT")


def downgrade() -> None:
    # Nota: o Postgres não suporta DROP VALUE em enum; downgrade mantém o
    # valor (aditivo e inócuo), mesmo padrão de 0011/0004/0003.
    pass
