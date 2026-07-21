"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import { COLUNAS_KANBAN, agruparPorStatus, corStatus, rotuloStatus, textoCriadoEm, textoPrazo } from "@/lib/processo-ui";

type Card = Schemas["CardProcessoResponse"];
type Unidade = Schemas["UnidadeResponse"];
type ModoVisualizacao = "kanban" | "lista";

const CHAVE_MODO_VISUALIZACAO = "setes:processos:modo-visualizacao";

// Rótulos da confirmação de sucesso pós-despacho/devolução (ver
// openspec/changes/corrigir-feedback-despacho-devolucao) — a ação já concluída
// é comunicada aqui, e não como erro de acesso ao processo movido.
const VERBO_ACAO: Record<string, string> = {
  despacho: "despachado",
  devolucao: "devolvido",
};

function PillStatus({ status }: { status: string }) {
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${corStatus(status)}`}>
      {rotuloStatus(status)}
    </span>
  );
}

function CardProcesso({ card }: { card: Card }) {
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
      <div className="mt-1 inline-block rounded bg-navy-50 px-2 py-0.5 text-xs font-medium text-navy-700">
        {card.tipo_processo_nome}
      </div>
      <div className="mt-1">{card.assunto}</div>
      <div className="mt-1 text-xs text-gray-500">{card.unidade_atual_nome}</div>
      <div className="mt-1 text-xs text-gray-500">{textoCriadoEm(card)}</div>
      <div className={`mt-1 text-xs ${card.vencido ? "text-red-600" : "text-gray-500"}`}>
        {card.vencido && <span aria-hidden>⏰ </span>}
        {textoPrazo(card)}
      </div>
    </Link>
  );
}

function LinhaProcesso({ card }: { card: Card }) {
  return (
    <Link
      href={`/processos/${card.id}`}
      className={`flex flex-wrap items-center gap-3 rounded-card border border-navy-50 bg-superficie-card p-3 text-sm shadow-card hover:bg-navy-50/40 ${
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
      <div className="rounded bg-navy-50 px-2 py-0.5 text-xs font-medium text-navy-700">
        {card.tipo_processo_nome}
      </div>
      <div className="flex-1">{card.assunto}</div>
      <div className="text-xs text-gray-500">{card.unidade_atual_nome}</div>
      <div className="text-xs text-gray-500">{textoCriadoEm(card)}</div>
      <PillStatus status={card.status} />
    </Link>
  );
}

function KanbanConteudo() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { usuario } = useAuth();
  const ehGestor = usuario?.perfil === "gestor";
  const ehServidor = usuario?.perfil === "servidor";
  const [cards, setCards] = useState<Card[]>([]);
  const [total, setTotal] = useState(0);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [filtroUnidade, setFiltroUnidade] = useState("");
  const [mensagemVazio, setMensagemVazio] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [modo, setModo] = useState<ModoVisualizacao>("kanban");
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  useEffect(() => {
    const acao = searchParams.get("acao");
    const destino = searchParams.get("destino");
    if (acao && destino && VERBO_ACAO[acao]) {
      setMensagemSucesso(`Processo ${VERBO_ACAO[acao]} para ${destino}.`);
      router.replace("/processos");
    }
  }, [searchParams, router]);

  useEffect(() => {
    const salvo = window.localStorage.getItem(CHAVE_MODO_VISUALIZACAO);
    if (salvo === "kanban" || salvo === "lista") setModo(salvo);
  }, []);

  const alternarModo = useCallback((novo: ModoVisualizacao) => {
    setModo(novo);
    window.localStorage.setItem(CHAVE_MODO_VISUALIZACAO, novo);
  }, []);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resp = await api.listarKanban(
        filtroUnidade ? { filtro_unidade: filtroUnidade } : undefined,
      );
      setCards(resp.items);
      setTotal(resp.total);
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
        const todas = await api.listarUnidades();
        setUnidades(todas.filter((u) => u.ativo));
      } catch {
        // filtro opcional — silencia
      }
    })();
  }, [ehGestor]);

  const grupos = agruparPorStatus(cards);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Processos</h1>
          <span className="text-sm text-gray-500">{total} processo(s)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex overflow-hidden rounded border">
            <button
              type="button"
              aria-pressed={modo === "kanban"}
              onClick={() => alternarModo("kanban")}
              className={`px-3 py-1 text-sm ${modo === "kanban" ? "bg-navy-900 text-white" : "bg-white text-gray-700"}`}
            >
              Kanban
            </button>
            <button
              type="button"
              aria-pressed={modo === "lista"}
              onClick={() => alternarModo("lista")}
              className={`px-3 py-1 text-sm ${modo === "lista" ? "bg-navy-900 text-white" : "bg-white text-gray-700"}`}
            >
              Lista
            </button>
          </div>
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

      {mensagemSucesso && (
        <p className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">{mensagemSucesso}</p>
      )}
      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {mensagemVazio && !carregando ? (
        <p className="mt-6 text-sm text-gray-500">{mensagemVazio}</p>
      ) : modo === "kanban" ? (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {COLUNAS_KANBAN.map((coluna) => (
            <section key={coluna.status} className="rounded bg-gray-50 p-3">
              <h2 className={`rounded px-2 py-1 text-sm font-medium ${coluna.corClasse}`}>
                {coluna.titulo} <span className="opacity-70">({grupos[coluna.status].length})</span>
              </h2>
              <div className="mt-2 space-y-2">
                {grupos[coluna.status].map((card) => (
                  <CardProcesso key={card.id} card={card} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="mt-6 space-y-2">
          {cards.map((card) => (
            <LinhaProcesso key={card.id} card={card} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProcessosPage() {
  return (
    <ProtectedShell>
      <Suspense fallback={<p className="p-4 text-sm text-gray-500">Carregando…</p>}>
        <KanbanConteudo />
      </Suspense>
    </ProtectedShell>
  );
}
