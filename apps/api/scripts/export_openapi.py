"""Emite o schema OpenAPI do FastAPI em stdout (consumido por scripts/gen-types.mjs)."""

from __future__ import annotations

import json
import sys

from app.main import app


def main() -> None:
    schema = app.openapi()
    json.dump(schema, sys.stdout, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
