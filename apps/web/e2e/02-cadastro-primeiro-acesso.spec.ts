import { expect, test } from "@playwright/test";

import { ADMIN_ROOT, NOVO_SERVIDOR, SETOR_INICIAL, UNIDADE_INICIAL } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Task 12.2 — Administrador cadastra usuário -> e-mail de primeiro acesso
// (mock do provedor via Settings.dev_email_inbox) -> usuário ativa conta -> login.
test("cadastro de usuário, primeiro acesso via e-mail mockado e login", async ({ page }) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  // Setor da unidade inicial: Servidor exige setor da própria unidade (D2).
  await cadastrarSetor(page, UNIDADE_INICIAL.nome, SETOR_INICIAL);

  await cadastrarUsuario(page, {
    nome: NOVO_SERVIDOR.nome,
    email: NOVO_SERVIDOR.email,
    unidadeNome: UNIDADE_INICIAL.nome,
    setor: SETOR_INICIAL,
  });

  const link = await obterUltimoLink(NOVO_SERVIDOR.email);
  await page.goto(link);

  await expect(page.getByRole("heading", { name: "Ativar sua conta" })).toBeVisible();
  await page.getByLabel("Nova senha", { exact: true }).fill(NOVO_SERVIDOR.senha);
  await page.getByLabel("Confirmar nova senha").fill(NOVO_SERVIDOR.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();

  await expect(page).toHaveURL(/\/perfil$/);
  await expect(page.getByText(`${NOVO_SERVIDOR.nome} · servidor`)).toBeVisible();

  await logout(page);
  await login(page, NOVO_SERVIDOR.email, NOVO_SERVIDOR.senha);
  await expect(page.getByText(`${NOVO_SERVIDOR.nome} · servidor`)).toBeVisible();
});
