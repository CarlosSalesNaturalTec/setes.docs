import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const push = vi.fn();
const login = vi.fn();
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ login }),
}));

import LoginPage from "./page";

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockReset();
    login.mockReset();
    searchParams = new URLSearchParams();
  });

  it("exibe a mensagem correspondente ao motivo na query string", () => {
    searchParams = new URLSearchParams({ motivo: "inatividade" });
    render(<LoginPage />);

    expect(
      screen.getByText("Sua sessão expirou por inatividade. Faça login novamente."),
    ).toBeInTheDocument();
  });

  it("faz login com sucesso e navega para /perfil", async () => {
    login.mockResolvedValue(undefined);
    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("E-mail"), "usuario@setes.gov.br");
    await userEvent.type(screen.getByLabelText("Senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(login).toHaveBeenCalledWith("usuario@setes.gov.br", "Senha123"));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/perfil"));
  });

  it("exibe a mensagem de erro da API em caso de falha (ex.: bloqueio/conta desativada)", async () => {
    login.mockRejectedValue(new ApiError(403, "Conta desativada"));
    render(<LoginPage />);

    await userEvent.type(screen.getByLabelText("E-mail"), "usuario@setes.gov.br");
    await userEvent.type(screen.getByLabelText("Senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Conta desativada")).toBeInTheDocument();
  });
});
