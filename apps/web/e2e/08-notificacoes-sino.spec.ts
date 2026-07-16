import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const UNIDADE_ORIGEM = { nome: "Unidade Origem Sino", sigla: "ORISN" };
const UNIDADE_DESTINO = { nome: "Unidade Destino Sino", sigla: "DESIN" };
const TIPO_PROCESSO = { nome: "Fluxo com Sino" };
const SERVIDOR_ORIGEM = {
  nome: "Servidor Origem Sino",
  email: "servidor.origem.sino@example.com",
  senha: "SenhaOrigemSino1",
};
const SERVIDOR_DESTINO = {
  nome: "Servidor Destino Sino",
  email: "servidor.destino.sino@example.com",
  senha: "SenhaDestinoSino1",
};
const ASSUNTO_PROCESSO = "Processo do sino";

async function cadastrarEAtivar(
  page: import("@playwright/test").Page,
  servidor: { nome: string; email: string; senha: string },
  unidadeNome: string,
): Promise<void> {
  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(servidor.nome);
  await page.getByLabel("E-mail").fill(servidor.email);
  await page.getByLabel("Unidade").selectOption({ label: unidadeNome });
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(`Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${servidor.email}.`),
  ).toBeVisible();

  const link = await obterUltimoLink(servidor.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(servidor.senha);
  await page.getByLabel("Confirmar nova senha").fill(servidor.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
}

// Task 7.1 — E2E obrigatório do sino (US 5.1). Despacho de A para B gera
// notificação interna para os servidores de B: o contador incrementa, o
// painel mostra número/assunto/unidade de origem, e marcar como lida
// decrementa o contador e persiste após reload.
test("Despacho entre unidades incrementa o sino do destinatário; marcar como lida persiste após reload", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_ORIGEM.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_ORIGEM.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_ORIGEM.nome })).toBeVisible();

  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_DESTINO.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_DESTINO.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_DESTINO.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByLabel("Adicionar unidade ao roteiro").selectOption({ label: UNIDADE_ORIGEM.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByLabel("Adicionar unidade ao roteiro").selectOption({ label: UNIDADE_DESTINO.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  await cadastrarEAtivar(page, SERVIDOR_ORIGEM, UNIDADE_ORIGEM.nome);
  await logout(page);
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarEAtivar(page, SERVIDOR_DESTINO, UNIDADE_DESTINO.nome);
  await logout(page);

  // Servidor da unidade origem cria e despacha o processo para a unidade destino.
  await login(page, SERVIDOR_ORIGEM.email, SERVIDOR_ORIGEM.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO_PROCESSO);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);

  // O despacho move o processo para a unidade destino — o próprio Servidor
  // Origem perde acesso de visualização imediatamente depois (visibilidade
  // por unidade, D6), então a confirmação é pela resposta HTTP, não pela UI
  // pós-despacho.
  const respostaDespacho = page.waitForResponse(
    (resp) => resp.url().includes("/despachar") && resp.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Despachar" }).click();
  expect((await respostaDespacho).ok()).toBeTruthy();
  await logout(page);

  // Servidor da unidade destino vê o sino incrementar.
  await login(page, SERVIDOR_DESTINO.email, SERVIDOR_DESTINO.senha);
  await expect(page.getByTestId("notificacoes-contador")).toHaveText("1");

  await page.getByLabel("Notificações").click();
  await expect(page.getByText(ASSUNTO_PROCESSO)).toBeVisible();
  await expect(page.getByText(new RegExp(`vindo de ${UNIDADE_ORIGEM.nome}`))).toBeVisible();

  await page.getByText(ASSUNTO_PROCESSO).click();
  await expect(page.getByTestId("notificacoes-contador")).toHaveCount(0);

  await page.reload();
  await expect(page.getByTestId("notificacoes-contador")).toHaveCount(0);
});
