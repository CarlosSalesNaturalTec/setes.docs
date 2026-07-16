"""permissao auditoria e desativacao de usuario — usuario.pode_auditar, eventos de log

Revision ID: 0011_permissao_auditoria
Revises: 0010_dias_para_processo_parado
Create Date: 2026-07-16

Épico 8 (US 8.3/8.4, design.md Migration Plan). Adiciona
`usuario.pode_auditar` (flag ortogonal ao perfil, D1) e os três novos valores
de `tipo_evento_log` usados pela concessão/revogação de auditoria e pela
desativação de usuário (D3).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_permissao_auditoria"
down_revision = "0010_dias_para_processo_parado"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("pode_auditar", sa.Boolean(), nullable=False, server_default="false"),
    )

    # ALTER TYPE ... ADD VALUE não pode rodar dentro de bloco transacional —
    # mesmo padrão de 0004/0003 (COMMIT antes de cada ADD VALUE).
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'permissao_auditoria_concedida'")
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'permissao_auditoria_revogada'")
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'usuario_desativado'")
    op.execute("COMMIT")


def downgrade() -> None:
    op.drop_column("usuario", "pode_auditar")

    # Nota: os valores adicionados a `tipo_evento_log` não são removidos — o
    # Postgres não suporta DROP VALUE em enum; downgrade os mantém (inócuo),
    # mesmo padrão de 0004/0003.
