"""arquivamento automatico — arquivar_em, prazo configurável, evento de sistema

Revision ID: 0004_arquivamento_automat
Revises: 0003_processos_workflow
Create Date: 2026-07-15

Fecha a lacuna deixada por `processos-e-workflow`: dá pernas de banco à
transição `Concluído → Arquivado` (design.md — Migration Plan). Adiciona o
valor de enum do evento de arquivamento, o congelamento `processo.arquivar_em`
(D1), o parâmetro `sistema_config.prazo_arquivamento_dias` (D2) e torna
`tramitacao.responsavel_id` nullable com CHECK para o evento de sistema (D3).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_arquivamento_automat"  # alembic_version.version_num é varchar(32)
down_revision = "0003_processos_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1 — enum (Migration Plan passo 1). ALTER TYPE ... ADD VALUE não pode
    # rodar dentro de bloco transacional; o Alembic abre a migration numa
    # transação, então COMMIT antes (mesmo padrão de 0003).
    op.execute("COMMIT")
    op.execute(
        "ALTER TYPE tipo_evento_tramitacao ADD VALUE IF NOT EXISTS 'arquivamento_automatico'"
    )
    # O novo valor só pode ser *usado* (CHECK abaixo) numa transação posterior
    # à que o criou — commit isolado antes de referenciá-lo (risco documentado
    # em design.md).
    op.execute("COMMIT")

    # 2 — processo.arquivar_em + índice para a varredura do job (Migration Plan passo 2)
    op.add_column("processo", sa.Column("arquivar_em", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_processo_status_arquivar_em", "processo", ["status", "arquivar_em"]
    )

    # 3 — sistema_config.prazo_arquivamento_dias (Migration Plan passo 3); default
    # mantém a linha singleton id=1 já semeada válida, sem backfill.
    op.add_column(
        "sistema_config",
        sa.Column(
            "prazo_arquivamento_dias", sa.Integer(), nullable=False, server_default="30"
        ),
    )

    # 4 — tramitacao.responsavel_id nullable + CHECK (Migration Plan passo 4, D3)
    op.alter_column("tramitacao", "responsavel_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.create_check_constraint(
        "ck_tramitacao_responsavel",
        "tramitacao",
        "responsavel_id IS NOT NULL OR tipo_evento = 'arquivamento_automatico'",
    )


def downgrade() -> None:
    # Ordem reversa (Migration Plan passo 5). Exige que não haja linhas de
    # arquivamento_automatico antes de restaurar o NOT NULL de responsavel_id.
    op.drop_constraint("ck_tramitacao_responsavel", "tramitacao", type_="check")
    op.alter_column(
        "tramitacao", "responsavel_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False
    )

    op.drop_column("sistema_config", "prazo_arquivamento_dias")

    op.drop_index("ix_processo_status_arquivar_em", table_name="processo")
    op.drop_column("processo", "arquivar_em")

    # Nota: o valor 'arquivamento_automatico' adicionado ao enum
    # `tipo_evento_tramitacao` não é removido — o Postgres não suporta DROP
    # VALUE em enum; downgrade o mantém (inócuo), mesmo padrão de 0003.
