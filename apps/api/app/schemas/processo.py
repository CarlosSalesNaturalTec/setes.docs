"""Schemas de processo e workflow (Épico 2).

A validação de CPF/CNPJ, destino e número acontecem no serviço
(`app/services/processo.py`), onde as mensagens exatas do PRD (US 2.1 Cen.3/3b/3c)
são emitidas como HTTPException. Aqui ficam a forma dos payloads e a serialização.

Change tramitacao-manual: `DespacharRequest` foi substituído por `EnviarRequest`,
`ReatribuirRequest` e `ConcluirRequest` — três ações distintas em vez de um
único despacho roteirizado (design.md D2).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class InteressadoInput(BaseModel):
    nome: str = Field(min_length=1)
    documento: str | None = None
    tipo_documento: Literal["cpf", "cnpj"] | None = None
    tipo_participacao: Literal["requerente", "representado", "terceiro"] | None = None


class InteressadoResponse(BaseModel):
    id: str
    nome: str
    documento: str | None
    tipo_documento: str | None
    tipo_participacao: str | None

    @classmethod
    def de(cls, interessado) -> "InteressadoResponse":
        return cls(
            id=str(interessado.id),
            nome=interessado.nome,
            documento=interessado.documento,
            tipo_documento=(
                interessado.tipo_documento.value if interessado.tipo_documento else None
            ),
            tipo_participacao=(
                interessado.tipo_participacao.value if interessado.tipo_participacao else None
            ),
        )


class CriarProcessoRequest(BaseModel):
    assunto: str = Field(min_length=1)
    tipo_processo_id: str
    prazo_dias: int = Field(gt=0)
    interessados: list[InteressadoInput] = Field(default_factory=list)


class ProcessoResponse(BaseModel):
    """Saída completa de um processo (criação e detalhe)."""

    id: str
    numero: str
    assunto: str
    status: str
    tipo_processo_id: str
    unidade_atual_id: str
    unidade_origem_id: str
    # Responsável corrente (D1, change tramitacao-manual).
    setor_atual_id: str
    servidor_atual_id: str
    prazo_dias: int
    prazo_em: date
    criado_por_id: str
    criado_em: datetime
    concluido_em: datetime | None
    sigiloso: bool
    interessados: list[InteressadoResponse] = Field(default_factory=list)

    @classmethod
    def de(cls, processo) -> "ProcessoResponse":
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            status=processo.status.value,
            tipo_processo_id=str(processo.tipo_processo_id),
            unidade_atual_id=str(processo.unidade_atual_id),
            unidade_origem_id=str(processo.unidade_origem_id),
            setor_atual_id=str(processo.setor_atual_id),
            servidor_atual_id=str(processo.servidor_atual_id),
            prazo_dias=processo.prazo_dias,
            prazo_em=processo.prazo_em,
            criado_por_id=str(processo.criado_por_id),
            criado_em=processo.criado_em,
            concluido_em=processo.concluido_em,
            sigiloso=processo.sigiloso,
            interessados=[InteressadoResponse.de(i) for i in processo.interessados],
        )


class CardProcessoResponse(BaseModel):
    """Card enxuto do Kanban/busca (US 2.3, 2.7, 2.8).

    `somente_leitura`, `devolvido` e `acao_requerida` são **contextuais ao
    usuário da requisição** (change visibilidade-processos-origem, design
    D2/D3; change kanban-por-servidor, design D2): não são propriedades
    intrínsecas do processo, variam conforme quem pediu o card.
    `servidor_atual_nome` também é exibido no card (design D2/D5 do change
    kanban-por-servidor) para identificar quem detém o processo quando ele
    está em modo de acompanhamento.
    """

    id: str
    numero: str
    assunto: str
    status: str
    unidade_atual_id: str
    tipo_processo_nome: str
    unidade_atual_nome: str
    servidor_atual_nome: str
    criado_em: datetime
    prazo_em: date
    dias_restantes: int
    vencido: bool
    sigiloso: bool
    somente_leitura: bool
    devolvido: bool
    acao_requerida: bool

    @classmethod
    def de(
        cls,
        processo,
        *,
        hoje: date,
        somente_leitura: bool = False,
        devolvido: bool = False,
        acao_requerida: bool = False,
    ) -> "CardProcessoResponse":
        dias = (processo.prazo_em - hoje).days
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            status=processo.status.value,
            unidade_atual_id=str(processo.unidade_atual_id),
            tipo_processo_nome=processo.tipo_processo.nome,
            unidade_atual_nome=processo.unidade_atual.nome,
            servidor_atual_nome=processo.servidor_atual.nome,
            criado_em=processo.criado_em,
            prazo_em=processo.prazo_em,
            dias_restantes=dias,
            vencido=dias < 0,
            sigiloso=processo.sigiloso,
            somente_leitura=somente_leitura,
            devolvido=devolvido,
            acao_requerida=acao_requerida,
        )


class KanbanResponse(BaseModel):
    items: list[CardProcessoResponse]
    total: int
    page: int
    page_size: int
    mensagem_vazio: str | None = None


class EnviarRequest(BaseModel):
    """Destino explícito do Envio (D2) — unidade, setor e servidor, com mensagem."""

    unidade_destino_id: str
    setor_destino_id: str
    servidor_destino_id: str
    mensagem: str | None = None


class DevolverRequest(BaseModel):
    """O destino da Devolução é resolvido no serviço a partir do histórico
    (D3) — nunca aceito do cliente. `motivo` é validado no serviço (US 2.2b
    Cen.3 exige a mensagem exata "Selecione um motivo para a devolução")."""

    motivo: str | None = None
    justificativa: str | None = None


class ReatribuirRequest(BaseModel):
    """Reatribuição (D2): permanece na unidade atual — não há campo de
    unidade — podendo trocar de setor; servidor de destino obrigatório."""

    setor_destino_id: str
    servidor_destino_id: str
    justificativa: str | None = None


class ConcluirRequest(BaseModel):
    """Conclusão (US 2.5/2.2): ação própria, sem payload — a confirmação é
    tratada na interface antes do envio da requisição."""


class EventoHistoricoResponse(BaseModel):
    id: str
    tipo_evento: str
    unidade_origem_id: str | None
    unidade_destino_id: str | None
    # Setor/servidor de origem e destino (D1, D6) — distintos de
    # `responsavel_id`: quem deteve o processo, não quem agiu.
    setor_origem_id: str | None
    setor_destino_id: str | None
    servidor_origem_id: str | None
    servidor_destino_id: str | None
    # Nullable: o evento de sistema `arquivamento_automatico` não tem responsável
    # humano (D3, change arquivamento-automatico).
    responsavel_id: str | None
    status_resultante: str
    motivo: str | None
    justificativa: str | None
    mensagem: str | None
    criado_em: datetime

    @classmethod
    def de(cls, evento) -> "EventoHistoricoResponse":
        return cls(
            id=str(evento.id),
            tipo_evento=evento.tipo_evento.value,
            unidade_origem_id=str(evento.unidade_origem_id) if evento.unidade_origem_id else None,
            unidade_destino_id=(
                str(evento.unidade_destino_id) if evento.unidade_destino_id else None
            ),
            setor_origem_id=str(evento.setor_origem_id) if evento.setor_origem_id else None,
            setor_destino_id=str(evento.setor_destino_id) if evento.setor_destino_id else None,
            servidor_origem_id=(
                str(evento.servidor_origem_id) if evento.servidor_origem_id else None
            ),
            servidor_destino_id=(
                str(evento.servidor_destino_id) if evento.servidor_destino_id else None
            ),
            responsavel_id=str(evento.responsavel_id) if evento.responsavel_id else None,
            status_resultante=evento.status_resultante.value,
            motivo=evento.motivo.value if evento.motivo else None,
            justificativa=evento.justificativa,
            mensagem=evento.mensagem,
            criado_em=evento.criado_em,
        )


class HistoricoResponse(BaseModel):
    processo_id: str
    criado_em: datetime
    eventos: list[EventoHistoricoResponse] = Field(default_factory=list)
    mensagem_vazio: str | None = None


class ProcessoAtuadoResponse(BaseModel):
    """Item de "Meu Perfil" (US 1.5 Cen.1)."""

    processo_id: str
    numero: str
    assunto: str
    data_acao: datetime
    tipo_acao: str
