import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { meuPerfil, atualizarMeuPerfil, recarregar } = vi.hoisted(() => ({
  meuPerfil: vi.fn(),
  atualizarMeuPerfil: vi.fn(),
  recarregar: vi.fn(),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ recarregar }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { meuPerfil, atualizarMeuPerfil },
  };
});

import PerfilPage from "./page";

const PERFIL = {
  usuario: {
    id: "u-1",
    nome: "Maria Souza",
    email: "maria@example.com",
    perfil: "servidor",
    status: "ativo",
    unidade_id: null,
    pode_auditar: false,
  },
  processos: [],
  documentos_assinados: [],
  mensagem_processos: "Nenhum processo registrado",
  mensagem_documentos: "Nenhum documento assinado",
};

describe("PerfilPage — editar o próprio nome (US 1.5)", () => {
  beforeEach(() => {
    meuPerfil.mockReset().mockResolvedValue(PERFIL);
    atualizarMeuPerfil.mockReset();
    recarregar.mockReset();
  });

  it("altera o nome com sucesso e atualiza a tela e o cabeçalho de sessão", async () => {
    atualizarMeuPerfil.mockResolvedValue({
      ...PERFIL,
      usuario: { ...PERFIL.usuario, nome: "Maria Souza Lima" },
    });

    render(<PerfilPage />);
    await screen.findByLabelText("Nome");

    const campoNome = screen.getByLabelText("Nome") as HTMLInputElement;
    await userEvent.clear(campoNome);
    await userEvent.type(campoNome, "Maria Souza Lima");
    await userEvent.click(screen.getByRole("button", { name: "Salvar nome" }));

    await waitFor(() => expect(atualizarMeuPerfil).toHaveBeenCalledWith({ nome: "Maria Souza Lima" }));
    expect(await screen.findByText("Nome atualizado com sucesso.")).toBeInTheDocument();
    await waitFor(() => expect(recarregar).toHaveBeenCalled());
  });

  it("exibe o erro de validação retornado pela API e mantém o nome anterior", async () => {
    atualizarMeuPerfil.mockRejectedValue(new ApiError(422, "Nome é obrigatório"));

    render(<PerfilPage />);
    await screen.findByLabelText("Nome");

    const campoNome = screen.getByLabelText("Nome") as HTMLInputElement;
    await userEvent.clear(campoNome);
    await userEvent.type(campoNome, "X");
    await userEvent.clear(campoNome);
    await userEvent.click(screen.getByRole("button", { name: "Salvar nome" }));

    expect(await screen.findByText("Nome é obrigatório")).toBeInTheDocument();
    expect(atualizarMeuPerfil).not.toHaveBeenCalled();
  });
});
