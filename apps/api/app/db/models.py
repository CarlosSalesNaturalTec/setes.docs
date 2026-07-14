"""Modelos SQLAlchemy 2.x de identidade e estrutura organizacional.

Espelha a migration `0002_identidade_estrutura_organizacional` (ver design.md
Migration Plan). Chaves primárias são UUID gerados no lado da aplicação
(`default=uuid.uuid4`), exceto `SistemaConfig` (singleton, id fixo=1).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PerfilUsuario(str, enum.Enum):
    SERVIDOR = "servidor"
    GESTOR = "gestor"
    ADMINISTRADOR = "administrador"


class StatusUsuario(str, enum.Enum):
    PENDENTE_PRIMEIRO_ACESSO = "pendente_primeiro_acesso"
    ATIVO = "ativo"
    INATIVO = "inativo"


class TipoTokenAutenticacao(str, enum.Enum):
    PRIMEIRO_ACESSO = "primeiro_acesso"
    RECUPERACAO_SENHA = "recuperacao_senha"


class TipoEventoLog(str, enum.Enum):
    ACESSO_NEGADO = "acesso_negado"
    LOGIN_BLOQUEADO = "login_bloqueado"
    RESET_SENHA_ADMIN = "reset_senha_admin"
    LOGIN_FALHA = "login_falha"


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Unidade(Base):
    __tablename__ = "unidade"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    sigla: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    gestor_responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )

    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="unidade", foreign_keys="Usuario.unidade_id"
    )


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(
        SAEnum(
            PerfilUsuario,
            name="perfil_usuario",
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ), nullable=False
    )
    status: Mapped[StatusUsuario] = mapped_column(
        SAEnum(
            StatusUsuario,
            name="status_usuario",
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=StatusUsuario.PENDENTE_PRIMEIRO_ACESSO,
    )
    unidade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=True
    )
    tentativas_login_falhas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    unidade: Mapped[Unidade | None] = relationship(
        "Unidade", back_populates="usuarios", foreign_keys=[unidade_id]
    )


class UnidadeGestor(Base):
    __tablename__ = "unidade_gestor"

    gestor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), primary_key=True
    )
    unidade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), primary_key=True
    )


class TipoProcesso(Base):
    __tablename__ = "tipo_processo"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nome: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Roteiro(Base):
    __tablename__ = "roteiro"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tipo_processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipo_processo.id"), nullable=False
    )
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    etapas: Mapped[list["RoteiroEtapa"]] = relationship(
        "RoteiroEtapa", back_populates="roteiro", order_by="RoteiroEtapa.ordem"
    )


class RoteiroEtapa(Base):
    __tablename__ = "roteiro_etapa"
    __table_args__ = (UniqueConstraint("roteiro_id", "ordem", name="uq_roteiro_etapa_ordem"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    roteiro_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roteiro.id"), nullable=False
    )
    unidade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    roteiro: Mapped[Roteiro] = relationship("Roteiro", back_populates="etapas")


class TokenAutenticacao(Base):
    __tablename__ = "token_autenticacao"

    id: Mapped[uuid.UUID] = _uuid_pk()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    tipo: Mapped[TipoTokenAutenticacao] = mapped_column(
        SAEnum(
            TipoTokenAutenticacao,
            name="tipo_token_autenticacao",
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SenhaHistorico(Base):
    __tablename__ = "senha_historico"

    id: Mapped[uuid.UUID] = _uuid_pk()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LogSeguranca(Base):
    __tablename__ = "log_seguranca"

    id: Mapped[uuid.UUID] = _uuid_pk()
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    tipo_evento: Mapped[TipoEventoLog] = mapped_column(
        SAEnum(
            TipoEventoLog,
            name="tipo_evento_log",
            native_enum=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    contexto: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Sessao(Base):
    __tablename__ = "sessao"

    id: Mapped[uuid.UUID] = _uuid_pk()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    jti: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ultima_atividade: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SistemaConfig(Base):
    __tablename__ = "sistema_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inicializado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
