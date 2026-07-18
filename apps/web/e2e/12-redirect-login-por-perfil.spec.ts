import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Tasks 3.1-3.4 — a rota inicial pós-login é determinística por
// perfil/auditoria (US 1.3 Cen.1): Servidor -> /processos, Gestor ->
// /dashboard, Administrador -> /admin/unidades, e a permissão de auditoria
// sobrepõe o destino do perfil.
const SERVIDOR_REDIRECT = {
  nome: "Servidor Redirect",
  email: "servidor.redirect@example.com",
  senha: "SenhaServidorRedirect1",
};
const GESTOR_REDIRECT = {
  nome: "Gestor Redirect",
  email: "gestor.redirect@example.com",
  senha: "SenhaGestorRedirect1",
};
const AUDITOR_REDIRECT = {
  nome: "Auditor Redirect",
  email: "auditor.redirect@example.com",
  senha: "SenhaAuditorRedirect1",
};

async function cadastrarEAtivar(
  page: import("@playwright/test").Page,
  usuario: { nome: string; email: string; senha: string },
  perfil: "servidor" | "gestor",
): Promise<void> {
  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(usuario.nome);
  await page.getByLabel("E-mail").fill(usuario.email);
  if (perfil === "gestor") {
    await page.getByLabel("Perfil").selectOption("gestor");
  }
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(`Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${usuario.email}.`),
  ).toBeVisible();

  const link = await obterUltimoLink(usuario.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(usuario.senha);
  await page.getByLabel("Confirmar nova senha").fill(usuario.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);
}

test.beforeAll(async ({ browser }) => {
  // 3 ciclos de cadastro + ativação em série — mais lento que o timeout
  // default de um único hook.
  test.setTimeout(90_000);
  const page = await browser.newPage();
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivar(page, SERVIDOR_REDIRECT, "servidor");

  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivar(page, GESTOR_REDIRECT, "gestor");

  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivar(page, AUDITOR_REDIRECT, "servidor");

  // `cadastrarEAtivar` termina com a sessão do usuário recém-ativado (não a
  // do Admin) deslogada — reautentica como Admin para conceder a permissão.
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await page.goto("/admin/usuarios");
  const linhaAuditor = page.getByRole("row", { name: new RegExp(AUDITOR_REDIRECT.nome) });
  await linhaAuditor.getByRole("button", { name: "Conceder Permissão de Auditoria" }).click();
  await expect(linhaAuditor.getByRole("button", { name: "Revogar Permissão de Auditoria" })).toBeVisible();
  await logout(page);

  await page.close();
});

test("Login como Administrador aterrissa em /admin/unidades", async ({ page }) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await expect(page).toHaveURL(/\/admin\/unidades$/);
});

test("Login como Servidor aterrissa em /processos", async ({ page }) => {
  await login(page, SERVIDOR_REDIRECT.email, SERVIDOR_REDIRECT.senha);
  await expect(page).toHaveURL(/\/processos$/);
});

test("Login como Gestor aterrissa em /dashboard", async ({ page }) => {
  await login(page, GESTOR_REDIRECT.email, GESTOR_REDIRECT.senha);
  await expect(page).toHaveURL(/\/dashboard$/);
});

test("Login com permissão de auditoria aterrissa em /auditoria/relatorios, sobrepondo o perfil", async ({
  page,
}) => {
  await login(page, AUDITOR_REDIRECT.email, AUDITOR_REDIRECT.senha);
  await expect(page).toHaveURL(/\/auditoria\/relatorios$/);
});
