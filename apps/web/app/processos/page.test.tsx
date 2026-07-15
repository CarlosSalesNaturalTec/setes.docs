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

describe("ProcessosPage (Kanban)", () => {
  beforeEach(() => {
    listarKanban.mockReset();
    listarUnidades.mockReset();
    listarUnidades.mockResolvedValue([]);
    usuario = { perfil: "servidor" };
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

  it("agrupa os cards por coluna e destaca processos vencidos (PRD US 2.3 Cen.1/4)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        {
          id: "proc-1",
          numero: "2026/000001",
          assunto: "Processo em dia",
          status: "aberto",
          unidade_atual_id: "un-1",
          prazo_em: "2026-08-01",
          dias_restantes: 5,
          vencido: false,
        },
        {
          id: "proc-2",
          numero: "2026/000002",
          assunto: "Processo vencido",
          status: "aberto",
          unidade_atual_id: "un-1",
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
});
