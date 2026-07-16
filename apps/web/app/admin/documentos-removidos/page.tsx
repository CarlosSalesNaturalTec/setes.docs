"use client";

import { useEffect, useState } from "react";

import { ProtectedShell } from "@/components/protected-shell";
import { ApiError, api, type Schemas } from "@/lib/api";

type DocumentoRemovido = Schemas["DocumentoRemovidoResponse"];

const RODAPE_PURGA =
  "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados.";

function formatarDataHora(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR");
}

function ConfirmacaoRestauracao({
  documento,
  onConfirmar,
  onCancelar,
  restaurando,
}: {
  documento: DocumentoRemovido;
  onConfirmar: () => void;
  onCancelar: () => void;
  restaurando: boolean;
}) {
  return (
    <div
      role="dialog"
      aria-label="Restaurar documento"
      className="fixed inset-0 z-10 flex items-center justify-center bg-black/40"
    >
      <div className="w-full max-w-md rounded bg-white p-6 shadow-lg">
        <h2 className="text-lg font-medium">Restaurar documento</h2>
        <p className="mt-2 text-sm text-gray-700">
          Restaurar &ldquo;{documento.nome_exibicao}&rdquo; para o processo {documento.processo_numero}?
          O documento volta a aparecer na lista de anexos do processo.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancelar}
            disabled={restaurando}
            className="rounded border px-3 py-2 text-sm"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={restaurando}
            className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {restaurando ? "Restaurando…" : "Restaurar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function DocumentosRemovidosConteudo() {
  const [documentos, setDocumentos] = useState<DocumentoRemovido[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState<DocumentoRemovido | null>(null);
  const [restaurando, setRestaurando] = useState(false);

  async function carregar() {
    setCarregando(true);
    try {
      const resposta = await api.listarDocumentosRemovidos();
      setDocumentos(resposta.items ?? []);
      setErro(null);
    } catch (err) {
      setErro(
        err instanceof ApiError ? err.detail : "Não foi possível carregar os documentos removidos.",
      );
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  async function restaurar(documento: DocumentoRemovido) {
    setRestaurando(true);
    setAviso(null);
    try {
      await api.restaurarDocumento(documento.id);
      setConfirmando(null);
      await carregar();
    } catch (err) {
      setConfirmando(null);
      // 404 = documento já purgado entre a listagem e a ação (US 8.7 Cen.2).
      if (err instanceof ApiError && err.status === 404) {
        setAviso(
          "Este documento não está mais disponível para restauração (removido há mais de 30 dias).",
        );
        await carregar();
      } else {
        setAviso(err instanceof ApiError ? err.detail : "Não foi possível restaurar o documento.");
      }
    } finally {
      setRestaurando(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Documentos Removidos</h1>
      <p className="mt-1 text-sm text-gray-600">
        Documentos em período de retenção podem ser restaurados enquanto não forem excluídos
        permanentemente.
      </p>

      {erro && <p className="mt-4 text-sm text-red-600">{erro}</p>}
      {aviso && <p className="mt-4 text-sm text-amber-700">{aviso}</p>}
      {carregando && <p className="mt-4 text-sm text-gray-500">Carregando…</p>}

      {!carregando && documentos.length === 0 && (
        <p className="mt-6 text-sm text-gray-500">Nenhum documento em período de retenção</p>
      )}

      {documentos.length > 0 && (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr className="border-b text-gray-500">
              <th className="py-2 pr-4 font-medium">Documento</th>
              <th className="py-2 pr-4 font-medium">Processo</th>
              <th className="py-2 pr-4 font-medium">Removido em</th>
              <th className="py-2 pr-4 font-medium">Removido por</th>
              <th className="py-2 font-medium">Ações</th>
            </tr>
          </thead>
          <tbody>
            {documentos.map((doc) => (
              <tr key={doc.id} className="border-b">
                <td className="py-2 pr-4">{doc.nome_exibicao}</td>
                <td className="py-2 pr-4">
                  <span className="font-medium">{doc.processo_numero}</span>
                  <span className="text-gray-500"> — {doc.processo_assunto}</span>
                </td>
                <td className="py-2 pr-4">{formatarDataHora(doc.removido_em)}</td>
                <td className="py-2 pr-4">{doc.removido_por_id}</td>
                <td className="py-2">
                  <button
                    type="button"
                    onClick={() => {
                      setAviso(null);
                      setConfirmando(doc);
                    }}
                    className="text-blue-600"
                  >
                    Restaurar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="mt-8 border-t pt-4 text-xs text-gray-500">{RODAPE_PURGA}</p>

      {confirmando && (
        <ConfirmacaoRestauracao
          documento={confirmando}
          restaurando={restaurando}
          onConfirmar={() => void restaurar(confirmando)}
          onCancelar={() => setConfirmando(null)}
        />
      )}
    </div>
  );
}

export default function DocumentosRemovidosPage() {
  return (
    <ProtectedShell>
      <DocumentosRemovidosConteudo />
    </ProtectedShell>
  );
}
