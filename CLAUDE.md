# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

Despapelize (cliente: SETES) — sistema de gestão de processos administrativos (tramitação manual,
sigilo, consulta pública, LGPD) para uma **instituição privada** (a premissa
anterior de órgão público estava incorreta — change `migracao-regiao-us-central1`
D6; a LGPD permanece obrigatória integralmente).
Monorepo poliglota: **Next.js (web) + FastAPI (api) + Terraform (infra)** em GCP.

Linguagem de código: **português brasileiro** para entidades e regras de negócio
(Processo, Unidade, Setor, Tramitação, Modelo de Documento); inglês só para termos
técnicos de infra (Repository, Service, Router). Comentários e docstrings em português.

### Ajustes pós-avaliação — o que **não** existe mais

Seis changes (`docs/Ajustes SETES DOCS.pdf`, arquivados entre 2026-07-31 e
2026-08-03) reescreveram partes centrais do domínio. O que foi **removido** e não
deve ser reintroduzido sem decisão explícita:

- **Roteiro / tramitação automática por tipo de processo**: eliminado
  (`tramitacao-manual`, migration `0024_remover_roteiro`). O servidor escolhe
  destino a cada passo — unidade, setor, servidor e mensagem. `TipoEventoTramitacao`
  passou a ser `envio` (ex-`despacho`), `reatribuicao`, `devolucao`, `conclusao`.
- **Kanban por unidade inteira**: o quadro do Servidor é **pessoal** (criados por ele
  ou direcionados a ele); Gestor vê as unidades sob sua gestão. Arquivados ficam
  ocultos por padrão (`kanban-por-servidor`).
- **Formulário inline de cadastro de usuário no index**: virou modal próprio; o
  espaço no index passou a ser filtro por nome (`setores-e-cadastro-usuario`).

O que foi **acrescentado**: `Setor` (2º nível da estrutura, 1:N com Unidade — não é
fronteira de permissão, o escopo de acesso continua sendo a Unidade); campos de
usuário `telefone`/`cargo`/`chefia_direta`/`setor_id`; catálogo de
`ModeloDocumento` com lacunas preenchidas na abertura do processo
(`modelos-de-documento`); "Meu Perfil" em abas (`perfil-em-abas`).

**Assinatura digital ICP-Brasil (Épico 4 do PRD) está FORA DE ESCOPO** — movida para
a Fase 2 em 2026-07-27. A aba "Documentos assinados" do perfil é placeholder vazio;
não há capability, spec Playwright nem código de assinatura.

O estudo de viabilidade da Fase 2 está em **`docs/fase2-assinatura/`** (estudo
técnico, questionário enviado ao cliente e o arquivo onde as respostas serão
registradas). **Leia o `README.md` de lá antes de qualquer trabalho de assinatura** —
ele documenta os dois portões que bloqueiam a implementação: a retomada formal do
épico ainda não foi decidida, e três critérios de aceite do Épico 4 descrevem um
fluxo tecnicamente impossível que precisa ser reescrito. O estudo **não** retoma o
épico nem autoriza implementação.

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
  tramitação **exigem** teste automatizado correspondente; login/tramitação/documentos/
  consulta pública exigem **teste E2E Playwright** (não opcional).
- Conformidade LGPD (Lei 13.709/2018) obrigatória ao tocar dados pessoais/documentos.

Skills OpenSpec disponíveis via Skill tool: `opsx:new`, `opsx:propose`, `opsx:apply`,
`opsx:continue`, `opsx:verify`, `opsx:archive` (e variantes). `openspec/specs/` guarda
as specs consolidadas por capability; `openspec/changes/archive/` os changes concluídos,
nomeados `YYYY-MM-DD-<slug>`.

### Decisões de design são citadas no código (`(Dx)`)

Cada change tem um `design.md` com decisões numeradas **D1, D2, …**. O código as cita
em comentários/docstrings — `# rate limit em memória do processo (D6)`, `Sessão (D1)`,
`Change visibilidade-processos-origem (design.md D7)`. São ~50 arquivos com essas
referências; **os `Dx` só fazem sentido dentro do change que os definiu**. Ao encontrar
um, localize o `design.md` correspondente em `openspec/changes/archive/` antes de mexer
na regra — e mantenha a citação ao editar a linha. Ao implementar um change novo, cite
a decisão da mesma forma.

### Manual do usuário (`docs/manual/`)

O manual do usuário final vive em `docs/manual/` e é publicado como site MkDocs no
GitHub Pages pelo workflow `.github/workflows/publicar-manual.yml`. A publicação só
ocorre **após merge em `main`** (`on: push: branches: [main]` + path filter em
`docs/manual/**`, `mkdocs.yml`, `requirements-docs.txt`) — nunca a partir de PR.
Valide localmente antes de abrir PR com `mkdocs build --strict` (mesmo comando que
roda em CI, ver CI/CD abaixo); ele transforma link quebrado ou página fora do `nav`
em erro.

**Nunca aponte `docs_dir` (em `mkdocs.yml`) para `docs/`** — apenas para
`docs/manual/`. O site do Pages é público e `docs/` contém o PRD, URLs de produção,
configuração do provedor de e-mail e o PDF comercial do cliente; simplificar o
`docs_dir` publicaria tudo isso.

Toda change que altere uma tela, um fluxo de usuário final ou o texto exibido ao
usuário deve incluir tarefa de atualizar `docs/manual/**` — regra vinculante em
`openspec/config.yaml` (`rules.tasks`), com o mesmo peso das regras de teste
automatizado, E2E e `gen:types`.

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

`ruff check .` cobre `app/`, `tests/` **e `migrations/`** (line-length 100, target py312).

Requer Postgres local — a suíte pytest usa **Postgres real** (fixture `db` em
`tests/conftest.py`), não sqlite/mocks:
```bash
docker run -d --name setes-postgres-dev -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=setes -p 5433:5432 postgres:16-alpine
```
Variáveis do `.env` (gitignored) documentadas em `apps/api/README.md` / `app/config.py`.

Isolamento dos testes tem duas consequências práticas:
- a fixture `db` chama `resetar_banco()` **depois de cada teste** — truncamento global,
  não transação por teste. A suíte **não é paralelizável** (nada de `-n auto`) e não
  pode rodar junto com o Playwright ou com um uvicorn apontando para o mesmo banco.
- a fixture `client` chama `limiter.reset()` porque o rate limit (slowapi) é contador
  em memória do processo; ao testar `/publico/*`, use essa fixture ou o contador vaza
  entre testes.

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
  modelos, unidades — que também expõe `/setores` —, usuarios, lgpd, consulta_publica,
  auditoria, dashboard, …). Montados em `main.py`.
- `services/` — regras de negócio (processo_estado = máquina de estados, arquivamento,
  modelo_documento, anonimizacao_lgpd, numero_processo, sigilo, …). Routers finos,
  lógica no service.
- `db/models.py` — SQLAlchemy 2.x; enums de domínio (`StatusProcesso`,
  `PerfilUsuario`, `TipoEventoTramitacao`, …) no topo. `migrations/` é Alembic.
- `schemas/` — modelos Pydantic de request/response, um arquivo por área (espelha
  `routers/`). É o que vira o OpenAPI → `packages/api-types`.
- `security/` — jwt, sessao, senha (bcrypt), oidc (endpoints internos), autorizacao.
- `jobs/` — Cloud Run Jobs. `entrypoint.py` = manutenção diária (arquivamento, purga
  de documentos, verificação de prazos, expurgo de notificações), idempotente por
  seleção de estado. `entrypoint_lgpd.py` = anonimização trimestral.
- Endpoints `/internal/*` são OIDC-only (chamados por Cloud Tasks/Scheduler);
  `/publico/*` são sem-auth com rate limiting (`app/rate_limit.py`, slowapi).

### Migrations (Alembic) — revisions sequenciais escritas à mão
`migrations/versions/` usa IDs **sequenciais legíveis** (`0019_ix_unidade_origem`), não
os hashes que o Alembic gera. Crie o arquivo manualmente seguindo o padrão do último:
`revision = "NNNN_<slug>"`, `down_revision` = o número anterior, e docstring com a
descrição + o change/decisão que a originou (`Change <nome> (design.md D7)`).
**Não use `alembic revision --autogenerate`** sem renomear revision/arquivo — o hash
quebra a convenção e a cadeia fica ilegível. Toda migration passa pelo `ruff check`.

### Frontend `apps/web` (Next.js App Router)
Rotas em `app/` espelham o domínio (`/processos`, `/admin/*` — inclui
`/admin/modelos` e `/admin/unidades`, que administra setores —, `/perfil` (abas),
`/consulta-publica`, `/lgpd`, `/auditoria`, `/setup`,
`/primeiro-acesso/[token]`). `lib/` = client HTTP,
session-store, validação, rota-inicial (redirect por perfil). `components/` = shell
protegido, auth-provider, session-watcher, sino de notificações. Testes Vitest ficam
**colocados** junto ao código (`lib/api.test.ts`, `components/*.test.tsx`), não em
diretório separado.

### Infra `infra/` (Terraform, GCP)
Região única **`us-central1`** (`var.region`) — escolha de custo pedida pelo cliente,
não residência de dados; a transferência internacional está documentada em
`docs/lgpd-transferencia-internacional-us-central1.md` (change
`migracao-regiao-us-central1`). Nenhum recurso deve fixar região literal.
Cloud Run (web + api), Cloud SQL (Postgres, IP privado), Cloud Storage (documentos),
Secret Manager (`db-password`, `jwt-signing-key`, `sendgrid-api-key`), Cloud Tasks
(fila `emails` assíncrona), Cloud Scheduler + Cloud Run Jobs (manutenção/LGPD). Deploy
via **Workload Identity Federation** (sem chave JSON). `terraform.tfvars` e
`backend.hcl` são gitignored (ver `.example`).

### CI/CD
- `.github/workflows/ci.yml` — path-filtered por app. Job **api**: Postgres service
  container real + `ruff check` + `pytest`. Job **web**: `typecheck` + `vitest`. Job
  **types-drift**: `gen:types:check`. Job **manual**: `mkdocs build --strict` em PR
  que toque `docs/manual/**` — valida, não publica (publicação continua exclusiva de
  `publicar-manual.yml` após merge em `main`).
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
