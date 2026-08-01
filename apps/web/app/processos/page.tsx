"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import {
  CHAVE_EXIBIR_ARQUIVADOS,
  COLUNAS_KANBAN,
  agruparPorStatus,
  corStatus,
  rotuloStatus,
  textoCriadoEm,
  textoPrazo,
} from "@/lib/processo-ui";

type Card = Schemas["CardProcessoResponse"];
type Unidade = Schemas["UnidadeResponse"];
type TipoProcesso = Schemas["TipoProcessoResponse"];
type ModoVisualizacao = "kanban" | "lista";

const CHAVE_MODO_VISUALIZACAO = "setes:processos:modo-visualizacao";
const DEBOUNCE_ASSUNTO_MS = 300;

// Rótulos da confirmação de sucesso pós-envio/devolução (ver
// openspec/changes/corrigir-feedback-despacho-devolucao) — a ação já concluída
// é comunicada aqui, e não como erro de acesso ao processo movido.
const VERBO_ACAO: Record<string, string> = {
  envio: "enviado",
  devolucao: "devolvido",
};

function PillStatus({ status }: { status: string }) {
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${corStatus(status)}`}>
      {rotuloStatus(status)}
    </span>
  );
}

// Fundo/borda contextuais do card (design D6 de visibilidade-processos-origem):
// somente_leitura acinzenta o fundo (processo acompanhado por origem, fora da
// unidade atual); devolvido destaca a borda esquerda em âmbar — vencido
// (borda vermelha) prevalece quando os dois coincidem, mas o badge
// "↩ Devolvido" permanece.
function classesFundoBorda(card: Card): string {
  const fundo = card.somente_leitura ? "bg-gray-100 opacity-75" : "bg-superficie-card";
  const borda = card.vencido
    ? "border-l-4 border-l-red-600 font-bold"
    : card.devolvido
      ? "border-l-4 border-l-amber-500"
      : "";
  return `${fundo} ${borda}`;
}

// Distinção ação/acompanhamento (change kanban-por-servidor, design D2):
// destaque sólido (anel navy) quando a ação é minha; borda tracejada e
// discreta quando estou apenas acompanhando — eixo independente de
// somente_leitura/devolvido, nunca sobrepõe as classes acima.
function classesAcao(card: Card): string {
  return card.acao_requerida ? "ring-1 ring-navy-400" : "border-dashed";
}

function BadgeDevolvido() {
  return (
    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
      ↩ Devolvido
    </span>
  );
}

function BadgeAcaoRequerida() {
  return (
    <span className="rounded-full bg-navy-900 px-2 py-0.5 text-xs font-medium text-white">
      Ação necessária
    </span>
  );
}

function LinhaAcompanhamento({ card }: { card: Card }) {
  if (card.acao_requerida) return null;
  return <div className="mt-1 text-xs italic text-gray-500">Com: {card.servidor_atual_nome}</div>;
}

function CardProcesso({ card }: { card: Card }) {
  return (
    <Link
      href={`/processos/${card.id}`}
      className={`block rounded-card border border-navy-50 p-3 text-sm shadow-card hover:bg-navy-50/40 ${classesFundoBorda(card)} ${classesAcao(card)}`}
    >
      <div className="flex items-center gap-1 font-mono text-xs text-gray-500">
        {card.numero}
        {card.sigiloso && (
          <span aria-label="Sigiloso" title="Sigiloso">
            🔒
          </span>
        )}
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-1">
        <span className="inline-block rounded bg-navy-50 px-2 py-0.5 text-xs font-medium text-navy-700">
          {card.tipo_processo_nome}
        </span>
        {card.acao_requerida && <BadgeAcaoRequerida />}
        {card.devolvido && <BadgeDevolvido />}
      </div>
      <div className="mt-1">{card.assunto}</div>
      <div className="mt-1 text-xs text-gray-500">{card.unidade_atual_nome}</div>
      <LinhaAcompanhamento card={card} />
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
      className={`flex flex-wrap items-center gap-3 rounded-card border border-navy-50 p-3 text-sm shadow-card hover:bg-navy-50/40 ${classesFundoBorda(card)} ${classesAcao(card)}`}
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
      {card.acao_requerida && <BadgeAcaoRequerida />}
      {card.devolvido && <BadgeDevolvido />}
      <div className="flex-1">{card.assunto}</div>
      <div className="text-xs text-gray-500">{card.unidade_atual_nome}</div>
      {!card.acao_requerida && (
        <div className="text-xs italic text-gray-500">Com: {card.servidor_atual_nome}</div>
      )}
      <div className="text-xs text-gray-500">{textoCriadoEm(card)}</div>
      <PillStatus status={card.status} />
    </Link>
  );
}

function BarraFiltros({
  tipos,
  filtroTipo,
  onFiltroTipo,
  assuntoInput,
  onAssuntoInput,
  dataInicial,
  onDataInicial,
  dataFinal,
  onDataFinal,
  onLimpar,
}: {
  tipos: TipoProcesso[];
  filtroTipo: string;
  onFiltroTipo: (v: string) => void;
  assuntoInput: string;
  onAssuntoInput: (v: string) => void;
  dataInicial: string;
  onDataInicial: (v: string) => void;
  dataFinal: string;
  onDataFinal: (v: string) => void;
  onLimpar: () => void;
}) {
  const temFiltro = Boolean(filtroTipo || assuntoInput || dataInicial || dataFinal);
  return (
    <div className="mt-3 flex flex-wrap items-end gap-2">
      <label className="flex flex-col text-xs text-gray-600">
        Tipo de processo
        <select
          aria-label="Filtrar por tipo de processo"
          value={filtroTipo}
          onChange={(e) => onFiltroTipo(e.target.value)}
          className="mt-0.5 rounded border px-2 py-1 text-sm"
        >
          <option value="">Todos os tipos</option>
          {tipos.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nome}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col text-xs text-gray-600">
        Assunto
        <input
          type="text"
          aria-label="Filtrar por assunto"
          placeholder="Buscar por assunto…"
          value={assuntoInput}
          onChange={(e) => onAssuntoInput(e.target.value)}
          className="mt-0.5 rounded border px-2 py-1 text-sm"
        />
      </label>
      <label className="flex flex-col text-xs text-gray-600">
        De
        <input
          type="date"
          aria-label="Data inicial"
          value={dataInicial}
          onChange={(e) => onDataInicial(e.target.value)}
          className="mt-0.5 rounded border px-2 py-1 text-sm"
        />
      </label>
      <label className="flex flex-col text-xs text-gray-600">
        Até
        <input
          type="date"
          aria-label="Data final"
          value={dataFinal}
          onChange={(e) => onDataFinal(e.target.value)}
          className="mt-0.5 rounded border px-2 py-1 text-sm"
        />
      </label>
      {temFiltro && (
        <button type="button" onClick={onLimpar} className="rounded border px-3 py-1 text-sm">
          Limpar filtros
        </button>
      )}
    </div>
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
  const [tipos, setTipos] = useState<TipoProcesso[]>([]);
  const [filtroUnidade, setFiltroUnidade] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [assuntoInput, setAssuntoInput] = useState("");
  const [filtroAssunto, setFiltroAssunto] = useState("");
  const [dataInicial, setDataInicial] = useState("");
  const [dataFinal, setDataFinal] = useState("");
  const [mensagemVazio, setMensagemVazio] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [modo, setModo] = useState<ModoVisualizacao>("kanban");
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [exibirArquivados, setExibirArquivados] = useState(false);

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
    setExibirArquivados(window.localStorage.getItem(CHAVE_EXIBIR_ARQUIVADOS) === "true");
  }, []);

  const alternarModo = useCallback((novo: ModoVisualizacao) => {
    setModo(novo);
    window.localStorage.setItem(CHAVE_MODO_VISUALIZACAO, novo);
  }, []);

  const alternarExibirArquivados = useCallback((novo: boolean) => {
    setExibirArquivados(novo);
    window.localStorage.setItem(CHAVE_EXIBIR_ARQUIVADOS, String(novo));
  }, []);

  // Debounce de 300ms do texto de assunto antes de refletir na query (D5/6.3).
  useEffect(() => {
    const timer = setTimeout(() => setFiltroAssunto(assuntoInput.trim()), DEBOUNCE_ASSUNTO_MS);
    return () => clearTimeout(timer);
  }, [assuntoInput]);

  const limparFiltros = useCallback(() => {
    setFiltroTipo("");
    setAssuntoInput("");
    setFiltroAssunto("");
    setDataInicial("");
    setDataFinal("");
  }, []);

  // Guarda contra corrida de requisições fora de ordem: alternar um filtro
  // rapidamente pode fazer uma resposta antiga (ex.: sem "Exibir Arquivados")
  // chegar depois de uma mais nova e sobrescrever o resultado correto —
  // só a resposta da última requisição disparada tem efeito no estado.
  const requisicaoAtualRef = useRef(0);

  const carregar = useCallback(async () => {
    const idRequisicao = ++requisicaoAtualRef.current;
    setCarregando(true);
    setErro(null);
    try {
      const resp = await api.listarKanban({
        ...(filtroUnidade ? { filtro_unidade: filtroUnidade } : {}),
        incluir_arquivados: exibirArquivados,
        ...(filtroTipo ? { tipo_processo_id: filtroTipo } : {}),
        ...(filtroAssunto ? { assunto: filtroAssunto } : {}),
        ...(dataInicial ? { data_inicial: dataInicial } : {}),
        ...(dataFinal ? { data_final: dataFinal } : {}),
      });
      if (idRequisicao !== requisicaoAtualRef.current) return;
      setCards(resp.items);
      setTotal(resp.total);
      setMensagemVazio(resp.total === 0 ? (resp.mensagem_vazio ?? null) : null);
    } catch (err) {
      if (idRequisicao !== requisicaoAtualRef.current) return;
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar o Kanban.");
    } finally {
      if (idRequisicao === requisicaoAtualRef.current) setCarregando(false);
    }
  }, [filtroUnidade, exibirArquivados, filtroTipo, filtroAssunto, dataInicial, dataFinal]);

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

  useEffect(() => {
    void (async () => {
      try {
        setTipos(await api.listarTiposProcesso());
      } catch {
        // filtro opcional — silencia
      }
    })();
  }, []);

  const grupos = agruparPorStatus(cards);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Processos</h1>
          <span className="text-sm text-gray-500">{total} processo(s)</span>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={exibirArquivados}
              onChange={(e) => alternarExibirArquivados(e.target.checked)}
            />
            Exibir Arquivados
          </label>
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

      <BarraFiltros
        tipos={tipos}
        filtroTipo={filtroTipo}
        onFiltroTipo={setFiltroTipo}
        assuntoInput={assuntoInput}
        onAssuntoInput={setAssuntoInput}
        dataInicial={dataInicial}
        onDataInicial={setDataInicial}
        dataFinal={dataFinal}
        onDataFinal={setDataFinal}
        onLimpar={limparFiltros}
      />

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
