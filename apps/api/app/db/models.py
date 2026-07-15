"""Modelos SQLAlchemy 2.x de identidade e estrutura organizacional.

Espelha a migration `0002_identidade_estrutura_organizacional` (ver design.md
Migration Plan). Chaves primárias são UUID gerados no lado da aplicação
(`default=uuid.uuid4`), exceto `SistemaConfig` (singleton, id fixo=1).
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
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
    # Épico 2 (D1) — capacidade da numeração de processos AAAA/NNNNNN.
    EXPANSAO_NUMERO_PROCESSO = "expansao_numero_processo"
    ALERTA_CAPACIDADE = "alerta_capacidade"


class StatusProcesso(str, enum.Enum):
    """Máquina de estados do processo (D4). `ARQUIVADO` só é alcançado pela
    rotina automática de arquivamento (change arquivamento-automatico)."""

    ABERTO = "aberto"
    EM_TRAMITACAO = "em_tramitacao"
    CONCLUIDO = "concluido"
    ARQUIVADO = "arquivado"


class TipoEventoTramitacao(str, enum.Enum):
    """Eventos do histórico imutável (D4). A criação do processo NÃO é evento
    de tramitação — a autoria vive em `Processo.criado_por_id`/`criado_em`."""

    DESPACHO = "despacho"
    DEVOLUCAO = "devolucao"
    CONCLUSAO = "conclusao"
    # Change B1 (US 2.5) — evento de sistema, sem responsável humano (D3).
    ARQUIVAMENTO_AUTOMATICO = "arquivamento_automatico"
    # US 2.6 — sigilo é ortogonal ao status; não altera status_resultante.
    MARCAR_SIGILO = "marcar_sigilo"
    REMOVER_SIGILO = "remover_sigilo"
    # US 3.1 — remoção de anexo é ortogonal ao status; não altera status_resultante.
    REMOVER_DOCUMENTO = "remover_documento"


class TipoDocumentoInteressado(str, enum.Enum):
    CPF = "cpf"
    CNPJ = "cnpj"


class TipoParticipacaoInteressado(str, enum.Enum):
    REQUERENTE = "requerente"
    REPRESENTADO = "representado"
    TERCEIRO = "terceiro"


class MotivoDevolucao(str, enum.Enum):
    DOCUMENTACAO_INSUFICIENTE = "documentacao_insuficiente"
    CORRECAO_DADOS = "correcao_dados"
    DILIGENCIA_COMPLEMENTAR = "diligencia_complementar"


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
    # Fatia mínima da US 8.5 (change arquivamento-automatico) — demais
    # parâmetros operacionais ficam para a tela de configurações completa.
    prazo_arquivamento_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30)


def _enum_col(enum_cls, name):
    """Coluna enum nativa no padrão do projeto (values_callable + native_enum)."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda ec: [e.value for e in ec],
    )


class ProcessoContadorAno(Base):
    """Suporte à geração atômica do número por ano (D1). Uma linha por ano;
    `ultimo_sequencial` incrementado via upsert na mesma transação do processo."""

    __tablename__ = "processo_contador_ano"

    ano: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ultimo_sequencial: Mapped[int] = mapped_column(Integer, nullable=False)


class Processo(Base):
    __tablename__ = "processo"

    id: Mapped[uuid.UUID] = _uuid_pk()
    numero: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    assunto: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo_processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipo_processo.id"), nullable=False
    )
    # Snapshot do roteiro vigente na criação (D2) — FK permanente, sem cópia de etapas.
    roteiro_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roteiro.id"), nullable=False
    )
    status: Mapped[StatusProcesso] = mapped_column(
        _enum_col(StatusProcesso, "status_processo"),
        nullable=False,
        default=StatusProcesso.ABERTO,
    )
    unidade_atual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False
    )
    unidade_origem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False
    )
    # Ordinal (roteiro_etapa.ordem) da etapa atual do snapshot (D3).
    ordem_atual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    prazo_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    prazo_em: Mapped[date] = mapped_column(Date, nullable=False)
    criado_por_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Congelado na conclusão (US 2.5 Cen.2, D1) — NULL enquanto não concluído.
    arquivar_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # US 2.6 — atributo de visibilidade, ortogonal ao status (D1).
    sigiloso: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", default=False)

    interessados: Mapped[list["ProcessoInteressado"]] = relationship(
        "ProcessoInteressado", back_populates="processo"
    )


class ProcessoInteressado(Base):
    """Dados pessoais de terceiro (LGPD): só `nome` é obrigatório; CPF/CNPJ e
    tipo de participação são opcionais (proposal — tratamento LGPD)."""

    __tablename__ = "processo_interessado"

    id: Mapped[uuid.UUID] = _uuid_pk()
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processo.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(14), nullable=True)
    tipo_documento: Mapped[TipoDocumentoInteressado | None] = mapped_column(
        _enum_col(TipoDocumentoInteressado, "tipo_documento_interessado"), nullable=True
    )
    tipo_participacao: Mapped[TipoParticipacaoInteressado | None] = mapped_column(
        _enum_col(TipoParticipacaoInteressado, "tipo_participacao_interessado"), nullable=True
    )

    processo: Mapped[Processo] = relationship("Processo", back_populates="interessados")


class Tramitacao(Base):
    """Histórico imutável de movimentações (D4). INSERT-only — nenhuma rota ou
    método de update/delete de evento (invariante de histórico imutável)."""

    __tablename__ = "tramitacao"

    id: Mapped[uuid.UUID] = _uuid_pk()
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processo.id"), nullable=False
    )
    tipo_evento: Mapped[TipoEventoTramitacao] = mapped_column(
        _enum_col(TipoEventoTramitacao, "tipo_evento_tramitacao"), nullable=False
    )
    unidade_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=True
    )
    unidade_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=True
    )
    # Nullable apenas para o evento de sistema `arquivamento_automatico` — CHECK
    # `ck_tramitacao_responsavel` (migration 0004, D3) preserva a obrigatoriedade
    # para os demais eventos (despacho/devolução/conclusão).
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    status_resultante: Mapped[StatusProcesso] = mapped_column(
        _enum_col(StatusProcesso, "status_processo"), nullable=False
    )
    motivo: Mapped[MotivoDevolucao | None] = mapped_column(
        _enum_col(MotivoDevolucao, "motivo_devolucao"), nullable=True
    )
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Documento(Base):
    """Anexo de processo (Épico 3, fatia A). Soft-delete derivado: `removido_em
    IS NULL` = visível (D2) — nenhuma coluna de status textual. `objeto_chave`
    é a chave opaca do objeto no bucket, desacoplada de `nome_exibicao` (D3)."""

    __tablename__ = "documento"
    __table_args__ = (CheckConstraint("tamanho_bytes > 0", name="ck_documento_tamanho_positivo"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processo.id"), nullable=False
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String(255), nullable=False)
    objeto_chave: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    tipo_conteudo: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    anexado_por_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    anexado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    removido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removido_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    purgar_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
