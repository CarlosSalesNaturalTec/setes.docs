"""identidade e estrutura organizacional — usuario, unidade, tipo_processo/roteiro,
autenticação e sessão

Revision ID: 0002_identidade_estrutura
Revises: 0001_baseline
Create Date: 2026-07-13

Primeira migration de negócio do projeto (design.md — Migration Plan). Cria o
schema completo de identidade (usuario, sessão, tokens, histórico de senha,
log de segurança) e de estrutura organizacional (unidade, unidade_gestor,
tipo_processo, roteiro, roteiro_etapa), além do singleton `sistema_config`
que guarda a inicialização atômica do sistema (D7).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_identidade_estrutura"  # alembic_version.version_num é varchar(32)
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

# Enums (D-schema): definidos uma vez, reaproveitados nas colunas com create_type=False.
perfil_usuario = postgresql.ENUM(
    "servidor", "gestor", "administrador", name="perfil_usuario"
)
status_usuario = postgresql.ENUM(
    "pendente_primeiro_acesso", "ativo", "inativo", name="status_usuario"
)
tipo_token_autenticacao = postgresql.ENUM(
    "primeiro_acesso", "recuperacao_senha", name="tipo_token_autenticacao"
)
tipo_evento_log = postgresql.ENUM(
    "acesso_negado", "login_bloqueado", "reset_senha_admin", "login_falha",
    name="tipo_evento_log",
)


def upgrade() -> None:
    bind = op.get_bind()

    # 1.1 — enums + unidade (sem gestor_responsavel_id ainda, evita ciclo com usuario)
    perfil_usuario.create(bind, checkfirst=True)
    status_usuario.create(bind, checkfirst=True)
    tipo_token_autenticacao.create(bind, checkfirst=True)
    tipo_evento_log.create(bind, checkfirst=True)

    op.create_table(
        "unidade",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("sigla", sa.String(20), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )

    # 1.2 — usuario
    op.create_table(
        "usuario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "perfil",
            postgresql.ENUM(name="perfil_usuario", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="status_usuario", create_type=False),
            nullable=False,
            server_default="pendente_primeiro_acesso",
        ),
        sa.Column(
            "unidade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("unidade.id"),
            nullable=True,
        ),
        sa.Column("tentativas_login_falhas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bloqueado_ate", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_unique_constraint("uq_usuario_email", "usuario", ["email"])

    # 1.3 — ciclo unidade<->usuario resolvido via ALTER após usuario existir
    op.add_column(
        "unidade",
        sa.Column(
            "gestor_responsavel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=True,
        ),
    )

    # 1.4 — unidade_gestor (N:N Gestor <-> unidades geridas, US 8.6b)
    op.create_table(
        "unidade_gestor",
        sa.Column(
            "gestor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"),
            primary_key=True,
        ),
        sa.Column(
            "unidade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("unidade.id"),
            primary_key=True,
        ),
    )

    # 1.5 — tipo_processo, roteiro (versionado, D8), roteiro_etapa
    op.create_table(
        "tipo_processo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_tipo_processo_nome", "tipo_processo", ["nome"])

    op.create_table(
        "roteiro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tipo_processo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tipo_processo.id"),
            nullable=False,
        ),
        sa.Column("vigente", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    # No máximo um roteiro vigente por tipo_processo (D8).
    op.create_index(
        "uq_roteiro_vigente_por_tipo_processo",
        "roteiro",
        ["tipo_processo_id"],
        unique=True,
        postgresql_where=sa.text("vigente"),
    )

    op.create_table(
        "roteiro_etapa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "roteiro_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roteiro.id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("unidade.id"),
            nullable=False,
        ),
        sa.Column("ordem", sa.Integer, nullable=False),
    )
    op.create_unique_constraint(
        "uq_roteiro_etapa_ordem", "roteiro_etapa", ["roteiro_id", "ordem"]
    )

    # 1.6 — token_autenticacao, senha_historico
    op.create_table(
        "token_autenticacao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            postgresql.ENUM(name="tipo_token_autenticacao", create_type=False),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_unique_constraint(
        "uq_token_autenticacao_hash", "token_autenticacao", ["token_hash"]
    )

    op.create_table(
        "senha_historico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 1.7 — log_seguranca (append-only, D11)
    op.create_table(
        "log_seguranca",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"),
            nullable=True,
        ),
        sa.Column(
            "tipo_evento",
            postgresql.ENUM(name="tipo_evento_log", create_type=False),
            nullable=False,
        ),
        sa.Column("contexto", postgresql.JSONB, nullable=True),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 1.8 — sessao (D1)
    op.create_table(
        "sessao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuario.id"),
            nullable=False,
        ),
        sa.Column("jti", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "ultima_atividade",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revogada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )
    op.create_unique_constraint("uq_sessao_jti", "sessao", ["jti"])
    op.create_index("ix_sessao_usuario_id", "sessao", ["usuario_id"])

    # 1.9 — sistema_config (singleton, D7) + seed
    op.create_table(
        "sistema_config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("inicializado", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.execute("INSERT INTO sistema_config (id, inicializado) VALUES (1, false)")


def downgrade() -> None:
    op.drop_table("sistema_config")
    op.drop_index("ix_sessao_usuario_id", table_name="sessao")
    op.drop_table("sessao")
    op.drop_table("log_seguranca")
    op.drop_table("senha_historico")
    op.drop_table("token_autenticacao")
    op.drop_table("roteiro_etapa")
    op.drop_index("uq_roteiro_vigente_por_tipo_processo", table_name="roteiro")
    op.drop_table("roteiro")
    op.drop_table("tipo_processo")
    op.drop_table("unidade_gestor")
    op.drop_constraint("unidade_gestor_responsavel_id_fkey", "unidade", type_="foreignkey")
    op.drop_column("unidade", "gestor_responsavel_id")
    op.drop_table("usuario")
    op.drop_table("unidade")

    bind = op.get_bind()
    tipo_evento_log.drop(bind, checkfirst=True)
    tipo_token_autenticacao.drop(bind, checkfirst=True)
    status_usuario.drop(bind, checkfirst=True)
    perfil_usuario.drop(bind, checkfirst=True)
