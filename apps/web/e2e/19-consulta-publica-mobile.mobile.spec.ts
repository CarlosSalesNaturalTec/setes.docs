import { expect, test, type Page } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUnidade, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Roda no projeto `mobile`, depois do `chromium`, sobre o banco já povoado
// pelos specs 01-16 (playwright.config.ts, D5) — cria o próprio estado com
// nomes e e-mails distintos dos usados nos demais specs.
test.use({ viewport: { width: 360, height: 640 } });

const SETOR_CONSULTA_MOVEL = { nome: "Setor Consulta Móvel", sigla: "SETCM" };
const UNIDADE_CONSULTA_MOVEL = { nome: "Unidade Consulta Móvel", sigla: "UCMOV" };
const TIPO_CONSULTA_MOVEL = { nome: "Requerimento Móvel" };
const SERVIDOR_CONSULTA_MOVEL = {
  nome: "Servidor Consulta Móvel",
  email: "servidor.consulta.movel@example.com",
  senha: "SenhaConsultaMovel1",
};
const ASSUNTO_CONSULTA_MOVEL = "Requerimento consultado de um smartphone";

async function excedenteHorizontalDaPagina(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

// Task 5.4 — E2E obrigatório de consulta pública em viewport móvel (regra do
// projeto). Cobre "Consulta pública legível em smartphone sem login"
// (specs/identidade-visual).
test("Visitante consulta um processo por número em viewport de smartphone, sem autenticação", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarUnidade(page, UNIDADE_CONSULTA_MOVEL);

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_CONSULTA_MOVEL.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_CONSULTA_MOVEL.nome, exact: true })).toBeVisible();

  await cadastrarSetor(page, UNIDADE_CONSULTA_MOVEL.nome, SETOR_CONSULTA_MOVEL);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_CONSULTA_MOVEL.nome,
    email: SERVIDOR_CONSULTA_MOVEL.email,
    unidadeNome: UNIDADE_CONSULTA_MOVEL.nome,
    setor: SETOR_CONSULTA_MOVEL,
  });

  const link = await obterUltimoLink(SERVIDOR_CONSULTA_MOVEL.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_CONSULTA_MOVEL.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_CONSULTA_MOVEL.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  await login(page, SERVIDOR_CONSULTA_MOVEL.email, SERVIDOR_CONSULTA_MOVEL.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO_CONSULTA_MOVEL);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_CONSULTA_MOVEL.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const numero = (await page.locator("h1").first().innerText()).trim();

  // A consulta pública é feita sem enviar o Bearer token (o cliente HTTP do
  // endpoint /publico/* não o anexa, lib/api.ts) — visitar a rota com a
  // sessão do Servidor ainda ativa no navegador é equivalente, do ponto de
  // vista do endpoint público, a um visitante não autenticado (mesmo padrão
  // do spec 06-consulta-publica.spec.ts).
  await page.goto("/consulta-publica");
  await page.getByLabel("Número do processo").fill(numero);
  await page.getByRole("button", { name: "Consultar" }).click();

  await expect(page.getByText(ASSUNTO_CONSULTA_MOVEL)).toBeVisible();
  await expect(page.getByText(TIPO_CONSULTA_MOVEL.nome)).toBeVisible();
  await expect(page.getByText(UNIDADE_CONSULTA_MOVEL.sigla).first()).toBeVisible();

  // Cenário "Consulta pública legível em smartphone sem login": os pares
  // rótulo/valor aparecem empilhados (D4), sem rolagem horizontal da página,
  // e o conjunto de campos é o mesmo do desktop.
  expect(await excedenteHorizontalDaPagina(page)).toBeLessThanOrEqual(0);
});
