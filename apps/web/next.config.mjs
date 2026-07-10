import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Saída standalone para imagem Docker enxuta (task 1.4).
  output: "standalone",
  // Monorepo: rastreia a partir da raiz do repo para incluir deps do workspace
  // (@setes/api-types) e produzir a estrutura apps/web/server.js no standalone.
  outputFileTracingRoot: path.join(__dirname, "../../"),
  // O pacote de tipos é TS puro consumido do workspace.
  transpilePackages: ["@setes/api-types"],
};

export default nextConfig;
