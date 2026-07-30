import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_DASHBOARD = { nome: "Unidade Dashboard", sigla: "DASHB" };
const TIPO_PROCESSO = { nome: "Processo Dashboard" };
const SERVIDOR_DASHBOARD = {
  nome: "Servidor Dashboard",
  email: "servidor.dashboard@example.com",
  senha: "SenhaServidorDash1",
};
const GESTORA_DASHBOARD = {
  nome: "Gestora Dashboard",
  email: "gestora.dashboard@example.com",
  senha: "SenhaGestoraDash1",
};

// Task 6.1 — Gestora vê os KPIs das unidades geridas, filtra por unidade e
// aciona o drill-down (US 6.1). Sem manipulação direta de banco, "Processos
// Parados" reflete o estado real (nenhum processo sem movimentação há mais
// que `dias_para_processo_parado`) — o clique exercita o mesmo caminho de
// integração ponta a ponta que um cenário com dado real.
test("Gestora vê os KPIs das unidades geridas, filtra por unidade e aciona o drill-down", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_DASHBOARD.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_DASHBOARD.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_DASHBOARD.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page
    .getByLabel("Adicionar unidade ao roteiro")
    .selectOption({ label: UNIDADE_DASHBOARD.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  // Servidor vinculado à unidade — cria o processo ativo usado pelos KPIs.
  await cadastrarSetor(page, UNIDADE_DASHBOARD.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_DASHBOARD.nome,
    email: SERVIDOR_DASHBOARD.email,
    unidadeNome: UNIDADE_DASHBOARD.nome,
    setor: SETOR_PADRAO,
  });

  // Gestora sem unidade (e sem setor, D2) — gerencia a unidade acima.
  await cadastrarUsuario(page, {
    nome: GESTORA_DASHBOARD.nome,
    email: GESTORA_DASHBOARD.email,
    perfil: "gestor",
  });

  const linhaGestora = page.getByRole("row", { name: new RegExp(GESTORA_DASHBOARD.nome) });
  await linhaGestora.getByRole("button", { name: "Unidades geridas" }).click();
  await linhaGestora.getByLabel(UNIDADE_DASHBOARD.nome).check();
  await linhaGestora.getByRole("button", { name: "Salvar" }).click();

  // Ativa as duas contas.
  const linkServidor = await obterUltimoLink(SERVIDOR_DASHBOARD.email);
  await page.goto(linkServidor);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_DASHBOARD.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_DASHBOARD.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  const linkGestora = await obterUltimoLink(GESTORA_DASHBOARD.email);
  await page.goto(linkGestora);
  await page.getByLabel("Nova senha", { exact: true }).fill(GESTORA_DASHBOARD.senha);
  await page.getByLabel("Confirmar nova senha").fill(GESTORA_DASHBOARD.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  // Servidor cria o processo ativo (US 2.1) na unidade do dashboard.
  await login(page, SERVIDOR_DASHBOARD.email, SERVIDOR_DASHBOARD.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Processo para o dashboard");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  await logout(page);

  // Gestora acessa o Dashboard (US 6.1 Cen.1).
  await login(page, GESTORA_DASHBOARD.email, GESTORA_DASHBOARD.senha);
  await page.goto("/dashboard");
  await expect(page.getByTestId("kpi-ativos")).toContainText("1");

  // Filtro por unidade gerida recalcula os KPIs (US 6.1 Cen.3).
  await page.getByLabel("Filtrar por unidade").selectOption({ label: UNIDADE_DASHBOARD.nome });
  await expect(page.getByTestId("kpi-ativos")).toContainText("1");

  // Drill-down de "Processos Ativos" chega à listagem detalhada (US 6.1 Cen.5).
  await page.getByTestId("kpi-ativos").click();
  await expect(page.getByRole("heading", { name: "Processos Ativos" })).toBeVisible();
  await expect(page.getByText("Processo para o dashboard")).toBeVisible();

  // Drill-down de "Processos Parados" chega à listagem detalhada (US 6.1 Cen.4).
  await page.getByTestId("kpi-parados").click();
  await expect(page.getByRole("heading", { name: "Processos Parados" })).toBeVisible();
});

// Task 6.2 — usuário sem perfil de Gestor não acessa a rota /dashboard.
test("Servidor não acessa o Dashboard (acesso negado)", async ({ page }) => {
  await login(page, SERVIDOR_DASHBOARD.email, SERVIDOR_DASHBOARD.senha);
  await page.goto("/dashboard");
  await expect(page.getByText("Acesso negado para o seu perfil.")).toBeVisible();
});
