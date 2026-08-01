// Adianta a rotina diária de arquivamento automático (Settings.dev_db_reset)
// — ver apps/api/app/routers/dev_tools.py. Necessário porque, em produção,
// o arquivamento só roda via Cloud Scheduler + Cloud Run Job; sem este atalho
// dev/E2E-only, o cenário do quadro pessoal (change kanban-por-servidor,
// task 7.2) não teria como alcançar o estado Arquivado sem esperar dias.
const API_BASE_URL = "http://localhost:8000";

export async function forcarArquivamento(): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/internal/dev/arquivar-vencidos`, { method: "POST" });
  if (!resp.ok) {
    throw new Error(`Falha ao forçar o arquivamento: HTTP ${resp.status}`);
  }
}
