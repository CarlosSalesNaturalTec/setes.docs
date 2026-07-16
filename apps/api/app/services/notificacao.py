"""Serviço de notificação interna (sino), Épico 5 — US 5.1, 5.3, 5.4.

`gerar_notificacoes` é chamada dentro da transação do evento de origem
(despacho/conclusão em `services/processo.py`, ou a rotina diária de prazo em
`services/prazo.py`) — o INSERT nasce atômico com o histórico de tramitação
(D1, design.md). Não comita: quem chama controla a transação.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Notificacao, PerfilUsuario, Processo, TipoNotificacao, Unidade, Usuario

RETENCAO_LIDAS_DIAS = 30


def servidores_da_unidade(db: Session, unidade_id: uuid.UUID) -> Sequence[Usuario]:
    return db.scalars(
        select(Usuario)
        .where(Usuario.unidade_id == unidade_id)
        .where(Usuario.perfil == PerfilUsuario.SERVIDOR)
    ).all()


def gerar_notificacoes(
    db: Session,
    *,
    tipo: TipoNotificacao,
    processo: Processo,
    unidade_id: uuid.UUID,
    unidade_origem_id: uuid.UUID | None = None,
    prazo_referencia: date | None = None,
) -> list[Notificacao]:
    """Gera uma `Notificacao` (não lida) por servidor de `unidade_id` (D2 — fan-out por linha)."""
    unidade = db.get(Unidade, unidade_id)
    unidade_origem = db.get(Unidade, unidade_origem_id) if unidade_origem_id else None

    notificacoes = []
    for servidor in servidores_da_unidade(db, unidade_id):
        notificacao = Notificacao(
            usuario_id=servidor.id,
            processo_id=processo.id,
            unidade_id=unidade_id,
            unidade_nome=unidade.nome,
            unidade_origem_id=unidade_origem_id,
            unidade_origem_nome=unidade_origem.nome if unidade_origem else None,
            tipo=tipo,
            numero_processo=processo.numero,
            assunto=processo.assunto,
            prazo_referencia=prazo_referencia,
        )
        db.add(notificacao)
        notificacoes.append(notificacao)
    return notificacoes


def expurgar_notificacoes_lidas(db: Session, *, agora: datetime) -> int:
    """Remove fisicamente notificações lidas há mais de 30 dias (D5); nunca toca não lidas.

    Idempotente por construção do WHERE — reexecutar sobre o mesmo estado remove 0.
    """
    limite = agora - timedelta(days=RETENCAO_LIDAS_DIAS)
    total = (
        db.query(Notificacao)
        .filter(Notificacao.lida_em.isnot(None), Notificacao.lida_em < limite)
        .delete(synchronize_session=False)
    )
    db.commit()
    return total
