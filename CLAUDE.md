# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

SETES.DOCS — sistema de gestão de processos administrativos (workflow roteirizado,
sigilo, consulta pública, LGPD) para um órgão da administração pública da Bahia.
Monorepo poliglota: **Next.js (web) + FastAPI (api) + Terraform (infra)** em GCP.

Linguagem de código: **português brasileiro** para entidades e regras de negócio
(Processo, Unidade, Tramitação, Despacho, Roteiro); inglês só para termos técnicos
de infra (Repository, Service, Router). Comentários e docstrings em português.

## Documento mestre: `docs/PRD.md`

`docs/PRD.md` é o documento mestre — define personas, escopo do
MVP, épicos e os critérios de aceite (Dado/Quando/Então) de cada história de usuário
(US x.y). **Ao planejar ou implementar qualquer feature de domínio, leia a US
relevante no PRD primeiro** — os cenários de erro e casos de borda ali são
vinculantes, não sugestões. Specs OpenSpec referenciam a US correspondente em vez de
reescrever os critérios.

## Fluxo de trabalho OpenSpec (spec-driven)

Todo trabalho de domínio passa por um *change* em `openspec/changes/`. As regras
(`openspec/config.yaml`) são vinculantes — destaques:

- **Histórico de tramitação é imutável**: modelar como INSERT de novo evento, nunca
  UPDATE. Estados de processo (Aberto, Em Tramitação, Concluído, Arquivado) são
  máquina de estados explícita, nunca campo de texto livre.
- Toda regra de visibilidade por unidade/perfil precisa de cenário de **"acesso
  negado" explícito**, não só o caminho feliz.
- Features que tocam dados pessoais (CPF/CNPJ, nome de interessado) ou histórico de
  tramitação **exigem** teste automatizado correspondente; login/despacho/assinatura/
  consulta pública exigem **teste E2E Playwright** (não opcional).
- Conformidade LGPD (Lei 13.709/2018) obrigatória ao tocar dados pessoais/documentos.

Skills OpenSpec disponíveis via Skill tool: `opsx:new`, `opsx:propose`, `opsx:apply`,
`opsx:continue`, `opsx:verify`, `opsx:archive` (e variantes). `openspec/specs/` guarda
as specs consolidadas por capability; `openspec/changes/archive/` os changes concluídos.

## Comandos

### Raiz do monorepo (pnpm)
```bash
pnpm install                 # instala deps do workspace web (a api é separada, ver abaixo)
pnpm dev                     # Next.js dev (apps/web) em :3000
pnpm build                   # build do web
pnpm gen:types               # regenera packages/api-types a partir do OpenAPI do FastAPI
pnpm gen:types:check         # falha se o snapshot de tipos estiver defasado (roda no CI)
```

### Frontend — `apps/web` (pnpm)
```bash
pnpm --filter @setes/web dev        # ou: pnpm dev na raiz
pnpm --filter @setes/web typecheck  # tsc --noEmit (o CI usa isto, não `lint`)
pnpm --filter @setes/web test       # Vitest (unit/component)
cd apps/web && pnpm vitest run lib/api.test.ts   # um único arquivo de teste
cd apps/web && pnpm test:e2e        # Playwright — sobe api+web e roda contra Postgres local
```

### Backend — `apps/api` (uv, **fora do workspace pnpm**)
```bash
cd apps/api
uv sync --extra dev                 # instala deps + dev (pytest, ruff)
uv run alembic upgrade head         # aplica migrations
uv run uvicorn app.main:app --reload   # API em :8000 (/health)
uv run ruff check .                  # lint (CI roda isto)
uv run pytest                        # suíte completa
uv run pytest tests/test_auth_login.py -q          # um arquivo
uv run pytest tests/test_auth_login.py::test_nome -q  # um teste
uv run python scripts/export_openapi.py            # exporta o contrato OpenAPI (stdout)
```

Requer Postgres local — a suíte pytest usa **Postgres real** (fixture `db` em
`tests/conftest.py`), não sqlite/mocks:
```bash
docker run -d --name setes-postgres-dev -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=setes -p 5433:5432 postgres:16-alpine
```
Variáveis do `.env` (gitignored) documentadas em `apps/api/README.md` / `app/config.py`.

## Arquitetura

### Contrato frontend-backend (tipos gerados)
O front **não escreve tipos de API à mão**. `apps/api` (FastAPI) é a fonte da verdade:
`pnpm gen:types` exporta o OpenAPI e roda `openapi-typescript` para
`packages/api-types/` (`openapi.json` + `schema.ts`, **ambos commitados**). O CI roda
`gen:types:check` e falha se o contrato do FastAPI mudou sem regenerar os tipos.
**Toda mudança de rota/schema no backend exige `pnpm gen:types` + commit de
`packages/api-types`.** O cliente HTTP tipado do front vive em `apps/web/lib/api.ts`
(objeto `api`), consumindo `@setes/api-types` — sem `any` nos payloads.

### Sessão (D1) — sliding window via header
Autenticação própria (login/senha, JWT HS256, sem SSO). Toda resposta autenticada
pode reemitir um JWT renovado no header **`X-Renewed-Token`**; `apps/web/lib/api.ts`
captura e persiste silenciosamente, e o backend (`app/security/autorizacao.py`
`get_current_user`) o reemite a cada chamada válida. Sessão é **Bearer token, não
cookie** — CORS com `allow_credentials=False`. `Content-Disposition` também é exposto
(download de documentos, D5). Camada de autorização compõe:
`get_current_user` → `require_perfil(*perfis)` → `require_acesso_unidade`; toda
rejeição grava `log_seguranca` (`acesso_negado`).

### Backend `apps/api/app`
- `routers/` — endpoints FastAPI, um por área de domínio (auth, processos, documentos,
  lgpd, consulta_publica, auditoria, dashboard, …). Montados em `main.py`.
- `services/` — regras de negócio (processo_estado = máquina de estados, arquivamento,
  anonimizacao_lgpd, numero_processo, sigilo, …). Routers finos, lógica no service.
- `db/models.py` — SQLAlchemy 2.x; enums de domínio (`StatusProcesso`,
  `PerfilUsuario`, `TipoEventoTramitacao`, …) no topo. `migrations/` é Alembic.
- `security/` — jwt, sessao, senha (bcrypt), oidc (endpoints internos), autorizacao.
- `jobs/` — Cloud Run Jobs. `entrypoint.py` = manutenção diária (arquivamento, purga
  de documentos, verificação de prazos, expurgo de notificações), idempotente por
  seleção de estado. `entrypoint_lgpd.py` = anonimização trimestral.
- Endpoints `/internal/*` são OIDC-only (chamados por Cloud Tasks/Scheduler);
  `/publico/*` são sem-auth com rate limiting (`app/rate_limit.py`, slowapi).

### Frontend `apps/web` (Next.js App Router)
Rotas em `app/` espelham o domínio (`/processos`, `/admin/*`, `/consulta-publica`,
`/lgpd`, `/auditoria`, `/setup`, `/primeiro-acesso/[token]`). `lib/` = client HTTP,
session-store, validação, rota-inicial (redirect por perfil). `components/` = shell
protegido, auth-provider, session-watcher, sino de notificações. Testes Vitest ficam
**colocados** junto ao código (`lib/api.test.ts`, `components/*.test.tsx`), não em
diretório separado.

### Infra `infra/` (Terraform, GCP)
Cloud Run (web + api), Cloud SQL (Postgres, IP privado), Cloud Storage (documentos),
Secret Manager (`db-password`, `jwt-signing-key`, `sendgrid-api-key`), Cloud Tasks
(fila `emails` assíncrona), Cloud Scheduler + Cloud Run Jobs (manutenção/LGPD). Deploy
via **Workload Identity Federation** (sem chave JSON). `terraform.tfvars` e
`backend.hcl` são gitignored (ver `.example`).

### CI/CD
- `.github/workflows/ci.yml` — path-filtered por app. Job **api**: Postgres service
  container real + `ruff check` + `pytest`. Job **web**: `typecheck` + `vitest`. Job
  **types-drift**: `gen:types:check`.
- `.github/workflows/deploy.yml` — push em `main`, path-filtered. Deploy da api roda
  **migrations num Cloud Run Job efêmero ANTES** de publicar o serviço; deploy via WIF.

### Testes E2E (Playwright)
`apps/web/playwright.config.ts` sobe a API com `DEV_EMAIL_INBOX=true` e
`DEV_DB_RESET=true` — flags **dev/E2E-only, nunca em produção** — que habilitam
`GET /internal/dev/emails` (lê link de primeiro-acesso/recuperação sem provedor real)
e `POST /internal/dev/reset` (banco limpo antes da suíte). Sem a flag, cada endpoint
responde 404. Specs em `apps/web/e2e/` — arquivos numerados por fluxo
(`05-processos-despacho.spec.ts`, …), com `fixtures.ts`/`helpers/` compartilhados e
`global-setup.ts` (reset do banco).

## Convenções de git

Branches `feature/<nome-do-change>`; merge para `main` com **`--no-ff` obrigatório**
(GitHub Flow, sem staging). Commit/push só quando o usuário pedir.
