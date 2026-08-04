import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";
import { forcarArquivamento } from "./helpers/dev-tools";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_A = { nome: "Coordenação Quadro Pessoal", sigla: "CQP" };
const UNIDADE_B = { nome: "Assessoria Quadro Pessoal", sigla: "AQP" };
const TIPO_PROCESSO = { nome: "Protocolo Quadro Pessoal" };
const SERVIDOR_A = {
  nome: "Servidor Quadro A",
  email: "servidor.quadro.a@example.com",
  senha: "SenhaQuadroA1",
};
const SERVIDOR_B = {
  nome: "Servidor Quadro B",
  email: "servidor.quadro.b@example.com",
  senha: "SenhaQuadroB1",
};
const SERVIDOR_C = {
  nome: "Servidor Quadro C",
  email: "servidor.quadro.c@example.com",
  senha: "SenhaQuadroC1",
};
const ASSUNTO = "Processo do quadro pessoal do Servidor";

async function ativarConta(
  page: import("@playwright/test").Page,
  usuario: { email: string; senha: string },
): Promise<void> {
  const link = await obterUltimoLink(usuario.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(usuario.senha);
  await page.getByLabel("Confirmar nova senha").fill(usuario.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
}

// Task 7.2 (obrigatório — change kanban-por-servidor). Servidor A cria (ação
// no quadro) -> envia para B, de outra unidade (acompanhamento no quadro de
// A, com o nome de B) -> C, da mesma unidade de A mas que nunca tocou o
// processo, não o vê no quadro pessoal mas o abre por URL direta (autorização
// por unidade preservada, D6 herdado de visibilidade-processos-origem) -> B
// conclui -> o processo permanece visível para A como concluído (D4) ->
// arquivado, some do quadro de A até que "Exibir Arquivados" seja marcado.
test("quadro pessoal do Servidor: ação, acompanhamento, acesso por unidade preservado e arquivados ocultos por padrão", async ({
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
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO.nome, exact: true })).toBeVisible();

  // A e C na mesma unidade; B em outra.
  await cadastrarSetor(page, UNIDADE_A.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_A.nome,
    email: SERVIDOR_A.email,
    unidadeNome: UNIDADE_A.nome,
    setor: SETOR_PADRAO,
  });
  await cadastrarUsuario(page, {
    nome: SERVIDOR_C.nome,
    email: SERVIDOR_C.email,
    unidadeNome: UNIDADE_A.nome,
    setor: SETOR_PADRAO,
  });
  await cadastrarSetor(page, UNIDADE_B.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_B.nome,
    email: SERVIDOR_B.email,
    unidadeNome: UNIDADE_B.nome,
    setor: SETOR_PADRAO,
  });

  await ativarConta(page, SERVIDOR_A);
  await logout(page);
  await ativarConta(page, SERVIDOR_B);
  await logout(page);
  await ativarConta(page, SERVIDOR_C);
  await logout(page);

  // A cria o processo — aparece no quadro como ação (D2: sou o responsável atual).
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();

  await page.goto("/processos");
  const cardAcao = page.getByText(ASSUNTO).locator("..");
  await expect(cardAcao.getByText("Ação necessária")).toBeVisible();

  // A envia para B — vira acompanhamento no quadro de A, com o nome de B.
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Tramitar" }).click();
  const modal = page.getByRole("dialog", { name: "Tramitar processo" });
  await modal.getByLabel("Unidade de destino").selectOption({ label: UNIDADE_B.nome });
  await modal.getByLabel("Setor de destino").selectOption({ label: SETOR_PADRAO.nome });
  await modal.getByLabel("Servidor de destino").selectOption({ label: SERVIDOR_B.nome });
  await modal.getByRole("button", { name: "Enviar" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo enviado para ${UNIDADE_B.sigla}.`)).toBeVisible();

  const cardAcompanhamento = page.getByText(ASSUNTO).locator("..");
  await expect(cardAcompanhamento.getByText("Ação necessária")).toHaveCount(0);
  await expect(cardAcompanhamento.getByText(new RegExp(SERVIDOR_B.nome))).toBeVisible();
  await logout(page);

  // C, da mesma unidade de A, nunca tocou o processo: some do quadro pessoal
  // dele, mas o acesso direto continua permitido (autorização por unidade).
  await login(page, SERVIDOR_C.email, SERVIDOR_C.senha);
  await page.goto("/processos");
  await expect(page.getByText(ASSUNTO)).toHaveCount(0);
  await page.goto(urlProcesso);
  await expect(page.getByText(ASSUNTO)).toBeVisible();
  await logout(page);

  // B conclui o processo.
  await login(page, SERVIDOR_B.email, SERVIDOR_B.senha);
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Concluir" }).click();
  await page
    .getByRole("dialog", { name: "Confirmar conclusão" })
    .getByRole("button", { name: "Concluir processo" })
    .click();
  await expect(page.getByText("Concluído")).toBeVisible();
  await logout(page);

  // Concluído continua visível para A por padrão (D4).
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos");
  await expect(page.getByText(ASSUNTO)).toBeVisible();
  await logout(page);

  // Arquivamento (adiantado via dev tool, task 7.2): some do quadro de A até
  // marcar "Exibir Arquivados".
  await forcarArquivamento();

  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);
  await page.goto("/processos");
  await expect(page.getByText(ASSUNTO)).toHaveCount(0);

  await page.getByLabel("Exibir Arquivados").check();
  await expect(page.getByText(ASSUNTO)).toBeVisible();
});
