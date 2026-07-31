import { expect, type Page } from "@playwright/test";

const API_BASE_URL = "http://localhost:8000";

/**
 * Zera o contador em memória do rate limit de `/auth/*` (10/min/IP, D6) via o
 * endpoint gated por Settings.dev_rate_limit_reset. A suíte inteira sai do
 * mesmo IP e faz muito mais que 10 logins por minuto — sem isso o limite
 * dispara no meio dos fluxos e o login falha com "Too Many Requests".
 * O bloqueio por conta após 3 tentativas (D5, vive no Postgres) não é afetado.
 */
async function resetarRateLimit(): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/internal/dev/reset-rate-limit`, { method: "POST" });
  if (!resp.ok) {
    throw new Error(
      `Falha ao resetar o rate limit de autenticação: HTTP ${resp.status}. ` +
        "Confirme que a API está rodando com DEV_RATE_LIMIT_RESET=true.",
    );
  }
}

export async function login(page: Page, email: string, senha: string): Promise<void> {
  await resetarRateLimit();
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  // A rota inicial pós-login varia por perfil/auditoria (US 1.3 Cen.1) — o
  // único invariante aqui é que a autenticação teve sucesso e saiu de /login.
  await expect(page).not.toHaveURL(/\/login$/);
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page).toHaveURL(/\/login$/);
}
