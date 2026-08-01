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
  query?: Record<string, string | number | boolean | undefined>;
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

// Upload multipart (anexação de documento, Épico 3) — não usa JSON no corpo,
// então não passa pelo `request()` genérico acima.
async function postMultipart<TResponse>(path: string, form: FormData): Promise<TResponse> {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resp = await fetch(buildUrl(path), { method: "POST", headers, body: form });

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

  return (await resp.json()) as TResponse;
}

export interface ConteudoDocumento {
  blob: Blob;
  nomeArquivo: string;
}

function extrairNomeArquivo(contentDisposition: string | null): string {
  if (!contentDisposition) return "arquivo";
  // filename*=UTF-8''<encoded> tem prioridade (acentuação, D3); senão filename="...".
  const estrela = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition);
  if (estrela) return decodeURIComponent(estrela[1]);
  const simples = /filename="?([^";]+)"?/i.exec(contentDisposition);
  return simples ? simples[1] : "arquivo";
}

// Streaming autenticado (D5) — conteúdo/download exigem o header Authorization,
// então não podem ser um <a href> direto; buscamos o blob via fetch.
async function getBlob(path: string): Promise<ConteudoDocumento> {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resp = await fetch(buildUrl(path), { headers });

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

  const blob = await resp.blob();
  const nomeArquivo = extrairNomeArquivo(resp.headers.get("content-disposition"));
  return { blob, nomeArquivo };
}

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
  atualizarMeuPerfil: (body: Schemas["AtualizarMeuPerfilRequest"]) =>
    patch<Schemas["AtualizarMeuPerfilRequest"], Schemas["MeuPerfilResponse"]>(
      "/usuarios/me/perfil",
      body,
      { auth: true },
    ),

  // Gestão de usuários — `nome` filtra por fragmento no backend (D5).
  listarUsuarios: (page = 1, nome?: string) =>
    get<Schemas["ListaUsuariosResponse"]>("/usuarios", {
      auth: true,
      query: { page, nome: nome || undefined },
    }),
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
  concederPermissaoAuditoria: (usuarioId: string) =>
    post<undefined, Schemas["UsuarioResponse"]>(`/usuarios/${usuarioId}/permissao-auditoria`, undefined, {
      auth: true,
    }),
  revogarPermissaoAuditoria: (usuarioId: string) =>
    del<Schemas["UsuarioResponse"]>(`/usuarios/${usuarioId}/permissao-auditoria`, { auth: true }),
  desativarUsuario: (usuarioId: string) =>
    post<undefined, Schemas["UsuarioResponse"]>(`/usuarios/${usuarioId}/desativar`, undefined, {
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
  reativarUnidade: (unidadeId: string) =>
    post<undefined, Schemas["UnidadeResponse"]>(`/unidades/${unidadeId}/reativar`, undefined, { auth: true }),

  // Setores da unidade (D1) — sem rota de exclusão: setor só é desativado (D3).
  listarSetores: (unidadeId: string, apenasAtivos = false) =>
    get<Schemas["SetorResponse"][]>(`/unidades/${unidadeId}/setores`, {
      auth: true,
      query: { apenas_ativos: apenasAtivos },
    }),
  cadastrarSetor: (unidadeId: string, body: Schemas["CadastrarSetorRequest"]) =>
    post<Schemas["CadastrarSetorRequest"], Schemas["SetorResponse"]>(
      `/unidades/${unidadeId}/setores`,
      body,
      { auth: true },
    ),
  editarSetor: (setorId: string, body: Schemas["EditarSetorRequest"]) =>
    patch<Schemas["EditarSetorRequest"], Schemas["SetorResponse"]>(`/setores/${setorId}`, body, {
      auth: true,
    }),
  desativarSetor: (setorId: string) =>
    post<undefined, Schemas["SetorResponse"]>(`/setores/${setorId}/desativar`, undefined, { auth: true }),
  reativarSetor: (setorId: string) =>
    post<undefined, Schemas["SetorResponse"]>(`/setores/${setorId}/reativar`, undefined, { auth: true }),

  // Tipos de processo (change tramitacao-manual: sem roteiro)
  listarTiposProcesso: () => get<Schemas["TipoProcessoResponse"][]>("/tipos-processo", { auth: true }),
  criarTipoProcesso: (body: Schemas["CriarTipoProcessoRequest"]) =>
    post<Schemas["CriarTipoProcessoRequest"], Schemas["TipoProcessoResponse"]>("/tipos-processo", body, {
      auth: true,
    }),
  atualizarTipoProcesso: (tipoProcessoId: string, body: Schemas["TipoProcessoUpdate"]) =>
    patch<Schemas["TipoProcessoUpdate"], Schemas["TipoProcessoResponse"]>(
      `/tipos-processo/${tipoProcessoId}`,
      body,
      { auth: true },
    ),

  // Apoio à cascata unidade→setor→servidor da tela de Tramitação.
  listarServidoresAtivosPorSetor: (setorId: string) =>
    get<Schemas["UsuarioResumoResponse"][]>("/usuarios/ativos-por-setor", {
      auth: true,
      query: { setor_id: setorId },
    }),

  // Processos e workflow (Épico 2)
  criarProcesso: (body: Schemas["CriarProcessoRequest"]) =>
    post<Schemas["CriarProcessoRequest"], Schemas["ProcessoResponse"]>("/processos", body, {
      auth: true,
    }),
  listarKanban: (query?: {
    filtro_unidade?: string;
    incluir_arquivados?: boolean;
    tipo_processo_id?: string;
    assunto?: string;
    data_inicial?: string;
    data_final?: string;
    page?: number;
    page_size?: number;
  }) => get<Schemas["KanbanResponse"]>("/processos", { auth: true, query }),
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
  enviarProcesso: (processoId: string, body: Schemas["EnviarRequest"]) =>
    post<Schemas["EnviarRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/enviar`,
      body,
      { auth: true },
    ),
  devolverProcesso: (processoId: string, body: Schemas["DevolverRequest"]) =>
    post<Schemas["DevolverRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/devolver`,
      body,
      { auth: true },
    ),
  reatribuirProcesso: (processoId: string, body: Schemas["ReatribuirRequest"]) =>
    post<Schemas["ReatribuirRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/reatribuir`,
      body,
      { auth: true },
    ),
  concluirProcesso: (processoId: string) =>
    post<Schemas["ConcluirRequest"], Schemas["ProcessoResponse"]>(
      `/processos/${processoId}/concluir`,
      {},
      { auth: true },
    ),
  marcarSigilo: (processoId: string) =>
    post<undefined, Schemas["ProcessoResponse"]>(`/processos/${processoId}/sigilo`, undefined, {
      auth: true,
    }),
  removerSigilo: (processoId: string) =>
    del<Schemas["ProcessoResponse"]>(`/processos/${processoId}/sigilo`, { auth: true }),

  // Documentos (Épico 3, fatia A)
  listarDocumentos: (processoId: string) =>
    get<Schemas["DocumentosListResponse"]>(`/processos/${processoId}/documentos`, { auth: true }),
  anexarDocumento: (processoId: string, arquivo: File) => {
    const form = new FormData();
    form.append("arquivo", arquivo);
    return postMultipart<Schemas["DocumentoResponse"]>(`/processos/${processoId}/documentos`, form);
  },
  conteudoDocumento: (processoId: string, documentoId: string) =>
    getBlob(`/processos/${processoId}/documentos/${documentoId}/conteudo`),
  baixarDocumento: (processoId: string, documentoId: string) =>
    getBlob(`/processos/${processoId}/documentos/${documentoId}/download`),
  removerDocumento: (processoId: string, documentoId: string) =>
    del<Schemas["DocumentoResponse"]>(`/processos/${processoId}/documentos/${documentoId}`, {
      auth: true,
    }),

  // Documentos removidos — área administrativa "Documentos Removidos" (US 8.7).
  listarDocumentosRemovidos: () =>
    get<Schemas["DocumentosRemovidosListResponse"]>("/admin/documentos-removidos", { auth: true }),
  restaurarDocumento: (documentoId: string) =>
    post<undefined, Schemas["DocumentoResponse"]>(
      `/admin/documentos-removidos/${documentoId}/restaurar`,
      undefined,
      { auth: true },
    ),

  // Notificações internas — sino (Épico 5, US 5.1/5.3/5.4).
  listarNotificacoes: () => get<Schemas["ListaNotificacoesResponse"]>("/notificacoes", { auth: true }),
  contarNotificacoes: () =>
    get<Schemas["ContadorNotificacoesResponse"]>("/notificacoes/contador", { auth: true }),
  marcarNotificacaoLida: (notificacaoId: string) =>
    post<undefined, Schemas["NotificacaoResponse"]>(`/notificacoes/${notificacaoId}/ler`, undefined, {
      auth: true,
    }),
  marcarTodasNotificacoesLidas: () =>
    post<undefined, Schemas["MarcarTodasLidasResponse"]>("/notificacoes/marcar-todas-lidas", undefined, {
      auth: true,
    }),

  // Dashboard de KPIs do Gestor (Épico 6, US 6.1).
  obterDashboardKpis: (query?: { unidade_id?: string }) =>
    get<Schemas["DashboardKpisResponse"]>("/dashboard/kpis", { auth: true, query }),
  obterDashboardContagens: (query?: { unidade_id?: string }) =>
    get<Schemas["ContagensPorStatusResponse"]>("/dashboard/contagens", { auth: true, query }),
  obterProcessosAtivosDashboard: (query?: { unidade_id?: string }) =>
    get<Schemas["ProcessosAtivosResponse"]>("/dashboard/processos-ativos", { auth: true, query }),
  obterProcessosParadosDashboard: (query?: { unidade_id?: string }) =>
    get<Schemas["ProcessosParadosResponse"]>("/dashboard/processos-parados", { auth: true, query }),
  obterDashboardDistribuicoes: (query?: { unidade_id?: string }) =>
    get<Schemas["DistribuicoesResponse"]>("/dashboard/distribuicoes", { auth: true, query }),

  // Auditoria — relatório consolidado em tela (Épico 9, US 9.2).
  obterRelatorioAuditoria: (query?: {
    inicio?: string;
    fim?: string;
    unidade_id?: string;
    tipo_processo_id?: string;
  }) => get<Schemas["RelatorioAuditoriaResponse"]>("/auditoria/relatorio", { auth: true, query }),

  // LGPD (Épico 10) — canal público de solicitação (US 10.1) e fila
  // administrativa de atendimento/rejeição (US 10.2).
  solicitarLgpd: (form: {
    numero_processo: string;
    nome: string;
    cpf: string;
    email: string;
    tipo: "exclusao" | "anonimizacao";
    arquivo: File;
  }) => {
    const data = new FormData();
    data.append("numero_processo", form.numero_processo);
    data.append("nome", form.nome);
    data.append("cpf", form.cpf);
    data.append("email", form.email);
    data.append("tipo", form.tipo);
    data.append("arquivo", form.arquivo);
    return postMultipart<Schemas["SolicitacaoLgpdCriadaResponse"]>("/publico/lgpd/solicitacoes", data);
  },
  listarSolicitacoesLgpd: (status?: string) =>
    get<Schemas["SolicitacoesLgpdListResponse"]>("/lgpd/solicitacoes", {
      auth: true,
      query: status ? { status } : undefined,
    }),
  atenderSolicitacaoLgpd: (solicitacaoId: string) =>
    post<undefined, Schemas["SolicitacaoLgpdResponse"]>(
      `/lgpd/solicitacoes/${solicitacaoId}/atender`,
      undefined,
      { auth: true },
    ),
  rejeitarSolicitacaoLgpd: (solicitacaoId: string, body: Schemas["RejeitarSolicitacaoLgpdRequest"]) =>
    post<Schemas["RejeitarSolicitacaoLgpdRequest"], Schemas["SolicitacaoLgpdResponse"]>(
      `/lgpd/solicitacoes/${solicitacaoId}/rejeitar`,
      body,
      { auth: true },
    ),

  // Consulta Pública (Épico 7) — sem autenticação, para o Cidadão.
  consultarProcessoPublico: (numero: string) =>
    get<Schemas["ProcessoPublicoResponse"]>(`/publico/processos/${encodeURIComponent(numero)}`),
  pesquisarProcessosPublico: (query: {
    assunto?: string;
    tipo_processo?: string;
    data_inicio?: string;
    data_fim?: string;
    pagina?: number;
  }) => get<Schemas["PesquisaPublicaResponse"]>("/publico/processos", { query }),
};

export type { Schemas };
