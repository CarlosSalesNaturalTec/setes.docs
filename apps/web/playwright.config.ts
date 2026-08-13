import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const apiDir = path.join(__dirname, "..", "api");
const uvicornBin =
  process.platform === "win32"
    ? path.join(apiDir, ".venv", "Scripts", "uvicorn.exe")
    : path.join(apiDir, ".venv", "bin", "uvicorn");

// Flags de dev/E2E (Settings.dev_email_inbox / dev_db_reset /
// dev_rate_limit_reset, app/config.py) — nunca setadas no `.env` de
// desenvolvimento normal (ver apps/api/.env): habilitam a caixa de entrada em
// memória (sem provedor de e-mail real), o reset de banco e o reset do
// contador de rate limit consumidos pelos fluxos críticos em `e2e/`.
const API_ENV = {
  DEV_EMAIL_INBOX: "true",
  DEV_DB_RESET: "true",
  DEV_RATE_LIMIT_RESET: "true",
};

export default defineConfig({
  testDir: "./e2e",
  // Os 4 fluxos críticos constroem estado uns sobre os outros (12.1 inicializa
  // o sistema; 12.2-12.4 reaproveitam o Administrador root criado em 12.1) —
  // rodam sempre em série, nunca em paralelo entre arquivos.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  // Os fluxos mais longos (auditoria, visibilidade por origem) encadeiam 4-6
  // sessões diferentes — login, logout e navegação de cada ator — e estouram o
  // default de 30 s do Playwright antes de qualquer asserção falhar de fato.
  timeout: 90_000,
  reporter: "list",
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  // O par testMatch/testIgnore é necessário nos dois sentidos: a suíte é
  // serial, com o banco zerado uma única vez pelo globalSetup e estado
  // encadeado entre specs (01-16). Sem o testIgnore no chromium, o desktop
  // também rodaria os specs .mobile.spec.ts, em viewport largo, onde eles não
  // testam nada; sem o testMatch no mobile, o projeto móvel repetiria os 16
  // specs desktop contra um banco já povoado, falhando em toda asserção de
  // criação. O projeto mobile roda depois do chromium, sobre o banco já
  // populado — seus specs criam o próprio estado com nomes distintos (D5).
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      testIgnore: /.*\.mobile\.spec\.ts/,
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 5"] },
      testMatch: /.*\.mobile\.spec\.ts/,
    },
  ],
  webServer: [
    {
      command: `${uvicornBin} app.main:app --port 8000`,
      cwd: apiDir,
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: API_ENV,
    },
    {
      command: "corepack pnpm dev",
      cwd: __dirname,
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
