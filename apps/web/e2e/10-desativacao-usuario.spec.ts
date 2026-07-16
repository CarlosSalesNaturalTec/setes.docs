import { expect, test } from "@playwright/test";

import { ADMIN_ROOT, NOVO_SERVIDOR } from "./fixtures";
import { login, logout } from "./helpers/auth";

// Task 7.1 — Admin desativa um Servidor sem pendências e o Servidor perde o
// acesso de login imediatamente (US 8.4 Cen.1). Reaproveita o Servidor de
// 02-cadastro-primeiro-acesso/03-bloqueio-recuperacao, cuja senha final é
// "SenhaRecuperada1" (redefinida em 03).
const SENHA_ATUAL_SERVIDOR = "SenhaRecuperada1";

test("Admin desativa Servidor sem pendências — Servidor não consegue mais fazer login", async ({ page }) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/usuarios");
  const linha = page.getByRole("row", { name: new RegExp(NOVO_SERVIDOR.nome) });
  await expect(linha).toBeVisible();
  await linha.getByRole("button", { name: "Desativar Usuário" }).click();
  await expect(linha.getByText("inativo")).toBeVisible();

  await logout(page);

  await page.goto("/login");
  await page.getByLabel("E-mail").fill(NOVO_SERVIDOR.email);
  await page.getByLabel("Senha", { exact: true }).fill(SENHA_ATUAL_SERVIDOR);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(
    page.getByText("Conta desativada. Entre em contato com o Administrador do sistema."),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});
