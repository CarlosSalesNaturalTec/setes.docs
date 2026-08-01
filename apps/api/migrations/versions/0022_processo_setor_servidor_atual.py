"""processo — setor_atual_id e servidor_atual_id (responsável corrente)

Revision ID: 0022_processo_setor_servidor_atual
Revises: 0021_usuario_setor_e_campos
Create Date: 2026-07-31

Change tramitacao-manual (design.md D1, D10). O processo passa a registrar
diretamente o setor e o servidor atualmente responsáveis, em vez de derivá-los
do roteiro. Backfill: `servidor_atual_id = criado_por_id` e `setor_atual_id` =
setor do criador — o processo nasce (e, para os já existentes, permanece)
atribuído a quem o criou. `SET NOT NULL` só depois do backfill.

Incidente no deploy de 2026-08-01: `usuario.setor_id` é nullable (migration
`0021`) — usuários anteriores ao change `setores-e-cadastro-usuario` nunca
tiveram setor atribuído, e o backfill original deixava `setor_atual_id` NULL
para os processos criados por eles, quebrando o `SET NOT NULL` com
`NotNullViolation` em produção. O backfill agora tem três níveis: (1) setor do
próprio criador; (2) qualquer setor já cadastrado na unidade atual do
processo, quando o criador não tinha setor; (3), último recurso, quando a
própria unidade não possui nenhum setor cadastrado, cria um setor placeholder
("Migração automática") nela — nunca perde a unidade correta, nunca falha a
migration. O placeholder é renomeável/consolidável depois pelo Administrador.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0022_processo_setor_servidor"  # alembic_version.version_num é varchar(32)
down_revision = "0021_usuario_setor_e_campos"
branch_labels = None
depends_on = None

_SETOR_PLACEHOLDER_NOME = "Migração automática"


def upgrade() -> None:
    op.add_column(
        "processo", sa.Column("setor_atual_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "processo", sa.Column("servidor_atual_id", postgresql.UUID(as_uuid=True), nullable=True)
    )

    op.execute("UPDATE processo SET servidor_atual_id = criado_por_id")

    # Nível 1: setor do próprio criador (caso comum).
    op.execute(
        """
        UPDATE processo
        SET setor_atual_id = usuario.setor_id
        FROM usuario
        WHERE usuario.id = processo.criado_por_id
          AND usuario.setor_id IS NOT NULL
        """
    )

    # Nível 2: criador sem setor vinculado — usa qualquer setor já existente
    # na unidade atual do processo, preservando a unidade correta.
    op.execute(
        """
        UPDATE processo
        SET setor_atual_id = (
            SELECT s.id FROM setor s
            WHERE s.unidade_id = processo.unidade_atual_id
            ORDER BY s.id
            LIMIT 1
        )
        WHERE processo.setor_atual_id IS NULL
        """
    )

    # Nível 3: a unidade atual não tem nenhum setor cadastrado — cria um
    # placeholder por unidade afetada (sigla derivada do id da unidade, única
    # por construção) e o usa. Só é alcançado nesse caso extremo.
    op.execute(
        f"""
        INSERT INTO setor (id, unidade_id, nome, sigla, ativo)
        SELECT gen_random_uuid(), p.unidade_atual_id, '{_SETOR_PLACEHOLDER_NOME}',
               'MIG' || substr(replace(p.unidade_atual_id::text, '-', ''), 1, 5), true
        FROM (
            SELECT DISTINCT unidade_atual_id FROM processo WHERE setor_atual_id IS NULL
        ) p
        """
    )
    op.execute(
        f"""
        UPDATE processo
        SET setor_atual_id = (
            SELECT s.id FROM setor s
            WHERE s.unidade_id = processo.unidade_atual_id AND s.nome = '{_SETOR_PLACEHOLDER_NOME}'
            LIMIT 1
        )
        WHERE processo.setor_atual_id IS NULL
        """
    )

    op.create_foreign_key(
        "fk_processo_setor_atual_id", "processo", "setor", ["setor_atual_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_processo_servidor_atual_id", "processo", "usuario", ["servidor_atual_id"], ["id"]
    )
    op.create_index("ix_processo_setor_atual_id", "processo", ["setor_atual_id"])
    op.create_index("ix_processo_servidor_atual_id", "processo", ["servidor_atual_id"])

    op.alter_column("processo", "servidor_atual_id", nullable=False)
    op.alter_column("processo", "setor_atual_id", nullable=False)


def downgrade() -> None:
    op.alter_column("processo", "setor_atual_id", nullable=True)
    op.alter_column("processo", "servidor_atual_id", nullable=True)
    op.drop_index("ix_processo_servidor_atual_id", table_name="processo")
    op.drop_index("ix_processo_setor_atual_id", table_name="processo")
    op.drop_constraint("fk_processo_servidor_atual_id", "processo", type_="foreignkey")
    op.drop_constraint("fk_processo_setor_atual_id", "processo", type_="foreignkey")
    op.drop_column("processo", "servidor_atual_id")
    op.drop_column("processo", "setor_atual_id")
