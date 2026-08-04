import { readFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUnidade, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Task 7.1 (obrigatório — altera fluxo de documentos). Change
// modelos-de-documento: Administrador cadastra um modelo com lacuna →
// Servidor cria processo escolhendo esse modelo, substitui a lacuna e salva →
// o PDF gerado aparece na lista de anexos do processo e é baixável → o
// Servidor remove o documento e o Administrador o restaura na área de
// documentos removidos.
const UNIDADE_MODELOS = { nome: "Unidade de Modelos", sigla: "UMOD" };
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GABM" };
const TIPO_PROCESSO = { nome: "Protocolo com Modelo" };
const SERVIDOR_MODELOS = {
  nome: "Servidor Modelos",
  email: "servidor.modelos@example.com",
  senha: "SenhaModelos1",
};
const MODELO = {
  nome: "Requerimento Padrão Modelo",
  categoria: "Pessoal",
};
const NOME_DOCUMENTO_GERADO = `${MODELO.nome}.pdf`;

test("Administrador cadastra modelo com lacuna; Servidor gera documento na abertura do processo; remoção e restauração funcionam", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  // Administrador cadastra o modelo com uma lacuna (US: Cadastro de modelo).
  // A tela de modelos abre na aba "Modelos cadastrados" por padrão (change
  // ajustes-ui-admin, design D2) — é preciso selecionar "Novo modelo" antes
  // de interagir com a ficha de cadastro.
  await page.goto("/admin/modelos");
  await page.getByRole("tab", { name: "Novo modelo" }).click();
  await page.getByLabel("Nome", { exact: true }).fill(MODELO.nome);
  await page.getByLabel("Categoria").fill(MODELO.categoria);
  await page.getByLabel("Tipo", { exact: true }).selectOption("requerimento");
  const editorModelo = page.getByRole("textbox", { name: "Conteúdo do modelo" });
  await editorModelo.click();
  await page.keyboard.type("Requerimento de [NOME DO SOLICITANTE], venho requerer análise.");
  await page.getByRole("button", { name: "Cadastrar modelo" }).click();
  await expect(page.getByRole("heading", { name: MODELO.nome })).toBeVisible();
  // Nenhuma ação de exclusão na tela (spec modelos-documento — Modelo não pode ser excluído).
  await expect(page.getByRole("button", { name: `Excluir ${MODELO.nome}` })).toHaveCount(0);

  // Estrutura organizacional + Servidor que vai usar o modelo.
  await cadastrarUnidade(page, UNIDADE_MODELOS);
  await cadastrarSetor(page, UNIDADE_MODELOS.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_MODELOS.nome,
    email: SERVIDOR_MODELOS.email,
    unidadeNome: UNIDADE_MODELOS.nome,
    setor: SETOR_PADRAO,
  });
  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  // Change ajustes-ui-admin: tipos de processo passam a ser listados em
  // tabela, uma linha por tipo, em vez de cards com título em heading.
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO.nome, exact: true })).toBeVisible();

  const link = await obterUltimoLink(SERVIDOR_MODELOS.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_MODELOS.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_MODELOS.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  await logout(page);
  await login(page, SERVIDOR_MODELOS.email, SERVIDOR_MODELOS.senha);

  // Servidor cria processo escolhendo o modelo e substituindo a lacuna.
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Processo aberto a partir de modelo");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByLabel("Modelo de documento (opcional)").selectOption({ label: MODELO.nome });

  const editorProcesso = page.getByRole("textbox", { name: "Conteúdo do documento a gerar" });
  await expect(editorProcesso).toContainText("[NOME DO SOLICITANTE]");
  await expect(page.getByText(/lacuna\(s\) ainda não preenchida/)).toBeVisible();

  await editorProcesso.click();
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.type("Requerimento de Maria da Silva, venho requerer análise.");
  await expect(page.getByText(/lacuna\(s\) ainda não preenchida/)).toHaveCount(0);

  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);

  // O PDF gerado aparece na lista de anexos do processo, disponível para download.
  await page.getByRole("button", { name: "Documentos" }).click();
  await expect(page.getByRole("button", { name: NOME_DOCUMENTO_GERADO })).toBeVisible();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Baixar" }).click(),
  ]);
  // O nome exato sugerido pelo navegador para nomes com acentuação é uma
  // particularidade do Chromium headless (fora do controle da aplicação — o
  // Content-Disposition do backend já é coberto por pytest); aqui validamos o
  // que importa para a US: o download é concluído e o conteúdo é um PDF real.
  const caminho = await download.path();
  const conteudo = caminho ? await readFile(caminho) : Buffer.alloc(0);
  expect(conteudo.subarray(0, 4).toString("latin1")).toBe("%PDF");

  // Servidor remove o documento.
  await page.getByRole("button", { name: "Remover" }).click();
  const modalRemocao = page.getByRole("dialog", { name: "Remover documento" });
  await modalRemocao.getByRole("button", { name: "Remover" }).click();
  await expect(page.getByText("Nenhum documento anexado.")).toBeVisible();

  // Administrador restaura o documento gerado na área de documentos removidos.
  await logout(page);
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await page.goto("/admin/documentos-removidos");
  const linhaDocumento = page
    .getByRole("row")
    .filter({ has: page.getByRole("cell", { name: NOME_DOCUMENTO_GERADO, exact: true }) });
  await expect(linhaDocumento).toBeVisible();
  await linhaDocumento.getByRole("button", { name: "Restaurar" }).click();
  await page.getByRole("dialog", { name: "Restaurar documento" }).getByRole("button", { name: "Restaurar" }).click();
  await expect(linhaDocumento).toHaveCount(0);
});
