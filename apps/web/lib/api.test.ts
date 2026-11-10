import { afterEach, describe, expect, it, vi } from "vitest";
import { api, apiHealthPath, isHealthy, type HealthResponse } from "./api";
import { setToken } from "./session-store";

describe("contrato da API (tipos gerados)", () => {
  it("expõe o path de health", () => {
    expect(apiHealthPath).toBe("/health");
  });

  it("isHealthy usa o tipo gerado do OpenAPI", () => {
    const ok: HealthResponse = { status: "ok", service: "api" };
    expect(isHealthy(ok)).toBe(true);
    expect(isHealthy({ status: "down", service: "api" })).toBe(false);
  });
});

describe("verificarAssinatura (change assinatura-verificacao-fundacao)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("chama GET …/verificacao autenticado e devolve o resultado tipado", async () => {
    const resultado = {
      documento_id: "doc-1",
      situacao: "sem_assinatura",
      resumo: null,
      mensagem_resumo: "Este documento não contém assinatura digital.",
      assinaturas: [],
      aviso_veredito_oficial: null,
      url_verificador_oficial: null,
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(resultado), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    setToken("tok-123");

    const resp = await api.verificarAssinatura("proc-1", "doc-1");

    expect(resp.situacao).toBe("sem_assinatura");
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/processos\/proc-1\/documentos\/doc-1\/verificacao$/);
    expect(init.method).toBe("GET");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer tok-123");
  });
});
