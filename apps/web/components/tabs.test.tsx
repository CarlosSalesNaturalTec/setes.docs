import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { Tabs } from "@/components/tabs";

const ABAS = [
  { id: "um", rotulo: "Um", conteudo: <p>Conteúdo um</p> },
  { id: "dois", rotulo: "Dois", conteudo: <p>Conteúdo dois</p> },
  { id: "tres", rotulo: "Três", conteudo: <p>Conteúdo três</p> },
];

function TabsControladas({ inicial = "um" }: { inicial?: string }) {
  const [aba, setAba] = useState(inicial);
  return <Tabs aria-label="Exemplo" abas={ABAS} abaAtiva={aba} onSelecionar={setAba} />;
}

describe("Tabs", () => {
  it("expõe a semântica ARIA de tablist/tab/tabpanel", () => {
    render(<TabsControladas />);

    const tablist = screen.getByRole("tablist", { name: "Exemplo" });
    expect(tablist).toBeInTheDocument();

    const abas = screen.getAllByRole("tab");
    expect(abas).toHaveLength(3);
    expect(abas[0]).toHaveAttribute("aria-selected", "true");
    expect(abas[1]).toHaveAttribute("aria-selected", "false");
    expect(abas[2]).toHaveAttribute("aria-selected", "false");

    const painel = screen.getByRole("tabpanel");
    expect(painel).toHaveAccessibleName("Um");
    expect(screen.getByText("Conteúdo um")).toBeInTheDocument();
  });

  it("cada aba é um botão, não um link", () => {
    render(<TabsControladas />);
    for (const aba of screen.getAllByRole("tab")) {
      expect(aba.tagName).toBe("BUTTON");
    }
  });

  it("troca de aba ao clicar", async () => {
    render(<TabsControladas />);

    await userEvent.click(screen.getByRole("tab", { name: "Dois" }));

    expect(screen.getByRole("tab", { name: "Dois" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Conteúdo dois")).toBeInTheDocument();
    expect(screen.queryByText("Conteúdo um")).toBeNull();
  });

  it("navega entre as abas com as setas esquerda e direita, com foco sempre visível", async () => {
    render(<TabsControladas />);

    const [um, dois, tres] = screen.getAllByRole("tab");
    um.focus();
    expect(um).toHaveFocus();

    await userEvent.keyboard("{ArrowRight}");
    expect(dois).toHaveFocus();
    expect(dois).toHaveAttribute("aria-selected", "true");

    await userEvent.keyboard("{ArrowRight}");
    expect(tres).toHaveFocus();
    expect(tres).toHaveAttribute("aria-selected", "true");

    // Roda para o início, sem armadilha de foco no fim da lista.
    await userEvent.keyboard("{ArrowRight}");
    expect(um).toHaveFocus();

    await userEvent.keyboard("{ArrowLeft}");
    expect(tres).toHaveFocus();
  });

  it("apenas a aba ativa tem tabIndex 0 (roving tabindex)", async () => {
    render(<TabsControladas />);

    const [um, dois, tres] = screen.getAllByRole("tab");
    expect(um).toHaveAttribute("tabindex", "0");
    expect(dois).toHaveAttribute("tabindex", "-1");
    expect(tres).toHaveAttribute("tabindex", "-1");
  });
});
