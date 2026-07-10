# apps/api — FastAPI. Build a partir de apps/api (contexto = este diretório).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instala uv (gerenciador do apps/api).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# O build backend (hatchling) precisa do pyproject.toml, do README e do pacote
# `app` para gerar o wheel — todos presentes antes do install.
COPY pyproject.toml README.md ./
COPY app ./app
RUN uv pip install --system --no-cache .

# Demais artefatos de runtime (migrations, alembic, scripts).
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

EXPOSE 8080
# Cloud Run injeta $PORT (default 8080).
ENV PORT=8080

# Health check do contêiner (task 1.4).
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/health').status==200 else 1)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
