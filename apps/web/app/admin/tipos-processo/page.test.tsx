import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listarTiposProcesso, atualizarTipoProcesso } = vi.hoisted(() => ({
  listarTiposProcesso: vi.fn(),
  atualizarTipoProcesso: vi.fn(),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarTiposProcesso, atualizarTipoProcesso },
  };
});

import AdminTiposProcessoPage from "./page";

const LICITACAO = { id: "t-1", nome: "Licitação", prazo_anonimizacao_anos: 5, ativo: true };
const REQUERIMENTO = { id: "t-2", nome: "Requerimento", prazo_anonimizacao_anos: 3, ativo: true };

function linha(nome: string) {
  return screen.getByText(nome).closest("tr") as HTMLElement;
}

describe("AdminTiposProcessoPage — tabela de tipos de processo (change ajustes-ui-admin)", () => {
  beforeEach(() => {
    listarTiposProcesso.mockReset().mockResolvedValue([LICITACAO, REQUERIMENTO]);
    atualizarTipoProcesso.mockReset();
  });

  it("salva o prazo de uma linha sem alterar nem revalidar as demais", async () => {
    atualizarTipoProcesso.mockResolvedValue({ ...LICITACAO, prazo_anonimizacao_anos: 7 });

    render(<AdminTiposProcessoPage />);
    await screen.findByText(LICITACAO.nome);

    const linhaLicitacao = linha(LICITACAO.nome);
    const campoPrazo = within(linhaLicitacao).getByRole("spinbutton");
    await userEvent.clear(campoPrazo);
    await userEvent.type(campoPrazo, "7");
    await userEvent.click(within(linhaLicitacao).getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(atualizarTipoProcesso).toHaveBeenCalledWith("t-1", { prazo_anonimizacao_anos: 7 }));
    expect(atualizarTipoProcesso).toHaveBeenCalledTimes(1);

    const campoRequerimento = within(linha(REQUERIMENTO.nome)).getByRole("spinbutton");
    expect(campoRequerimento).toHaveValue(3);
  });

  it("erro ao salvar uma linha aparece só nela; as demais continuam editáveis", async () => {
    atualizarTipoProcesso.mockRejectedValue(new Error("falha"));

    render(<AdminTiposProcessoPage />);
    await screen.findByText(LICITACAO.nome);

    const linhaLicitacao = linha(LICITACAO.nome);
    await userEvent.click(within(linhaLicitacao).getByRole("button", { name: "Salvar" }));

    expect(
      await within(linhaLicitacao).findByText("Não foi possível salvar o prazo de anonimização."),
    ).toBeInTheDocument();

    const linhaRequerimento = linha(REQUERIMENTO.nome);
    expect(within(linhaRequerimento).queryByText("Não foi possível salvar o prazo de anonimização.")).toBeNull();
    expect(within(linhaRequerimento).getByRole("spinbutton")).toBeEnabled();
    expect(within(linhaRequerimento).getByRole("button", { name: "Salvar" })).toBeEnabled();
  });

  it("exibe indicação explícita quando não há nenhum tipo cadastrado, mantendo o cadastro disponível", async () => {
    listarTiposProcesso.mockReset().mockResolvedValue([]);

    render(<AdminTiposProcessoPage />);

    expect(await screen.findByText("Nenhum tipo de processo cadastrado.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).toBeNull();
    expect(screen.getByLabelText("Nome do tipo de processo")).toBeInTheDocument();
  });
});
