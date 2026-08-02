"use client";

import { useRef } from "react";

export interface TabDefinicao {
  id: string;
  rotulo: string;
  conteudo: React.ReactNode;
}

// Widget de abas ARIA (change perfil-em-abas, design D4): tablist/tab/tabpanel,
// navegação por setas esquerda/direita com foco em roving tabindex, ativação
// por clique ou Enter/Espaço (nativos do <button>). Sem armadilha de foco: Tab
// sempre sai da lista de abas para o painel ativo.
export function Tabs({
  abas,
  abaAtiva,
  onSelecionar,
  "aria-label": ariaLabel,
}: {
  abas: TabDefinicao[];
  abaAtiva: string;
  onSelecionar: (id: string) => void;
  "aria-label": string;
}) {
  const botoesRef = useRef<Record<string, HTMLButtonElement | null>>({});
  const abaSelecionada = abas.find((a) => a.id === abaAtiva) ?? abas[0];

  function selecionarEFocar(id: string) {
    onSelecionar(id);
    botoesRef.current[id]?.focus();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLButtonElement>, indice: number) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const delta = e.key === "ArrowRight" ? 1 : -1;
    const proxima = abas[(indice + delta + abas.length) % abas.length];
    selecionarEFocar(proxima.id);
  }

  return (
    <div>
      <div role="tablist" aria-label={ariaLabel} className="flex gap-1 border-b border-navy-50">
        {abas.map((aba, indice) => {
          const ativa = aba.id === abaSelecionada.id;
          return (
            <button
              key={aba.id}
              ref={(el) => {
                botoesRef.current[aba.id] = el;
              }}
              type="button"
              role="tab"
              id={`tab-${aba.id}`}
              aria-selected={ativa}
              aria-controls={`tabpanel-${aba.id}`}
              tabIndex={ativa ? 0 : -1}
              onClick={() => onSelecionar(aba.id)}
              onKeyDown={(e) => onKeyDown(e, indice)}
              className={
                "rounded-t-card border-b-2 px-4 py-2 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-navy-600 " +
                (ativa
                  ? "border-navy-600 text-navy-900"
                  : "border-transparent text-gray-500 hover:text-navy-700")
              }
            >
              {aba.rotulo}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`tabpanel-${abaSelecionada.id}`}
        aria-labelledby={`tab-${abaSelecionada.id}`}
        tabIndex={0}
        className="pt-4"
      >
        {abaSelecionada.conteudo}
      </div>
    </div>
  );
}
