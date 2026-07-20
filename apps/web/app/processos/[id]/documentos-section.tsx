"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, api, type Schemas } from "@/lib/api";

type Documento = Schemas["DocumentoResponse"];
type EventoHistorico = Schemas["EventoHistoricoResponse"];

// Espelha `_MIME_INLINE` de `routers/documentos.py` — PDF/imagem abrem inline
// (US 3.2 Cen.1); os demais (DOC/DOCX) disparam download automático (Cen.3).
const MIME_INLINE = new Set(["application/pdf", "image/jpeg", "image/png"]);
const AVISO_SEM_INLINE = "Formato não permite visualização inline — o download será iniciado";

function formatarTamanho(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Espelha `services/documento.pode_remover` (D1): a UI não decide sozinha —
// reflete a mesma regra de custódia lida do histórico já carregado pela página.
export function podeRemoverDocumento(status: string, eventos: EventoHistorico[]): boolean {
  if (status === "aberto") return true;
  if (status !== "em_tramitacao") return false;
  const movimentos = eventos.filter(
    (e) => e.tipo_evento === "despacho" || e.tipo_evento === "devolucao",
  );
  if (movimentos.length === 0) return false;
  return movimentos[movimentos.length - 1].tipo_evento === "devolucao";
}

function dispararDownload(blob: Blob, nomeArquivo: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function ModalConfirmarRemocao({
  nome,
  onConfirmar,
  onCancelar,
}: {
  nome: string;
  onConfirmar: () => void;
  onCancelar: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-label="Remover documento"
      className="fixed inset-0 flex items-center justify-center bg-black/30 p-4"
    >
      <div className="w-full max-w-sm rounded bg-white p-4 shadow-lg">
        <p className="text-sm">
          Remover o documento &quot;{nome}&quot;? O arquivo ficará em retenção por 30 dias.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancelar} className="rounded border px-3 py-1 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            className="rounded bg-red-600 px-3 py-1 text-sm font-medium text-white"
          >
            Remover
          </button>
        </div>
      </div>
    </div>
  );
}

function ModalVisualizacao({
  documento,
  url,
  onFechar,
}: {
  documento: Documento;
  url: string;
  onFechar: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-label={`Visualizar ${documento.nome_exibicao}`}
      className="fixed inset-0 flex items-center justify-center bg-black/30 p-4"
    >
      <div className="flex h-[80vh] w-full max-w-3xl flex-col rounded bg-white p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium">{documento.nome_exibicao}</h2>
          <button type="button" onClick={onFechar} className="rounded border px-2 py-1 text-sm">
            Fechar
          </button>
        </div>
        <div className="mt-3 flex-1 overflow-auto">
          {documento.tipo_conteudo === "application/pdf" ? (
            <iframe title={documento.nome_exibicao} src={url} className="h-full w-full" />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element -- blob: URL, next/image não se aplica
            <img src={url} alt={documento.nome_exibicao} className="max-h-full max-w-full" />
          )}
        </div>
      </div>
    </div>
  );
}

export function DocumentosSection({
  processoId,
  status,
  eventos,
}: {
  processoId: string;
  status: string;
  eventos: EventoHistorico[];
}) {
  const [documentos, setDocumentos] = useState<Documento[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [remocaoPendente, setRemocaoPendente] = useState<Documento | null>(null);
  const [visualizando, setVisualizando] = useState<{ documento: Documento; url: string } | null>(
    null,
  );

  const carregar = useCallback(async () => {
    try {
      const resp = await api.listarDocumentos(processoId);
      setDocumentos(resp.items ?? []);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível carregar os documentos.");
    }
  }, [processoId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const podeRemover = podeRemoverDocumento(status, eventos);

  async function anexar(arquivo: File) {
    setErro(null);
    setEnviando(true);
    try {
      await api.anexarDocumento(processoId, arquivo);
      await carregar();
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível anexar o documento.");
    } finally {
      setEnviando(false);
    }
  }

  // Não mexe em `erro` — usado tanto pelo botão "Baixar" (que limpa antes)
  // quanto pelo aviso de DOC/DOCX (que precisa manter a mensagem exibida).
  async function realizarDownload(documento: Documento) {
    try {
      const { blob, nomeArquivo } = await api.baixarDocumento(processoId, documento.id);
      dispararDownload(blob, nomeArquivo);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível baixar o documento.");
    }
  }

  async function baixar(documento: Documento) {
    setErro(null);
    await realizarDownload(documento);
  }

  async function abrir(documento: Documento) {
    setErro(null);
    if (!MIME_INLINE.has(documento.tipo_conteudo)) {
      // US 3.2 Cen.3 — DOC/DOCX: avisa e dispara o download automaticamente.
      setErro(AVISO_SEM_INLINE);
      await realizarDownload(documento);
      return;
    }
    try {
      const { blob } = await api.conteudoDocumento(processoId, documento.id);
      setVisualizando({ documento, url: URL.createObjectURL(blob) });
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível visualizar o documento.");
    }
  }

  function fecharVisualizacao() {
    if (visualizando) URL.revokeObjectURL(visualizando.url);
    setVisualizando(null);
  }

  async function confirmarRemocao() {
    if (!remocaoPendente) return;
    setErro(null);
    try {
      await api.removerDocumento(processoId, remocaoPendente.id);
      setRemocaoPendente(null);
      await carregar();
    } catch (err) {
      setRemocaoPendente(null);
      setErro(err instanceof ApiError ? err.detail : "Não foi possível remover o documento.");
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium">Documentos</h2>
        <label className="cursor-pointer rounded-card bg-navy-900 px-3 py-1 text-sm font-medium text-white">
          {enviando ? "Enviando…" : "Anexar Documento"}
          <input
            type="file"
            className="hidden"
            disabled={enviando}
            aria-label="Anexar Documento"
            onChange={(e) => {
              const arquivo = e.target.files?.[0];
              e.target.value = "";
              if (arquivo) void anexar(arquivo);
            }}
          />
        </label>
      </div>

      {erro && <p className="mt-2 text-sm text-red-600">{erro}</p>}

      {documentos === null ? (
        <p className="mt-2 text-sm text-gray-500">Carregando…</p>
      ) : documentos.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">Nenhum documento anexado.</p>
      ) : (
        <ul className="mt-2 divide-y text-sm">
          {documentos.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between gap-2 py-2">
              <button
                type="button"
                onClick={() => void abrir(doc)}
                className="truncate text-left text-navy-700 underline"
              >
                {doc.nome_exibicao}
              </button>
              <span className="shrink-0 text-xs text-gray-500">
                {formatarTamanho(doc.tamanho_bytes)} · {doc.anexado_em.slice(0, 10)}
              </span>
              <div className="flex shrink-0 gap-2">
                <button
                  type="button"
                  onClick={() => void baixar(doc)}
                  className="rounded border px-2 py-1 text-xs"
                >
                  Baixar
                </button>
                {podeRemover && (
                  <button
                    type="button"
                    onClick={() => setRemocaoPendente(doc)}
                    className="rounded border px-2 py-1 text-xs text-red-600"
                  >
                    Remover
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {remocaoPendente && (
        <ModalConfirmarRemocao
          nome={remocaoPendente.nome_exibicao}
          onConfirmar={() => void confirmarRemocao()}
          onCancelar={() => setRemocaoPendente(null)}
        />
      )}
      {visualizando && (
        <ModalVisualizacao
          documento={visualizando.documento}
          url={visualizando.url}
          onFechar={fecharVisualizacao}
        />
      )}
    </section>
  );
}
