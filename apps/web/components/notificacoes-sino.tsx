"use client";

// Sino de notificações internas (Épico 5, US 5.1/5.3/5.4). Sem push/websocket
// no MVP (design.md) — revalida ao focar a aba e ao abrir o painel. Abrir o
// painel NÃO marca como lida (US 5.1 Cen.2) — só a ação explícita decrementa
// o contador.
import { useCallback, useEffect, useRef, useState } from "react";

import { api, type Schemas } from "@/lib/api";

type Notificacao = Schemas["NotificacaoResponse"];

function descricaoTipo(notificacao: Notificacao): string {
  switch (notificacao.tipo) {
    case "novo_processo":
      return notificacao.unidade_origem_nome
        ? `Novo processo recebido, vindo de ${notificacao.unidade_origem_nome}`
        : "Novo processo recebido";
    case "concluido":
      return "Processo concluído";
    case "alerta_prazo":
      return "Prazo próximo";
    case "reatribuido_para_voce":
      return "Reatribuído para você";
    case "destino_corrigido":
      return "Destino da tramitação corrigido";
    default:
      return notificacao.tipo;
  }
}

export function NotificacoesSino() {
  const [contador, setContador] = useState(0);
  const [aberto, setAberto] = useState(false);
  const [itens, setItens] = useState<Notificacao[]>([]);
  const [carregando, setCarregando] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const recarregarContador = useCallback(async () => {
    try {
      const resp = await api.contarNotificacoes();
      setContador(resp.nao_lidas);
    } catch {
      // silencioso — falha transitória não deve quebrar a navegação
    }
  }, []);

  const recarregarLista = useCallback(async () => {
    setCarregando(true);
    try {
      const resp = await api.listarNotificacoes();
      setItens(resp.items ?? []);
    } catch {
      // silencioso
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void recarregarContador();
    function aoFocar() {
      void recarregarContador();
    }
    window.addEventListener("focus", aoFocar);
    return () => window.removeEventListener("focus", aoFocar);
  }, [recarregarContador]);

  useEffect(() => {
    if (aberto) void recarregarLista();
  }, [aberto, recarregarLista]);

  useEffect(() => {
    function aoClicarFora(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setAberto(false);
      }
    }
    document.addEventListener("mousedown", aoClicarFora);
    return () => document.removeEventListener("mousedown", aoClicarFora);
  }, []);

  async function marcarLida(id: string) {
    try {
      await api.marcarNotificacaoLida(id);
      const agora = new Date().toISOString();
      setItens((atual) => atual.map((n) => (n.id === id ? { ...n, lida_em: agora } : n)));
      setContador((atual) => Math.max(0, atual - 1));
    } catch {
      // silencioso
    }
  }

  async function marcarTodasLidas() {
    try {
      await api.marcarTodasNotificacoesLidas();
      const agora = new Date().toISOString();
      setItens((atual) => atual.map((n) => ({ ...n, lida_em: n.lida_em ?? agora })));
      setContador(0);
    } catch {
      // silencioso
    }
  }

  const naoLidas = itens.filter((n) => n.lida_em === null).length;

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        aria-label="Notificações"
        onClick={() => setAberto((v) => !v)}
        className="relative rounded p-1.5 hover:bg-gray-100"
      >
        <span aria-hidden>🔔</span>
        {contador > 0 && (
          <span
            data-testid="notificacoes-contador"
            className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white"
          >
            {contador}
          </span>
        )}
      </button>
      {aberto && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded border bg-white shadow-lg">
          <div className="flex items-center justify-between border-b p-2 text-sm">
            <span className="font-medium">Notificações</span>
            <button
              type="button"
              onClick={() => void marcarTodasLidas()}
              disabled={naoLidas === 0}
              className="text-xs text-blue-600 hover:underline disabled:text-gray-400 disabled:no-underline"
            >
              Marcar todas como lidas
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {carregando && <p className="p-3 text-xs text-gray-500">Carregando…</p>}
            {!carregando && itens.length === 0 && (
              <p className="p-3 text-xs text-gray-500">Nenhuma notificação encontrada</p>
            )}
            {itens.map((notificacao) => (
              <button
                key={notificacao.id}
                type="button"
                onClick={() => void marcarLida(notificacao.id)}
                className={`block w-full border-b p-3 text-left text-sm last:border-b-0 hover:bg-gray-50 ${
                  notificacao.lida_em ? "bg-white" : "bg-blue-50"
                }`}
              >
                <div className="flex items-center gap-2">
                  {notificacao.lida_em === null && (
                    <span
                      aria-label="não lida"
                      className="h-2 w-2 shrink-0 rounded-full bg-blue-600"
                    />
                  )}
                  <span className="font-medium">{notificacao.numero_processo}</span>
                </div>
                <p className="text-gray-700">{notificacao.assunto}</p>
                <p className="text-xs text-gray-500">{descricaoTipo(notificacao)}</p>
                {notificacao.justificativa && (
                  <p className="text-xs text-gray-500">{notificacao.justificativa}</p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
