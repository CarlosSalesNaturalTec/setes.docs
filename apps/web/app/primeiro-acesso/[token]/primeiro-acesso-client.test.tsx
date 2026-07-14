import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "@/lib/api";

const push = vi.fn();
const definirSessao = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ definirSessao }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { ...actual.api, primeiroAcesso: vi.fn() },
  };
});

import { PrimeiroAcessoClient } from "./primeiro-acesso-client";

describe("PrimeiroAcessoClient", () => {
  beforeEach(() => {
    push.mockReset();
    definirSessao.mockReset();
    vi.mocked(api.primeiroAcesso).mockReset();
  });

  it("ativa a conta, estabelece a sessão e navega para /perfil", async () => {
    const usuario = { id: "u1", nome: "Fulano", email: "f@x.com", perfil: "servidor", status: "ativo" };
    vi.mocked(api.primeiroAcesso).mockResolvedValue({
      token: "jwt-emitido",
      exp: "2026-07-14T12:00:00Z",
      usuario,
    });

    render(<PrimeiroAcessoClient token="token-abc" />);

    await userEvent.type(screen.getByLabelText("Nova senha"), "Senha123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Ativar conta" }));

    await waitFor(() =>
      expect(api.primeiroAcesso).toHaveBeenCalledWith("token-abc", { senha: "Senha123" }),
    );
    expect(definirSessao).toHaveBeenCalledWith(usuario, "jwt-emitido");
    expect(push).toHaveBeenCalledWith("/perfil");
  });

  it("exibe erro de link expirado/já utilizado devolvido pela API", async () => {
    vi.mocked(api.primeiroAcesso).mockRejectedValue(new ApiError(410, "Link expirado"));

    render(<PrimeiroAcessoClient token="token-abc" />);

    await userEvent.type(screen.getByLabelText("Nova senha"), "Senha123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Ativar conta" }));

    expect(await screen.findByText("Link expirado")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });
});
