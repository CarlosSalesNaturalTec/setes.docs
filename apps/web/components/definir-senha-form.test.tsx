import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";
import { MENSAGEM_COMPLEXIDADE_SENHA } from "@/lib/validacao";
import { DefinirSenhaForm } from "./definir-senha-form";

describe("DefinirSenhaForm (primeiro-acesso e redefinir-senha)", () => {
  it("rejeita senha que não atende à complexidade sem chamar onSubmit", async () => {
    const onSubmit = vi.fn();
    render(
      <DefinirSenhaForm titulo="t" descricao="d" textoBotao="Confirmar" onSubmit={onSubmit} />,
    );

    await userEvent.type(screen.getByLabelText("Nova senha"), "fraca");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "fraca");
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    // A dica estática e a mensagem de erro compartilham o mesmo texto (MENSAGEM_COMPLEXIDADE_SENHA).
    expect(await screen.findAllByText(MENSAGEM_COMPLEXIDADE_SENHA)).toHaveLength(2);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("rejeita quando a confirmação não coincide com a senha", async () => {
    const onSubmit = vi.fn();
    render(
      <DefinirSenhaForm titulo="t" descricao="d" textoBotao="Confirmar" onSubmit={onSubmit} />,
    );

    await userEvent.type(screen.getByLabelText("Nova senha"), "Senha123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "Senha456");
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText("As senhas não coincidem.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("chama onSubmit com a senha quando válida", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <DefinirSenhaForm titulo="t" descricao="d" textoBotao="Confirmar" onSubmit={onSubmit} />,
    );

    await userEvent.type(screen.getByLabelText("Nova senha"), "Senha123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("Senha123"));
  });

  it("exibe a mensagem de erro devolvida pela API (ex.: link expirado/já utilizado)", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new ApiError(410, "Link já utilizado"));
    render(
      <DefinirSenhaForm titulo="t" descricao="d" textoBotao="Confirmar" onSubmit={onSubmit} />,
    );

    await userEvent.type(screen.getByLabelText("Nova senha"), "Senha123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "Senha123");
    await userEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText("Link já utilizado")).toBeInTheDocument();
  });
});
