#!/usr/bin/env node
// Contrato OpenAPI -> TS (D9).
// 1. Emite openapi.json a partir do FastAPI (apps/api).
// 2. Roda openapi-typescript para packages/api-types/schema.ts.
//
// Uso:
//   node scripts/gen-types.mjs           # regenera o snapshot commitado
//   node scripts/gen-types.mjs --check   # falha se o snapshot estiver defasado (drift check no CI)
//
// O snapshot (openapi.json + schema.ts) é commitado para dar DX local sem
// precisar subir a API. O CI roda --check e falha se o commit estiver desatualizado.

import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const apiDir = join(root, "apps", "api");
const pkgDir = join(root, "packages", "api-types");
const openapiPath = join(pkgDir, "openapi.json");
const schemaPath = join(pkgDir, "schema.ts");

const check = process.argv.includes("--check");

function run(cmd, args, opts = {}) {
  return execFileSync(cmd, args, { stdio: ["ignore", "pipe", "inherit"], encoding: "utf8", ...opts });
}

// 1. Exporta o schema OpenAPI do FastAPI usando o interpretador Python do próprio app.
//    Preferimos `uv run` (fora do workspace pnpm); caímos para `python` se uv ausente.
function exportOpenapi() {
  const script = "scripts/export_openapi.py";
  const runners = [
    ["uv", ["run", "python", script]],
    ["python", [script]],
    ["python3", [script]],
  ];
  let lastErr;
  for (const [bin, args] of runners) {
    try {
      const out = run(bin, args, { cwd: apiDir });
      return out;
    } catch (err) {
      lastErr = err;
    }
  }
  throw new Error(
    `Não foi possível exportar o OpenAPI do FastAPI (tentado uv/python). Detalhe: ${lastErr?.message ?? lastErr}`,
  );
}

function normalize(json) {
  // Estabiliza a serialização para o drift check ser determinístico.
  return `${JSON.stringify(JSON.parse(json), null, 2)}\n`;
}

const freshOpenapi = normalize(exportOpenapi());

if (check) {
  if (!existsSync(openapiPath)) {
    console.error("api-types: openapi.json ausente. Rode `pnpm gen:types`.");
    process.exit(1);
  }
  const committed = readFileSync(openapiPath, "utf8");
  if (committed !== freshOpenapi) {
    console.error(
      "api-types: snapshot OpenAPI defasado. O contrato do FastAPI mudou sem regenerar os tipos.\n" +
        "Rode `pnpm gen:types` e commite packages/api-types.",
    );
    process.exit(1);
  }
  console.log("api-types: snapshot OpenAPI em dia.");
  process.exit(0);
}

mkdirSync(pkgDir, { recursive: true });
writeFileSync(openapiPath, freshOpenapi);

// 2. Gera o TS a partir do openapi.json (invoca o binário local diretamente,
//    portável entre shells/CI sem depender do shim do gerenciador).
const cli = join(root, "node_modules", "openapi-typescript", "bin", "cli.js");
run(process.execPath, [cli, openapiPath, "-o", schemaPath], { cwd: root });

console.log("api-types: openapi.json e schema.ts regenerados.");
