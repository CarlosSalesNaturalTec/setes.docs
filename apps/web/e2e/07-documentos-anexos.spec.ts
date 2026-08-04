import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PARECER_PDF = path.join(__dirname, "fixtures", "parecer.pdf");

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_DOCUMENTOS = { nome: "Setor de Documentos", sigla: "SEDOC" };
const TIPO_PROCESSO = { nome: "Protocolo com Anexo" };
const SERVIDOR_DOCUMENTOS = {
  nome: "Servidor Documentos",
  email: "servidor.documentos@example.com",
  senha: "SenhaDocumentos1",
};

// Task 8.1 — E2E obrigatório do fluxo de anexo (US 3.1, US 3.2). A conclusão
// (change tramitacao-manual) é ação própria e não muda `unidade_atual_id`,
// então o mesmo Servidor permanece com acesso e podemos observar o bloqueio
// de remoção pós-conclusão na própria UI.
test("Servidor anexa, visualiza inline, baixa e remove um documento; remoção é bloqueada após conclusão", async ({
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
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO.nome, exact: true })).toBeVisible();

  await cadastrarSetor(page, UNIDADE_DOCUMENTOS.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_DOCUMENTOS.nome,
    email: SERVIDOR_DOCUMENTOS.email,
    unidadeNome: UNIDADE_DOCUMENTOS.nome,
    setor: SETOR_PADRAO,
  });

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

  // Anexa um segundo documento e conclui o processo (ação própria, US 2.5).
  await page.getByLabel("Anexar Documento").setInputFiles(PARECER_PDF);
  await expect(page.getByRole("button", { name: "parecer.pdf" })).toBeVisible();

  await page.getByRole("button", { name: "Detalhes" }).click();
  await page.getByRole("button", { name: "Concluir" }).click();
  const modalConclusao = page.getByRole("dialog", { name: "Confirmar conclusão" });
  await modalConclusao.getByRole("button", { name: "Concluir processo" }).click();
  await expect(page.getByText("Concluído")).toBeVisible();

  // Remoção bloqueada após conclusão — a ação não fica mais disponível (US 3.1 Cen.4).
  await page.getByRole("button", { name: "Documentos" }).click();
  await expect(page.getByRole("button", { name: "parecer.pdf" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Remover" })).toHaveCount(0);
});
