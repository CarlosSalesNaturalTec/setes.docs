"""tipo_solicitacao_lgpd e status_solicitacao_lgpd — enums da solicitação LGPD

Revision ID: 0014_lgpd_enums
Revises: 0013_lgpd_contador_ano
Create Date: 2026-07-17

Épico 10 (US 10.1/10.2, design.md Migration Plan passo 2).
"""

from __future__ import annotations

from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_lgpd_enums"
down_revision = "0013_lgpd_contador_ano"
branch_labels = None
depends_on = None

_TIPO_SOLICITACAO_LGPD = postgresql.ENUM(
    "exclusao", "anonimizacao", name="tipo_solicitacao_lgpd"
)
_STATUS_SOLICITACAO_LGPD = postgresql.ENUM(
    "pendente", "em_analise", "atendida", "rejeitada", name="status_solicitacao_lgpd"
)


def upgrade() -> None:
    _TIPO_SOLICITACAO_LGPD.create(op.get_bind(), checkfirst=True)
    _STATUS_SOLICITACAO_LGPD.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    _STATUS_SOLICITACAO_LGPD.drop(op.get_bind(), checkfirst=True)
    _TIPO_SOLICITACAO_LGPD.drop(op.get_bind(), checkfirst=True)
