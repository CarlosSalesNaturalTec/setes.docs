"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import { MOTIVOS_DEVOLUCAO, rotuloEvento, rotuloStatus } from "@/lib/processo-ui";

type Processo = Schemas["ProcessoResponse"];
type Historico = Schemas["HistoricoResponse"];
type Unidade = Schemas["UnidadeResponse"];

function ModalConclusao({
  mensagem,
  onConfirmar,
  onCancelar,
}: {
  mensagem: string;
  onConfirmar: () => void;
  onCancelar: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-label="Confirmar conclusão"
      className="fixed inset-0 flex items-center justify-center bg-black/30 p-4"
    >
      <div className="w-full max-w-sm rounded bg-white p-4 shadow-lg">
        <p className="text-sm">{mensagem}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancelar} className="rounded border px-3 py-1 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white"
          >
            Concluir processo
          </button>
        </div>
      </div>
    </div>
  );
}

function ModalDevolucao({
  onConfirmar,
  onCancelar,
}: {
  onConfirmar: (motivo: string, justificativa: string) => void;
  onCancelar: () => void;
}) {
  const [motivo, setMotivo] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  function confirmar() {
    if (!motivo) {
      setErro("Selecione um motivo para a devolução");
      return;
    }
    onConfirmar(motivo, justificativa);
  }

  return (
    <div
      role="dialog"
      aria-label="Devolver processo"
      className="fixed inset-0 flex items-center justify-center bg-black/30 p-4"
    >
      <div className="w-full max-w-sm rounded bg-white p-4 shadow-lg">
        <h2 className="text-sm font-medium">Devolver para a unidade anterior</h2>
        <label htmlFor="motivo" className="mt-3 block text-sm">
          Motivo
        </label>
        <select
          id="motivo"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          className="mt-1 w-full rounded border px-2 py-1 text-sm"
        >
          <option value="">Selecione…</option>
          {MOTIVOS_DEVOLUCAO.map((m) => (
            <option key={m.valor} value={m.valor}>
              {m.rotulo}
            </option>
          ))}
        </select>
        <label htmlFor="justificativa" className="mt-3 block text-sm">
          Justificativa (opcional)
        </label>
        <textarea
          id="justificativa"
          value={justificativa}
          onChange={(e) => setJustificativa(e.target.value)}
          className="mt-1 w-full rounded border px-2 py-1 text-sm"
          rows={3}
        />
        {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancelar} className="rounded border px-3 py-1 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={confirmar}
            className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white"
          >
            Confirmar devolução
          </button>
        </div>
      </div>
    </div>
  );
}

function DetalheConteudo({ id }: { id: string }) {
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [historico, setHistorico] = useState<Historico | null>(null);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [aba, setAba] = useState<"detalhe" | "historico">("detalhe");
  const [erro, setErro] = useState<string | null>(null);
  const [promptConclusao, setPromptConclusao] = useState<string | null>(null);
  const [mostrarDevolucao, setMostrarDevolucao] = useState(false);

  const carregar = useCallback(async () => {
    setErro(null);
    try {
      const [proc, hist] = await Promise.all([api.obterProcesso(id), api.historicoProcesso(id)]);
      setProcesso(proc);
      setHistorico(hist);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar o processo.");
    }
  }, [id]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useEffect(() => {
    void (async () => {
      try {
        setUnidades(await api.listarUnidades());
      } catch {
        // rótulos de unidade são opcionais
      }
    })();
  }, []);

  const nomeUnidade = useMemo(() => {
    const mapa = new Map(unidades.map((u) => [u.id, u.sigla]));
    return (uid: string | null) => (uid ? (mapa.get(uid) ?? uid) : "—");
  }, [unidades]);

  async function despachar(confirmar: boolean) {
    setErro(null);
    try {
      await api.despacharProcesso(id, { confirmar });
      setPromptConclusao(null);
      await carregar();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Última etapa: backend pede confirmação de conclusão (US 2.2 Cen.2/4).
        setPromptConclusao(err.detail);
        return;
      }
      setErro(err instanceof ApiError ? err.detail : "Não foi possível despachar.");
    }
  }

  async function devolver(motivo: string, justificativa: string) {
    setErro(null);
    try {
      await api.devolverProcesso(id, { motivo, justificativa: justificativa || null });
      setMostrarDevolucao(false);
      await carregar();
    } catch (err) {
      setMostrarDevolucao(false);
      setErro(err instanceof ApiError ? err.detail : "Não foi possível devolver.");
    }
  }

  if (erro && !processo) return <p className="text-sm text-red-600">{erro}</p>;
  if (!processo || !historico) return <p className="text-sm text-gray-500">Carregando…</p>;

  const concluido = processo.status === "concluido" || processo.status === "arquivado";

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-mono text-xl font-semibold">{processo.numero}</h1>
          <p className="text-sm text-gray-600">{processo.assunto}</p>
        </div>
        {!concluido && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void despachar(false)}
              className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white"
            >
              Despachar
            </button>
            <button
              type="button"
              onClick={() => setMostrarDevolucao(true)}
              className="rounded border px-3 py-1 text-sm"
            >
              Devolver
            </button>
          </div>
        )}
      </div>

      {erro && <p className="mt-3 text-sm text-red-600">{erro}</p>}

      <div className="mt-4 flex gap-4 border-b text-sm">
        <button
          type="button"
          onClick={() => setAba("detalhe")}
          className={`pb-2 ${aba === "detalhe" ? "border-b-2 border-blue-600 font-medium" : "text-gray-500"}`}
        >
          Detalhes
        </button>
        <button
          type="button"
          onClick={() => setAba("historico")}
          className={`pb-2 ${aba === "historico" ? "border-b-2 border-blue-600 font-medium" : "text-gray-500"}`}
        >
          Histórico
        </button>
      </div>

      {aba === "detalhe" ? (
        <div className="mt-4 space-y-4">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-gray-500">Status</dt>
            <dd>{rotuloStatus(processo.status)}</dd>
            <dt className="text-gray-500">Unidade atual</dt>
            <dd>{nomeUnidade(processo.unidade_atual_id)}</dd>
            <dt className="text-gray-500">Prazo</dt>
            <dd>{processo.prazo_em}</dd>
          </dl>

          <section>
            <h2 className="text-sm font-medium">Interessados</h2>
            {(processo.interessados ?? []).length === 0 ? (
              <p className="mt-1 text-sm text-gray-500">Nenhum interessado cadastrado.</p>
            ) : (
              <ul className="mt-1 text-sm">
                {(processo.interessados ?? []).map((i) => (
                  <li key={i.id}>
                    {i.nome}
                    {i.documento && ` — ${i.documento}`}
                    {i.tipo_participacao && ` (${i.tipo_participacao})`}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : (
        <div className="mt-4">
          {(historico.eventos ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">
              {historico.mensagem_vazio} — criado em {historico.criado_em}
            </p>
          ) : (
            <ol className="space-y-2 text-sm">
              {(historico.eventos ?? []).map((e) => (
                <li key={e.id} className="rounded border p-2">
                  <div className="font-medium">{rotuloEvento(e.tipo_evento)}</div>
                  <div className="text-gray-600">
                    {nomeUnidade(e.unidade_origem_id)} → {nomeUnidade(e.unidade_destino_id)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {e.criado_em} · {rotuloStatus(e.status_resultante)}
                  </div>
                  {e.motivo && <div className="text-xs text-gray-500">Motivo: {e.motivo}</div>}
                  {e.justificativa && (
                    <div className="text-xs text-gray-500">Justificativa: {e.justificativa}</div>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {promptConclusao && (
        <ModalConclusao
          mensagem={promptConclusao}
          onConfirmar={() => void despachar(true)}
          onCancelar={() => setPromptConclusao(null)}
        />
      )}
      {mostrarDevolucao && (
        <ModalDevolucao onConfirmar={devolver} onCancelar={() => setMostrarDevolucao(false)} />
      )}
    </div>
  );
}

export default function DetalheProcessoPage() {
  const params = useParams<{ id: string }>();
  return (
    <ProtectedShell>
      <DetalheConteudo id={params.id} />
    </ProtectedShell>
  );
}
