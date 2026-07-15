// Cliente HTTP tipado do contrato OpenAPI (@setes/api-types, task 11.7 — sem
// `any` nos payloads de request/response). Consome app.security.autorizacao's
// contrato de sessão (D1): toda resposta autenticada pode trazer um novo JWT
// no header `X-Renewed-Token` (sliding window) — capturado aqui e persistido.
import type { components, paths } from "@setes/api-types";

import { getToken, setToken } from "./session-store";

type Schemas = components["schemas"];

// Tipo da resposta do /health do backend, derivado do contrato OpenAPI.
export type HealthResponse =
  paths["/health"]["get"]["responses"]["200"]["content"]["application/json"];

export const apiHealthPath = "/health" satisfies keyof paths;

export function isHealthy(payload: HealthResponse): boolean {
  return payload.status === "ok";
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  auth?: boolean;
  query?: Record<string, string | number | undefined>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function request<TResponse>(
  path: string,
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE",
  body: unknown,
  options: RequestOptions = {},
): Promise<TResponse> {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (options.auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const resp = await fetch(buildUrl(path, options.query), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const renewed = resp.headers.get("x-renewed-token");
  if (renewed) setToken(renewed);

  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const errorBody = (await resp.json()) as { detail?: string };
      if (errorBody.detail) detail = errorBody.detail;
    } catch {
      // corpo de erro não é JSON — mantém statusText
    }
    throw new ApiError(resp.status, detail);
  }

  if (resp.status === 204) return undefined as TResponse;
  return (await resp.json()) as TResponse;
}

const get = <TResponse>(path: string, options?: RequestOptions) =>
  request<TResponse>(path, "GET", undefined, options);
const post = <TBody, TResponse>(path: string, body: TBody, options?: RequestOptions) =>
  request<TResponse>(path, "POST", body, options);
const patch = <TBody, TResponse>(path: string, body: TBody, options?: RequestOptions) =>
  request<TResponse>(path, "PATCH", body, options);
const put = <TBody, TResponse>(path: string, body: TBody, options?: RequestOptions) =>
  request<TResponse>(path, "PUT", body, options);
const del = <TResponse>(path: string, options?: RequestOptions) =>
  request<TResponse>(path, "DELETE", undefined, options);

export const api = {
  // Inicialização (US 8.0)
  setupStatus: () => get<Schemas["SetupStatusResponse"]>("/setup/status"),
  setup: (body: Schemas["SetupRequest"]) => post<Schemas["SetupRequest"], Schemas["SetupResponse"]>("/setup", body),

  // Autenticação
  login: (body: Schemas["LoginRequest"]) =>
    post<Schemas["LoginRequest"], Schemas["LoginResponse"]>("/auth/login", body),
  logout: () => post<undefined, Schemas["MensagemResponse"]>("/auth/logout", undefined, { auth: true }),
  me: () => get<Schemas["MeResponse"]>("/auth/me", { auth: true }),
  primeiroAcesso: (token: string, body: Schemas["PrimeiroAcessoRequest"]) =>
    post<Schemas["PrimeiroAcessoRequest"], Schemas["LoginResponse"]>(
      `/auth/primeiro-acesso/${encodeURIComponent(token)}`,
      body,
    ),
  recuperarSenha: (body: Schemas["RecuperarSenhaRequest"]) =>
    post<Schemas["RecuperarSenhaRequest"], Schemas["MensagemResponse"]>("/auth/recuperar-senha", body),
  redefinirSenha: (token: string, body: Schemas["RedefinirSenhaRequest"]) =>
    post<Schemas["RedefinirSenhaRequest"], Schemas["MensagemResponse"]>(
      `/auth/redefinir-senha/${encodeURIComponent(token)}`,
      body,
    ),
  trocarSenha: (body: Schemas["TrocarSenhaRequest"]) =>
    post<Schemas["TrocarSenhaRequest"], Schemas["MensagemResponse"]>("/auth/trocar-senha", body, { auth: true }),

  // Meu Perfil
  meuPerfil: () => get<Schemas["MeuPerfilResponse"]>("/usuarios/me/perfil", { auth: true }),

  // Gestão de usuários
  listarUsuarios: (page = 1) =>
    get<Schemas["ListaUsuariosResponse"]>("/usuarios", { auth: true, query: { page } }),
  cadastrarUsuario: (body: Schemas["CadastroUsuarioRequest"]) =>
    post<Schemas["CadastroUsuarioRequest"], Schemas["UsuarioResponse"]>("/usuarios", body, { auth: true }),
  transferirUnidade: (usuarioId: string, body: Schemas["TransferirUnidadeRequest"]) =>
    patch<Schemas["TransferirUnidadeRequest"], Schemas["UsuarioResponse"]>(
      `/usuarios/${usuarioId}/unidade`,
      body,
      { auth: true },
    ),
  obterUnidadesGeridas: (usuarioId: string) =>
    get<string[]>(`/usuarios/${usuarioId}/unidades-geridas`, { auth: true }),
  definirUnidadesGeridas: (usuarioId: string, body: Schemas["UnidadesGeridasRequest"]) =>
    put<Schemas["UnidadesGeridasRequest"], string[]>(`/usuarios/${usuarioId}/unidades-geridas`, body, {
      auth: true,
    }),
  resetarSenhaAdmin: (usuarioId: string) =>
    post<undefined, Schemas["MensagemResponse"]>(`/admin/usuarios/${usuarioId}/resetar-senha`, undefined, {
      auth: true,
    }),

  // Unidades administrativas
  listarUnidades: () => get<Schemas["UnidadeResponse"][]>("/unidades", { auth: true }),
  cadastrarUnidade: (body: Schemas["CadastroUnidadeRequest"]) =>
    post<Schemas["CadastroUnidadeRequest"], Schemas["UnidadeResponse"]>("/unidades", body, { auth: true }),
  editarUnidade: (unidadeId: string, body: Schemas["EditarUnidadeRequest"]) =>
    patch<Schemas["EditarUnidadeRequest"], Schemas["UnidadeResponse"]>(`/unidades/${unidadeId}`, body, {
      auth: true,
    }),
  desativarUnidade: (unidadeId: string) =>
    post<undefined, Schemas["UnidadeResponse"]>(`/unidades/${unidadeId}/desativar`, undefined, { auth: true }),

  // Tipos de processo e roteiros
  listarTiposProcesso: () => get<Schemas["TipoProcessoResponse"][]>("/tipos-processo", { auth: true }),
  criarTipoProcesso: (body: Schemas["CriarTipoProcessoRequest"]) =>
    post<Schemas["CriarTipoProcessoRequest"], Schemas["TipoProcessoResponse"]>("/tipos-processo", body, {
      auth: true,
    }),
  atualizarRoteiro: (tipoProcessoId: string, body: Schemas["AtualizarRoteiroRequest"]) =>
    put<Schemas["AtualizarRoteiroRequest"], Schemas["RoteiroResponse"]>(
      `/tipos-processo/${tipoProcessoId}/roteiro`,
      body,
      { auth: true },
    ),

  // Processos e workflow (Épico 2)
  criarProcesso: (body: Schemas["CriarProcessoRequest"]) =>
    post<Schemas["CriarProcessoRequest"], Schemas["ProcessoResponse"]>("/processos", body, {
      auth: true,
    }),
  listarKanban: (query?: { filtro_unidade?: string; page?: number; page_size?: number }) =>
    get<Schemas["KanbanResponse"]>("/processos", { auth: true, query }),
  buscarProcessos: (query: {
    numero?: string;
    assunto?: string;
    data_inicial?: string;
    data_final?: string;
  }) => get<Schemas["KanbanResponse"]>("/processos/busca", { auth: true, query }),
  obterProcesso: (processoId: string) =>
    get<Schemas["ProcessoResponse"]>(`/processos/${processoId}`, { auth: true }),
  historicoProcesso: (processoId: string) =>
    get<Schemas["HistoricoResponse"]>(`/processos/${processoId}/historico`, { auth: true }),
  despacharProcesso: (processoId: string, body: Schemas["DespacharRequest"]) =>
    post<Schemas["DespacharRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/despachar`,
      body,
      { auth: true },
    ),
  devolverProcesso: (processoId: string, body: Schemas["DevolverRequest"]) =>
    post<Schemas["DevolverRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/devolver`,
      body,
      { auth: true },
    ),
  marcarSigilo: (processoId: string) =>
    post<undefined, Schemas["ProcessoResponse"]>(`/processos/${processoId}/sigilo`, undefined, {
      auth: true,
    }),
  removerSigilo: (processoId: string) =>
    del<Schemas["ProcessoResponse"]>(`/processos/${processoId}/sigilo`, { auth: true }),
};

export type { Schemas };
