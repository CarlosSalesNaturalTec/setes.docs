"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

import { GraficoDistribuicao } from "./grafico-distribuicao";

type Kpis = Schemas["DashboardKpisResponse"];
type Distribuicoes = Schemas["DistribuicoesResponse"];
type Unidade = Schemas["UnidadeResponse"];
type ProcessoAtivoItem = Schemas["ProcessoAtivoItem"];
type ProcessoParadoItem = Schemas["ProcessoParadoItem"];

const MSG_VAZIO = "Nenhum dado disponível para o período";

type DrillDown =
  | { tipo: "ativos"; titulo: string; items: ProcessoAtivoItem[] }
  | { tipo: "parados"; titulo: string; items: ProcessoParadoItem[] };

function DashboardConteudo() {
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [distribuicoes, setDistribuicoes] = useState<Distribuicoes | null>(null);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [filtroUnidade, setFiltroUnidade] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [drillDown, setDrillDown] = useState<DrillDown | null>(null);
  const [carregandoDrillDown, setCarregandoDrillDown] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    setDrillDown(null);
    try {
      const resp = await api.obterDashboardKpis(
        filtroUnidade ? { unidade_id: filtroUnidade } : undefined,
      );
      setKpis(resp);
    } catch (err) {
      setKpis(null);
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar o dashboard.");
    } finally {
      setCarregando(false);
    }
  }, [filtroUnidade]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const carregarDistribuicoes = useCallback(async () => {
    try {
      const resp = await api.obterDashboardDistribuicoes(
        filtroUnidade ? { unidade_id: filtroUnidade } : undefined,
      );
      setDistribuicoes(resp);
    } catch {
      setDistribuicoes(null);
    }
  }, [filtroUnidade]);

  useEffect(() => {
    void carregarDistribuicoes();
  }, [carregarDistribuicoes]);

  useEffect(() => {
    void (async () => {
      try {
        setUnidades(await api.listarUnidades());
      } catch {
        // filtro opcional — silencia
      }
    })();
  }, []);

  const nomeUnidade = useMemo(() => {
    const mapa = new Map(unidades.map((u) => [u.id, u.nome]));
    return (id: string) => mapa.get(id) ?? id;
  }, [unidades]);

  const abrirDrillDown = useCallback(
    async (tipo: "ativos" | "parados", titulo: string) => {
      setCarregandoDrillDown(true);
      setErro(null);
      try {
        const query = filtroUnidade ? { unidade_id: filtroUnidade } : undefined;
        if (tipo === "ativos") {
          const resp = await api.obterProcessosAtivosDashboard(query);
          setDrillDown({ tipo: "ativos", titulo, items: resp.items ?? [] });
        } else {
          const resp = await api.obterProcessosParadosDashboard(query);
          setDrillDown({ tipo: "parados", titulo, items: resp.items ?? [] });
        }
      } catch (err) {
        setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar a listagem.");
      } finally {
        setCarregandoDrillDown(false);
      }
    },
    [filtroUnidade],
  );

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <select
          aria-label="Filtrar por unidade"
          value={filtroUnidade}
          onChange={(e) => setFiltroUnidade(e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="">Todas as unidades</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>
              {u.nome}
            </option>
          ))}
        </select>
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {kpis && !carregando && (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <button
              type="button"
              data-testid="kpi-ativos"
              onClick={() => void abrirDrillDown("ativos", "Processos Ativos")}
              className="rounded-card border border-navy-50 bg-superficie-card p-4 text-left shadow-card hover:bg-navy-50/40"
            >
              <div className="text-xs text-gray-500">Total de Processos Ativos</div>
              <div className="mt-1 text-2xl font-semibold">{kpis.total_processos_ativos}</div>
            </button>

            <div data-testid="kpi-tempo-medio" className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
              <div className="text-xs text-gray-500">Tempo Médio de Tramitação</div>
              {kpis.tempo_medio_tramitacao_dias === null ? (
                <p className="mt-1 text-sm text-gray-500">{MSG_VAZIO}</p>
              ) : (
                <div className="mt-1 text-2xl font-semibold">
                  {kpis.tempo_medio_tramitacao_dias.toFixed(1)} dias
                </div>
              )}
            </div>

            <button
              type="button"
              data-testid="kpi-parados"
              onClick={() => void abrirDrillDown("parados", "Processos Parados")}
              className="rounded-card border border-navy-50 bg-superficie-card p-4 text-left shadow-card hover:bg-navy-50/40"
            >
              <div className="text-xs text-gray-500">Processos Parados</div>
              <div className="mt-1 text-2xl font-semibold">{kpis.total_processos_parados}</div>
            </button>

            <div data-testid="kpi-produtividade" className="rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
              <div className="text-xs text-gray-500">Produtividade por Unidade</div>
              {(kpis.produtividade_por_unidade ?? []).length === 0 ? (
                <p className="mt-1 text-sm text-gray-500">{MSG_VAZIO}</p>
              ) : (
                <ul className="mt-1 space-y-1 text-sm">
                  {(kpis.produtividade_por_unidade ?? []).map((item) => (
                    <li key={item.unidade_id}>
                      {item.unidade_nome}: <span className="font-medium">{item.quantidade}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <section className="mt-6 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
            <h2 className="text-sm font-medium text-gray-700">Prazos em Risco</h2>
            {(kpis.prazos_em_risco ?? []).length === 0 ? (
              <p className="mt-2 text-sm text-gray-500">{MSG_VAZIO}</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {(kpis.prazos_em_risco ?? []).map((item) => (
                  <li
                    key={item.id}
                    className={`text-sm ${item.vencido ? "font-medium text-red-600" : "text-gray-700"}`}
                  >
                    <span className="font-mono text-xs">{item.numero}</span> — {item.assunto} (
                    {nomeUnidade(item.unidade_atual_id)}) —{" "}
                    {item.vencido
                      ? `vencido há ${Math.abs(item.dias_restantes)} dia(s)`
                      : `${item.dias_restantes} dia(s) restante(s)`}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {distribuicoes && (
        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <GraficoDistribuicao titulo="Processos por Unidade" itens={distribuicoes.por_unidade ?? []} />
          <GraficoDistribuicao titulo="Processos por Tipo" itens={distribuicoes.por_tipo ?? []} />
          <GraficoDistribuicao titulo="Processos por Usuário" itens={distribuicoes.por_usuario ?? []} />
        </div>
      )}

      {carregandoDrillDown && <p className="mt-4 text-sm text-gray-500">Carregando listagem…</p>}

      {drillDown && !carregandoDrillDown && (
        <section className="mt-6 rounded-card border border-navy-50 bg-superficie-card p-4 shadow-card">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-700">{drillDown.titulo}</h2>
            <button
              type="button"
              onClick={() => setDrillDown(null)}
              className="text-xs text-gray-500"
            >
              Fechar
            </button>
          </div>
          {drillDown.items.length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">{MSG_VAZIO}</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {drillDown.tipo === "ativos"
                ? drillDown.items.map((item) => (
                    <li key={item.id} className="text-sm">
                      <span className="font-mono text-xs">{item.numero}</span> — {item.assunto} (
                      {nomeUnidade(item.unidade_atual_id)}) — {item.dias_restantes} dia(s) restante(s)
                    </li>
                  ))
                : drillDown.items.map((item) => (
                    <li key={item.id} className="text-sm">
                      <span className="font-mono text-xs">{item.numero}</span> — {item.assunto} (
                      {nomeUnidade(item.unidade_atual_id)}) — {item.dias_parados} dia(s) parado
                    </li>
                  ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedShell perfisPermitidos={["gestor"]}>
      <DashboardConteudo />
    </ProtectedShell>
  );
}
