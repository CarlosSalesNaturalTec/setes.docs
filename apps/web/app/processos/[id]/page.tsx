"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";
import { MOTIVOS_DEVOLUCAO, rotuloEvento, rotuloStatus } from "@/lib/processo-ui";

import { DocumentosSection } from "./documentos-section";

type Processo = Schemas["ProcessoResponse"];
type Historico = Schemas["HistoricoResponse"];
type Unidade = Schemas["UnidadeResponse"];
type Setor = Schemas["SetorResponse"];
type ServidorResumo = Schemas["UsuarioResumoResponse"];

type TipoAcaoTramitacao = "enviar" | "devolver" | "reatribuir";

function ModalConclusao({
  onConfirmar,
  onCancelar,
}: {
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
        <p className="text-sm">Deseja concluir este processo?</p>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancelar} className="rounded border px-3 py-1 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            className="rounded-card bg-navy-900 px-3 py-1 text-sm font-medium text-white"
          >
            Concluir processo
          </button>
        </div>
      </div>
    </div>
  );
}

function useSetoresDaUnidade(unidadeId: string | null) {
  const [setores, setSetores] = useState<Setor[]>([]);
  useEffect(() => {
    if (!unidadeId) {
      setSetores([]);
      return;
    }
    let ativo = true;
    void (async () => {
      try {
        const lista = await api.listarSetores(unidadeId, true);
        if (ativo) setSetores(lista);
      } catch {
        if (ativo) setSetores([]);
      }
    })();
    return () => {
      ativo = false;
    };
  }, [unidadeId]);
  return setores;
}

function useServidoresDoSetor(setorId: string | null) {
  const [servidores, setServidores] = useState<ServidorResumo[]>([]);
  useEffect(() => {
    if (!setorId) {
      setServidores([]);
      return;
    }
    let ativo = true;
    void (async () => {
      try {
        const lista = await api.listarServidoresAtivosPorSetor(setorId);
        if (ativo) setServidores(lista);
      } catch {
        if (ativo) setServidores([]);
      }
    })();
    return () => {
      ativo = false;
    };
  }, [setorId]);
  return servidores;
}

function ModalTramitacao({
  processo,
  unidades,
  permitirEnvioDevolucao,
  onConfirmarEnvio,
  onConfirmarDevolucao,
  onConfirmarReatribuicao,
  onCancelar,
}: {
  processo: Processo;
  unidades: Unidade[];
  // Change migracao-regiao-us-central1 (tasks.md 6.5) — Envio e Devolução são
  // exclusivos do Servidor no backend (`_require_servidor` em
  // routers/processos.py); o Gestor só reatribui e conclui.
  permitirEnvioDevolucao: boolean;
  onConfirmarEnvio: (body: Schemas["EnviarRequest"]) => Promise<void>;
  onConfirmarDevolucao: (motivo: string, justificativa: string) => Promise<void>;
  onConfirmarReatribuicao: (body: Schemas["ReatribuirRequest"]) => Promise<void>;
  onCancelar: () => void;
}) {
  const [tipoAcao, setTipoAcao] = useState<TipoAcaoTramitacao>(
    permitirEnvioDevolucao ? "enviar" : "reatribuir",
  );
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Envio: unidade → setor → servidor em cascata, mais mensagem.
  const [unidadeDestino, setUnidadeDestino] = useState("");
  const [setorEnvio, setSetorEnvio] = useState("");
  const [servidorEnvio, setServidorEnvio] = useState("");
  const [mensagem, setMensagem] = useState("");
  const setoresEnvio = useSetoresDaUnidade(unidadeDestino || null);
  const servidoresEnvio = useServidoresDoSetor(setorEnvio || null);

  // Devolução: destino resolvido pelo backend — só motivo + justificativa.
  const [motivo, setMotivo] = useState("");
  const [justificativaDevolucao, setJustificativaDevolucao] = useState("");

  // Reatribuição: unidade FIXA (a atual) — setor → servidor + justificativa.
  const [setorReatribuicao, setSetorReatribuicao] = useState("");
  const [servidorReatribuicao, setServidorReatribuicao] = useState("");
  const [justificativaReatribuicao, setJustificativaReatribuicao] = useState("");
  const setoresReatribuicao = useSetoresDaUnidade(processo.unidade_atual_id);
  const servidoresReatribuicao = useServidoresDoSetor(setorReatribuicao || null);

  const nomeUnidadeAtual =
    unidades.find((u) => u.id === processo.unidade_atual_id)?.nome ?? processo.unidade_atual_id;

  async function confirmar() {
    setErro(null);
    setEnviando(true);
    try {
      if (tipoAcao === "enviar") {
        if (!unidadeDestino || !setorEnvio || !servidorEnvio) {
          setErro("Selecione unidade, setor e servidor de destino.");
          return;
        }
        if (servidorEnvio === processo.servidor_atual_id) {
          setErro("O destino deve ser um servidor diferente do responsável atual.");
          return;
        }
        await onConfirmarEnvio({
          unidade_destino_id: unidadeDestino,
          setor_destino_id: setorEnvio,
          servidor_destino_id: servidorEnvio,
          mensagem: mensagem || null,
        });
      } else if (tipoAcao === "devolver") {
        if (!motivo) {
          setErro("Selecione um motivo para a devolução");
          return;
        }
        await onConfirmarDevolucao(motivo, justificativaDevolucao);
      } else {
        if (!setorReatribuicao || !servidorReatribuicao) {
          setErro("Selecione setor e servidor de destino.");
          return;
        }
        if (servidorReatribuicao === processo.servidor_atual_id) {
          setErro("O destino deve ser um servidor diferente do responsável atual.");
          return;
        }
        if (!justificativaReatribuicao.trim()) {
          setErro("Informe a justificativa da reatribuição.");
          return;
        }
        await onConfirmarReatribuicao({
          setor_destino_id: setorReatribuicao,
          servidor_destino_id: servidorReatribuicao,
          justificativa: justificativaReatribuicao,
        });
      }
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível concluir a ação.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-label={permitirEnvioDevolucao ? "Tramitar processo" : "Reatribuir processo"}
      className="fixed inset-0 flex items-center justify-center bg-black/30 p-4"
    >
      <div className="w-full max-w-md rounded bg-white p-4 shadow-lg">
        <h2 className="text-sm font-medium">
          {permitirEnvioDevolucao ? "Tramitar processo" : "Reatribuir processo"}
        </h2>

        {permitirEnvioDevolucao && (
          <>
            <label htmlFor="tipo-acao" className="mt-3 block text-sm">
              Tipo de ação
            </label>
            <select
              id="tipo-acao"
              value={tipoAcao}
              onChange={(e) => setTipoAcao(e.target.value as TipoAcaoTramitacao)}
              className="mt-1 w-full rounded border px-2 py-1 text-sm"
            >
              <option value="enviar">Envio</option>
              <option value="devolver">Devolução</option>
              <option value="reatribuir">Reatribuir</option>
            </select>
          </>
        )}

        {tipoAcao === "enviar" && (
          <div className="mt-3 space-y-3">
            <div>
              <label htmlFor="unidade-destino" className="block text-sm">
                Unidade de destino
              </label>
              <select
                id="unidade-destino"
                value={unidadeDestino}
                onChange={(e) => {
                  setUnidadeDestino(e.target.value);
                  setSetorEnvio("");
                  setServidorEnvio("");
                }}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              >
                <option value="">Selecione…</option>
                {unidades
                  .filter((u) => u.ativo)
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nome}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label htmlFor="setor-envio" className="block text-sm">
                Setor de destino
              </label>
              <select
                id="setor-envio"
                value={setorEnvio}
                onChange={(e) => {
                  setSetorEnvio(e.target.value);
                  setServidorEnvio("");
                }}
                disabled={!unidadeDestino}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              >
                <option value="">Selecione…</option>
                {setoresEnvio.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="servidor-envio" className="block text-sm">
                Servidor de destino
              </label>
              <select
                id="servidor-envio"
                value={servidorEnvio}
                onChange={(e) => setServidorEnvio(e.target.value)}
                disabled={!setorEnvio}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              >
                <option value="">Selecione…</option>
                {servidoresEnvio.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="mensagem-envio" className="block text-sm">
                Mensagem
              </label>
              <textarea
                id="mensagem-envio"
                value={mensagem}
                onChange={(e) => setMensagem(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              />
            </div>
          </div>
        )}

        {tipoAcao === "devolver" && (
          <div className="mt-3 space-y-3">
            <p className="rounded bg-gray-100 p-2 text-sm text-gray-600">
              O processo será devolvido automaticamente para quem o enviou.
            </p>
            <div>
              <label htmlFor="motivo" className="block text-sm">
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
            </div>
            <div>
              <label htmlFor="justificativa-devolucao" className="block text-sm">
                Justificativa (opcional)
              </label>
              <textarea
                id="justificativa-devolucao"
                value={justificativaDevolucao}
                onChange={(e) => setJustificativaDevolucao(e.target.value)}
                rows={3}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              />
            </div>
          </div>
        )}

        {tipoAcao === "reatribuir" && (
          <div className="mt-3 space-y-3">
            <div>
              <label htmlFor="unidade-reatribuicao" className="block text-sm">
                Unidade
              </label>
              <input
                id="unidade-reatribuicao"
                value={nomeUnidadeAtual}
                readOnly
                disabled
                className="mt-1 w-full rounded border bg-gray-100 px-2 py-1 text-sm text-gray-600"
              />
            </div>
            <div>
              <label htmlFor="setor-reatribuicao" className="block text-sm">
                Setor de destino
              </label>
              <select
                id="setor-reatribuicao"
                value={setorReatribuicao}
                onChange={(e) => {
                  setSetorReatribuicao(e.target.value);
                  setServidorReatribuicao("");
                }}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              >
                <option value="">Selecione…</option>
                {setoresReatribuicao.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="servidor-reatribuicao" className="block text-sm">
                Servidor de destino
              </label>
              <select
                id="servidor-reatribuicao"
                value={servidorReatribuicao}
                onChange={(e) => setServidorReatribuicao(e.target.value)}
                disabled={!setorReatribuicao}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              >
                <option value="">Selecione…</option>
                {servidoresReatribuicao.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="justificativa-reatribuicao" className="block text-sm">
                Justificativa
              </label>
              <textarea
                id="justificativa-reatribuicao"
                value={justificativaReatribuicao}
                onChange={(e) => setJustificativaReatribuicao(e.target.value)}
                rows={3}
                className="mt-1 w-full rounded border px-2 py-1 text-sm"
              />
            </div>
          </div>
        )}

        {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancelar} className="rounded border px-3 py-1 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => void confirmar()}
            disabled={enviando}
            className="rounded-card bg-navy-900 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
          >
            {tipoAcao === "enviar" && "Enviar"}
            {tipoAcao === "devolver" && "Confirmar devolução"}
            {tipoAcao === "reatribuir" && "Reatribuir"}
          </button>
        </div>
      </div>
    </div>
  );
}

function DetalheConteudo({ id }: { id: string }) {
  const router = useRouter();
  const { usuario } = useAuth();
  const ehServidor = usuario?.perfil === "servidor";
  // Change migracao-regiao-us-central1 (tasks.md 6.5) — Reatribuir e Concluir
  // também são permitidos ao Gestor da unidade (D5 do change tramitacao-manual);
  // a checagem de qual unidade é feita pelo backend (`require_acesso_unidade`).
  const ehGestor = usuario?.perfil === "gestor";
  const podeTramitarOuConcluir = ehServidor || ehGestor;
  const [processo, setProcesso] = useState<Processo | null>(null);
  // Change visibilidade-processos-origem (design D2/D5) — Servidor fora da
  // unidade atual do processo (acompanhamento por origem, sem sigilo) vê o
  // acompanhamento em modo leitura: sem Tramitar/Concluir/sigilo/anexos.
  const somenteLeitura =
    ehServidor && !!processo && usuario?.unidade_id !== processo.unidade_atual_id;
  const [historico, setHistorico] = useState<Historico | null>(null);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [aba, setAba] = useState<"detalhe" | "documentos" | "historico">("detalhe");
  const [erro, setErro] = useState<string | null>(null);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);
  const [mostrarConclusao, setMostrarConclusao] = useState(false);
  const [mostrarTramitacao, setMostrarTramitacao] = useState(false);
  const [alterandoSigilo, setAlterandoSigilo] = useState(false);

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

  async function irParaKanbanComSucesso(acao: "envio" | "devolucao", unidadeDestinoId: string | null) {
    const params = new URLSearchParams({ acao, destino: nomeUnidade(unidadeDestinoId) });
    router.push(`/processos?${params.toString()}`);
  }

  async function enviar(body: Schemas["EnviarRequest"]) {
    const unidadeAnterior = processo?.unidade_atual_id ?? null;
    const resposta = await api.enviarProcesso(id, body);
    setMostrarTramitacao(false);
    if (resposta.unidade_atual_id !== unidadeAnterior) {
      // O processo saiu do escopo da unidade: navegar sem reler o detalhe
      // (uma releitura aqui retornaria 403).
      await irParaKanbanComSucesso("envio", resposta.unidade_atual_id);
      return;
    }
    setProcesso(resposta);
    try {
      setHistorico(await api.historicoProcesso(id));
    } catch {
      // atualização do histórico é best-effort — o envio já foi concluído
    }
  }

  async function devolver(motivo: string, justificativa: string) {
    const unidadeAnterior = processo?.unidade_atual_id ?? null;
    const resposta = await api.devolverProcesso(id, { motivo, justificativa: justificativa || null });
    setMostrarTramitacao(false);
    if (resposta.unidade_atual_id !== unidadeAnterior) {
      await irParaKanbanComSucesso("devolucao", resposta.unidade_atual_id);
      return;
    }
    setProcesso(resposta);
    try {
      setHistorico(await api.historicoProcesso(id));
    } catch {
      // atualização do histórico é best-effort — a devolução já foi concluída
    }
  }

  async function reatribuir(body: Schemas["ReatribuirRequest"]) {
    const resposta = await api.reatribuirProcesso(id, body);
    setMostrarTramitacao(false);
    // Reatribuição nunca muda de unidade (D2/D9) — permanece na tela.
    setProcesso(resposta);
    setMensagemSucesso("Processo reatribuído. O prazo foi mantido.");
    try {
      setHistorico(await api.historicoProcesso(id));
    } catch {
      // atualização do histórico é best-effort — a reatribuição já foi concluída
    }
  }

  async function concluir() {
    setErro(null);
    try {
      const resposta = await api.concluirProcesso(id);
      setMostrarConclusao(false);
      setProcesso(resposta);
      try {
        setHistorico(await api.historicoProcesso(id));
      } catch {
        // atualização do histórico é best-effort — a conclusão já foi concluída
      }
    } catch (err) {
      setMostrarConclusao(false);
      setErro(err instanceof ApiError ? err.detail : "Não foi possível concluir.");
    }
  }

  async function alternarSigilo(marcar: boolean) {
    setErro(null);
    setAlterandoSigilo(true);
    try {
      if (marcar) {
        await api.marcarSigilo(id);
      } else {
        await api.removerSigilo(id);
      }
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível alterar o sigilo.");
    } finally {
      setAlterandoSigilo(false);
    }
  }

  if (erro && !processo) return <p className="text-sm text-red-600">{erro}</p>;
  if (!processo || !historico) return <p className="text-sm text-gray-500">Carregando…</p>;

  const concluido = processo.status === "concluido" || processo.status === "arquivado";

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 font-mono text-xl font-semibold">
            {processo.numero}
            {processo.sigiloso && (
              <span aria-label="Sigiloso" title="Sigiloso">
                🔒
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-600">{processo.assunto}</p>
        </div>
        <div className="flex gap-2">
          {podeTramitarOuConcluir && !concluido && !somenteLeitura && (
            <>
              <button
                type="button"
                onClick={() => setMostrarTramitacao(true)}
                className="rounded-card bg-navy-900 px-3 py-1 text-sm font-medium text-white"
              >
                {ehServidor ? "Tramitar" : "Reatribuir"}
              </button>
              <button
                type="button"
                onClick={() => setMostrarConclusao(true)}
                className="rounded border px-3 py-1 text-sm"
              >
                Concluir
              </button>
            </>
          )}
          {ehServidor &&
            !somenteLeitura &&
            (processo.sigiloso ? (
              <button
                type="button"
                onClick={() => void alternarSigilo(false)}
                disabled={alterandoSigilo}
                className="rounded border px-3 py-1 text-sm"
              >
                Remover Sigilo
              </button>
            ) : (
              <button
                type="button"
                onClick={() => void alternarSigilo(true)}
                disabled={alterandoSigilo}
                className="rounded border px-3 py-1 text-sm"
              >
                Marcar como Sigiloso
              </button>
            ))}
        </div>
      </div>

      {erro && <p className="mt-3 text-sm text-red-600">{erro}</p>}
      {mensagemSucesso && <p className="mt-3 text-sm text-green-700">{mensagemSucesso}</p>}
      {somenteLeitura && (
        <p className="mt-3 rounded bg-gray-100 p-2 text-sm text-gray-600">
          Acompanhamento em modo leitura — este processo está atualmente em outra unidade.
        </p>
      )}

      <div className="mt-4 flex gap-4 border-b text-sm">
        <button
          type="button"
          onClick={() => setAba("detalhe")}
          className={`pb-2 ${aba === "detalhe" ? "border-b-2 border-navy-600 font-medium" : "text-gray-500"}`}
        >
          Detalhes
        </button>
        <button
          type="button"
          onClick={() => setAba("documentos")}
          className={`pb-2 ${aba === "documentos" ? "border-b-2 border-navy-600 font-medium" : "text-gray-500"}`}
        >
          Documentos
        </button>
        <button
          type="button"
          onClick={() => setAba("historico")}
          className={`pb-2 ${aba === "historico" ? "border-b-2 border-navy-600 font-medium" : "text-gray-500"}`}
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
      ) : aba === "documentos" ? (
        <div className="mt-4">
          <DocumentosSection
            processoId={processo.id}
            status={processo.status}
            eventos={historico.eventos ?? []}
            somenteLeitura={somenteLeitura}
          />
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
                <li key={e.id} className="rounded-card border border-navy-50 bg-superficie-card p-2 shadow-card">
                  <div className="font-medium">{rotuloEvento(e.tipo_evento)}</div>
                  <div className="text-gray-600">
                    {nomeUnidade(e.unidade_origem_id)} → {nomeUnidade(e.unidade_destino_id)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {e.criado_em} · {rotuloStatus(e.status_resultante)}
                  </div>
                  {e.mensagem && <div className="text-xs text-gray-500">Mensagem: {e.mensagem}</div>}
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

      {mostrarConclusao && (
        <ModalConclusao onConfirmar={() => void concluir()} onCancelar={() => setMostrarConclusao(false)} />
      )}
      {mostrarTramitacao && (
        <ModalTramitacao
          processo={processo}
          unidades={unidades}
          permitirEnvioDevolucao={ehServidor}
          onConfirmarEnvio={enviar}
          onConfirmarDevolucao={devolver}
          onConfirmarReatribuicao={reatribuir}
          onCancelar={() => setMostrarTramitacao(false)}
        />
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
