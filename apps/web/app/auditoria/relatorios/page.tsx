"use client";

import { useEffect, useMemo, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type Relatorio = Schemas["RelatorioAuditoriaResponse"];
type Unidade = Schemas["UnidadeResponse"];
type TipoProcesso = Schemas["TipoProcessoResponse"];

const LABEL_STATUS: Record<Schemas["StatusProcesso"], string> = {
  aberto: "Aberto",
  em_tramitacao: "Em Tramitação",
  concluido: "Concluído",
  arquivado: "Arquivado",
};

function RelatorioAuditoriaConteudo() {
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [tipos, setTipos] = useState<TipoProcesso[]>([]);
  const [inicio, setInicio] = useState("");
  const [fim, setFim] = useState("");
  const [unidadeId, setUnidadeId] = useState("");
  const [tipoProcessoId, setTipoProcessoId] = useState("");
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        setUnidades(await api.listarUnidades());
      } catch {
        // filtro opcional — silencia
      }
      try {
        setTipos(await api.listarTiposProcesso());
      } catch {
        // filtro opcional — silencia
      }
    })();
  }, []);

  const nomeUnidade = useMemo(() => {
    const mapa = new Map(unidades.map((u) => [u.id, u.nome]));
    return (id: string) => mapa.get(id) ?? id;
  }, [unidades]);

  const nomeTipo = useMemo(() => {
    const mapa = new Map(tipos.map((t) => [t.id, t.nome]));
    return (id: string) => mapa.get(id) ?? id;
  }, [tipos]);

  async function gerarRelatorio() {
    setCarregando(true);
    setErro(null);
    try {
      const resp = await api.obterRelatorioAuditoria({
        inicio: inicio || undefined,
        fim: fim || undefined,
        unidade_id: unidadeId || undefined,
        tipo_processo_id: tipoProcessoId || undefined,
      });
      setRelatorio(resp);
    } catch (err) {
      setRelatorio(null);
      setErro(err instanceof ApiError ? err.detail : "Não foi possível gerar o relatório.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Relatório de Auditoria</h1>

      <form
        className="mt-4 flex flex-wrap items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          void gerarRelatorio();
        }}
      >
        <div>
          <label htmlFor="relatorio-inicio" className="block text-sm">
            Período — início
          </label>
          <input
            id="relatorio-inicio"
            type="date"
            value={inicio}
            onChange={(e) => setInicio(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label htmlFor="relatorio-fim" className="block text-sm">
            Período — fim
          </label>
          <input
            id="relatorio-fim"
            type="date"
            value={fim}
            onChange={(e) => setFim(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          />
        </div>
        <div>
          <label htmlFor="relatorio-unidade" className="block text-sm">
            Unidade
          </label>
          <select
            id="relatorio-unidade"
            value={unidadeId}
            onChange={(e) => setUnidadeId(e.target.value)}
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
        <div>
          <label htmlFor="relatorio-tipo" className="block text-sm">
            Tipo de processo
          </label>
          <select
            id="relatorio-tipo"
            value={tipoProcessoId}
            onChange={(e) => setTipoProcessoId(e.target.value)}
            className="rounded border px-2 py-1 text-sm"
          >
            <option value="">Todos os tipos</option>
            {tipos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="rounded bg-gray-900 px-3 py-1.5 text-sm text-white disabled:opacity-50"
          disabled={carregando}
        >
          Gerar relatório
        </button>
      </form>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {relatorio && !carregando && (
        <>
          {relatorio.mensagem_vazio ? (
            <p className="mt-6 text-sm text-gray-500">{relatorio.mensagem_vazio}</p>
          ) : (
            <>
              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div data-testid="relatorio-total" className="rounded border bg-white p-4 shadow-sm">
                  <div className="text-xs text-gray-500">Total de Processos no Período</div>
                  <div className="mt-1 text-2xl font-semibold">{relatorio.total_processos}</div>
                </div>
                <div data-testid="relatorio-tempo-medio" className="rounded border bg-white p-4 shadow-sm">
                  <div className="text-xs text-gray-500">Tempo Médio de Tramitação</div>
                  <div className="mt-1 text-2xl font-semibold">
                    {relatorio.tempo_medio_tramitacao_dias === null
                      ? "—"
                      : `${relatorio.tempo_medio_tramitacao_dias.toFixed(1)} dias`}
                  </div>
                </div>
              </div>

              <ul className="mt-6 space-y-2" data-testid="relatorio-lista">
                {(relatorio.items ?? []).map((item) => (
                  <li key={item.id} className="rounded border bg-white p-3 text-sm shadow-sm">
                    <span className="font-mono text-xs">{item.numero}</span> — {item.assunto} (
                    {nomeUnidade(item.unidade_atual_id)} · {nomeTipo(item.tipo_processo_id)}) —{" "}
                    {LABEL_STATUS[item.status]}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default function RelatorioAuditoriaPage() {
  return (
    <ProtectedShell exigirAuditoria>
      <RelatorioAuditoriaConteudo />
    </ProtectedShell>
  );
}
