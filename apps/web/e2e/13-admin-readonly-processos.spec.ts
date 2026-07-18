import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const UNIDADE_ADMIN_RO = { nome: "Unidade Admin RO", sigla: "ADMRO" };
const TIPO_PROCESSO_ADMIN_RO = { nome: "Tipo Admin RO" };
const SERVIDOR_ADMIN_RO = {
  nome: "Servidor Admin RO",
  email: "servidor.adminro@example.com",
  senha: "SenhaAdminRo1",
};

// Task 9.3 — o Administrador tem acesso read-only ao Kanban consolidado
// (US 2.3/2.8): mantém o link "Processos", mas nenhum controle de ação
// (Novo processo/Despachar/Devolver/sigilo) é exibido, pois o backend já
// rejeita essas ações para perfis não-Servidor.
test("Administrador não vê controles de ação em Processos nem no detalhe de um processo", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_ADMIN_RO.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_ADMIN_RO.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_ADMIN_RO.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO_ADMIN_RO.nome);
  await page
    .getByLabel("Adicionar unidade ao roteiro")
    .selectOption({ label: UNIDADE_ADMIN_RO.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO_ADMIN_RO.nome })).toBeVisible();

  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(SERVIDOR_ADMIN_RO.nome);
  await page.getByLabel("E-mail").fill(SERVIDOR_ADMIN_RO.email);
  await page.getByLabel("Unidade", { exact: true }).selectOption({ label: UNIDADE_ADMIN_RO.nome });
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(
      `Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${SERVIDOR_ADMIN_RO.email}.`,
    ),
  ).toBeVisible();

  const link = await obterUltimoLink(SERVIDOR_ADMIN_RO.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_ADMIN_RO.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_ADMIN_RO.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  // O Servidor cria o processo — o Admin nunca teria como (backend SERVIDOR-only).
  await logout(page);
  await login(page, SERVIDOR_ADMIN_RO.email, SERVIDOR_ADMIN_RO.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Processo para verificação de read-only do Admin");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO_ADMIN_RO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();

  // Reautentica como Administrador para inspecionar as telas de Processos.
  await logout(page);
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/processos");
  await expect(page.getByText("Processo para verificação de read-only do Admin")).toBeVisible();
  await expect(page.getByRole("link", { name: "Novo processo" })).toHaveCount(0);

  await page.goto(urlProcesso);
  await expect(page.getByText("Processo para verificação de read-only do Admin")).toBeVisible();
  await expect(page.getByRole("button", { name: "Despachar" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Devolver" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Marcar como Sigiloso" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Remover Sigilo" })).toHaveCount(0);
});
