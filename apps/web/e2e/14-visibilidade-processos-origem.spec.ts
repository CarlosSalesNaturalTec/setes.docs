import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario as cadastrarUsuarioAdmin } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_ORIGEM = { nome: "Coordenação Vis Origem", sigla: "CVORI" };
const UNIDADE_DESTINO = { nome: "Assessoria Vis Destino", sigla: "AVDES" };
const TIPO_PROCESSO = { nome: "Protocolo Visibilidade Origem" };
const SERVIDOR_A = {
  nome: "Servidor Vis A",
  email: "servidor.visa@example.com",
  senha: "SenhaVisA1",
};
const SERVIDOR_B = {
  nome: "Servidor Vis B",
  email: "servidor.visb@example.com",
  senha: "SenhaVisB1",
};
const ASSUNTO = "Processo de acompanhamento por origem";

async function cadastrarUsuario(
  page: import("@playwright/test").Page,
  usuario: { nome: string; email: string; senha: string },
  unidadeNome: string,
): Promise<void> {
  await cadastrarSetor(page, unidadeNome, SETOR_PADRAO);
  await cadastrarUsuarioAdmin(page, {
    nome: usuario.nome,
    email: usuario.email,
    unidadeNome,
    setor: SETOR_PADRAO,
  });

  const link = await obterUltimoLink(usuario.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(usuario.senha);
  await page.getByLabel("Confirmar nova senha").fill(usuario.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
}

// Task 6.1 (obrigatório) — change visibilidade-processos-origem. Cenário
// completo: despacho -> acompanhamento read-only na origem -> sigiloso some
// do acompanhamento -> devolução destaca o card -> novo despacho apaga o
// destaque. US 1.4 (revisada), US 2.3, US 2.6.
test("Servidor da origem acompanha em modo leitura, sigiloso some, devolução destaca e novo despacho apaga o destaque", async ({
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

  await cadastrarUsuario(page, SERVIDOR_A, UNIDADE_ORIGEM.nome);
  await logout(page);
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarUsuario(page, SERVIDOR_B, UNIDADE_DESTINO.nome);
  await logout(page);

  // Servidor A cria e despacha para a unidade de destino.
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();

  await page.getByRole("button", { name: "Despachar" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo despachado para ${UNIDADE_DESTINO.sigla}.`)).toBeVisible();

  // Kanban de A: card acinzentado (somente leitura), acompanhamento por origem.
  const cardOrigem = page.getByText(ASSUNTO).locator("..");
  await expect(cardOrigem).toHaveClass(/bg-gray-100/);

  // Detalhe em modo leitura: sem controles de ação.
  await page.goto(urlProcesso);
  await expect(
    page.getByText("Acompanhamento em modo leitura — este processo está atualmente em outra unidade."),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Despachar" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Devolver" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Marcar como Sigiloso" })).toHaveCount(0);

  // Servidor B marca o processo como sigiloso na unidade de destino.
  await logout(page);
  await login(page, SERVIDOR_B.email, SERVIDOR_B.senha);
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Marcar como Sigiloso" }).click();
  await expect(page.getByLabel("Sigiloso")).toBeVisible();

  // Sigiloso em outra unidade some do acompanhamento por origem de A —
  // Kanban e acesso direto negados.
  await logout(page);
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos");
  await expect(page.getByText(ASSUNTO)).toHaveCount(0);
  await page.goto(urlProcesso);
  await expect(page.getByText("Acesso restrito — solicite autorização ao Administrador")).toBeVisible();

  // Servidor B remove o sigilo e devolve o processo à origem.
  await logout(page);
  await login(page, SERVIDOR_B.email, SERVIDOR_B.senha);
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Remover Sigilo" }).click();
  await expect(page.getByLabel("Sigiloso")).toHaveCount(0);

  await page.getByRole("button", { name: "Devolver" }).click();
  const modalDevolucao = page.getByRole("dialog", { name: "Devolver processo" });
  await modalDevolucao.getByLabel("Motivo").selectOption({ label: "Documentação insuficiente" });
  await modalDevolucao.getByRole("button", { name: "Confirmar devolução" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo devolvido para ${UNIDADE_ORIGEM.sigla}.`)).toBeVisible();

  // Card de A exibe "↩ Devolvido" e volta acionável (não é mais somente leitura).
  await logout(page);
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos");
  const cardDevolvido = page.getByText(ASSUNTO).locator("..");
  await expect(cardDevolvido.getByText("↩ Devolvido")).toBeVisible();
  await expect(cardDevolvido).not.toHaveClass(/bg-gray-100/);

  await page.goto(urlProcesso);
  await expect(page.getByRole("button", { name: "Despachar" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Devolver" })).toBeVisible();

  // Novo despacho de A: o destaque de devolução some (histórico avançou).
  await page.getByRole("button", { name: "Despachar" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo despachado para ${UNIDADE_DESTINO.sigla}.`)).toBeVisible();

  await page.goto("/processos");
  const cardAposRedespacho = page.getByText(ASSUNTO).locator("..");
  await expect(cardAposRedespacho.getByText("↩ Devolvido")).toHaveCount(0);
  await expect(cardAposRedespacho).toHaveClass(/bg-gray-100/);
});
