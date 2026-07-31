"use client";

import { useEffect } from "react";

/**
 * Modal simples (D6) — usado pelo cadastro de usuário, que deixou de ser
 * formulário permanentemente renderizado no índice de /admin/usuarios.
 * Fecha por Esc ou clique no fundo; o conteúdo não propaga o clique.
 */
export function Modal({
  titulo,
  aberto,
  onFechar,
  children,
}: {
  titulo: string;
  aberto: boolean;
  onFechar: () => void;
  children: React.ReactNode;
}) {
  useEffect(() => {
    if (!aberto) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [aberto, onFechar]);

  if (!aberto) return null;

  return (
    <div
      role="presentation"
      onClick={onFechar}
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:p-8"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl rounded-card border border-navy-50 bg-superficie-card p-5 shadow-card"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-medium">{titulo}</h2>
          <button
            type="button"
            onClick={onFechar}
            aria-label="Fechar"
            className="text-xl leading-none text-gray-500 hover:text-gray-800"
          >
            ×
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}
