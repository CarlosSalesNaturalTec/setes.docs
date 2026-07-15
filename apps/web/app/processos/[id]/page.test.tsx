import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { obterProcesso, historicoProcesso, listarUnidades, despacharProcesso, devolverProcesso } =
  vi.hoisted(() => ({
    obterProcesso: vi.fn(),
    historicoProcesso: vi.fn(),
    listarUnidades: vi.fn(),
    despacharProcesso: vi.fn(),
    devolverProcesso: vi.fn(),
  }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "proc-1" }),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { obterProcesso, historicoProcesso, listarUnidades, despacharProcesso, devolverProcesso },
  };
});

import DetalheProcessoPage from "./page";

const PROCESSO_BASE = {
  id: "proc-1",
  numero: "2026/000001",
  assunto: "Pedido de compra de material",
  status: "em_tramitacao",
  unidade_atual_id: "un-1",
  unidade_origem_id: "un-1",
  tipo_processo_id: "tipo-1",
  roteiro_id: "rot-1",
  ordem_atual: 0,
  prazo_dias: 10,
  prazo_em: "2026-08-01",
  criado_por_id: "user-1",
  criado_em: "2026-07-15T10:00:00Z",
  concluido_em: null,
  interessados: [],
};

const HISTORICO_VAZIO = {
  processo_id: "proc-1",
  criado_em: "2026-07-15T10:00:00Z",
  eventos: [],
  mensagem_vazio: "Nenhuma movimentação registrada",
};

describe("DetalheProcessoPage", () => {
  beforeEach(() => {
    obterProcesso.mockReset();
    historicoProcesso.mockReset();
    listarUnidades.mockReset();
    despacharProcesso.mockReset();
    devolverProcesso.mockReset();
    listarUnidades.mockResolvedValue([{ id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true }]);
    historicoProcesso.mockResolvedValue(HISTORICO_VAZIO);
  });

  it("pede confirmação de conclusão na última etapa e conclui ao confirmar (PRD US 2.2 Cen.2/4)", async () => {
    obterProcesso
      .mockResolvedValueOnce(PROCESSO_BASE)
      .mockResolvedValue({ ...PROCESSO_BASE, status: "concluido", concluido_em: "2026-07-16T10:00:00Z" });
    despacharProcesso.mockImplementation((_id: string, body: { confirmar: boolean }) =>
      body.confirmar
        ? Promise.resolve({ ...PROCESSO_BASE, status: "concluido" })
        : Promise.reject(
            new ApiError(409, "Este é o destino final do roteiro. Deseja concluir o processo?"),
          ),
    );

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Despachar" }));

    const modal = await screen.findByRole("dialog", { name: "Confirmar conclusão" });
    expect(
      within(modal).getByText("Este é o destino final do roteiro. Deseja concluir o processo?"),
    ).toBeInTheDocument();

    await userEvent.click(within(modal).getByRole("button", { name: "Concluir processo" }));

    await waitFor(() => expect(despacharProcesso).toHaveBeenCalledTimes(2));
    expect(despacharProcesso).toHaveBeenLastCalledWith("proc-1", { confirmar: true });
    expect(await screen.findByText("Concluído")).toBeInTheDocument();
  });

  it("cancelar no modal de conclusão não altera o processo (PRD US 2.2 Cen.3)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    despacharProcesso.mockRejectedValue(
      new ApiError(409, "Este é o destino final do roteiro. Deseja concluir o processo?"),
    );

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Despachar" }));

    const modal = await screen.findByRole("dialog", { name: "Confirmar conclusão" });
    await userEvent.click(within(modal).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog", { name: "Confirmar conclusão" })).not.toBeInTheDocument();
    expect(despacharProcesso).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Em Tramitação")).toBeInTheDocument();
  });

  it("exige a seleção de um motivo antes de confirmar a devolução (PRD US 2.2b Cen.3)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Devolver" }));

    const modal = await screen.findByRole("dialog", { name: "Devolver processo" });
    await userEvent.click(within(modal).getByRole("button", { name: "Confirmar devolução" }));

    expect(
      within(modal).getByText("Selecione um motivo para a devolução"),
    ).toBeInTheDocument();
    expect(devolverProcesso).not.toHaveBeenCalled();

    await userEvent.selectOptions(within(modal).getByLabelText("Motivo"), "documentacao_insuficiente");
    await userEvent.click(within(modal).getByRole("button", { name: "Confirmar devolução" }));

    await waitFor(() =>
      expect(devolverProcesso).toHaveBeenCalledWith("proc-1", {
        motivo: "documentacao_insuficiente",
        justificativa: null,
      }),
    );
  });

  it("exibe o estado vazio do histórico para processo recém-criado (PRD US 2.4 Cen.2)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await screen.findByRole("button", { name: "Despachar" });
    await userEvent.click(screen.getByRole("button", { name: "Histórico" }));

    expect(await screen.findByText(/Nenhuma movimentação registrada/)).toBeInTheDocument();
  });
});
