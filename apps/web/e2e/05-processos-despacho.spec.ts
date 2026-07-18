import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const UNIDADE_PROCESSO = { nome: "Protocolo Central", sigla: "PROTC" };
const TIPO_PROCESSO = { nome: "Protocolo Simples" };
const SERVIDOR_PROTOCOLO = {
  nome: "Servidor Protocolo",
  email: "servidor.protocolo@example.com",
  senha: "SenhaProtocolo1",
};

// Task 4.5 — E2E obrigatório do despacho (US 2.1, 2.2 Cen.4, 2.4). Usa um
// roteiro de unidade única para exercitar o caminho mais curto até a
// conclusão: criar processo -> despachar (última/única etapa pede
// confirmação de conclusão) -> confirmar -> status "Concluído" -> evento de
// conclusão no histórico.
test("Servidor cria processo e despacha até a conclusão, com registro no histórico", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  // Unidade + tipo de processo com roteiro de uma única unidade (US 2.2 Cen.4).
  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_PROCESSO.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_PROCESSO.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_PROCESSO.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page
    .getByLabel("Adicionar unidade ao roteiro")
    .selectOption({ label: UNIDADE_PROCESSO.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  // Servidor vinculado à nova unidade.
  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(SERVIDOR_PROTOCOLO.nome);
  await page.getByLabel("E-mail").fill(SERVIDOR_PROTOCOLO.email);
  await page.getByLabel("Unidade", { exact: true }).selectOption({ label: UNIDADE_PROCESSO.nome });
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(
      `Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${SERVIDOR_PROTOCOLO.email}.`,
    ),
  ).toBeVisible();

  const link = await obterUltimoLink(SERVIDOR_PROTOCOLO.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_PROTOCOLO.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_PROTOCOLO.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  await logout(page);
  await login(page, SERVIDOR_PROTOCOLO.email, SERVIDOR_PROTOCOLO.senha);

  // Criação do processo (US 2.1) — redireciona direto para o detalhe.
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Solicitação de protocolo simples");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();

  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();
  await expect(page.getByText("Solicitação de protocolo simples")).toBeVisible();
  await expect(page.getByText("Aberto")).toBeVisible();

  // Kanban reflete o processo recém-criado na coluna "Aberto" (US 2.3).
  await page.goto("/processos");
  await expect(page.getByText("Solicitação de protocolo simples")).toBeVisible();

  // Despacho na única etapa do roteiro pede confirmação de conclusão (US 2.2 Cen.4).
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Despachar" }).click();
  const modal = page.getByRole("dialog", { name: "Confirmar conclusão" });
  await expect(
    modal.getByText(
      "Esta é a unidade de origem e destino final do roteiro. Deseja concluir o processo?",
    ),
  ).toBeVisible();
  await modal.getByRole("button", { name: "Concluir processo" }).click();

  await expect(page.getByText("Concluído")).toBeVisible();
  await expect(page.getByRole("button", { name: "Despachar" })).toHaveCount(0);

  // Histórico registra o evento de conclusão (US 2.4).
  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Conclusão")).toBeVisible();
});
