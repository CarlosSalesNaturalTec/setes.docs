import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listarKanban, listarUnidades } = vi.hoisted(() => ({
  listarKanban: vi.fn(),
  listarUnidades: vi.fn(),
}));
let usuario: { perfil: string } = { perfil: "servidor" };

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ usuario }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarKanban, listarUnidades },
  };
});

import ProcessosPage from "./page";

const CARD_BASE = {
  status: "aberto",
  unidade_atual_id: "un-1",
  unidade_atual_nome: "Coordenação de Finanças",
  tipo_processo_nome: "Licitação",
  criado_em: "2026-07-15T10:30:00Z",
  prazo_em: "2026-08-01",
  dias_restantes: 5,
  vencido: false,
  sigiloso: false,
};

describe("ProcessosPage (Kanban)", () => {
  beforeEach(() => {
    listarKanban.mockReset();
    listarUnidades.mockReset();
    listarUnidades.mockResolvedValue([]);
    usuario = { perfil: "servidor" };
    window.localStorage.clear();
  });

  it("exibe a mensagem de Kanban vazio da unidade (PRD US 2.3 Cen.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);

    expect(
      await screen.findByText("Nenhum processo encontrado nesta unidade"),
    ).toBeInTheDocument();
  });

  it("agrupa os cards por coluna, exibe tipo/unidade/data e destaca vencidos (PRD US 2.3 Cen.1/4)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo em dia" },
        {
          ...CARD_BASE,
          id: "proc-2",
          numero: "2026/000002",
          assunto: "Processo vencido",
          prazo_em: "2026-07-01",
          dias_restantes: -5,
          vencido: true,
        },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const coluna = (await screen.findByText(/Aberto/)).closest("section");
    expect(coluna).not.toBeNull();
    const emDia = within(coluna as HTMLElement).getByText("2026/000001").closest("a");
    const vencido = within(coluna as HTMLElement).getByText("2026/000002").closest("a");

    expect(emDia?.className).not.toContain("border-l-red-600");
    expect(vencido?.className).toContain("border-l-red-600");
    expect(within(vencido as HTMLElement).getByText(/⏰/)).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText("Licitação")).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText("Coordenação de Finanças")).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText(/Criado em 15\/07\/2026/)).toBeInTheDocument();
  });

  it("exibe o indicador de sigilo apenas no card sigiloso (PRD US 2.6 Cen.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo comum" },
        { ...CARD_BASE, id: "proc-2", numero: "2026/000002", assunto: "Processo sigiloso", sigiloso: true },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const comum = (await screen.findByText("2026/000001")).closest("a");
    const sigiloso = screen.getByText("2026/000002").closest("a");

    expect(within(comum as HTMLElement).queryByLabelText("Sigiloso")).not.toBeInTheDocument();
    expect(within(sigiloso as HTMLElement).getByLabelText("Sigiloso")).toBeInTheDocument();
  });

  it("exibe o filtro por unidade apenas para o Gestor (PRD US 2.8 Cen.2)", async () => {
    usuario = { perfil: "gestor" };
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nas unidades gerenciadas",
    });
    listarUnidades.mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: true },
    ]);

    render(<ProcessosPage />);

    const filtro = await screen.findByLabelText("Filtrar por unidade");
    await userEvent.selectOptions(filtro, "un-2");

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ filtro_unidade: "un-2" }),
    );
  });

  it("não exibe o filtro por unidade para o Servidor", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);
    await screen.findByText("Nenhum processo encontrado nesta unidade");

    expect(screen.queryByLabelText("Filtrar por unidade")).not.toBeInTheDocument();
  });

  it("exibe o contador de processos no cabeçalho (PRD — contador corrigido)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "A" },
        { ...CARD_BASE, id: "proc-2", numero: "2026/000002", assunto: "B" },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    expect(await screen.findByText("2 processo(s)")).toBeInTheDocument();
  });

  it("aplica cor por status no cabeçalho de cada coluna do Kanban", async () => {
    listarKanban.mockResolvedValue({
      items: [{ ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "A" }],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const aberto = (await screen.findByText(/Aberto/)).closest("h2");
    expect(aberto?.className).toContain("bg-status-aberto-bg");
    expect(aberto?.className).toContain("text-status-aberto");
  });

  it("alterna entre Kanban e Lista mantendo os mesmos processos (toggle)", async () => {
    listarKanban.mockResolvedValue({
      items: [{ ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo único" }],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);
    await screen.findByText("2026/000001");

    // Kanban por padrão: card dentro de uma coluna ("section").
    expect(screen.getByText("2026/000001").closest("section")).not.toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Lista" }));

    // Lista: mesma numeração, agora como linha (fora de "section"), com a pill de status.
    const linha = screen.getByText("2026/000001").closest("a");
    expect(linha).not.toBeNull();
    expect(linha?.closest("section")).toBeNull();
    expect(within(linha as HTMLElement).getByText("Aberto")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Kanban" }));
    expect(screen.getByText("2026/000001").closest("section")).not.toBeNull();

    // Só uma chamada à API para ambos os modos — mesma resposta reaproveitada (D2).
    expect(listarKanban).toHaveBeenCalledTimes(1);
  });
});
