import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { push, listarTiposProcesso, criarProcesso } = vi.hoisted(() => ({
  push: vi.fn(),
  listarTiposProcesso: vi.fn(),
  criarProcesso: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarTiposProcesso, criarProcesso },
  };
});

import NovoProcessoPage from "./page";

const TIPO = { id: "tipo-1", nome: "Licitação", ativo: true, prazo_anonimizacao_anos: 5 };

describe("NovoProcessoPage", () => {
  beforeEach(() => {
    push.mockReset();
    criarProcesso.mockReset();
    listarTiposProcesso.mockReset();
    listarTiposProcesso.mockResolvedValue([TIPO]);
  });

  it("rejeita submissão sem assunto, tipo ou prazo (PRD US 2.1 Cen.2)", async () => {
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    expect(await screen.findByText("Informe o assunto.")).toBeInTheDocument();
    expect(screen.getByText("Selecione o tipo de processo.")).toBeInTheDocument();
    expect(screen.getByText("Informe um prazo em dias.")).toBeInTheDocument();
    expect(criarProcesso).not.toHaveBeenCalled();
  });

  it("cria o processo com dados válidos e navega para o detalhe", async () => {
    criarProcesso.mockResolvedValue({ id: "proc-1" });
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido de compra de material");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "30");
    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    await waitFor(() =>
      expect(criarProcesso).toHaveBeenCalledWith({
        assunto: "Pedido de compra de material",
        tipo_processo_id: TIPO.id,
        prazo_dias: 30,
        interessados: [],
      }),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos/proc-1"));
  });

  it("exibe o erro de CPF inválido retornado pela API (PRD US 2.1 Cen.3)", async () => {
    criarProcesso.mockRejectedValue(
      new ApiError(422, "CPF inválido — verifique o número informado"),
    );
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido de compra");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "10");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar interessado" }));
    await userEvent.type(screen.getByLabelText("Nome do interessado"), "Fulano de Tal");
    await userEvent.type(screen.getByLabelText("Documento do interessado"), "11111111111");
    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    expect(
      await screen.findByText("CPF inválido — verifique o número informado"),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });
});
