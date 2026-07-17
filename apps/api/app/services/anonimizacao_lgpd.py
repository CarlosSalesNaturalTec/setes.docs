"""Rotina automática trimestral de anonimização LGPD (Épico 10, US 10.3, D3).

Seleciona processos `Arquivado` cujo prazo legal de anonimização — configurável
por tipo de processo — já expirou desde `arquivar_em` (congelado na conclusão,
mesmo campo usado por `services/arquivamento.py` como referência do
arquivamento), e ainda têm ao menos um interessado não anonimizado. Idempotente
por construção (D2/D3, mesmo contrato
de `services/arquivamento.py`): a seleção é função do estado atual
(`processo_interessado.anonimizado_em IS NULL`), então um processo com todos
os interessados já anonimizados não satisfaz o `EXISTS` e não é reselecionado.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import Processo
from app.services.lgpd import anonimizar_interessados

_QUERY_ELEGIVEIS = text(
    """
    SELECT p.id FROM processo p
    JOIN tipo_processo tp ON tp.id = p.tipo_processo_id
    WHERE p.status = 'arquivado'
      AND p.arquivar_em IS NOT NULL
      AND (p.arquivar_em + (tp.prazo_anonimizacao_anos || ' years')::interval) <= :agora
      AND EXISTS (
        SELECT 1 FROM processo_interessado pi
        WHERE pi.processo_id = p.id AND pi.anonimizado_em IS NULL
      )
    """
)


def processar_anonimizacao_automatica(db: Session, *, agora: datetime) -> int:
    """US 10.3 Cen.1/2/3/4 — anonimiza os processos elegíveis; retorna o total
    de processos efetivamente processados (com ao menos um interessado
    anonimizado nesta execução)."""
    ids = [row[0] for row in db.execute(_QUERY_ELEGIVEIS, {"agora": agora}).all()]
    if not ids:
        return 0

    processos = db.scalars(select(Processo).where(Processo.id.in_(ids))).all()

    total = 0
    for processo in processos:
        afetados = anonimizar_interessados(db, processo, agora=agora, origem="automatico")
        if afetados > 0:
            total += 1
    return total
