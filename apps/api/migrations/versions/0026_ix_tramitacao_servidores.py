"""índices em tramitacao.servidor_origem_id/servidor_destino_id — quadro pessoal

Revision ID: 0026_ix_tramitacao_servidores
Revises: 0025_notificacao_justificativa
Create Date: 2026-08-01

Change kanban-por-servidor (design.md D7). O escopo pessoal do quadro do
Servidor (D1) passa a filtrar processos pelo ramo `EXISTS (tramitacao WHERE
:eu IN (servidor_origem_id, servidor_destino_id))` a cada montagem — os
índices compostos, com `processo_id` como segunda coluna, tornam essa
subconsulta *covering*. Sem mudança de dado.

Nota: numeração sequencial da revisão anterior a este change previa
`0025_ix_tramitacao_servidores`, mas `0025` já foi ocupada por
`0025_notificacao_justificativa` (change tramitacao-manual) entre o design e
a implementação — esta migration assume `0026`, encadeada sobre o head atual.
"""

from __future__ import annotations

from alembic import op

revision = "0026_ix_tramitacao_servidores"
down_revision = "0025_notificacao_justificativa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_tramitacao_servidor_destino", "tramitacao", ["servidor_destino_id", "processo_id"]
    )
    op.create_index(
        "ix_tramitacao_servidor_origem", "tramitacao", ["servidor_origem_id", "processo_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_tramitacao_servidor_origem", table_name="tramitacao")
    op.drop_index("ix_tramitacao_servidor_destino", table_name="tramitacao")
