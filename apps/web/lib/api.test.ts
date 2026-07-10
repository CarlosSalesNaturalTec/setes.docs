import { describe, expect, it } from "vitest";
import { apiHealthPath, isHealthy, type HealthResponse } from "./api";

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
