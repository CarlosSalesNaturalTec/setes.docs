import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { obterRelatorioAuditoria, listarUnidades, listarTiposProcesso } = vi.hoisted(() => ({
  obterRelatorioAuditoria: vi.fn(),
  listarUnidades: vi.fn(),
  listarTiposProcesso: vi.fn(),
}));

let podeAuditar = true;

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({
    children,
    exigirAuditoria,
  }: {
    children: React.ReactNode;
    exigirAuditoria?: boolean;
  }) => {
    if (exigirAuditoria && !podeAuditar) {
      return <p>Acesso negado — permissão de auditoria necessária.</p>;
    }
    return children;
  },
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { obterRelatorioAuditoria, listarUnidades, listarTiposProcesso },
  };
});

import RelatorioAuditoriaPage from "./page";

describe("RelatorioAuditoriaPage", () => {
  beforeEach(() => {
    podeAuditar = true;
    obterRelatorioAuditoria.mockReset();
    listarUnidades.mockReset().mockResolvedValue([{ id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true }]);
    listarTiposProcesso
      .mockReset()
      .mockResolvedValue([{ id: "tp-1", nome: "Licitação", ativo: true, roteiro: { etapas: [] } }]);
  });

  it("renderiza o relatório com dados (US 9.2 Cen.1)", async () => {
    obterRelatorioAuditoria.mockResolvedValue({
      total_processos: 2,
      tempo_medio_tramitacao_dias: 12.5,
      mensagem_vazio: null,
      items: [
        {
          id: "p1",
          numero: "2026/000001",
          assunto: "Processo auditado",
          status: "concluido",
          unidade_atual_id: "un-1",
          tipo_processo_id: "tp-1",
          criado_em: "2026-06-01T00:00:00Z",
          concluido_em: "2026-06-11T00:00:00Z",
        },
      ],
    });

    render(<RelatorioAuditoriaPage />);

    await userEvent.click(screen.getByRole("button", { name: "Gerar relatório" }));

    expect(await screen.findByTestId("relatorio-total")).toHaveTextContent("2");
    expect(screen.getByTestId("relatorio-tempo-medio")).toHaveTextContent("12.5 dias");
    expect(screen.getByTestId("relatorio-lista")).toHaveTextContent("2026/000001");
    expect(screen.getByTestId("relatorio-lista")).toHaveTextContent("Concluído");
    expect(screen.getByTestId("relatorio-lista")).toHaveTextContent("COFIN");
    expect(screen.getByTestId("relatorio-lista")).toHaveTextContent("Licitação");
  });

  it("exibe o tempo médio como travessão quando ausente", async () => {
    obterRelatorioAuditoria.mockResolvedValue({
      total_processos: 1,
      tempo_medio_tramitacao_dias: null,
      mensagem_vazio: null,
      items: [
        {
          id: "p1",
          numero: "2026/000002",
          assunto: "Em tramitação",
          status: "em_tramitacao",
          unidade_atual_id: "un-1",
          tipo_processo_id: "tp-1",
          criado_em: "2026-06-01T00:00:00Z",
          concluido_em: null,
        },
      ],
    });

    render(<RelatorioAuditoriaPage />);
    await userEvent.click(screen.getByRole("button", { name: "Gerar relatório" }));

    expect(await screen.findByTestId("relatorio-tempo-medio")).toHaveTextContent("—");
  });

  it("exibe a mensagem de estado vazio quando os filtros não retornam dados (US 9.2 Cen.2)", async () => {
    obterRelatorioAuditoria.mockResolvedValue({
      total_processos: 0,
      tempo_medio_tramitacao_dias: null,
      mensagem_vazio: "Nenhum dado encontrado para os filtros informados",
      items: [],
    });

    render(<RelatorioAuditoriaPage />);
    await userEvent.click(screen.getByRole("button", { name: "Gerar relatório" }));

    expect(
      await screen.findByText("Nenhum dado encontrado para os filtros informados"),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("relatorio-total")).not.toBeInTheDocument();
  });

  it("oculta o conteúdo para usuário sem permissão de auditoria", () => {
    podeAuditar = false;

    render(<RelatorioAuditoriaPage />);

    expect(
      screen.getByText("Acesso negado — permissão de auditoria necessária."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Gerar relatório" })).not.toBeInTheDocument();
    expect(obterRelatorioAuditoria).not.toHaveBeenCalled();
  });

  it("chama a API com os filtros informados", async () => {
    obterRelatorioAuditoria.mockResolvedValue({
      total_processos: 0,
      tempo_medio_tramitacao_dias: null,
      mensagem_vazio: "Nenhum dado encontrado para os filtros informados",
      items: [],
    });

    render(<RelatorioAuditoriaPage />);
    await screen.findByLabelText("Unidade");

    await userEvent.type(screen.getByLabelText("Período — início"), "2026-06-01");
    await userEvent.type(screen.getByLabelText("Período — fim"), "2026-06-30");
    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "un-1");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), "tp-1");
    await userEvent.click(screen.getByRole("button", { name: "Gerar relatório" }));

    await waitFor(() =>
      expect(obterRelatorioAuditoria).toHaveBeenCalledWith({
        inicio: "2026-06-01",
        fim: "2026-06-30",
        unidade_id: "un-1",
        tipo_processo_id: "tp-1",
      }),
    );
  });
});
