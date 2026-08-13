import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUnidade, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Roda no projeto `mobile`, depois do `chromium`, sobre o banco já povoado
// pelos specs 01-16 (playwright.config.ts, D5) — cria o próprio estado com
// nomes e e-mails distintos dos usados nos demais specs.
test.use({ viewport: { width: 360, height: 640 } });

const SETOR_MOVEL = { nome: "Setor Móvel", sigla: "SETMOV" };
const UNIDADE_MOVEL_ORIGEM = { nome: "Unidade Móvel Origem", sigla: "UMORI" };
const UNIDADE_MOVEL_DESTINO = { nome: "Unidade Móvel Destino", sigla: "UMDES" };
const TIPO_PROCESSO_MOVEL = { nome: "Protocolo Móvel" };
const SERVIDOR_MOVEL_ORIGEM = {
  nome: "Servidor Móvel Origem",
  email: "servidor.movel.origem@example.com",
  senha: "SenhaMovelOrigem1",
};
const SERVIDOR_MOVEL_DESTINO = {
  nome: "Servidor Móvel Destino",
  email: "servidor.movel.destino@example.com",
  senha: "SenhaMovelDestino1",
};
const ASSUNTO_MOVEL = "Processo tramitado a partir de smartphone";

// Task 5.3 — E2E obrigatório de tramitação em viewport móvel (regra do
// projeto). Cobre "Modal de tramitação mais alto que a tela é rolável" e
// "Tramitação se completa a partir de um smartphone" (specs/identidade-visual).
test("Servidor tramita um processo a partir de um smartphone, com o modal rolável e o histórico acrescido", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await cadastrarUnidade(page, UNIDADE_MOVEL_ORIGEM);
  await cadastrarUnidade(page, UNIDADE_MOVEL_DESTINO);

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO_MOVEL.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO_MOVEL.nome, exact: true })).toBeVisible();

  await cadastrarSetor(page, UNIDADE_MOVEL_ORIGEM.nome, SETOR_MOVEL);
  await cadastrarSetor(page, UNIDADE_MOVEL_DESTINO.nome, SETOR_MOVEL);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_MOVEL_ORIGEM.nome,
    email: SERVIDOR_MOVEL_ORIGEM.email,
    unidadeNome: UNIDADE_MOVEL_ORIGEM.nome,
    setor: SETOR_MOVEL,
  });
  await cadastrarUsuario(page, {
    nome: SERVIDOR_MOVEL_DESTINO.nome,
    email: SERVIDOR_MOVEL_DESTINO.email,
    unidadeNome: UNIDADE_MOVEL_DESTINO.nome,
    setor: SETOR_MOVEL,
  });

  const linkOrigem = await obterUltimoLink(SERVIDOR_MOVEL_ORIGEM.email);
  await page.goto(linkOrigem);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_MOVEL_ORIGEM.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_MOVEL_ORIGEM.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  const linkDestino = await obterUltimoLink(SERVIDOR_MOVEL_DESTINO.email);
  await page.goto(linkDestino);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_MOVEL_DESTINO.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_MOVEL_DESTINO.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  await login(page, SERVIDOR_MOVEL_ORIGEM.email, SERVIDOR_MOVEL_ORIGEM.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO_MOVEL);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO_MOVEL.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();

  // Modal de tramitação, ação "Enviar": unidade, setor, servidor e mensagem
  // mais cabeçalho e botões — em conteúdo mais longo (change futura, campo
  // adicional) isso excede a altura do viewport. O contêiner (o próprio
  // elemento role="dialog", com overflow-y-auto e items-start, D3) precisa
  // absorver esse excedente para que "Enviar" continue alcançável; quando não
  // há excedente, o botão já está visível sem rolagem — os dois casos são
  // cobertos abaixo sem assumir qual deles ocorre neste conteúdo.
  await page.getByRole("button", { name: "Tramitar" }).click();
  const modalEnvio = page.getByRole("dialog", { name: "Tramitar processo" });
  await modalEnvio.getByLabel("Unidade de destino").selectOption({ label: UNIDADE_MOVEL_DESTINO.nome });
  await modalEnvio.getByLabel("Setor de destino").selectOption({ label: SETOR_MOVEL.nome });
  await modalEnvio
    .getByLabel("Servidor de destino")
    .selectOption({ label: SERVIDOR_MOVEL_DESTINO.nome });
  await modalEnvio.getByLabel("Mensagem").fill("Enviado de um smartphone");

  const excedenteModal = await modalEnvio.evaluate((el) => el.scrollHeight - el.clientHeight);
  if (excedenteModal > 0) {
    await modalEnvio.evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    expect(await modalEnvio.evaluate((el) => el.scrollTop)).toBeGreaterThan(0);
  }

  const botaoEnviar = modalEnvio.getByRole("button", { name: "Enviar" });
  await expect(botaoEnviar).toBeVisible();
  await expect(botaoEnviar).toBeInViewport();
  await botaoEnviar.click();

  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo enviado para ${UNIDADE_MOVEL_DESTINO.sigla}.`)).toBeVisible();
  await logout(page);

  // O destinatário devolve — segundo evento no histórico, que deve se somar
  // ao primeiro, nunca substituí-lo (histórico imutável, CLAUDE.md).
  await login(page, SERVIDOR_MOVEL_DESTINO.email, SERVIDOR_MOVEL_DESTINO.senha);
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Tramitar" }).click();
  const modalDevolucao = page.getByRole("dialog", { name: "Tramitar processo" });
  await modalDevolucao.getByLabel("Tipo de ação").selectOption("devolver");
  await modalDevolucao.getByLabel("Motivo").selectOption({ label: "Documentação insuficiente" });
  await modalDevolucao
    .getByRole("button", { name: "Confirmar devolução" })
    .click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo devolvido para ${UNIDADE_MOVEL_ORIGEM.sigla}.`)).toBeVisible();
  await logout(page);

  await login(page, SERVIDOR_MOVEL_ORIGEM.email, SERVIDOR_MOVEL_ORIGEM.senha);
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Envio")).toBeVisible();
  await expect(page.getByText("Devolução")).toBeVisible();
});
