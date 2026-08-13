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

  // Change login-logo-destaque: hero de marca original do cliente, sem chip.
  await expect(page.getByRole("heading", { name: "Despapelize" })).toBeVisible();
  await expect(page.getByAltText("Despapelize")).toBeVisible();

  await page.getByLabel("E-mail").fill(ADMIN_ROOT.email);
  await page.getByLabel("Senha", { exact: true }).fill(ADMIN_ROOT.senha);
  await page.getByRole("button", { name: "Entrar" }).click();

  // Administrador aterrissa em /admin/unidades — sua "razão de ser" é a
  // configuração do sistema, não há dashboard para esse perfil (US 1.3 Cen.1).
  await expect(page).toHaveURL(/\/admin\/unidades$/);
  await expect(page.getByText(`${ADMIN_ROOT.nome} · administrador`)).toBeVisible();
});
