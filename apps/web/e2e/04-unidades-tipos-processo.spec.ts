import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const NOVA_UNIDADE = { nome: "Unidade de Licitações", sigla: "COLIC" };
const TIPO_PROCESSO = { nome: "Processo de Compra" };
const GESTORA = {
  nome: "Gestora Teste",
  email: "gestora.teste@example.com",
  senha: "SenhaGestora1",
};

// Task 12.4 — Administrador cadastra unidade e tipo de processo com roteiro;
// Gestor tenta as mesmas ações (admin-only, D4) e recebe acesso negado.
test("Administrador cadastra unidade/tipo de processo; Gestor recebe acesso negado nas mesmas ações", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(NOVA_UNIDADE.nome);
  await page.getByLabel("Sigla").fill(NOVA_UNIDADE.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: NOVA_UNIDADE.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByLabel("Adicionar unidade ao roteiro").selectOption({ label: NOVA_UNIDADE.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  // Administrador cadastra uma Gestora e ativa a conta (para o teste de acesso negado abaixo).
  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(GESTORA.nome);
  await page.getByLabel("E-mail").fill(GESTORA.email);
  await page.getByLabel("Perfil").selectOption("gestor");
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(`Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${GESTORA.email}.`),
  ).toBeVisible();

  const link = await obterUltimoLink(GESTORA.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(GESTORA.senha);
  await page.getByLabel("Confirmar nova senha").fill(GESTORA.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  // Gestora tenta cadastrar unidade -> acesso negado (require_perfil("administrador")).
  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill("Unidade Indevida");
  await page.getByLabel("Sigla").fill("IND");
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByText("Acesso negado para o seu perfil.")).toBeVisible();

  // Gestora tenta a página de tipos de processo -> também admin-only (US 8.2).
  await page.goto("/admin/tipos-processo");
  await expect(page.getByText("Acesso negado para o seu perfil.")).toBeVisible();
});
