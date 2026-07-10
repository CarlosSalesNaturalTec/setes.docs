// Consome um tipo gerado de @setes/api-types (prova do contrato OpenAPI->TS, task 1.5).
import type { paths } from "@setes/api-types";

// Tipo da resposta do /health do backend, derivado do contrato OpenAPI.
export type HealthResponse =
  paths["/health"]["get"]["responses"]["200"]["content"]["application/json"];

export const apiHealthPath = "/health" satisfies keyof paths;

export function isHealthy(payload: HealthResponse): boolean {
  return payload.status === "ok";
}
