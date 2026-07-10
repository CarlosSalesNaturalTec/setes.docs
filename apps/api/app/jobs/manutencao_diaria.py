"""Contrato de idempotência das rotinas agendadas (D5, task 8.4).

Este módulo NÃO implementa a lógica de negócio (arquivamento US 2.5, purga
US 8.7 etc.) — ela vem em changes futuros. Ele estabelece e testa o *contrato*
que toda rotina deve honrar:

    A rotina não processa "os vencidos de ontem"; processa "tudo que está
    vencido AGORA". A seleção é função do estado atual; a transição de estado
    é o guard contra reprocessamento.

O passo de exemplo abaixo (arquivamento) é modelado sobre estruturas em memória
para ser testável sem banco. A query real do design é:

    SELECT * FROM processo
    WHERE status = 'Concluído'
      AND concluido_em + prazo_arquivamento_vigente <= now();

Rodar 1x, 10x, ou retomar após dias de indisponibilidade produz o mesmo
resultado, sem duplicar evento de histórico.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class StatusProcesso(str, Enum):
    CONCLUIDO = "Concluído"
    ARQUIVADO = "Arquivado"


@dataclass
class Processo:
    id: str
    status: StatusProcesso
    # Momento em que o prazo de arquivamento vigente expira (congelado na conclusão).
    arquivar_a_partir_de: datetime
    arquivado_em: datetime | None = None


@dataclass
class EventoHistorico:
    processo_id: str
    tipo: str
    em: datetime


@dataclass
class Historico:
    eventos: list[EventoHistorico] = field(default_factory=list)


def selecionar_para_arquivar(processos: list[Processo], *, agora: datetime) -> list[Processo]:
    """Seleção idempotente: função do ESTADO ATUAL, não do intervalo desde a última run.

    Um processo já 'Arquivado' não satisfaz o predicado, logo nunca reentra —
    esse é o guard de transição (spec rotinas-agendadas — "Guard de transição").
    """
    return [
        p
        for p in processos
        if p.status == StatusProcesso.CONCLUIDO and p.arquivar_a_partir_de <= agora
    ]


def arquivar_processos(
    processos: list[Processo], historico: Historico, *, agora: datetime
) -> int:
    """Arquiva os processos vencidos; retorna quantos foram efetivamente transicionados.

    Idempotente: reexecução sobre o mesmo estado seleciona conjunto vazio (todos
    já 'Arquivado'), então não duplica efeito nem evento de histórico.
    """
    alvos = selecionar_para_arquivar(processos, agora=agora)
    for p in alvos:
        # Guard explícito além do predicado de seleção (defesa em profundidade).
        if p.status != StatusProcesso.CONCLUIDO:
            continue
        p.status = StatusProcesso.ARQUIVADO
        p.arquivado_em = agora
        historico.eventos.append(
            EventoHistorico(processo_id=p.id, tipo="ARQUIVAMENTO_AUTOMATICO", em=agora)
        )
    return len(alvos)
