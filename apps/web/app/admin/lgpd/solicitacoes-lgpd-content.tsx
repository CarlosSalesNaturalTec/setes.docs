"use client";

import { useEffect, useState } from "react";

import { ApiError, api, type Schemas } from "@/lib/api";

type SolicitacaoLgpd = Schemas["SolicitacaoLgpdResponse"];

const ROTULO_TIPO: Record<string, string> = {
  exclusao: "Exclusão de dados",
  anonimizacao: "Anonimização de dados",
};

const ROTULO_STATUS: Record<string, string> = {
  pendente: "Pendente",
  em_analise: "Em análise",
  atendida: "Atendida",
  rejeitada: "Rejeitada",
};

function formatarDataHora(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR");
}

function ModalJustificativa({
  solicitacao,
  onConfirmar,
  onCancelar,
  processando,
}: {
  solicitacao: SolicitacaoLgpd;
  onConfirmar: (justificativa: string) => void;
  onCancelar: () => void;
  processando: boolean;
}) {
  const [justificativa, setJustificativa] = useState("");

  return (
    <div
      role="dialog"
      aria-label="Rejeitar solicitação"
      className="fixed inset-0 z-10 flex items-center justify-center bg-black/40"
    >
      <div className="w-full max-w-md rounded bg-white p-6 shadow-lg">
        <h2 className="text-lg font-medium">Rejeitar solicitação {solicitacao.protocolo}</h2>
        <label className="mt-3 block text-sm font-medium" htmlFor="justificativa">
          Justificativa
        </label>
        <textarea
          id="justificativa"
          className="mt-1 w-full rounded border px-3 py-2 text-sm"
          rows={3}
          value={justificativa}
          onChange={(e) => setJustificativa(e.target.value)}
        />
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancelar}
            disabled={processando}
            className="rounded border px-3 py-2 text-sm"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => onConfirmar(justificativa)}
            disabled={processando || justificativa.trim() === ""}
            className="rounded bg-red-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {processando ? "Rejeitando…" : "Rejeitar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function SolicitacoesLgpdConteudo() {
  const [solicitacoes, setSolicitacoes] = useState<SolicitacaoLgpd[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [processandoId, setProcessandoId] = useState<string | null>(null);
  const [rejeitando, setRejeitando] = useState<SolicitacaoLgpd | null>(null);

  async function carregar() {
    setCarregando(true);
    try {
      const resposta = await api.listarSolicitacoesLgpd();
      setSolicitacoes(resposta.items ?? []);
      setErro(null);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar as solicitações.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  async function atender(solicitacao: SolicitacaoLgpd) {
    setProcessandoId(solicitacao.id);
    setErro(null);
    try {
      await api.atenderSolicitacaoLgpd(solicitacao.id);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível atender a solicitação.");
    } finally {
      setProcessandoId(null);
    }
  }

  async function rejeitar(solicitacao: SolicitacaoLgpd, justificativa: string) {
    setProcessandoId(solicitacao.id);
    setErro(null);
    try {
      await api.rejeitarSolicitacaoLgpd(solicitacao.id, { justificativa });
      setRejeitando(null);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível rejeitar a solicitação.");
    } finally {
      setProcessandoId(null);
    }
  }

  const acionavel = (s: SolicitacaoLgpd) => s.status === "pendente" || s.status === "em_analise";

  return (
    <div>
      <h1 className="text-2xl font-semibold">Solicitações LGPD</h1>
      <p className="mt-1 text-sm text-gray-600">
        Fila de solicitações de exclusão/anonimização registradas pelo canal público.
      </p>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {!carregando && solicitacoes.length === 0 && (
        <p className="mt-6 text-sm text-gray-500">Nenhuma solicitação registrada</p>
      )}

      {solicitacoes.length > 0 && (
        <table className="mt-6 w-full overflow-hidden rounded-card border border-navy-50 text-left text-sm shadow-card">
          <thead>
            <tr className="border-b text-gray-500">
              <th className="py-2 pr-4 font-medium">Protocolo</th>
              <th className="py-2 pr-4 font-medium">Data</th>
              <th className="py-2 pr-4 font-medium">Solicitante</th>
              <th className="py-2 pr-4 font-medium">Processo</th>
              <th className="py-2 pr-4 font-medium">Tipo</th>
              <th className="py-2 pr-4 font-medium">Status</th>
              <th className="py-2 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody>
            {solicitacoes.map((s) => (
              <tr key={s.id} className="border-b">
                <td className="py-2 pr-4 font-mono text-xs">{s.protocolo}</td>
                <td className="py-2 pr-4">{formatarDataHora(s.criado_em)}</td>
                <td className="py-2 pr-4">{s.nome_solicitante}</td>
                <td className="py-2 pr-4">{s.processo_numero}</td>
                <td className="py-2 pr-4">{ROTULO_TIPO[s.tipo] ?? s.tipo}</td>
                <td className="py-2 pr-4">{ROTULO_STATUS[s.status] ?? s.status}</td>
                <td className="py-2">
                  {acionavel(s) && (
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => void atender(s)}
                        disabled={processandoId === s.id}
                        className="text-navy-600 disabled:opacity-50"
                      >
                        Atender
                      </button>
                      <button
                        type="button"
                        onClick={() => setRejeitando(s)}
                        disabled={processandoId === s.id}
                        className="text-red-600 disabled:opacity-50"
                      >
                        Rejeitar
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {rejeitando && (
        <ModalJustificativa
          solicitacao={rejeitando}
          processando={processandoId === rejeitando.id}
          onConfirmar={(justificativa) => void rejeitar(rejeitando, justificativa)}
          onCancelar={() => setRejeitando(null)}
        />
      )}
    </div>
  );
}
