# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

SETES.DOCS — sistema de gestão de processos administrativos (workflow roteirizado,
assinatura digital ICP-Brasil, consulta pública) para um órgão da administração pública
da Bahia. Digitaliza o trâmite de processos entre unidades, elimina o papel e dá métricas
de eficiência a gestores. Monorepo **poliglota**: Next.js (`apps/web`) + FastAPI
(`apps/api`) + Terraform GCP (`infra`). Código de domínio em **português brasileiro**
(Processo, Unidade, Tramitação, Despacho, Roteiro); termos técnicos de infra em inglês
(Repository, Service, Router). Comentários e docstrings em português.

## PRD é a fonte da verdade do produto

**`docs/PRD.md` é o documento mestre** — define personas, escopo do MVP, 10 épicos e os
critérios de aceite (Dado/Quando/Então) de cada história de usuário (US x.y). Todo change
OpenSpec implementa um recorte do PRD, e as specs **referenciam a US correspondente** em
vez de reescrever critérios já definidos. Ao planejar ou implementar qualquer feature de
domínio, leia a US relevante no PRD primeiro — os cenários de erro e casos de borda ali
são vinculantes, não sugestões.

### Perfis (a base de todo controle de acesso)

- **Servidor** — vinculado a **exatamente uma** unidade; só vê/movimenta processos da
  própria unidade. Executor do dia a dia (cria, despacha, devolve, anexa, assina).
- **Gestor** — gerencia **uma ou mais** unidades; vê Kanban consolidado + dashboards
  delas e cadastra Servidores nelas.
- **Administrador** — acesso irrestrito; guardião da configuração (unidades, tipos de
  processo, roteiros, usuários, parâmetros do sistema).
- **Auditor** — permissão concedida pelo Administrador; enxerga qualquer processo,
  inclusive sigilosos, e gera relatórios consolidados.
- **Cidadão** — sem autenticação; usa a consulta pública e o canal LGPD.

### Roadmap: o que está construído vs. pendente

O MVP é entregue por changes incrementais. Estado atual (ver `openspec/changes/` e
`openspec/specs/`):

- **Construído** — Épico 1 (autenticação, controle de acesso por perfil/unidade) e a
  base do Épico 8 (inicialização do sistema, unidades, tipos de processo + roteiros,
  gestão de usuários). É o change `identidade-e-estrutura-organizacional` (arquivado).
- **Pendente** (próximos changes) — Épico 2 (processos + workflow Kanban), Épico 3
  (gestão documental / Cloud Storage), Épico 4 (assinatura ICP-Brasil — *condicional a
  Discovery Técnico*), Épico 5 (notificações internas + e-mail), Épico 6 (dashboard de
  KPIs), Épico 7 (consulta pública), Épico 9 (auditoria/relatórios), Épico 10 (canal e
  rotinas LGPD).

Ao criar um novo change, situe-o nesse roadmap e declare de qual change anterior ele
depende (regra do `proposal` em `openspec/config.yaml`).

### Invariantes de domínio (valem para todos os épicos)

Regras estruturais que atravessam o produto — respeite-as ao modelar qualquer feature:

- **Histórico de tramitação é imutável**: cada movimentação (despacho, devolução,
  arquivamento, sigilo, assinatura) é um INSERT de evento, nunca UPDATE. Guarda data,
  hora, unidade origem/destino, responsável e ação. Já há o precedente `log_seguranca`.
- **Status do processo é máquina de estados explícita**: `Aberto → Em Tramitação →
  Concluído → Arquivado`. Transições só por ação explícita (Despachar/Concluir) ou pela
  rotina automática de arquivamento — nunca campo de texto livre, nunca drag-and-drop no
  Kanban (que é só visualização no MVP).
- **Roteiros são lineares e versionados por snapshot**: sequência ordenada de unidades
  por tipo de processo; alterá-lo afeta só processos **novos** — os em andamento mantêm o
  roteiro vigente na criação. (O código já versiona roteiros.)
- **Número do processo**: `AAAA/NNNNNN` (sequencial de 6 dígitos, reinicia por ano,
  expande dígitos sem limite superior).
- **Visibilidade por unidade tem sempre o caminho de "acesso negado"**: toda regra de
  acesso precisa do cenário de rejeição explícito, registrado em log de segurança — não
  só o caminho feliz.
- **LGPD é requisito, não opcional**: dados pessoais (CPF/CNPJ, nome de interessado)
  nunca aparecem na consulta pública; anonimização é **irreversível**; há canal público
  de solicitação e rotina automática de anonimização de arquivados. Assinatura segue
  MP 2.200-2/2001 / ICP-Brasil.
- **Parâmetros operacionais são configuráveis em runtime** (não hardcoded): prazo de
  arquivamento, timeout de sessão, tentativas de login, validade de links, etc. vivem em
  configuração do sistema (`sistema_config`, já singleton id=1), editável pelo Admin.
- **Endpoints públicos têm rate limiting**: consulta pública ≤ 60 req/min por IP (a infra
  do `slowapi` já está montada — ver `app/rate_limit.py`).

## Fluxo de trabalho: OpenSpec (spec-driven)

Este repo usa OpenSpec — **nenhum código de feature é escrito sem um change**. Antes de
tocar código de negócio, leia o change em `openspec/changes/<nome>/` (`proposal.md`,
`design.md`, `tasks.md`, `specs/`). As convenções obrigatórias de cada artefato vivem em
`openspec/config.yaml` (`rules:`) — em resumo:

- **proposal** — declara de qual change anterior depende, tabelas PostgreSQL novas/
  afetadas (com FKs), novos segredos/buckets e o tratamento LGPD quando houver dado pessoal.
- **specs** — Dado/Quando/Então referenciando a US do PRD; estados de processo como
  máquina de estados; toda visibilidade por unidade/perfil com cenário de "acesso negado".
- **design** — diagrama de sequência para fluxos que cruzam front/back/job; migrations
  Alembic descritas **antes** dos endpoints; para rotinas automáticas, documentar gatilho,
  janela e idempotência (retomada após falha).
- **tasks** — atômicas (≤ 2h). Tarefa que toque histórico/dado pessoal exige tarefa de
  teste automatizado; tarefa que altere login/despacho/assinatura/consulta pública exige
  teste **E2E Playwright** — ambos obrigatórios, não opcionais.

Specs consolidadas ficam em `openspec/specs/`; changes concluídos vão para
`openspec/changes/archive/`. Use os skills `opsx:*` / `openspec-*` para operar o fluxo.
As invariantes de domínio acima valem para todos eles.

Branches: `feature/<nome-do-change>` → `main` (GitHub Flow, sem staging). Merge `--no-ff`
obrigatório. Validação pré-produção via traffic splitting do Cloud Run, não por branch.

## Contrato frontend↔backend (crítico)

O contrato é **gerado**, não escrito à mão. O FastAPI é a fonte da verdade do OpenAPI;
`packages/api-types` contém o snapshot commitado (`openapi.json` + `schema.ts`) que
`apps/web` consome via `@setes/api-types`. **Ao mudar qualquer schema/rota do FastAPI,
regenere:**

```bash
pnpm gen:types          # regenera o snapshot commitado (chama uv/python por baixo)
pnpm gen:types:check    # o CI roda isto e FALHA se o snapshot estiver defasado
```

`apps/web/lib/api.ts` é o único cliente HTTP tipado — sem `any` nos payloads. Toda
resposta autenticada pode trazer um JWT renovado no header `X-Renewed-Token` (sliding
window); o cliente captura e persiste automaticamente.

## Comandos

**Web (`apps/web`, workspace pnpm — rode da raiz ou com `--filter @setes/web`):**
```bash
pnpm dev                                 # next dev (atalho da raiz p/ @setes/web)
pnpm --filter @setes/web typecheck       # tsc --noEmit
pnpm --filter @setes/web test            # vitest run (unit + RTL)
pnpm --filter @setes/web test -- <file>  # um arquivo/teste específico
pnpm --filter @setes/web lint            # next lint
cd apps/web && pnpm test:e2e             # Playwright (sobe api+web contra Postgres local)
```

**API (`apps/api` — gerenciada por `uv`, FORA do workspace pnpm):**
```bash
cd apps/api
uv sync --extra dev
uv run alembic upgrade head              # migrations (precisa de Postgres — ver abaixo)
uv run uvicorn app.main:app --reload     # http://localhost:8000/health
uv run pytest                            # suíte completa
uv run pytest tests/test_auth_login.py   # um arquivo
uv run pytest -k <expr>                  # por expressão
uv run ruff check .                      # lint (line-length 100)
```

Os testes pytest usam **Postgres real** (fixture `db` em `tests/conftest.py`), não
sqlite/mocks. Suba um local:
```bash
docker run -d --name setes-postgres-dev -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=setes -p 5433:5432 postgres:16-alpine
```
A fixture trunca as tabelas após cada teste. Config via `.env` (gitignored) —
ver `apps/api/.env.example` e `app/config.py`.

**Infra (`infra` — Terraform, state em GCS):**
```bash
cd infra
terraform init -backend-config=backend.hcl
terraform plan && terraform apply
```
Ver `infra/README.md` para bootstrap do state, ordem de dependências e notas de
residência de dados (tudo em `southamerica-east1`).

## Arquitetura da API

FastAPI em camadas explícitas (`apps/api/app/`):
- `routers/` — endpoints por domínio (`auth`, `usuarios`, `unidades`, `tipos_processo`,
  `setup`, `dev_tools`). Montados em `main.py`.
- `security/` — `sessao` (JWT HS256 + tabela `sessao`), `autorizacao`, `jwt`, `senha`,
  `oidc` (verifica tokens do Cloud Tasks nos endpoints `/internal/*`).
- `services/`, `schemas/` (Pydantic), `db/` (SQLAlchemy 2.x `Mapped[...]` + `models.py`,
  `session.py`, `migrations/` Alembic), `email/` (fila Cloud Tasks), `jobs/`
  (Cloud Run Jobs — manutenção diária).

**Autorização por perfil e unidade** (`security/autorizacao.py`) é central: composição
`get_current_user → require_perfil(*perfis) → require_acesso_unidade`. Perfis:
`SERVIDOR` (só a própria unidade), `GESTOR` (unidades geridas), `ADMINISTRADOR` (todas).
Toda rejeição grava uma linha imutável em `log_seguranca` (`tipo_evento=acesso_negado`).
PKs são UUID gerados na aplicação; `sistema_config` é singleton (id=1).

Endpoints `/internal/*` são OIDC-only (chamados pelo Cloud Tasks), sem sessão de usuário.
Endpoints de e-mail seguem contrato de falha: SEMPRE ACK (200) mesmo em erro de entrega,
para não redespachar (fila com `maxAttempts=1`).

`DEV_EMAIL_INBOX` / `DEV_DB_RESET` são flags **dev/E2E-only** (nunca em produção):
habilitam `GET /internal/dev/emails` e `POST /internal/dev/reset`, usados pelo Playwright
para ler links de e-mail e limpar o banco. Cada endpoint responde 404 com a flag desligada.

## Arquitetura do frontend

Next.js 15 App Router (`apps/web/app/`), React 19, Tailwind. Rotas por pasta:
`login`, `setup`, `primeiro-acesso/[token]`, `recuperar-senha`, `redefinir-senha/[token]`,
`perfil`, `admin/{unidades,usuarios,tipos-processo}`. Sessão via Bearer token em
`lib/session-store.ts` (não cookies). `components/auth-provider.tsx` +
`protected-shell.tsx` guardam rotas autenticadas. Build usa `output: standalone`.

## CI/CD

- **CI** (`.github/workflows/ci.yml`): path-filtered por app (`dorny/paths-filter`). Job
  `api` (Postgres service container → migrations → ruff → pytest), job `web` (typecheck +
  vitest), job `types-drift` (`pnpm gen:types:check`). Rode os equivalentes locais antes
  de abrir PR.
- **Deploy** (`.github/workflows/deploy.yml`, só em `main`): autentica no GCP via
  **Workload Identity Federation (WIF, sem chave JSON)**. `deploy-api` roda migrations num
  Cloud Run Job efêmero **antes** de trocar o serviço. `NEXT_PUBLIC_API_URL` não é
  configurado em build-time (gap conhecido — ver `infra/README.md`).

O `github_repository` no WIF (`infra/terraform.tfvars`, gitignored) precisa casar com o
nome real do repo GitHub, senão a autenticação de deploy falha com `unauthorized_client`.
