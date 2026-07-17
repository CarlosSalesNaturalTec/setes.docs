"""Serviço único de anonimização de interessado (Épico 10, D1).

`anonimizar_interessados` é o único ponto que produz o efeito irreversível
"dado pessoal anonimizado" — consumido tanto pelo atendimento manual de
solicitação LGPD (`routers/lgpd.py`, US 10.2) quanto pela rotina automática
trimestral (`services/anonimizacao_lgpd.py`, US 10.3), com `origem` distinta
mas o mesmo critério do que constitui "anonimizado" (D1, spec
`anonimizacao-lgpd` — "Efeito idêntico entre anonimização manual e
automática").
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LogSeguranca, Processo, ProcessoInteressado, TipoEventoLog

NOME_ANONIMIZADO = "Titular Anonimizado"


def gerar_identificador_anonimizado() -> str:
    """Identificador irreversível para o documento (CPF/CNPJ) anonimizado (D1).

    Hash de um valor aleatório (não do documento original) — ao contrário de um
    hash determinístico do CPF/CNPJ, não permite correlação por força bruta
    (testar candidatos de CPF contra o hash), garantindo irreversibilidade real.
    Truncado a 14 caracteres — mesmo teto de `processo_interessado.documento`.
    """
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:14]


def anonimizar_interessados(
    db: Session,
    processo: Processo,
    *,
    agora: datetime,
    origem: str,
    solicitacao_lgpd_id: uuid.UUID | None = None,
) -> int:
    """Anonimiza os interessados do `processo` ainda não anonimizados (US 10.2/10.3).

    Guard de idempotência (D2): só afeta `processo_interessado.anonimizado_em
    IS NULL`. Registra **um único** evento `interessado_anonimizado` em
    `log_seguranca` por processo — nenhum evento é gravado quando não há
    interessado elegível (reexecução sobre o mesmo estado é no-op, D2/D3).
    Preserva número do processo, datas, unidades, status e histórico de
    tramitação — só toca `processo_interessado.nome`/`documento`.
    """
    interessados = list(
        db.scalars(
            select(ProcessoInteressado)
            .where(ProcessoInteressado.processo_id == processo.id)
            .where(ProcessoInteressado.anonimizado_em.is_(None))
        ).all()
    )
    if not interessados:
        return 0

    for interessado in interessados:
        interessado.nome = NOME_ANONIMIZADO
        if interessado.documento is not None:
            interessado.documento = gerar_identificador_anonimizado()
        interessado.anonimizado_em = agora

    db.add(
        LogSeguranca(
            tipo_evento=TipoEventoLog.INTERESSADO_ANONIMIZADO,
            contexto={
                "processo_id": str(processo.id),
                "origem": origem,
                "solicitacao_lgpd_id": str(solicitacao_lgpd_id) if solicitacao_lgpd_id else None,
            },
        )
    )
    db.commit()
    return len(interessados)
