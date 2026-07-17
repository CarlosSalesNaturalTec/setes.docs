"""Geração do protocolo `LGPD/AAAA/NNNNNN` (D5).

Mesmo padrão de concorrência-segura de `services/numero_processo.py`:
alocação atômica via upsert-incremento (`INSERT ... ON CONFLICT DO UPDATE
... RETURNING`) na mesma transação da criação da `solicitacao_lgpd`. Tabela
própria (`solicitacao_lgpd_contador_ano`) — sequência independente da
numeração de processo (D5, design.md).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def gerar_protocolo(db: Session, *, ano: int | None = None) -> str:
    """Aloca e retorna o próximo protocolo do ano corrente (ou `ano`, se informado).

    Deve ser chamada dentro da transação que insere a `solicitacao_lgpd` (o
    commit é responsabilidade do chamador).
    """
    ano = ano if ano is not None else date.today().year
    seq = db.execute(
        text(
            """
            INSERT INTO solicitacao_lgpd_contador_ano (ano, ultimo_sequencial)
            VALUES (:ano, 1)
            ON CONFLICT (ano) DO UPDATE
              SET ultimo_sequencial = solicitacao_lgpd_contador_ano.ultimo_sequencial + 1
            RETURNING ultimo_sequencial
            """
        ),
        {"ano": ano},
    ).scalar_one()
    return f"LGPD/{ano}/{seq:06d}"
