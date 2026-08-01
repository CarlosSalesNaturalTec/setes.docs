import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_CONSULTA = { nome: "Ouvidoria Pública", sigla: "OUVID" };
const TIPO_CONSULTA = { nome: "Requerimento Público" };
const SERVIDOR_CONSULTA = {
  nome: "Servidor Ouvidoria",
  email: "servidor.ouvidoria@example.com",
  senha: "SenhaOuvidoria1",
};

// Tasks 7.1/7.2/7.3 — E2E obrigatório da Consulta Pública (US 7.1, 7.2). A
// conclusão é ação própria (change tramitacao-manual) — não depende de
// roteiro/despacho (removidos pelo change tramitacao-manual). A consulta
// pública não exige logout — o endpoint público
// não envia o Bearer token (lib/api.ts) — então visitamos /consulta-publica
// com a sessão do Servidor ainda ativa no navegador, o que também evita
// consumir mais tentativas do rate limit de login (10/min/IP) do que o necessário.
test("cidadão consulta processo por número, sigiloso é indistinguível de inexistente, e pesquisa lista/pagina resultados", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_CONSULTA.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_CONSULTA.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_CONSULTA.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_CONSULTA.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_CONSULTA.nome })).toBeVisible();

  await cadastrarSetor(page, UNIDADE_CONSULTA.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_CONSULTA.nome,
    email: SERVIDOR_CONSULTA.email,
    unidadeNome: UNIDADE_CONSULTA.nome,
    setor: SETOR_PADRAO,
  });

  const link = await obterUltimoLink(SERVIDOR_CONSULTA.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_CONSULTA.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_CONSULTA.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  await logout(page);
  await login(page, SERVIDOR_CONSULTA.email, SERVIDOR_CONSULTA.senha);

  // Processo A: será consultado publicamente e depois marcado sigiloso.
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Requerimento de acesso à informação");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_CONSULTA.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcessoA = page.url();
  const numeroA = (await page.locator("h1").first().innerText()).trim();

  // Conclusão como ação própria — direto de "Aberto" (US 2.5).
  await page.getByRole("button", { name: "Concluir" }).click();
  await page
    .getByRole("dialog", { name: "Confirmar conclusão" })
    .getByRole("button", { name: "Concluir processo" })
    .click();
  await expect(page.getByText("Concluído")).toBeVisible();

  // 7.1 — Consulta pública do Processo A (não sigiloso), sem precisar sair da
  // sessão: o endpoint público não usa o Bearer token (US 7.1 Cen.1).
  await page.goto("/consulta-publica");
  await page.getByLabel("Número do processo").fill(numeroA);
  await page.getByRole("button", { name: "Consultar" }).click();
  await expect(page.getByText("Requerimento de acesso à informação")).toBeVisible();
  await expect(page.getByText("Concluído").first()).toBeVisible();
  await expect(page.getByText("Histórico de movimentações")).toBeVisible();
  await expect(page.getByText(UNIDADE_CONSULTA.sigla).first()).toBeVisible();

  // Marca o Processo A como sigiloso (Servidor da própria unidade já pode, US 2.6).
  await page.goto(urlProcessoA);
  await page.getByRole("button", { name: /sigilo/i }).click();

  // 7.2 — Consulta pelo número do sigiloso é indistinguível de inexistente.
  await page.goto("/consulta-publica");
  await page.getByLabel("Número do processo").fill(numeroA);
  await page.getByRole("button", { name: "Consultar" }).click();
  await expect(
    page.getByText("Nenhum processo encontrado com o número informado"),
  ).toBeVisible();

  await page.getByLabel("Número do processo").fill("2026/000000");
  await page.getByRole("button", { name: "Consultar" }).click();
  await expect(
    page.getByText("Nenhum processo encontrado com o número informado"),
  ).toBeVisible();

  // Processo B: permanece não sigiloso, usado na pesquisa por assunto (US 7.2).
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Requerimento de segunda via de documento");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_CONSULTA.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);

  await logout(page);

  // 7.3 — Pesquisa pública lista o Processo B (não sigiloso) e não o Processo A.
  await page.goto("/consulta-publica");
  await page.getByLabel("Assunto").fill("Requerimento de segunda via");
  await page.getByRole("button", { name: "Pesquisar" }).click();
  await expect(page.getByText("Requerimento de segunda via de documento")).toBeVisible();

  await page.getByLabel("Assunto").fill("Termo que não casa com nenhum processo");
  await page.getByRole("button", { name: "Pesquisar" }).click();
  await expect(
    page.getByText("Nenhum processo encontrado para os filtros informados"),
  ).toBeVisible();
});
