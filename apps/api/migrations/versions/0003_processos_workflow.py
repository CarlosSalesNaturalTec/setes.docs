"""processos e workflow — processo, processo_interessado, tramitacao, contador anual

Revision ID: 0003_processos_workflow
Revises: 0002_identidade_estrutura
Create Date: 2026-07-15

Núcleo transacional de processo e workflow roteirizado (design.md — Migration
Plan). Cria os enums de status/evento, o contador anual do número
`AAAA/NNNNNN` (D1), a entidade `processo` com snapshot de roteiro (D2) e
ordinal de posição (D3), os interessados (dado pessoal LGPD) e o histórico
imutável `tramitacao` (D4). Amplia `tipo_evento_log` com os eventos de
capacidade da numeração.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_processos_workflow"  # alembic_version.version_num é varchar(32)
down_revision = "0002_identidade_estrutura"
branch_labels = None
depends_on = None

# Enums novos (Migration Plan passo 1). `status_processo` é reaproveitado por
# `processo.status` e `tramitacao.status_resultante` — criado uma vez.
status_processo = postgresql.ENUM(
    "aberto", "em_tramitacao", "concluido", "arquivado", name="status_processo"
)
tipo_evento_tramitacao = postgresql.ENUM(
    "despacho", "devolucao", "conclusao", name="tipo_evento_tramitacao"
)
tipo_documento_interessado = postgresql.ENUM(
    "cpf", "cnpj", name="tipo_documento_interessado"
)
tipo_participacao_interessado = postgresql.ENUM(
    "requerente", "representado", "terceiro", name="tipo_participacao_interessado"
)
motivo_devolucao = postgresql.ENUM(
    "documentacao_insuficiente",
    "correcao_dados",
    "diligencia_complementar",
    name="motivo_devolucao",
)


def upgrade() -> None:
    bind = op.get_bind()

    # 1 — enums novos + novos valores em tipo_evento_log (D1)
    status_processo.create(bind, checkfirst=True)
    tipo_evento_tramitacao.create(bind, checkfirst=True)
    tipo_documento_interessado.create(bind, checkfirst=True)
    tipo_participacao_interessado.create(bind, checkfirst=True)
    motivo_devolucao.create(bind, checkfirst=True)
    # ALTER TYPE ... ADD VALUE não pode rodar dentro de bloco transacional; o
    # Alembic abre a migration numa transação, então COMMIT antes.
    op.execute("COMMIT")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'expansao_numero_processo'")
    op.execute("ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'alerta_capacidade'")

    # 2 — contador anual do número (D1)
    op.create_table(
        "processo_contador_ano",
        sa.Column("ano", sa.Integer, primary_key=True, autoincrement=False),
        sa.Column("ultimo_sequencial", sa.Integer, nullable=False),
    )

    # 3 — processo (6 FKs + unique em numero)
    op.create_table(
        "processo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("assunto", sa.String(500), nullable=False),
        sa.Column(
            "tipo_processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tipo_processo.id"),
            nullable=False,
        ),
        sa.Column(
            "roteiro_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roteiro.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_processo", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "unidade_atual_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=False,
        ),
        sa.Column("ordem_atual", sa.Integer, nullable=False),
        sa.Column("prazo_dias", sa.Integer, nullable=False),
        sa.Column("prazo_em", sa.Date, nullable=False),
        sa.Column(
            "criado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_processo_numero", "processo", ["numero"])

    # 4 — processo_interessado (dado pessoal LGPD; só nome obrigatório)
    op.create_table(
        "processo_interessado",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("processo.id"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("documento", sa.String(14), nullable=True),
        sa.Column(
            "tipo_documento",
            postgresql.ENUM(name="tipo_documento_interessado", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "tipo_participacao",
            postgresql.ENUM(name="tipo_participacao_interessado", create_type=False),
            nullable=True,
        ),
    )

    # 5 — tramitacao (histórico imutável, append-only)
    op.create_table(
        "tramitacao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("processo.id"),
            nullable=False,
        ),
        sa.Column(
            "tipo_evento",
            postgresql.ENUM(name="tipo_evento_tramitacao", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "unidade_origem_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=True,
        ),
        sa.Column(
            "unidade_destino_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=True,
        ),
        sa.Column(
            "responsavel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column(
            "status_resultante",
            postgresql.ENUM(name="status_processo", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "motivo",
            postgresql.ENUM(name="motivo_devolucao", create_type=False),
            nullable=True,
        ),
        sa.Column("justificativa", sa.Text, nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 6 — índices (Migration Plan)
    op.create_index("ix_processo_unidade_atual_status", "processo", ["unidade_atual_id", "status"])
    op.create_index("ix_processo_tipo_processo_id", "processo", ["tipo_processo_id"])
    op.create_index("ix_processo_criado_por_id", "processo", ["criado_por_id"])
    op.create_index("ix_tramitacao_processo_criado_em", "tramitacao", ["processo_id", "criado_em"])
    op.create_index("ix_tramitacao_responsavel_id", "tramitacao", ["responsavel_id"])
    op.create_index("ix_processo_interessado_processo_id", "processo_interessado", ["processo_id"])


def downgrade() -> None:
    # Ordem reversa: índices → tramitacao → processo_interessado → processo →
    # processo_contador_ano → enums.
    op.drop_index("ix_processo_interessado_processo_id", table_name="processo_interessado")
    op.drop_index("ix_tramitacao_responsavel_id", table_name="tramitacao")
    op.drop_index("ix_tramitacao_processo_criado_em", table_name="tramitacao")
    op.drop_index("ix_processo_criado_por_id", table_name="processo")
    op.drop_index("ix_processo_tipo_processo_id", table_name="processo")
    op.drop_index("ix_processo_unidade_atual_status", table_name="processo")

    op.drop_table("tramitacao")
    op.drop_table("processo_interessado")
    op.drop_constraint("uq_processo_numero", "processo", type_="unique")
    op.drop_table("processo")
    op.drop_table("processo_contador_ano")

    bind = op.get_bind()
    motivo_devolucao.drop(bind, checkfirst=True)
    tipo_participacao_interessado.drop(bind, checkfirst=True)
    tipo_documento_interessado.drop(bind, checkfirst=True)
    tipo_evento_tramitacao.drop(bind, checkfirst=True)
    status_processo.drop(bind, checkfirst=True)
    # Nota: valores adicionados a `tipo_evento_log` não são removidos — o
    # Postgres não suporta DROP VALUE em enum; downgrade os mantém (inócuos).
