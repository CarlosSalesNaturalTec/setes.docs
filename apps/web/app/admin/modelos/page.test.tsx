import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listarModelos, criarModelo } = vi.hoisted(() => ({
  listarModelos: vi.fn(),
  criarModelo: vi.fn(),
}));

const { push } = vi.hoisted(() => ({ push: vi.fn() }));

let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarModelos, criarModelo },
  };
});

import AdminModelosPage from "./page";

const MODELO_EXISTENTE = {
  id: "m-1",
  nome: "Requerimento padrão",
  categoria: "Pessoal",
  tipo: "requerimento" as const,
  descricao: null,
  conteudo: "<p>Texto</p>",
  ativo: true,
};

const MODELO_NOVO = {
  ...MODELO_EXISTENTE,
  id: "m-2",
  nome: "Ofício de encaminhamento",
};

describe("AdminModelosPage — abas (change ajustes-ui-admin)", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    listarModelos.mockReset().mockResolvedValue([MODELO_EXISTENTE]);
    criarModelo.mockReset();
    push.mockReset();
  });

  it("abre com 'Modelos cadastrados' ativa por padrão, sem a ficha de cadastro", async () => {
    render(<AdminModelosPage />);

    expect(await screen.findByRole("tab", { name: "Modelos cadastrados" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await screen.findByText(MODELO_EXISTENTE.nome);
    expect(screen.queryByLabelText("Nome", { exact: true })).toBeNull();
  });

  it("cadastro bem-sucedido recarrega a listagem e troca para a aba 'Modelos cadastrados'", async () => {
    searchParams = new URLSearchParams("aba=novo");
    listarModelos.mockResolvedValueOnce([]).mockResolvedValueOnce([MODELO_EXISTENTE, MODELO_NOVO]);
    criarModelo.mockResolvedValue(MODELO_NOVO);

    render(<AdminModelosPage />);
    await screen.findByLabelText("Nome", { exact: true });

    await userEvent.type(screen.getByLabelText("Nome", { exact: true }), MODELO_NOVO.nome);
    await userEvent.type(screen.getByLabelText("Categoria"), MODELO_NOVO.categoria);
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar modelo" }));

    await waitFor(() => expect(criarModelo).toHaveBeenCalledTimes(1));
    // A troca de aba só acontece depois da listagem recarregada (design D3):
    // as duas chamadas de listarModelos precisam ter terminado antes do push.
    await waitFor(() => expect(listarModelos).toHaveBeenCalledTimes(2));
    expect(push).toHaveBeenCalledWith("/admin/modelos?aba=lista", { scroll: false });
  });

  it("cadastro rejeitado permanece na aba 'Novo modelo' com os dados preenchidos preservados", async () => {
    searchParams = new URLSearchParams("aba=novo");
    criarModelo.mockRejectedValue(new Error("falha"));

    render(<AdminModelosPage />);
    const campoNome = await screen.findByLabelText("Nome", { exact: true });

    await userEvent.type(campoNome, MODELO_NOVO.nome);
    await userEvent.type(screen.getByLabelText("Categoria"), MODELO_NOVO.categoria);
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar modelo" }));

    expect(await screen.findByText("Não foi possível cadastrar o modelo.")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
    expect(campoNome).toHaveValue(MODELO_NOVO.nome);
  });

  it("valor de aba desconhecido na URL cai na aba padrão 'Modelos cadastrados', sem erro", async () => {
    searchParams = new URLSearchParams("aba=inexistente");

    render(<AdminModelosPage />);

    expect(await screen.findByRole("tab", { name: "Modelos cadastrados" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.queryByText(/erro/i)).toBeNull();
  });
});
