"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import { COLUNAS_KANBAN, agruparPorStatus, textoPrazo } from "@/lib/processo-ui";

type Card = Schemas["CardProcessoResponse"];
type Unidade = Schemas["UnidadeResponse"];

function CardProcesso({ card, nomeUnidade }: { card: Card; nomeUnidade: (id: string) => string }) {
  return (
    <Link
      href={`/processos/${card.id}`}
      className={`block rounded-card border border-navy-50 bg-superficie-card p-3 text-sm shadow-card hover:bg-navy-50/40 ${
        card.vencido ? "border-l-4 border-l-red-600 font-bold" : ""
      }`}
    >
      <div className="flex items-center gap-1 font-mono text-xs text-gray-500">
        {card.numero}
        {card.sigiloso && (
          <span aria-label="Sigiloso" title="Sigiloso">
            🔒
          </span>
        )}
      </div>
      <div className="mt-1">{card.assunto}</div>
      <div className="mt-1 text-xs text-gray-500">{nomeUnidade(card.unidade_atual_id)}</div>
      <div className={`mt-1 text-xs ${card.vencido ? "text-red-600" : "text-gray-500"}`}>
        {card.vencido && <span aria-hidden>⏰ </span>}
        {textoPrazo(card)}
      </div>
    </Link>
  );
}

function KanbanConteudo() {
  const { usuario } = useAuth();
  const ehGestor = usuario?.perfil === "gestor";
  const ehServidor = usuario?.perfil === "servidor";
  const [cards, setCards] = useState<Card[]>([]);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [filtroUnidade, setFiltroUnidade] = useState("");
  const [mensagemVazio, setMensagemVazio] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resp = await api.listarKanban(
        filtroUnidade ? { filtro_unidade: filtroUnidade } : undefined,
      );
      setCards(resp.items);
      setMensagemVazio(resp.total === 0 ? (resp.mensagem_vazio ?? null) : null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar o Kanban.");
    } finally {
      setCarregando(false);
    }
  }, [filtroUnidade]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  // O filtro do Gestor lista só as unidades que aparecem no consolidado (US 2.8 Cen.2).
  useEffect(() => {
    if (!ehGestor) return;
    void (async () => {
      try {
        setUnidades(await api.listarUnidades());
      } catch {
        // filtro opcional — silencia
      }
    })();
  }, [ehGestor]);

  const nomeUnidade = useMemo(() => {
    const mapa = new Map(unidades.map((u) => [u.id, u.sigla]));
    return (id: string) => mapa.get(id) ?? "";
  }, [unidades]);

  const grupos = agruparPorStatus(cards);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Processos</h1>
        <div className="flex items-center gap-2">
          {ehGestor && (
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
          )}
          <button
            type="button"
            onClick={() => void carregar()}
            className="rounded border px-3 py-1 text-sm"
          >
            Atualizar
          </button>
          {ehServidor && (
            <Link
              href="/processos/novo"
              className="rounded-card bg-navy-900 px-3 py-1 text-sm font-medium text-white hover:bg-navy-700"
            >
              Novo processo
            </Link>
          )}
        </div>
      </div>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {mensagemVazio && !carregando ? (
        <p className="mt-6 text-sm text-gray-500">{mensagemVazio}</p>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {COLUNAS_KANBAN.map((coluna) => (
            <section key={coluna.status} className="rounded bg-gray-50 p-3">
              <h2 className="text-sm font-medium text-gray-700">
                {coluna.titulo} <span className="text-gray-400">({grupos[coluna.status].length})</span>
              </h2>
              <div className="mt-2 space-y-2">
                {grupos[coluna.status].map((card) => (
                  <CardProcesso key={card.id} card={card} nomeUnidade={nomeUnidade} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProcessosPage() {
  return (
    <ProtectedShell>
      <KanbanConteudo />
    </ProtectedShell>
  );
}
