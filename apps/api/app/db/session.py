"""Engine SQLAlchemy com pool pequeno por instância.

Cloud Run escala horizontalmente; `nº_instâncias × pool_size` não pode exceder
`max_connections` do Cloud SQL. Por isso `pool_size=5, max_overflow=0` por
instância (D-risk "Esgotamento de conexões", task 6.4). O teto é documentado
em infra/cloudrun.tf (max-instances) e aqui.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,      # 5
        max_overflow=settings.db_max_overflow,  # 0 — não abre conexões além do pool
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )
