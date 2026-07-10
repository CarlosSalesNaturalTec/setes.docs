# setes-api

Backend FastAPI do SETES.DOCS. Gerenciado por `uv` (fora do workspace pnpm).

## Desenvolvimento local

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
# health: http://localhost:8000/health
```

Sem `uv`, o equivalente com venv:

```bash
python -m venv .venv && source .venv/Scripts/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

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
