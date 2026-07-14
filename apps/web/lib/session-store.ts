// Armazena o token JWT (D1) fora do React — um singleton simples com
// notificação de mudança, para que o cliente HTTP (lib/api.ts) e o contexto
// de autenticação (components/auth-provider.tsx) compartilhem a mesma fonte
// de verdade sem import circular.

const TOKEN_STORAGE_KEY = "setes.token";

type Listener = () => void;

let currentToken: string | null = null;
let hydrated = false;
const listeners = new Set<Listener>();

function hydrate(): void {
  if (hydrated || typeof window === "undefined") return;
  currentToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  hydrated = true;
}

export function getToken(): string | null {
  hydrate();
  return currentToken;
}

export function setToken(token: string | null): void {
  hydrate();
  currentToken = token;
  if (typeof window !== "undefined") {
    if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
  listeners.forEach((listener) => listener());
}

export function subscribeToken(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Decodifica o claim `exp` (segundos, epoch) de um JWT sem validar assinatura
 * — uso apenas para agendar o aviso de inatividade no client; a validação
 * real acontece sempre no backend. */
export function decodeJwtExp(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const claims = JSON.parse(json) as { exp?: number };
    return typeof claims.exp === "number" ? claims.exp : null;
  } catch {
    return null;
  }
}
