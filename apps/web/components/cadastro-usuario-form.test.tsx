import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api, type Schemas } from "@/lib/api";
import { CadastroUsuarioForm } from "./cadastro-usuario-form";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { ...actual.api, cadastrarUsuario: vi.fn(), listarSetores: vi.fn() },
  };
});

const COFIN: Schemas["UnidadeResponse"] = {
  id: "u-cofin",
  nome: "COFIN",
  sigla: "COFIN",
  ativo: true,
  gestor_responsavel_id: null,
};
const AJUR: Schemas["UnidadeResponse"] = {
  id: "u-ajur",
  nome: "AJUR",
  sigla: "AJUR",
  ativo: true,
  gestor_responsavel_id: null,
};

const setor = (id: string, unidadeId: string, nome: string, sigla: string): Schemas["SetorResponse"] => ({
  id,
  unidade_id: unidadeId,
  nome,
  sigla,
  ativo: true,
});

const SETORES: Record<string, Schemas["SetorResponse"][]> = {
  "u-cofin": [setor("s-gab", "u-cofin", "Gabinete", "GAB")],
  "u-ajur": [setor("s-cons", "u-ajur", "Consultivo", "CONS")],
};

describe("CadastroUsuarioForm", () => {
  beforeEach(() => {
    vi.mocked(api.cadastrarUsuario).mockReset();
    vi.mocked(api.listarSetores).mockReset();
    vi.mocked(api.listarSetores).mockImplementation(async (unidadeId: string) => SETORES[unidadeId] ?? []);
  });

  it("exige setor para o perfil Servidor sem chamar a API", async () => {
    render(<CadastroUsuarioForm unidades={[COFIN]} perfilAtual="administrador" onCriado={vi.fn()} />);

    await userEvent.type(screen.getByLabelText("Nome"), "Maria Silva");
    await userEvent.type(screen.getByLabelText("E-mail"), "maria@example.com");
    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "u-cofin");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar usuário" }));

    expect(await screen.findByText(/setor é obrigatório/i)).toBeInTheDocument();
    expect(api.cadastrarUsuario).not.toHaveBeenCalled();
  });

  it("carrega os setores ativos da unidade escolhida e envia os campos novos", async () => {
    const onCriado = vi.fn();
    render(<CadastroUsuarioForm unidades={[COFIN, AJUR]} perfilAtual="administrador" onCriado={onCriado} />);

    await userEvent.type(screen.getByLabelText("Nome"), "Maria Silva");
    await userEvent.type(screen.getByLabelText("E-mail"), "maria@example.com");
    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "u-cofin");
    await waitFor(() => expect(api.listarSetores).toHaveBeenCalledWith("u-cofin", true));

    await userEvent.selectOptions(await screen.findByLabelText(/^Setor/), "s-gab");
    await userEvent.type(screen.getByLabelText("Telefone"), "(71) 99999-0000");
    await userEvent.type(screen.getByLabelText("Cargo"), "Analista");
    await userEvent.type(screen.getByLabelText("Chefia direta"), "Chefe Externo");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar usuário" }));

    await waitFor(() => expect(api.cadastrarUsuario).toHaveBeenCalledTimes(1));
    expect(api.cadastrarUsuario).toHaveBeenCalledWith({
      nome: "Maria Silva",
      email: "maria@example.com",
      perfil: "servidor",
      unidade_id: "u-cofin",
      setor_id: "s-gab",
      telefone: "(71) 99999-0000",
      cargo: "Analista",
      chefia_direta: "Chefe Externo",
    });
    expect(onCriado).toHaveBeenCalled();
  });

  it("limpa o setor e recarrega a lista ao trocar de unidade", async () => {
    render(<CadastroUsuarioForm unidades={[COFIN, AJUR]} perfilAtual="administrador" onCriado={vi.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "u-cofin");
    const selectSetor = await screen.findByLabelText<HTMLSelectElement>(/^Setor/);
    await userEvent.selectOptions(selectSetor, "s-gab");
    expect(selectSetor.value).toBe("s-gab");

    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "u-ajur");

    await waitFor(() => expect(selectSetor.value).toBe(""));
    await waitFor(() => expect(api.listarSetores).toHaveBeenCalledWith("u-ajur", true));
    expect(await screen.findByRole("option", { name: "Consultivo (CONS)" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Gabinete (GAB)" })).not.toBeInTheDocument();
  });

  it("aceita Gestor sem setor", async () => {
    render(<CadastroUsuarioForm unidades={[COFIN]} perfilAtual="administrador" onCriado={vi.fn()} />);

    await userEvent.type(screen.getByLabelText("Nome"), "Gestor Geral");
    await userEvent.type(screen.getByLabelText("E-mail"), "gestor@example.com");
    await userEvent.selectOptions(screen.getByLabelText("Perfil"), "gestor");
    await userEvent.selectOptions(screen.getByLabelText("Unidade"), "u-cofin");
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar usuário" }));

    await waitFor(() => expect(api.cadastrarUsuario).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.cadastrarUsuario).mock.calls[0][0].setor_id).toBeNull();
  });
});
