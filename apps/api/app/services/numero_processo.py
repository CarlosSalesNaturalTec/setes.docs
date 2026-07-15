"""Geração do número de processo `AAAA/NNNNNN` (D1).

Alocação atômica via upsert-incremento na mesma transação do INSERT do
processo: `INSERT ... ON CONFLICT (ano) DO UPDATE ... RETURNING`. O lock de
linha do Postgres resolve concorrência num só round-trip; como o incremento
vive na transação do processo, um rollback desfaz o número (sem gaps por
transação abortada). Formatação `f"{ano}/{seq:06d}"` garante piso de 6 dígitos
e expande naturalmente para 7, 8+ sem limite (US 2.1 Cen.1).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import LogSeguranca, TipoEventoLog

# Limiares de expansão de dígitos (D1): ao cruzar 10^6 (7 dígitos) e 10^7
# (8 dígitos) registra-se o evento; 10^7 também emite alerta de capacidade.
_LIMIAR_7_DIGITOS = 1_000_000
_LIMIAR_8_DIGITOS = 10_000_000


def alocar_numero(db: Session, ano: int) -> str:
    """Aloca e retorna o próximo número do `ano`, incrementando o contador.

    Deve ser chamada dentro da transação que insere o `processo` (o commit é
    responsabilidade do chamador). Registra `expansao_numero_processo` ao
    cruzar 10^6/10^7 e `alerta_capacidade` ao atingir 10^7.
    """
    seq = db.execute(
        text(
            """
            INSERT INTO processo_contador_ano (ano, ultimo_sequencial)
            VALUES (:ano, 1)
            ON CONFLICT (ano) DO UPDATE
              SET ultimo_sequencial = processo_contador_ano.ultimo_sequencial + 1
            RETURNING ultimo_sequencial
            """
        ),
        {"ano": ano},
    ).scalar_one()

    _registrar_capacidade(db, ano=ano, seq=seq)
    return f"{ano}/{seq:06d}"


def _registrar_capacidade(db: Session, *, ano: int, seq: int) -> None:
    if seq == _LIMIAR_7_DIGITOS:
        db.add(
            LogSeguranca(
                tipo_evento=TipoEventoLog.EXPANSAO_NUMERO_PROCESSO,
                contexto={"ano": ano, "sequencial": seq, "digitos": 7},
            )
        )
    elif seq == _LIMIAR_8_DIGITOS:
        db.add(
            LogSeguranca(
                tipo_evento=TipoEventoLog.EXPANSAO_NUMERO_PROCESSO,
                contexto={"ano": ano, "sequencial": seq, "digitos": 8},
            )
        )
        db.add(
            LogSeguranca(
                tipo_evento=TipoEventoLog.ALERTA_CAPACIDADE,
                contexto={"ano": ano, "sequencial": seq},
            )
        )
