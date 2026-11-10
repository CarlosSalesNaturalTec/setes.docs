"""Schemas da verificação de assinatura (Épico 4, US 4.2).

Change assinatura-verificacao-fundacao (design.md D2, D6). O veredito é enum
fechado — nunca texto livre; `mensagem` traz o texto canônico da spec, que o
frontend exibe sem reescrever.
"""

from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel


class VereditoAssinatura(str, enum.Enum):
    """Veredito de UMA assinatura (D2). A ordem de gravidade para o resumo do
    documento é `invalida > inconclusiva > fora_icp_brasil >
    alterada_apos_assinatura > valida`."""

    VALIDA = "valida"
    ALTERADA_APOS_ASSINATURA = "alterada_apos_assinatura"
    FORA_ICP_BRASIL = "fora_icp_brasil"
    INCONCLUSIVA = "inconclusiva"
    INVALIDA = "invalida"


class SituacaoVerificacao(str, enum.Enum):
    """Situação do DOCUMENTO como um todo (D2)."""

    ASSINADO = "assinado"
    SEM_ASSINATURA = "sem_assinatura"
    ILEGIVEL = "ilegivel"


class OrigemDataAssinatura(str, enum.Enum):
    """De onde vem a data/hora exibida (D6): carimbo de tempo verificado ou
    data declarada pelo próprio signatário (sem prova)."""

    CARIMBO = "carimbo"
    DECLARADA = "declarada"


class AssinaturaVerificada(BaseModel):
    ordem: int
    veredito: VereditoAssinatura
    mensagem: str
    signatario_nome: str | None
    # Extraído do otherName ICP-Brasil 2.16.76.1.3.1; nulo quando ausente (D6).
    signatario_cpf: str | None
    autoridade_certificadora: str | None
    data_assinatura: datetime | None
    origem_data: OrigemDataAssinatura
    autoridade_carimbo: str | None = None
    certificado_expirado_em: datetime | None = None


class ResultadoVerificacaoResponse(BaseModel):
    """Resultado efêmero (D4): devolvido só nesta resposta, nunca persistido."""

    documento_id: str
    situacao: SituacaoVerificacao
    resumo: VereditoAssinatura | None
    mensagem_resumo: str
    assinaturas: list[AssinaturaVerificada]
    # Aviso fixo + link do verificador oficial do ITI (D7); nulos quando não
    # há assinatura a conferir.
    aviso_veredito_oficial: str | None
    url_verificador_oficial: str | None
