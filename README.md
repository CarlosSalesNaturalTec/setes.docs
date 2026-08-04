# Despapelize

Sistema de gestão de processos administrativos para um órgão da administração pública
da Bahia: workflow roteirizado de tramitação entre unidades, quadro Kanban, gestão
documental, sigilo, notificações, dashboard de KPIs, consulta pública sem autenticação
e conformidade LGPD (anonimização e canal do titular).

Monorepo poliglota:

| Diretório | Stack | Descrição |
| --- | --- | --- |
| `apps/web` | Next.js 15 (App Router, TypeScript, Tailwind) | Frontend — specs E2E Playwright em `apps/web/e2e/` |
| `apps/api` | Python 3.12, FastAPI, SQLAlchemy 2.x + Alembic | Backend — ver [`apps/api/README.md`](apps/api/README.md) |
| `packages/api-types` | openapi-typescript | Tipos TS gerados do OpenAPI do FastAPI (commitados) |
| `infra` | Terraform (GCP) | Cloud Run, Cloud SQL, Storage, Tasks, Scheduler — ver [`infra/README.md`](infra/README.md) |
| `docs` | Markdown | [`docs/PRD.md`](docs/PRD.md) (documento mestre), manual do usuário |
| `openspec` | OpenSpec | Specs por capability e changes (fluxo spec-driven) |

## Documentação

- **[`docs/PRD.md`](docs/PRD.md)** — documento mestre: personas, escopo do MVP,
  épicos e critérios de aceite (Dado/Quando/Então) de cada história de usuário.
- **[`openspec/specs/`](openspec/specs/)** — specs consolidadas por capability;
  todo trabalho de domínio passa por um change em `openspec/changes/`
  (regras em `openspec/config.yaml`).
- **[`CLAUDE.md`](CLAUDE.md)** — guia de arquitetura e comandos para agentes de código.
- **[`docs/manual-usuario.md`](docs/manual-usuario.md)** — manual do usuário final.

## Desenvolvimento local

Pré-requisitos: Node 22 + pnpm, Python 3.12 + [uv](https://docs.astral.sh/uv/), Docker.

### 1. Banco (Postgres local)

```bash
docker run -d --name setes-postgres-dev -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=setes -p 5433:5432 postgres:16-alpine
```

### 2. Backend (`apps/api` — gerenciado por uv, fora do workspace pnpm)

```bash
cd apps/api
cp .env.example .env            # ajuste as variáveis (ver apps/api/README.md)
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload   # http://localhost:8000/health
```

### 3. Frontend (`apps/web`)

```bash
pnpm install
pnpm dev                        # http://localhost:3000
```

## Comandos principais

```bash
# raiz
pnpm dev / pnpm build           # Next.js dev / build
pnpm gen:types                  # regenera packages/api-types a partir do OpenAPI
pnpm gen:types:check            # falha se os tipos estiverem defasados (roda no CI)

# web
pnpm --filter @setes/web typecheck   # tsc --noEmit (é o que o CI roda)
pnpm --filter @setes/web test        # Vitest (unit/component)
cd apps/web && pnpm test:e2e         # Playwright (sobe api+web, requer Postgres local)

# api
cd apps/api
uv run ruff check .             # lint
uv run pytest                   # suíte completa (usa Postgres real, não mocks)
```

**Contrato frontend-backend:** o FastAPI é a fonte da verdade. Toda mudança de
rota/schema no backend exige `pnpm gen:types` + commit de `packages/api-types` —
o CI falha no job de drift caso contrário.

## CI/CD

- `.github/workflows/ci.yml` — path-filtered por app: **api** (ruff + pytest com
  Postgres service container), **web** (typecheck + Vitest), **types-drift**
  (`gen:types:check`).
- `.github/workflows/deploy.yml` — push em `main` → deploy no Cloud Run via
  Workload Identity Federation; migrations rodam num Cloud Run Job efêmero
  **antes** de publicar a API.

## Convenções

- Código em **português brasileiro** para entidades e regras de negócio
  (Processo, Unidade, Tramitação, Despacho, Roteiro); inglês só para termos
  técnicos de infra. Comentários e docstrings em português.
- Branches `feature/<nome-do-change>`; merge para `main` com `--no-ff`
  (GitHub Flow, sem staging).
- Histórico de tramitação é **imutável** (INSERT de evento, nunca UPDATE);
  estados de processo são máquina de estados explícita.
