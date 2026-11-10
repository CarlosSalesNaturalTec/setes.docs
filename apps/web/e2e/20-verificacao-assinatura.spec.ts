import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUnidade, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Gerados por apps/api/scripts/pki_teste.py (webServer do playwright.config.ts).
const PKI_DIR = path.join(__dirname, ".pki");
const PDF_VALIDO = path.join(PKI_DIR, "assinado-valido.pdf");
const PDF_ADULTERADO = path.join(PKI_DIR, "assinado-adulterado.pdf");
const PDF_SEM_ASSINATURA = path.join(PKI_DIR, "sem-assinatura.pdf");
const API_BASE_URL = "http://localhost:8000";

const SETOR = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE = { nome: "Setor de Contratos", sigla: "SECON" };
const UNIDADE_OUTRA = { nome: "Setor Alheio", sigla: "SEALH" };
const TIPO_PROCESSO = { nome: "Contrato com Fornecedor" };
const SERVIDOR = {
  nome: "Servidor Contratos",
  email: "servidor.contratos@example.com",
  senha: "SenhaContratos1",
};
const INTRUSO = {
  nome: "Servidor Alheio",
  email: "servidor.alheio@example.com",
  senha: "SenhaAlheio1",
};

async function ativarConta(page: import("@playwright/test").Page, email: string, senha: string) {
  const link = await obterUltimoLink(email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(senha);
  await page.getByLabel("Confirmar nova senha").fill(senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

// Change assinatura-verificacao-fundacao, task 6.2 — E2E obrigatório (documentos
// é fluxo crítico). US 4.2 Cen.1/2 para PDFs assinados fora do sistema (G3), com a
// PKI de teste aceita só pela flag dev DEV_TRUST_ANCHOR_TESTE (D8).
test("Servidor verifica assinaturas de PDFs anexados; outra unidade tem acesso negado", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  await cadastrarUnidade(page, UNIDADE);
  await cadastrarUnidade(page, UNIDADE_OUTRA);
  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO.nome, exact: true })).toBeVisible();
  await cadastrarSetor(page, UNIDADE.nome, SETOR);
  await cadastrarSetor(page, UNIDADE_OUTRA.nome, SETOR);
  await cadastrarUsuario(page, {
    nome: SERVIDOR.nome,
    email: SERVIDOR.email,
    unidadeNome: UNIDADE.nome,
    setor: SETOR,
  });
  await cadastrarUsuario(page, {
    nome: INTRUSO.nome,
    email: INTRUSO.email,
    unidadeNome: UNIDADE_OUTRA.nome,
    setor: SETOR,
  });
  await logout(page);
  await ativarConta(page, SERVIDOR.email, SERVIDOR.senha);
  await ativarConta(page, INTRUSO.email, INTRUSO.senha);

  await login(page, SERVIDOR.email, SERVIDOR.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Contrato assinado pelo fornecedor");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const processoId = page.url().split("/").pop() as string;

  await page.getByRole("button", { name: "Documentos" }).click();
  await page.getByLabel("Anexar Documento").setInputFiles(PDF_VALIDO);
  await expect(page.getByRole("button", { name: "assinado-valido.pdf" })).toBeVisible();
  await page.getByLabel("Anexar Documento").setInputFiles(PDF_ADULTERADO);
  await expect(page.getByRole("button", { name: "assinado-adulterado.pdf" })).toBeVisible();
  await page.getByLabel("Anexar Documento").setInputFiles(PDF_SEM_ASSINATURA);
  await expect(page.getByRole("button", { name: "sem-assinatura.pdf" })).toBeVisible();
  await page.getByLabel("Anexar Documento").setInputFiles({
    name: "oficio.docx",
    mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    buffer: Buffer.concat([Buffer.from("PK\x03\x04", "binary"), Buffer.alloc(64)]),
  });
  await expect(page.getByRole("button", { name: "oficio.docx" })).toBeVisible();

  const linha = (nome: string) =>
    page.getByRole("listitem").filter({ has: page.getByRole("button", { name: nome }) });

  // DOCX não oferece a verificação — só PDF.
  await expect(
    linha("oficio.docx").getByRole("button", { name: "Verificar Assinatura" }),
  ).toHaveCount(0);

  // US 4.2 Cen.1 — assinatura válida, documento íntegro.
  await linha("assinado-valido.pdf").getByRole("button", { name: "Verificar Assinatura" }).click();
  const painel = page.getByRole("region", {
    name: "Verificação de assinatura — assinado-valido.pdf",
  });
  await expect(painel.getByText("Assinatura válida — documento íntegro")).toBeVisible();
  await expect(painel.getByText("MARIA DE TESTE DA SILVA")).toBeVisible();
  await expect(painel.getByText("12345678909")).toBeVisible();
  await expect(painel.getByText("AC Intermediaria de Teste")).toBeVisible();
  await expect(
    painel.getByRole("link", { name: "Abrir o verificador oficial do ITI" }),
  ).toHaveAttribute("href", "https://validar.iti.gov.br");

  // Painel cabe no celular sem rolagem horizontal (task 5.3).
  await page.setViewportSize({ width: 390, height: 844 });
  const semRolagem = await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  );
  expect(semRolagem).toBe(true);
  await page.setViewportSize({ width: 1280, height: 720 });
  await painel.getByRole("button", { name: "Fechar" }).click();
  await expect(painel).toHaveCount(0);

  // US 4.2 Cen.2 — adulterado após a assinatura: alerta de INVÁLIDA.
  await linha("assinado-adulterado.pdf")
    .getByRole("button", { name: "Verificar Assinatura" })
    .click();
  const painelAdulterado = page.getByRole("region", {
    name: "Verificação de assinatura — assinado-adulterado.pdf",
  });
  await expect(
    painelAdulterado.getByText(
      "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado",
    ),
  ).toBeVisible();
  await expect(painelAdulterado.getByRole("img", { name: "Alerta" })).toBeVisible();

  // PDF sem assinatura.
  await linha("sem-assinatura.pdf").getByRole("button", { name: "Verificar Assinatura" }).click();
  await expect(
    page
      .getByRole("region", { name: "Verificação de assinatura — sem-assinatura.pdf" })
      .getByText("Este documento não contém assinatura digital."),
  ).toBeVisible();

  const documentos = (await page.evaluate(async ([base, id]) => {
    const token = window.localStorage.getItem("setes.token");
    const resp = await fetch(`${base}/processos/${id}/documentos`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return (await resp.json()).items;
  }, [API_BASE_URL, processoId])) as { id: string; nome_exibicao: string }[];
  const docValido = documentos.find((d) => d.nome_exibicao === "assinado-valido.pdf");
  expect(docValido).toBeDefined();
  await logout(page);

  // Acesso negado explícito: servidor de outra unidade não verifica o documento.
  await login(page, INTRUSO.email, INTRUSO.senha);
  const status = await page.evaluate(
    async ([base, id, doc]) => {
      const token = window.localStorage.getItem("setes.token");
      const resp = await fetch(`${base}/processos/${id}/documentos/${doc}/verificacao`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return resp.status;
    },
    [API_BASE_URL, processoId, docValido!.id],
  );
  expect(status).toBe(403);
});
