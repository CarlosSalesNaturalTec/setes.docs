import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "@/lib/api";
import { TrocarSenhaForm } from "./trocar-senha-form";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { ...actual.api, trocarSenha: vi.fn() },
  };
});

describe("TrocarSenhaForm", () => {
  beforeEach(() => {
    vi.mocked(api.trocarSenha).mockReset();
  });


  it("rejeita nova senha que não atende à complexidade sem chamar a API", async () => {
    render(<TrocarSenhaForm />);

    await userEvent.type(screen.getByLabelText("Senha atual"), "AtualSenha1");
    await userEvent.type(screen.getByLabelText("Nova senha"), "fraca");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "fraca");
    await userEvent.click(screen.getByRole("button", { name: "Trocar senha" }));

    expect(await screen.findByText(/mínimo 8 caracteres/i)).toBeInTheDocument();
    expect(api.trocarSenha).not.toHaveBeenCalled();
  });

  it("rejeita quando a confirmação da nova senha não coincide", async () => {
    render(<TrocarSenhaForm />);

    await userEvent.type(screen.getByLabelText("Senha atual"), "AtualSenha1");
    await userEvent.type(screen.getByLabelText("Nova senha"), "NovaSenha1");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "NovaSenha2");
    await userEvent.click(screen.getByRole("button", { name: "Trocar senha" }));

    expect(await screen.findByText("As senhas não coincidem.")).toBeInTheDocument();
    expect(api.trocarSenha).not.toHaveBeenCalled();
  });

  it("envia a troca e exibe a mensagem de sucesso da API", async () => {
    vi.mocked(api.trocarSenha).mockResolvedValue({ mensagem: "Senha alterada com sucesso." });
    render(<TrocarSenhaForm />);

    await userEvent.type(screen.getByLabelText("Senha atual"), "AtualSenha1");
    await userEvent.type(screen.getByLabelText("Nova senha"), "NovaSenha1");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "NovaSenha1");
    await userEvent.click(screen.getByRole("button", { name: "Trocar senha" }));

    await waitFor(() =>
      expect(api.trocarSenha).toHaveBeenCalledWith({
        senha_atual: "AtualSenha1",
        nova_senha: "NovaSenha1",
      }),
    );
    expect(await screen.findByText("Senha alterada com sucesso.")).toBeInTheDocument();
  });

  it("exibe a mensagem de erro da API (ex.: senha atual incorreta/repetida no histórico)", async () => {
    vi.mocked(api.trocarSenha).mockRejectedValue(
      new ApiError(400, "Senha já utilizada recentemente"),
    );
    render(<TrocarSenhaForm />);

    await userEvent.type(screen.getByLabelText("Senha atual"), "AtualSenha1");
    await userEvent.type(screen.getByLabelText("Nova senha"), "NovaSenha1");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "NovaSenha1");
    await userEvent.click(screen.getByRole("button", { name: "Trocar senha" }));

    expect(await screen.findByText("Senha já utilizada recentemente")).toBeInTheDocument();
  });
});
