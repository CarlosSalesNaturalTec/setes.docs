import { expect, test } from "@playwright/test";

import { ADMIN_ROOT, NOVO_SERVIDOR } from "./fixtures";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Task 12.2 — Administrador cadastra usuário -> e-mail de primeiro acesso
// (mock do provedor via Settings.dev_email_inbox) -> usuário ativa conta -> login.
test("cadastro de usuário, primeiro acesso via e-mail mockado e login", async ({ page }) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(NOVO_SERVIDOR.nome);
  await page.getByLabel("E-mail").fill(NOVO_SERVIDOR.email);
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();

  await expect(
    page.getByText(
      `Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${NOVO_SERVIDOR.email}.`,
    ),
  ).toBeVisible();

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
