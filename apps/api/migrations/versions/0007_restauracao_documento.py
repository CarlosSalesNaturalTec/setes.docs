"""restauração de documento — evento restaurar_documento no histórico imutável

Revision ID: 0007_restauracao_documento
Revises: 0006_gestao_documental
Create Date: 2026-07-16

Change `restauracao-documento` (US 8.7) — a operação inversa do soft-delete de
`0006`. Nenhuma tabela nova, nenhuma coluna nova: apenas acresce o valor
`restaurar_documento` ao enum `tipo_evento_tramitacao` (histórico imutável, D6),
para registrar a restauração de um anexo pelo Administrador.
"""

from __future__ import annotations

from alembic import op

revision = "0007_restauracao_documento"
down_revision = "0006_gestao_documental"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enum (Migration Plan passo 1). ALTER TYPE ... ADD VALUE não pode rodar
    # dentro de bloco transacional; mesmo padrão de 0004/0005/0006.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'restaurar_documento'")
    op.execute("COMMIT")


def downgrade() -> None:
    # Nota: o valor 'restaurar_documento' adicionado ao enum
    # `tipo_evento_tramitacao` não é removido — o Postgres não suporta DROP
    # VALUE em enum; downgrade o mantém (inócuo), mesmo padrão de 0004/0005/0006.
    pass
