"use client";

import { useEffect, useRef, useState } from "react";

import { contarLacunas, sanitizarHtmlModelo } from "@/lib/sanitize-html";

// Editor de texto formatado (change modelos-de-documento, task 6.1) — barra
// restrita a negrito, itálico, sublinhado, alinhamento e listas, exatamente o
// subconjunto pedido pelo cliente (design.md D3). Todo conteúdo emitido passa
// por `sanitizarHtmlModelo` antes de chegar ao `onChange`, então nenhum
// controle da barra pode produzir tag fora da whitelist — mesmo que o
// navegador insira marcação extra por conta própria.
function blocoMaisProximo(no: Node | null, raiz: HTMLElement): HTMLElement | null {
  let el: HTMLElement | null = no instanceof HTMLElement ? no : (no?.parentElement ?? null);
  while (el && el !== raiz && !["P", "LI", "DIV"].includes(el.tagName)) {
    el = el.parentElement;
  }
  return el && el !== raiz ? el : null;
}

export function EditorFormatado({
  valorInicial,
  onChange,
  ariaLabel = "Conteúdo do modelo",
}: {
  valorInicial: string;
  onChange: (html: string) => void;
  ariaLabel?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [lacunas, setLacunas] = useState(() => contarLacunas(valorInicial));

  useEffect(() => {
    if (ref.current) ref.current.innerHTML = valorInicial;
    setLacunas(contarLacunas(valorInicial));
    // Só na montagem — trocar de modelo remonta o componente via `key` no
    // chamador, em vez de reescrever o conteúdo sob o cursor do usuário.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function emitir() {
    if (!ref.current) return;
    const sanitizado = sanitizarHtmlModelo(ref.current.innerHTML);
    setLacunas(contarLacunas(sanitizado));
    onChange(sanitizado);
  }

  function comando(nome: string) {
    ref.current?.focus();
    document.execCommand(nome, false);
    emitir();
  }

  function alinhar(valor: "left" | "center" | "right" | "justify") {
    ref.current?.focus();
    const selecao = window.getSelection();
    const bloco =
      ref.current && selecao && selecao.rangeCount > 0
        ? blocoMaisProximo(selecao.getRangeAt(0).startContainer, ref.current)
        : null;
    if (bloco) {
      bloco.setAttribute("align", valor);
      bloco.style.removeProperty("text-align");
    }
    emitir();
  }

  const botao = "rounded border px-2 py-1 text-sm hover:bg-navy-50";

  return (
    <div>
      <div
        role="toolbar"
        aria-label="Formatação do texto"
        className="flex flex-wrap gap-1 rounded-t-card border border-b-0 border-navy-50 bg-gray-50 p-2"
      >
        <button type="button" aria-label="Negrito" onClick={() => comando("bold")} className={`${botao} font-bold`}>
          B
        </button>
        <button type="button" aria-label="Itálico" onClick={() => comando("italic")} className={`${botao} italic`}>
          I
        </button>
        <button
          type="button"
          aria-label="Sublinhado"
          onClick={() => comando("underline")}
          className={`${botao} underline`}
        >
          S
        </button>
        <button type="button" aria-label="Alinhar à esquerda" onClick={() => alinhar("left")} className={botao}>
          ⇤
        </button>
        <button type="button" aria-label="Centralizar" onClick={() => alinhar("center")} className={botao}>
          ⇔
        </button>
        <button type="button" aria-label="Alinhar à direita" onClick={() => alinhar("right")} className={botao}>
          ⇥
        </button>
        <button type="button" aria-label="Justificar" onClick={() => alinhar("justify")} className={botao}>
          ☰
        </button>
        <button
          type="button"
          aria-label="Lista com marcadores"
          onClick={() => comando("insertUnorderedList")}
          className={botao}
        >
          • Lista
        </button>
        <button
          type="button"
          aria-label="Lista numerada"
          onClick={() => comando("insertOrderedList")}
          className={botao}
        >
          1. Lista
        </button>
      </div>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-multiline="true"
        aria-label={ariaLabel}
        onInput={emitir}
        onBlur={emitir}
        className="min-h-[220px] rounded-b-card border border-navy-50 bg-white p-3 text-sm focus:outline-none"
      />
      {lacunas > 0 && (
        <p className="mt-1 text-sm text-amber-700" role="status">
          {lacunas} lacuna(s) ainda não preenchida(s) neste texto — a geração não é bloqueada, mas
          revise antes de salvar.
        </p>
      )}
    </div>
  );
}
