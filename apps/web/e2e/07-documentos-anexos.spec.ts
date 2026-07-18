import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARECER_PDF = path.join(__dirname, "fixtures", "parecer.pdf");

const UNIDADE_DOCUMENTOS = { nome: "Setor de Documentos", sigla: "SEDOC" };
const TIPO_PROCESSO = { nome: "Protocolo com Anexo" };
const SERVIDOR_DOCUMENTOS = {
  nome: "Servidor Documentos",
  email: "servidor.documentos@example.com",
  senha: "SenhaDocumentos1",
};

// Task 8.1 — E2E obrigatório do fluxo de anexo (US 3.1, US 3.2). Usa um
// roteiro de unidade única: o despacho conclui o processo sem mudar
// `unidade_atual_id` (design.md), então o mesmo Servidor permanece com
// acesso e podemos observar o bloqueio de remoção pós-despacho na própria UI.
test("Servidor anexa, visualiza inline, baixa e remove um documento; remoção é bloqueada após despacho", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_DOCUMENTOS.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_DOCUMENTOS.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_DOCUMENTOS.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page
    .getByLabel("Adicionar unidade ao roteiro")
    .selectOption({ label: UNIDADE_DOCUMENTOS.nome });
  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("heading", { name: TIPO_PROCESSO.nome })).toBeVisible();

  await page.goto("/admin/usuarios");
  await page.getByLabel("Nome", { exact: true }).fill(SERVIDOR_DOCUMENTOS.nome);
  await page.getByLabel("E-mail").fill(SERVIDOR_DOCUMENTOS.email);
  await page.getByLabel("Unidade", { exact: true }).selectOption({ label: UNIDADE_DOCUMENTOS.nome });
  await page.getByRole("button", { name: "Cadastrar usuário" }).click();
  await expect(
    page.getByText(
      `Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${SERVIDOR_DOCUMENTOS.email}.`,
    ),
  ).toBeVisible();

  const link = await obterUltimoLink(SERVIDOR_DOCUMENTOS.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_DOCUMENTOS.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_DOCUMENTOS.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await login(page, SERVIDOR_DOCUMENTOS.email, SERVIDOR_DOCUMENTOS.senha);

  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Processo com anexos");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);

  await page.getByRole("button", { name: "Documentos" }).click();
  await expect(page.getByText("Nenhum documento anexado.")).toBeVisible();

  // Anexar (US 3.1 Cen.1).
  await page.getByLabel("Anexar Documento").setInputFiles(PARECER_PDF);
  await expect(page.getByRole("button", { name: "parecer.pdf" })).toBeVisible();

  // Visualizar inline (US 3.2 Cen.1).
  await page.getByRole("button", { name: "parecer.pdf" }).click();
  const modalVisualizacao = page.getByRole("dialog", { name: "Visualizar parecer.pdf" });
  await expect(modalVisualizacao).toBeVisible();
  await modalVisualizacao.getByRole("button", { name: "Fechar" }).click();
  await expect(modalVisualizacao).not.toBeVisible();

  // Baixar mantendo nome e formato (US 3.2 Cen.2).
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Baixar" }).click(),
  ]);
  expect(download.suggestedFilename()).toBe("parecer.pdf");

  // Remover com confirmação, processo ainda Aberto (US 3.1 Cen.3).
  await page.getByRole("button", { name: "Remover" }).click();
  const modalRemocao = page.getByRole("dialog", { name: "Remover documento" });
  await modalRemocao.getByRole("button", { name: "Remover" }).click();
  await expect(page.getByText("Nenhum documento anexado.")).toBeVisible();

  // Anexa um segundo documento e despacha (roteiro de unidade única -> conclusão).
  await page.getByLabel("Anexar Documento").setInputFiles(PARECER_PDF);
  await expect(page.getByRole("button", { name: "parecer.pdf" })).toBeVisible();

  await page.getByRole("button", { name: "Detalhes" }).click();
  await page.getByRole("button", { name: "Despachar" }).click();
  const modalConclusao = page.getByRole("dialog", { name: "Confirmar conclusão" });
  await modalConclusao.getByRole("button", { name: "Concluir processo" }).click();
  await expect(page.getByText("Concluído")).toBeVisible();

  // Remoção bloqueada após despacho — a ação não fica mais disponível (US 3.1 Cen.4).
  await page.getByRole("button", { name: "Documentos" }).click();
  await expect(page.getByRole("button", { name: "parecer.pdf" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Remover" })).toHaveCount(0);
});
