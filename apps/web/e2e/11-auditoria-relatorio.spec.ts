import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_A = { nome: "Unidade Auditoria A", sigla: "AUDA" };
const UNIDADE_B = { nome: "Unidade Auditoria B", sigla: "AUDB" };
const TIPO_PROCESSO = { nome: "Processo Auditoria" };
const DONO = {
  nome: "Servidor Dono Auditoria",
  email: "dono.auditoria@example.com",
  senha: "SenhaDonoAuditoria1",
};
const INTRUSO = {
  nome: "Servidor Intruso Auditoria",
  email: "intruso.auditoria@example.com",
  senha: "SenhaIntrusoAuditoria1",
};
const AUDITOR = {
  nome: "Auditor Autorizado",
  email: "auditor.autorizado@example.com",
  senha: "SenhaAuditorAutorizado1",
};

const MSG_ACESSO_RESTRITO = "Acesso restrito — solicite autorização ao Administrador";

let processoUrl = "";

async function cadastrarEAtivarServidor(
  page: import("@playwright/test").Page,
  usuario: { nome: string; email: string; senha: string },
  unidade: { nome: string },
): Promise<void> {
  await cadastrarSetor(page, unidade.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: usuario.nome,
    email: usuario.email,
    unidadeNome: unidade.nome,
    setor: SETOR_PADRAO,
  });

  const link = await obterUltimoLink(usuario.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(usuario.senha);
  await page.getByLabel("Confirmar nova senha").fill(usuario.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);
}

// Task 6.1 — auditor autorizado enxerga processo sigiloso de outra unidade
// (US 9.1 Cen.1); usuário sem permissão recebe a mensagem específica do PRD
// (US 9.1 Cen.2). Prepara o cenário: duas unidades, um Dono (unidade A) que
// cria e marca o processo como sigiloso, um Intruso (unidade B, sem
// permissão) e um Auditor (unidade B, com `pode_auditar` concedida).
test("Auditor autorizado acessa processo sigiloso de outra unidade; usuário sem permissão recebe acesso restrito", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_A.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_A.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_A.nome })).toBeVisible();

  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_B.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_B.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_B.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivarServidor(page, DONO, UNIDADE_A);

  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivarServidor(page, INTRUSO, UNIDADE_B);

  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarUsuario(page, {
    nome: AUDITOR.nome,
    email: AUDITOR.email,
    unidadeNome: UNIDADE_B.nome,
    setor: SETOR_PADRAO,
  });
  const linhaAuditor = page.getByRole("row", { name: new RegExp(AUDITOR.nome) });
  await linhaAuditor.getByRole("button", { name: "Conceder Permissão de Auditoria" }).click();
  await expect(linhaAuditor.getByRole("button", { name: "Revogar Permissão de Auditoria" })).toBeVisible();

  const linkAuditor = await obterUltimoLink(AUDITOR.email);
  await page.goto(linkAuditor);
  await page.getByLabel("Nova senha", { exact: true }).fill(AUDITOR.senha);
  await page.getByLabel("Confirmar nova senha").fill(AUDITOR.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  // Dono (unidade A) cria o processo e o marca como sigiloso.
  await login(page, DONO.email, DONO.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Processo Confidencial de Auditoria");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  processoUrl = page.url();

  await page.getByRole("button", { name: "Marcar como Sigiloso" }).click();
  await expect(page.getByTitle("Sigiloso")).toBeVisible();
  await logout(page);

  // Intruso (unidade B, sem permissão de auditoria) tenta acessar direto pela URL.
  await login(page, INTRUSO.email, INTRUSO.senha);
  await page.goto(processoUrl);
  await expect(page.getByText(MSG_ACESSO_RESTRITO)).toBeVisible();
  // A rota de relatório também é bloqueada para quem não tem a permissão.
  await expect(page.getByRole("link", { name: "Relatório de Auditoria" })).not.toBeVisible();
  await page.goto("/auditoria/relatorios");
  await expect(page.getByText("Acesso negado — permissão de auditoria necessária.")).toBeVisible();
  await logout(page);

  // Auditor autorizado (unidade B) enxerga o processo sigiloso completo.
  await login(page, AUDITOR.email, AUDITOR.senha);
  await page.goto(processoUrl);
  await expect(page.getByText(MSG_ACESSO_RESTRITO)).not.toBeVisible();
  await expect(page.getByText("Processo Confidencial de Auditoria")).toBeVisible();
  await expect(page.getByTitle("Sigiloso")).toBeVisible();
  await logout(page);
});

// Task 6.2 — Auditor gera o relatório consolidado (US 9.2 Cen.1) e vê o
// estado vazio quando os filtros não retornam resultado (US 9.2 Cen.2).
// Reaproveita o processo sigiloso criado no teste anterior (mesma unidade A).
test("Auditor gera relatório consolidado com filtros e vê o estado vazio", async ({ page }) => {
  await login(page, AUDITOR.email, AUDITOR.senha);

  await page.getByRole("link", { name: "Relatório de Auditoria" }).click();
  await expect(page).toHaveURL(/\/auditoria\/relatorios$/);

  await page.getByLabel("Unidade", { exact: true }).selectOption({ label: UNIDADE_A.nome });
  await page.getByRole("button", { name: "Gerar relatório" }).click();
  await expect(page.getByTestId("relatorio-total")).toContainText("1");
  await expect(page.getByTestId("relatorio-lista")).toContainText("Processo Confidencial de Auditoria");

  // Período sem processos criados -> estado vazio (US 9.2 Cen.2).
  await page.getByLabel("Período — início").fill("2000-01-01");
  await page.getByLabel("Período — fim").fill("2000-01-02");
  await page.getByRole("button", { name: "Gerar relatório" }).click();
  await expect(
    page.getByText("Nenhum dado encontrado para os filtros informados"),
  ).toBeVisible();
});
