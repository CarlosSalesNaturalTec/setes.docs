// Lê o link de primeiro acesso/recuperação de senha da caixa de entrada de
// dev (Settings.dev_email_inbox) em vez de um provedor de e-mail real —
// ver apps/api/app/routers/dev_tools.py.
const API_BASE_URL = "http://localhost:8000";

interface DevEmailItem {
  to: string;
  subject: string;
  body: string;
  event_id: string;
}

async function obterUltimoEmail(to: string): Promise<DevEmailItem> {
  const resp = await fetch(`${API_BASE_URL}/internal/dev/emails?to=${encodeURIComponent(to)}`);
  if (!resp.ok) throw new Error(`Falha ao consultar a caixa de entrada de dev: HTTP ${resp.status}`);
  const emails = (await resp.json()) as DevEmailItem[];
  const ultimo = emails.at(-1);
  if (!ultimo) throw new Error(`Nenhum e-mail encontrado para ${to}`);
  return ultimo;
}

/** Extrai o primeiro link http(s) do corpo do último e-mail enviado a `to`. */
export async function obterUltimoLink(to: string): Promise<string> {
  const email = await obterUltimoEmail(to);
  const match = email.body.match(/https?:\/\/\S+/);
  if (!match) throw new Error(`Link não encontrado no corpo do e-mail: ${email.body}`);
  return match[0];
}
