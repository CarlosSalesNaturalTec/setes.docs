// Roda uma vez, depois que os webServers (API + web) já estão de pé — garante
// "banco limpo" (task 12.1) antes da suíte inteira via o endpoint de dev
// gated por Settings.dev_db_reset (nunca habilitado em produção).
const API_BASE_URL = "http://localhost:8000";

export default async function globalSetup(): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/internal/dev/reset`, { method: "POST" });
  if (!resp.ok) {
    throw new Error(
      `Falha ao resetar o banco de dev antes da suíte E2E: HTTP ${resp.status}. ` +
        "Confirme que a API está rodando com DEV_DB_RESET=true.",
    );
  }
}
