import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  obterDashboardKpis,
  obterProcessosAtivosDashboard,
  obterProcessosParadosDashboard,
  listarUnidades,
} = vi.hoisted(() => ({
  obterDashboardKpis: vi.fn(),
  obterProcessosAtivosDashboard: vi.fn(),
  obterProcessosParadosDashboard: vi.fn(),
  listarUnidades: vi.fn(),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      obterDashboardKpis,
      obterProcessosAtivosDashboard,
      obterProcessosParadosDashboard,
      listarUnidades,
    },
  };
});

import DashboardPage from "./page";

const KPIS_VAZIO = {
  total_processos_ativos: 0,
  tempo_medio_tramitacao_dias: null,
  total_processos_parados: 0,
  produtividade_por_unidade: [],
  prazos_em_risco: [],
};

describe("DashboardPage", () => {
  beforeEach(() => {
    obterDashboardKpis.mockReset();
    obterProcessosAtivosDashboard.mockReset();
    obterProcessosParadosDashboard.mockReset();
    listarUnidades.mockReset().mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: true },
    ]);
  });

  it("exibe estado vazio em cada seção sem dados (US 6.1 Cen.2)", async () => {
    obterDashboardKpis.mockResolvedValue(KPIS_VAZIO);

    render(<DashboardPage />);

    expect(await screen.findByTestId("kpi-ativos")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-tempo-medio")).toHaveTextContent(
      "Nenhum dado disponível para o período",
    );
    expect(screen.getByTestId("kpi-parados")).toHaveTextContent("0");
    expect(screen.getByTestId("kpi-produtividade")).toHaveTextContent(
      "Nenhum dado disponível para o período",
    );
    expect(screen.getByText("Prazos em Risco").closest("section")).toHaveTextContent(
      "Nenhum dado disponível para o período",
    );
  });

  it("renderiza os cards de KPI com dados (US 6.1 Cen.1)", async () => {
    obterDashboardKpis.mockResolvedValue({
      total_processos_ativos: 42,
      tempo_medio_tramitacao_dias: 12.5,
      total_processos_parados: 7,
      produtividade_por_unidade: [{ unidade_id: "un-1", unidade_nome: "COFIN", quantidade: 3 }],
      prazos_em_risco: [
        {
          id: "p1",
          numero: "2026/000001",
          assunto: "Processo urgente",
          unidade_atual_id: "un-1",
          prazo_em: "2026-07-10",
          dias_restantes: -6,
          vencido: true,
        },
      ],
    });

    render(<DashboardPage />);

    expect(await screen.findByTestId("kpi-ativos")).toHaveTextContent("42");
    expect(screen.getByTestId("kpi-tempo-medio")).toHaveTextContent("12.5 dias");
    expect(screen.getByTestId("kpi-parados")).toHaveTextContent("7");
    expect(screen.getByTestId("kpi-produtividade")).toHaveTextContent("COFIN");
    expect(screen.getByTestId("kpi-produtividade")).toHaveTextContent("3");
    expect(screen.getByText(/2026\/000001/)).toBeInTheDocument();
    expect(screen.getByText(/vencido há 6 dia\(s\)/)).toBeInTheDocument();
  });

  it("recarrega ao selecionar o filtro por unidade (US 6.1 Cen.3)", async () => {
    obterDashboardKpis.mockResolvedValue(KPIS_VAZIO);

    render(<DashboardPage />);
    await screen.findByTestId("kpi-ativos");

    const filtro = screen.getByLabelText("Filtrar por unidade");
    await userEvent.selectOptions(filtro, "un-1");

    await waitFor(() =>
      expect(obterDashboardKpis).toHaveBeenLastCalledWith({ unidade_id: "un-1" }),
    );
  });

  it("aciona drill-down em Processos Ativos e Processos Parados (US 6.1 Cen.4/5)", async () => {
    obterDashboardKpis.mockResolvedValue({
      ...KPIS_VAZIO,
      total_processos_ativos: 1,
      total_processos_parados: 1,
    });
    obterProcessosAtivosDashboard.mockResolvedValue({
      items: [
        {
          id: "p1",
          numero: "2026/000010",
          assunto: "Processo ativo",
          unidade_atual_id: "un-1",
          dias_restantes: 5,
        },
      ],
      total: 1,
    });
    obterProcessosParadosDashboard.mockResolvedValue({
      items: [
        {
          id: "p2",
          numero: "2026/000011",
          assunto: "Processo parado",
          unidade_atual_id: "un-1",
          dias_parados: 9,
        },
      ],
      total: 1,
    });

    render(<DashboardPage />);
    await screen.findByTestId("kpi-ativos");

    await userEvent.click(screen.getByTestId("kpi-ativos"));
    expect(await screen.findByText(/2026\/000010/)).toBeInTheDocument();
    expect(screen.getByText(/5 dia\(s\) restante\(s\)/)).toBeInTheDocument();

    await userEvent.click(screen.getByTestId("kpi-parados"));
    expect(await screen.findByText(/2026\/000011/)).toBeInTheDocument();
    expect(screen.getByText(/9 dia\(s\) parado/)).toBeInTheDocument();
  });

  it("não dispara drill-down para Tempo Médio ou Produtividade (US 6.1 Cen.6)", async () => {
    obterDashboardKpis.mockResolvedValue(KPIS_VAZIO);

    render(<DashboardPage />);
    await screen.findByTestId("kpi-ativos");

    expect(screen.getByTestId("kpi-tempo-medio").querySelector("button")).toBeNull();
    expect(screen.getByTestId("kpi-produtividade").querySelector("button")).toBeNull();
    expect(obterProcessosAtivosDashboard).not.toHaveBeenCalled();
    expect(obterProcessosParadosDashboard).not.toHaveBeenCalled();
  });
});
