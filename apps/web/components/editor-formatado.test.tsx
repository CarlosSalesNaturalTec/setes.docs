import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EditorFormatado } from "./editor-formatado";

describe("EditorFormatado", () => {
  beforeEach(() => {
    document.execCommand = vi.fn();
  });

  it("carrega o valor inicial no conteúdo editável", () => {
    render(<EditorFormatado valorInicial="<p><b>Olá</b></p>" onChange={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Conteúdo do modelo" })).toHaveTextContent("Olá");
  });

  it("os controles de negrito/itálico/sublinhado/listas usam apenas comandos do próprio navegador", async () => {
    render(<EditorFormatado valorInicial="" onChange={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Negrito" }));
    await userEvent.click(screen.getByRole("button", { name: "Itálico" }));
    await userEvent.click(screen.getByRole("button", { name: "Sublinhado" }));
    await userEvent.click(screen.getByRole("button", { name: "Lista com marcadores" }));
    await userEvent.click(screen.getByRole("button", { name: "Lista numerada" }));

    expect(document.execCommand).toHaveBeenCalledWith("bold", false);
    expect(document.execCommand).toHaveBeenCalledWith("italic", false);
    expect(document.execCommand).toHaveBeenCalledWith("underline", false);
    expect(document.execCommand).toHaveBeenCalledWith("insertUnorderedList", false);
    expect(document.execCommand).toHaveBeenCalledWith("insertOrderedList", false);
  });

  it("qualquer marcação inserida pelo navegador é sanitizada antes de chegar ao onChange", () => {
    const onChange = vi.fn();
    render(<EditorFormatado valorInicial="" onChange={onChange} />);
    const editor = screen.getByRole("textbox", { name: "Conteúdo do modelo" });

    // Simula o navegador inserindo marcação fora da whitelist (ex.: um
    // `<div style="...">` que alguns navegadores produzem para alinhamento).
    editor.innerHTML = '<div style="text-align:center"><b>Texto</b></div><script>alert(1)</script>';
    fireEvent.input(editor);

    const html = onChange.mock.calls.at(-1)?.[0] as string;
    expect(html).not.toContain("<div");
    expect(html).not.toContain("style");
    expect(html).not.toContain("<script");
    expect(html).toContain("<b>Texto</b>");
  });

  it("destaca lacunas pendentes sem impedir a digitação", () => {
    const onChange = vi.fn();
    render(<EditorFormatado valorInicial="" onChange={onChange} />);
    const editor = screen.getByRole("textbox", { name: "Conteúdo do modelo" });

    editor.innerHTML = "<p>Nome: [NOME DO SOLICITANTE]</p>";
    fireEvent.input(editor);

    expect(screen.getByRole("status")).toHaveTextContent(/1 lacuna\(s\) ainda não preenchida/);
    expect(onChange).toHaveBeenCalledWith("<p>Nome: [NOME DO SOLICITANTE]</p>");
  });

  it("sem lacunas pendentes, não exibe nenhum aviso", () => {
    render(<EditorFormatado valorInicial="<p>Texto completo</p>" onChange={vi.fn()} />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
