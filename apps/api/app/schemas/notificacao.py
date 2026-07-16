"""Schemas de notificação interna (sino), Épico 5 — US 5.1, 5.3, 5.4."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class NotificacaoResponse(BaseModel):
    id: str
    tipo: str
    processo_id: str
    numero_processo: str
    assunto: str
    unidade_id: str
    unidade_nome: str
    unidade_origem_id: str | None
    unidade_origem_nome: str | None
    prazo_referencia: date | None
    lida_em: datetime | None
    criado_em: datetime

    @classmethod
    def de(cls, notificacao) -> "NotificacaoResponse":
        return cls(
            id=str(notificacao.id),
            tipo=notificacao.tipo.value,
            processo_id=str(notificacao.processo_id),
            numero_processo=notificacao.numero_processo,
            assunto=notificacao.assunto,
            unidade_id=str(notificacao.unidade_id),
            unidade_nome=notificacao.unidade_nome,
            unidade_origem_id=(
                str(notificacao.unidade_origem_id) if notificacao.unidade_origem_id else None
            ),
            unidade_origem_nome=notificacao.unidade_origem_nome,
            prazo_referencia=notificacao.prazo_referencia,
            lida_em=notificacao.lida_em,
            criado_em=notificacao.criado_em,
        )


class ListaNotificacoesResponse(BaseModel):
    items: list[NotificacaoResponse] = Field(default_factory=list)
    mensagem_vazio: str | None = None


class ContadorNotificacoesResponse(BaseModel):
    nao_lidas: int = Field(examples=[3])


class MarcarTodasLidasResponse(BaseModel):
    marcadas: int = Field(examples=[3])
