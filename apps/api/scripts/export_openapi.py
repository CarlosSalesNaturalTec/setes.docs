"""Emite o schema OpenAPI do FastAPI em stdout (consumido por scripts/gen-types.mjs)."""

from __future__ import annotations

import json
import sys

from app.main import app


def main() -> None:
    # stdout é capturado via pipe por scripts/gen-types.mjs; sem forçar utf-8 aqui,
    # o Windows usa o encoding do locale (ex.: cp1252) e o decoder utf-8 do Node
    # substitui os bytes inválidos por U+FFFD, corrompendo acentos silenciosamente.
    sys.stdout.reconfigure(encoding="utf-8")
    schema = app.openapi()
    json.dump(schema, sys.stdout, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
