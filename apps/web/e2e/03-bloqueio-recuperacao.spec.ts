import { expect, test } from "@playwright/test";

import { NOVO_SERVIDOR } from "./fixtures";
import { login } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Task 12.3 — 3 tentativas incorretas -> bloqueio -> recuperação de senha ->
// desbloqueio automático (US 1.3 Cen.2/2b/2c). Reaproveita o Servidor ativado
// em 02-cadastro-primeiro-acesso.spec.ts.
test("bloqueio após 3 tentativas incorretas, recuperação de senha e desbloqueio automático", async ({
  page,
}) => {
  await page.goto("/login");

  for (let tentativa = 1; tentativa <= 3; tentativa++) {
    await page.getByLabel("E-mail").fill(NOVO_SERVIDOR.email);
    await page.getByLabel("Senha", { exact: true }).fill("SenhaErrada123");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(page.getByText("Credenciais inválidas.")).toBeVisible();
  }

  // 4ª tentativa, mesmo com a senha CORRETA, é rejeitada por bloqueio — não
  // reinicia o timer (US 1.3 Cen.2b).
  await page.getByLabel("E-mail").fill(NOVO_SERVIDOR.email);
  await page.getByLabel("Senha", { exact: true }).fill(NOVO_SERVIDOR.senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByText(/Conta bloqueada temporariamente/)).toBeVisible();

  await page.goto("/recuperar-senha");
  await page.getByLabel("E-mail").fill(NOVO_SERVIDOR.email);
  await page.getByRole("button", { name: "Enviar link de redefinição" }).click();
  await expect(
    page.getByText("Se o e-mail informado estiver cadastrado, um link de redefinição será enviado"),
  ).toBeVisible();

  const link = await obterUltimoLink(NOVO_SERVIDOR.email);
  await page.goto(link);
  await expect(page.getByRole("heading", { name: "Redefinir senha" })).toBeVisible();

  const novaSenha = "SenhaRecuperada1";
  await page.getByLabel("Nova senha", { exact: true }).fill(novaSenha);
  await page.getByLabel("Confirmar nova senha").fill(novaSenha);
  await page.getByRole("button", { name: "Redefinir senha" }).click();

  await expect(page).toHaveURL(/\/login\?motivo=senha-redefinida/);
  await expect(
    page.getByText("Senha redefinida com sucesso. Faça login com a nova senha."),
  ).toBeVisible();

  // Login com a nova senha só funciona se bloqueado_ate/tentativas tiverem
  // sido zerados na redefinição — confirma o desbloqueio automático.
  await login(page, NOVO_SERVIDOR.email, novaSenha);
  await expect(page.getByText(`${NOVO_SERVIDOR.nome} · servidor`)).toBeVisible();
});
