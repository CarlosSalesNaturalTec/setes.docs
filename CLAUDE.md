# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SETES.DOCS — sistema de gestão de processos administrativos (workflow roteirizado,
assinatura digital ICP-Brasil, consulta pública) para um órgão da administração
pública da Bahia. Monorepo poliglota: Next.js (web) + FastAPI (api) + Terraform (infra),
gerenciado com um workflow spec-driven via OpenSpec (`openspec/`).

Stack: Next.js 15 (App Router, TS) + Tailwind · Python 3.12 / FastAPI · SQLAlchemy 2.x
+ Alembic · PostgreSQL (Cloud SQL) · GCP (Cloud Run, Cloud Storage, Secret Manager,
Cloud Scheduler + Cloud Run Jobs, Cloud Tasks) · região `southamerica-east1` (residência
de dados obrigatória no Brasil).

## Commands

The two apps are in **separate package managers** — `apps/api` is managed by `uv`,
outside the pnpm workspace (`pnpm-workspace.yaml` only covers `apps/web` + `packages/*`).

### API (`apps/api`, run from that directory)
```bash
uv sync --extra dev                          # install deps
uv run uvicorn app.main:app --reload         # dev server (health: /health)
uv run pytest                                # all tests
uv run pytest tests/test_auth_login.py -k foo  # single file / test
uv run ruff check .                          # lint (CI-enforced)
uv run alembic upgrade head                  # apply migrations
uv run alembic revision -m "..." --autogenerate
uv run python scripts/export_openapi.py > /dev/null  # print OpenAPI JSON to stdout
```
Tests that use the `db` fixture (`tests/conftest.py`) hit a **real local Postgres**
(docker), not sqlite/mocks — the fixture truncates business tables after each test.
The `client` fixture resets the in-process rate limiter and overrides `get_settings`.

### Web (`apps/web`) and root-level pnpm scripts
```bash
pnpm install
pnpm dev                              # apps/web dev server (root shortcut)
pnpm --filter @setes/web typecheck    # tsc --noEmit
pnpm --filter @setes/web test         # vitest run
pnpm --filter @setes/web test -- path/to/file.test.ts  # single file
pnpm --filter @setes/web lint
pnpm build
```

### Cross-app contract (OpenAPI → TypeScript)
```bash
pnpm gen:types          # regenerates packages/api-types/{openapi.json,schema.ts} from FastAPI
pnpm gen:types:check    # fails if the committed snapshot has drifted (CI job `types-drift`)
```
`apps/web` never talks to loosely-typed JSON — `apps/web/lib/api.ts` imports
`components`/`paths` from `@setes/api-types` (workspace package, generated, committed).
**Whenever a FastAPI route/schema changes, run `pnpm gen:types` and commit the diff**,
or CI's drift check fails.

### Infra (`infra/`, Terraform)
```bash
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```
GCS state bucket and `backend.hcl`/`terraform.tfvars` must exist first — see `infra/README.md`.
Dependency order: APIs → org policies → network/PSA → Cloud SQL → Secret Manager → IAM →
Artifact Registry → Cloud Tasks → Cloud Run → Jobs/Scheduler → WIF. Service images start as
placeholders; the deploy pipeline (`.github/workflows/deploy.yml`) replaces them
(`ignore_changes` on `image`).

### CI (`.github/workflows/ci.yml`)
Path-filtered: `api` job (ruff + pytest) runs only on `apps/api/**` changes; `web` job
(typecheck + vitest) only on `apps/web/**`; `types-drift` runs whenever the API changes
and fails if `packages/api-types` wasn't regenerated.

## Architecture

### Auth & sessions
Own login/password auth, no external SSO in the MVP. JWT with a **sliding-window
renewal**: every authenticated request re-issues the token in the `X-Renewed-Token`
response header (see `app/security/autorizacao.py:get_current_user`); `apps/web/lib/api.ts`
reads that header and silently persists the renewed token via `session-store.ts`.
Sessions are backed by a `sessao` DB row (`jti`, `ultima_atividade`, `revogada_em`) —
validated/renewed in `app/security/sessao.py`. Auth is Bearer-token only, not cookies
(`allow_credentials=False` in CORS setup).

### Authorization
Dependency chain: `get_current_user` → `require_perfil(*perfis)` →
`require_acesso_unidade` (`app/security/autorizacao.py`). Three profiles
(`PerfilUsuario`): `servidor` (own unit only), `gestor` (units they manage, via
`unidade_gestor`), `administrador` (any unit). **Every** access-denied path writes a
`log_seguranca` row (`tipo_evento=acesso_negado`) — this is a hard requirement from the
PRD (US 1.4 Cen.2), not incidental logging.

### Internal service-to-service calls
`/internal/tasks/email` is OIDC-only (`app/security/oidc.py:require_tasks_invoker`),
called by Cloud Tasks. It **always returns 200/ACK even on delivery failure** (queue has
`maxAttempts=1`, no redispatch) — logging the failure instead of raising, because raising
would make Cloud Tasks treat it as retryable. Follow this ack-always contract for any new
internal task-queue endpoint.

### Database
One SQLAlchemy engine per Cloud Run instance with a deliberately small pool
(`pool_size=5, max_overflow=0`, `app/db/session.py`) — `instances × pool_size` must stay
under Cloud SQL's `max_connections` (enforced via `infra/cloudrun.tf` max-instances, see
`infra/README.md` "Teto de conexões"). Don't raise pool size without also checking the
Cloud Run max-instances cap. Migrations are Alembic (`apps/api/migrations/`); models are
in `app/db/models.py` — UUID PKs generated app-side (`default=uuid.uuid4`), except
`SistemaConfig`, a singleton row with fixed `id=1` used as an app-initialized flag.

Core entities: `Unidade` / `Usuario` (+ `UnidadeGestor` for gestor↔unidade M:N) for
identity/org structure; `TipoProcesso` / `Roteiro` / `RoteiroEtapa` for process-type
routing templates; `TokenAutenticacao` / `SenhaHistorico` / `Sessao` / `LogSeguranca` for
auth/security bookkeeping.

**Tramitação (process transition) history is append-only** — model as INSERT of a new
event, never UPDATE. This is an explicit project rule (`openspec/config.yaml`), not yet
reflected in models.py since that capability isn't built yet.

### Frontend structure
Next.js App Router under `apps/web/app/**`; `protected-shell.tsx` +
`session-watcher.tsx` + `auth-provider.tsx` (`apps/web/components/`) wrap authenticated
pages and drive the token-renewal/session-expiry UX. All API calls go through the typed
`api` object in `apps/web/lib/api.ts` (one method per backend endpoint) — add new backend
routes there rather than calling `fetch` ad hoc from components.

### Async email delivery
`app/email/queue.py` enqueues to Cloud Tasks (queue `emails`, region
`CLOUD_TASKS_LOCATION`); `app/email/provider.py` does the actual SendGrid send, invoked
from the internal endpoint above.

## OpenSpec workflow

This repo uses **spec-driven development via OpenSpec**: `openspec/specs/` holds the
current source-of-truth capability specs (currently `conectividade-e-seguranca`,
`fila-notificacoes`, `plataforma-gcp`, `rotinas-agendadas`); `openspec/changes/` holds
in-flight change proposals (`proposal.md`, `design.md`, `tasks.md`, delta specs), archived
to `openspec/changes/archive/` once merged. `openspec/config.yaml` encodes project-wide
rules that apply to every change — notably:

- Every proposal must declare which prior change it depends on, new/affected Postgres
  tables with FKs, and any new Secret Manager secret or Storage bucket.
- Any change touching personal data (CPF/CNPJ, nome de interessado) must state its LGPD
  treatment (collection, retention, anonymization) explicitly.
- Specs use Dado/Quando/Então (Gherkin-style) scenarios; process states/transitions
  (Aberto, Em Tramitação, Concluído, Arquivado) must be an explicit state machine, never a
  free-text field; every unit/profile visibility rule needs an explicit "acesso negado"
  scenario.
- Designs need a sequence diagram for 3+ step flows crossing front/back/async job, and
  must document trigger/window/idempotent-resume behavior for any Cloud
  Scheduler/Cloud Run Job.
- Tasks are ≤2h each; migration/schema tasks are separated from endpoint/UI tasks; any
  task touching tramitação history or personal data requires a paired automated-test task;
  any task implementing/changing login, despacho, assinatura, or consulta pública requires
  a paired Playwright E2E task.

Use the `openspec-*` skills (`/opsx:*` commands) for proposing, continuing, applying, and
archiving changes rather than editing `openspec/` by hand.

## Conventions

- **Naming language**: domain/business terms in Portuguese (Processo, Unidade,
  Tramitação, Despacho, Roteiro — matches DB tables and Python identifiers); generic
  infra terms in English (Repository, Service, Router). Comments and docstrings in
  Portuguese.
- **Branching**: `feature/<change-name>`, merged to `main` via `--no-ff` (GitHub Flow, no
  staging branch — pre-prod validation is via Cloud Run traffic splitting).
- **Testing**: pytest + pytest-asyncio for the API, Vitest + React Testing Library for the
  web app, Playwright for critical E2E flows (login, despacho, assinatura, consulta
  pública) — see the OpenSpec task rules above for when Playwright coverage is mandatory.
- **Compliance**: LGPD (Lei 13.709/2018) and, where applicable, MP 2.200-2/2001 + ICP-Brasil
  norms apply to any change touching personal data or documents.
