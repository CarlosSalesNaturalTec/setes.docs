import { expect, type Page } from "@playwright/test";

export async function login(page: Page, email: string, senha: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  // A rota inicial pós-login varia por perfil/auditoria (US 1.3 Cen.1) — o
  // único invariante aqui é que a autenticação teve sucesso e saiu de /login.
  await expect(page).not.toHaveURL(/\/login$/);
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page).toHaveURL(/\/login$/);
}
