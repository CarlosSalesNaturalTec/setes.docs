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
    Index,
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
    # US 8.3/8.4 (D3, administracao-usuario-auditoria) — permissão de auditoria e desativação.
    PERMISSAO_AUDITORIA_CONCEDIDA = "permissao_auditoria_concedida"
    PERMISSAO_AUDITORIA_REVOGADA = "permissao_auditoria_revogada"
    USUARIO_DESATIVADO = "usuario_desativado"
    # Épico 9 (US 9.1, D3, auditoria-e-relatorios) — acesso de auditoria destravado fora da unidade.
    ACESSO_AUDITORIA = "acesso_auditoria"
    # Épico 10 (D1, conformidade-lgpd) — anonimização irreversível de interessado
    # (atendimento manual ou rotina automática trimestral).
    INTERESSADO_ANONIMIZADO = "interessado_anonimizado"


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

    # Change tramitacao-manual (design.md D7) — `despacho` renomeado para
    # `envio` (vocabulário da tela); `reatribuicao` é o terceiro tipo de ação.
    ENVIO = "envio"
    REATRIBUICAO = "reatribuicao"
    DEVOLUCAO = "devolucao"
    CONCLUSAO = "conclusao"
    # Change B1 (US 2.5) — evento de sistema, sem responsável humano (D3).
    ARQUIVAMENTO_AUTOMATICO = "arquivamento_automatico"
    # US 2.6 — sigilo é ortogonal ao status; não altera status_resultante.
    MARCAR_SIGILO = "marcar_sigilo"
    REMOVER_SIGILO = "remover_sigilo"
    # US 3.1 — remoção de anexo é ortogonal ao status; não altera status_resultante.
    REMOVER_DOCUMENTO = "remover_documento"
    # US 8.7 — restauração de anexo (inversa do soft-delete); também ortogonal ao status.
    RESTAURAR_DOCUMENTO = "restaurar_documento"


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


class TipoNotificacao(str, enum.Enum):
    """Épico 5 (US 5.1, 5.3, 5.4) — tipo da notificação interna (sino)."""

    NOVO_PROCESSO = "novo_processo"
    CONCLUIDO = "concluido"
    ALERTA_PRAZO = "alerta_prazo"
    # Change tramitacao-manual (design.md D8) — fluxo de reatribuição.
    REATRIBUIDO_PARA_VOCE = "reatribuido_para_voce"
    DESTINO_CORRIGIDO = "destino_corrigido"


class TipoSolicitacaoLgpd(str, enum.Enum):
    """Épico 10 (US 10.1) — tipo da solicitação registrada no canal público."""

    EXCLUSAO = "exclusao"
    ANONIMIZACAO = "anonimizacao"


class StatusSolicitacaoLgpd(str, enum.Enum):
    """Épico 10 (US 10.2, D8) — máquina de estados: pendente/em_analise só
    transicionam para os estados terminais atendida/rejeitada, sem retorno."""

    PENDENTE = "pendente"
    EM_ANALISE = "em_analise"
    ATENDIDA = "atendida"
    REJEITADA = "rejeitada"


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
    setores: Mapped[list["Setor"]] = relationship(
        "Setor", back_populates="unidade", order_by="Setor.nome"
    )


class Setor(Base):
    """Segundo nível da estrutura organizacional (D1) — 1:N com `Unidade`.

    Sigla única *dentro* da unidade: duas unidades podem ter um "GAB". Nunca é
    excluído, apenas desativado (`ativo`), porque o histórico imutável de
    tramitação passa a referenciá-lo (D3). Setor **não** é fronteira de
    permissão — o escopo de acesso continua sendo a Unidade.
    """

    __tablename__ = "setor"
    __table_args__ = (
        UniqueConstraint("unidade_id", "sigla", name="uq_setor_unidade_sigla"),
        Index("ix_setor_unidade_id", "unidade_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    unidade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    sigla: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )

    unidade: Mapped[Unidade] = relationship("Unidade", back_populates="setores")


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
    # Nullable no schema, obrigatório apenas para o perfil Servidor (D2) — a
    # regra depende de `perfil`, então é validada na aplicação, não por CHECK.
    # Invariante adicional: `setor.unidade_id == usuario.unidade_id`.
    setor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("setor.id"), nullable=True
    )
    # Dados pessoais de servidor (identificação funcional): fora da consulta
    # pública. `chefia_direta` é texto livre, sem FK — a chefia pode ser pessoa
    # externa ao sistema (D4).
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    chefia_direta: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tentativas_login_falhas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # US 8.3 (D1, administracao-usuario-auditoria) — permissão de auditoria,
    # ortogonal ao `perfil`; concedida/revogada pelo Administrador.
    pode_auditar: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    unidade: Mapped[Unidade | None] = relationship(
        "Unidade", back_populates="usuarios", foreign_keys=[unidade_id]
    )
    setor: Mapped[Setor | None] = relationship("Setor", foreign_keys=[setor_id])


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
    # US 10.3 Cen.2 (Épico 10) — prazo legal de anonimização LGPD, em anos,
    # usado pela rotina automática trimestral; não retroativo (D-config runtime).
    prazo_anonimizacao_anos: Mapped[int] = mapped_column(Integer, nullable=False, default=5)


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
    # Épico 5 (US 8.5, US 5.4) — janela de antecedência do alerta de prazo,
    # lida em runtime pela rotina diária de verificação de prazos (D4).
    dias_antecedencia_alerta_prazo: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    # Épico 6 (US 8.5, US 6.1) — limiar do KPI "Processos parados", lido em
    # runtime pelo service de agregação do dashboard (D1, design.md dashboard-kpis-gestor).
    dias_para_processo_parado: Mapped[int] = mapped_column(Integer, nullable=False, default=7)


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
    # Responsável corrente (D1, change tramitacao-manual) — nasce igual ao
    # criador; atualizado a cada Envio/Devolução/Reatribuição. Nunca NULL: o
    # processo sempre tem exatamente um responsável.
    setor_atual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("setor.id"), nullable=False
    )
    servidor_atual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
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
    # Somente leitura, para enriquecer o card do Kanban/busca (D1, change
    # ajustar-visualizacao-processos) — carregadas com eager loading em
    # `processo_consulta` para evitar N+1.
    tipo_processo: Mapped["TipoProcesso"] = relationship(
        "TipoProcesso", foreign_keys=[tipo_processo_id]
    )
    unidade_atual: Mapped["Unidade"] = relationship("Unidade", foreign_keys=[unidade_atual_id])
    # Nome do detentor atual no card (change kanban-por-servidor, design D2/D5)
    # — eager loading em `processo_consulta` para evitar N+1.
    servidor_atual: Mapped["Usuario"] = relationship("Usuario", foreign_keys=[servidor_atual_id])


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
    # Épico 10 (D2) — guard explícito de idempotência da anonimização: NULL =
    # dado pessoal original; preenchida = nome/documento já sobrescritos com
    # os marcadores irreversíveis.
    anonimizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    # Setor/servidor de origem e destino (D1, D6, change tramitacao-manual) —
    # nullable pelo mesmo motivo de unidade_origem/destino: eventos ortogonais
    # ao status (sigilo, documento) não os preenchem. Distintos de
    # `responsavel_id`: aqui é quem **deteve** o processo, não quem agiu (D6).
    setor_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("setor.id"), nullable=True
    )
    setor_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("setor.id"), nullable=True
    )
    servidor_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    servidor_destino_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )
    # Nullable apenas para o evento de sistema `arquivamento_automatico` — CHECK
    # `ck_tramitacao_responsavel` (migration 0004, D3) preserva a obrigatoriedade
    # para os demais eventos (envio/devolução/reatribuição/conclusão).
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
    # Mensagem livre do Envio (change tramitacao-manual) — Devolução e
    # Reatribuição usam `motivo`/`justificativa` acima, não este campo.
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    # Só leitura — a área administrativa "Documentos Removidos" (US 8.7) exibe
    # número/assunto do processo de origem na listagem cross-processo.
    processo: Mapped[Processo] = relationship("Processo")


class Notificacao(Base):
    """Notificação interna (sino), Épico 5 — US 5.1, 5.3, 5.4.

    Fan-out por linha (D2, design.md): uma linha por (destinatário, evento).
    Snapshot mínimo de render (`numero_processo`/`assunto`/`unidade_nome`) — o
    histórico não muda se o processo (ou o nome da unidade) mudar depois.
    `unidade_origem_id`/`unidade_origem_nome` só são preenchidos para
    `novo_processo`; `prazo_referencia` só para `alerta_prazo` (base do guard
    de idempotência D3 da rotina diária).
    """

    __tablename__ = "notificacao"

    id: Mapped[uuid.UUID] = _uuid_pk()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=False
    )
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processo.id"), nullable=False
    )
    # Unidade de contexto do evento (destino no despacho, unidade de
    # conclusão, ou unidade atual no alerta de prazo) — coincide com a
    # unidade do destinatário no momento da geração.
    unidade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=False
    )
    unidade_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    unidade_origem_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("unidade.id"), nullable=True
    )
    unidade_origem_nome: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo: Mapped[TipoNotificacao] = mapped_column(
        _enum_col(TipoNotificacao, "tipo_notificacao"), nullable=False
    )
    numero_processo: Mapped[str] = mapped_column(String(20), nullable=False)
    assunto: Mapped[str] = mapped_column(String(500), nullable=False)
    # Change tramitacao-manual (D8) — justificativa da reatribuição, para
    # REATRIBUIDO_PARA_VOCE; texto descritivo do novo destino, para
    # DESTINO_CORRIGIDO. NULL para os demais tipos de notificação.
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    prazo_referencia: Mapped[date | None] = mapped_column(Date, nullable=True)
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_notificacao_usuario_lida_em", "usuario_id", "lida_em"),
        Index(
            "ix_notificacao_prazo_guard",
            "processo_id",
            "usuario_id",
            "tipo",
            "prazo_referencia",
        ),
        Index("ix_notificacao_lida_em", "lida_em"),
    )


class SolicitacaoLgpdContadorAno(Base):
    """Suporte à geração atômica do protocolo LGPD por ano (D5) — mesmo padrão
    de `ProcessoContadorAno`, sequência independente."""

    __tablename__ = "solicitacao_lgpd_contador_ano"

    ano: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    ultimo_sequencial: Mapped[int] = mapped_column(Integer, nullable=False)


class SolicitacaoLgpd(Base):
    """Canal público de solicitação LGPD (US 10.1) e fila administrativa de
    atendimento/rejeição (US 10.2). Dado pessoal do solicitante (nome/CPF/
    e-mail) coletado só para validar a titularidade do pedido (proposal —
    tratamento LGPD)."""

    __tablename__ = "solicitacao_lgpd"

    id: Mapped[uuid.UUID] = _uuid_pk()
    protocolo: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processo.id"), nullable=False
    )
    nome_solicitante: Mapped[str] = mapped_column(String(200), nullable=False)
    cpf_solicitante: Mapped[str] = mapped_column(String(11), nullable=False)
    email_solicitante: Mapped[str] = mapped_column(String(320), nullable=False)
    tipo: Mapped[TipoSolicitacaoLgpd] = mapped_column(
        _enum_col(TipoSolicitacaoLgpd, "tipo_solicitacao_lgpd"), nullable=False
    )
    status: Mapped[StatusSolicitacaoLgpd] = mapped_column(
        _enum_col(StatusSolicitacaoLgpd, "status_solicitacao_lgpd"),
        nullable=False,
        default=StatusSolicitacaoLgpd.PENDENTE,
    )
    documento_identificacao_chave: Mapped[str] = mapped_column(String(500), nullable=False)
    justificativa_rejeicao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    atendido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    atendido_por_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True
    )

    processo: Mapped[Processo] = relationship("Processo")
