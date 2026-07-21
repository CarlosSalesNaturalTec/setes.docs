"""Schemas do dashboard de KPIs do Gestor (Épico 6, US 6.1).

A forma dos payloads espelha as regras de `services/dashboard.py` (D3,
design.md `dashboard-kpis-gestor`) — nunca duplica cálculo aqui.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ProdutividadeUnidadeItem(BaseModel):
    unidade_id: str
    unidade_nome: str
    quantidade: int


class PrazoRiscoItem(BaseModel):
    id: str
    numero: str
    assunto: str
    unidade_atual_id: str
    prazo_em: date
    dias_restantes: int
    vencido: bool

    @classmethod
    def de(cls, processo, *, hoje: date) -> "PrazoRiscoItem":
        dias = (processo.prazo_em - hoje).days
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            unidade_atual_id=str(processo.unidade_atual_id),
            prazo_em=processo.prazo_em,
            dias_restantes=dias,
            vencido=dias < 0,
        )


class DashboardKpisResponse(BaseModel):
    """US 6.1 Cen.1 — os 5 indicadores + a lista de prazo em risco, no escopo do Gestor."""

    total_processos_ativos: int
    tempo_medio_tramitacao_dias: float | None
    total_processos_parados: int
    produtividade_por_unidade: list[ProdutividadeUnidadeItem] = Field(default_factory=list)
    prazos_em_risco: list[PrazoRiscoItem] = Field(default_factory=list)


class ProcessoAtivoItem(BaseModel):
    """Item de drill-down de "Processos Ativos" (US 6.1 Cen.5)."""

    id: str
    numero: str
    assunto: str
    unidade_atual_id: str
    dias_restantes: int

    @classmethod
    def de(cls, processo, *, hoje: date) -> "ProcessoAtivoItem":
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            unidade_atual_id=str(processo.unidade_atual_id),
            dias_restantes=(processo.prazo_em - hoje).days,
        )


class ProcessoParadoItem(BaseModel):
    """Item de drill-down de "Processos Parados" (US 6.1 Cen.4)."""

    id: str
    numero: str
    assunto: str
    unidade_atual_id: str
    dias_parados: int

    @classmethod
    def de(cls, processo, *, dias_parados: int) -> "ProcessoParadoItem":
        return cls(
            id=str(processo.id),
            numero=processo.numero,
            assunto=processo.assunto,
            unidade_atual_id=str(processo.unidade_atual_id),
            dias_parados=dias_parados,
        )


class ProcessosAtivosResponse(BaseModel):
    items: list[ProcessoAtivoItem] = Field(default_factory=list)
    total: int


class ProcessosParadosResponse(BaseModel):
    items: list[ProcessoParadoItem] = Field(default_factory=list)
    total: int


class DistribuicaoItem(BaseModel):
    """Item de distribuição por dimensão (unidade/tipo/usuário) — US 6.2."""

    rotulo: str
    quantidade: int


class DistribuicoesResponse(BaseModel):
    """US 6.2 — distribuição de processos ativos por unidade, por tipo e por usuário."""

    por_unidade: list[DistribuicaoItem] = Field(default_factory=list)
    por_tipo: list[DistribuicaoItem] = Field(default_factory=list)
    por_usuario: list[DistribuicaoItem] = Field(default_factory=list)
