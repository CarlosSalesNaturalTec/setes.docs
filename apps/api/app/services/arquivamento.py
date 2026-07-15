"""Rotina diária de arquivamento automático (US 2.5, D4/D5).

Seleciona processos `Concluído` cujo `arquivar_em` (congelado na conclusão,
D1) já expirou e os transiciona para `Arquivado`, registrando um evento
imutável por processo. A seleção é função do estado atual — reexecução ou
retomada após indisponibilidade não duplicam efeito (a transição é o guard,
Cen.3/4). Commit por processo: uma falha a meio caminho preserva o progresso
já feito (D5).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Processo, StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services.processo_estado import validar_transicao


def arquivar_vencidos(db: Session, *, agora: datetime) -> int:
    """Arquiva os processos concluídos vencidos; retorna quantos foram transicionados."""
    processos = db.scalars(
        select(Processo)
        .where(Processo.status == StatusProcesso.CONCLUIDO)
        .where(Processo.arquivar_em <= agora)
    ).all()

    total = 0
    for processo in processos:
        validar_transicao(processo.status, StatusProcesso.ARQUIVADO)
        processo.status = StatusProcesso.ARQUIVADO
        db.add(
            Tramitacao(
                processo_id=processo.id,
                tipo_evento=TipoEventoTramitacao.ARQUIVAMENTO_AUTOMATICO,
                unidade_origem_id=None,
                unidade_destino_id=None,
                responsavel_id=None,
                status_resultante=StatusProcesso.ARQUIVADO,
            )
        )
        db.commit()  # por processo (D5) — retomável a meio caminho
        total += 1

    return total
