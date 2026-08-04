# setes-api

Backend FastAPI do Despapelize (cliente: SETES). Gerenciado por `uv` (fora do workspace pnpm).

## Desenvolvimento local

Requer um Postgres local (as tabelas de negócio nascem em
`migrations/0002_identidade_estrutura_organizacional.py`) e um `.env`
(gitignored) com as variáveis abaixo — veja `.env.example`:

```bash
docker run -d --name setes-postgres-dev -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=senha -e POSTGRES_DB=setes -p 5433:5432 postgres:16-alpine
```

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# health: http://localhost:8000/health
```

Sem `uv`, o equivalente com venv:

```bash
python -m venv .venv && source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Variáveis principais do `.env` (ver `app/config.py` para a lista completa):
`DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`, `JWT_SIGNING_KEY`
(assinatura HS256 das sessões, D1), `FRONTEND_BASE_URL` (base dos links de
e-mail de primeiro acesso/recuperação de senha), `SENDGRID_API_KEY`/
`EMAIL_FROM` (provedor de e-mail transacional), `CLOUD_TASKS_LOCATION`/
`CLOUD_TASKS_QUEUE`/`OIDC_AUDIENCE`/`TASKS_INVOKER_SA_EMAIL` (fila assíncrona
de e-mail, D10). `DEV_EMAIL_INBOX`/`DEV_DB_RESET` são dev/E2E-only — nunca
setadas em produção — ver "Testes E2E (Playwright)" abaixo.

## Rotas de autenticação e identidade (change `identidade-e-estrutura-organizacional`)

- `POST /setup`, `GET /setup/status` — inicialização única do sistema (US 8.0).
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` — sessão (D1).
- `POST /auth/primeiro-acesso/{token}`, `POST /auth/recuperar-senha`,
  `POST /auth/redefinir-senha/{token}`, `POST /auth/trocar-senha` — tokens de
  uso único e troca de senha (D3).
- `POST /admin/usuarios/{id}/resetar-senha` — reset administrativo (US 1.10).
- `GET/POST /usuarios`, `PATCH /usuarios/{id}/unidade`,
  `GET/PUT /usuarios/{id}/unidades-geridas`, `GET /usuarios/me/perfil` — gestão
  de usuários e "Meu Perfil".
- `GET/POST/PATCH /unidades`, `POST /unidades/{id}/desativar` — unidades
  administrativas (US 8.1).
- `GET/POST /tipos-processo`, `PUT /tipos-processo/{id}/roteiro` — tipos de
  processo e roteiro de tramitação versionado (US 8.2).

Todas exigem `Authorization: Bearer <token>` exceto `/setup*`, `/auth/login`,
`/auth/primeiro-acesso/{token}`, `/auth/recuperar-senha`,
`/auth/redefinir-senha/{token}` e `/internal/*`.

## Testes

```bash
uv run pytest
```

## Exportar o contrato OpenAPI (para gerar os tipos TS)

```bash
uv run python scripts/export_openapi.py > /dev/null   # imprime o JSON em stdout
```

Do raiz do monorepo: `pnpm gen:types`.

## Migrations (Alembic)

Baseline vazia (sem tabela de negócio). Ver `migrations/`.

```bash
uv run alembic upgrade head
```

## Testes E2E (Playwright)

Os fluxos críticos (`apps/web/e2e/`) sobem esta API + o Next.js dev server e
rodam contra o Postgres local de desenvolvimento. `apps/web/playwright.config.ts`
inicia a API com `DEV_EMAIL_INBOX=true` e `DEV_DB_RESET=true` — habilitam
`GET /internal/dev/emails` (lê o link de primeiro acesso/recuperação de senha
sem um provedor de e-mail real) e `POST /internal/dev/reset` (banco limpo
antes da suíte). Nenhuma das duas é setada no `.env` de dev normal nem em
produção — cada endpoint responde 404 quando sua flag está desligada.

```bash
cd apps/web && pnpm test:e2e
```

<!-- no-op: valida deploy-api via WIF após correcao-pipeline-deploy-wif -->

