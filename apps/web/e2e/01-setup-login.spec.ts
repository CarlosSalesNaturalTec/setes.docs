import { expect, test } from "@playwright/test";

import { ADMIN_ROOT, UNIDADE_INICIAL } from "./fixtures";

// Task 12.1 — roda contra banco limpo (reset em global-setup.ts, antes de
// toda a suíte): US 8.0, setup só fica disponível enquanto não há Administrador.
test("setup inicial e login do Administrador root", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/setup$/);

  await page.getByLabel("Nome", { exact: true }).fill(ADMIN_ROOT.nome);
  await page.getByLabel("E-mail").fill(ADMIN_ROOT.email);
  await page.getByLabel("Senha", { exact: true }).fill(ADMIN_ROOT.senha);
  await page.getByLabel("Confirmar senha").fill(ADMIN_ROOT.senha);
  await page.getByLabel("Nome da unidade").fill(UNIDADE_INICIAL.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_INICIAL.sigla);
  await page.getByRole("button", { name: "Inicializar sistema" }).click();

  await expect(page).toHaveURL(/\/login\?motivo=setup-concluido/);
  await expect(
    page.getByText("Sistema inicializado com sucesso. Faça login para continuar."),
  ).toBeVisible();

  await page.getByLabel("E-mail").fill(ADMIN_ROOT.email);
  await page.getByLabel("Senha", { exact: true }).fill(ADMIN_ROOT.senha);
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/perfil$/);
  await expect(page.getByText(`${ADMIN_ROOT.nome} · administrador`)).toBeVisible();
});
