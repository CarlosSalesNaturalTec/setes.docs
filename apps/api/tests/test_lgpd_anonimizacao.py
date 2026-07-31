"""Testes obrigatórios do serviço único de anonimização (Épico 10, D1/D2) —
dado pessoal: substituição irreversível, idempotência e não-recuperação do
documento original (tasks 3.3/3.4/3.5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import (
    LogSeguranca,
    ProcessoInteressado,
    StatusProcesso,
    TipoDocumentoInteressado,
    TipoEventoLog,
    Tramitacao,
)
from app.services.lgpd import NOME_ANONIMIZADO, anonimizar_interessados
from tests.helpers_processo import processo_concluido, servidor_com_setor, tipo_processo, unidade

CPF_ORIGINAL = "52998224725"


def _processo_com_interessado(db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    processo = processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=datetime.now(timezone.utc) - timedelta(days=1900),
        arquivar_em=datetime.now(timezone.utc) - timedelta(days=1),
        status=StatusProcesso.ARQUIVADO,
    )
    interessado = ProcessoInteressado(
        processo_id=processo.id,
        nome="Fulano de Tal",
        documento=CPF_ORIGINAL,
        tipo_documento=TipoDocumentoInteressado.CPF,
    )
    db.add(interessado)
    db.commit()
    db.refresh(interessado)
    return processo, interessado


def test_anonimizar_substitui_dados_e_preserva_processo(db):
    processo, interessado = _processo_com_interessado(db)
    numero_original = processo.numero
    status_original = processo.status
    unidade_original = processo.unidade_atual_id
    agora = datetime.now(timezone.utc)

    total = anonimizar_interessados(db, processo, agora=agora, origem="manual")

    assert total == 1
    db.refresh(interessado)
    db.refresh(processo)
    assert interessado.nome == NOME_ANONIMIZADO
    assert interessado.documento != CPF_ORIGINAL
    assert interessado.anonimizado_em == agora
    # processo intocado
    assert processo.numero == numero_original
    assert processo.status == status_original
    assert processo.unidade_atual_id == unidade_original
    assert db.query(Tramitacao).filter(Tramitacao.processo_id == processo.id).count() == 0

    eventos = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.INTERESSADO_ANONIMIZADO)
        .all()
    )
    assert len(eventos) == 1
    assert eventos[0].contexto["processo_id"] == str(processo.id)
    assert eventos[0].contexto["origem"] == "manual"


def test_anonimizar_duas_vezes_e_idempotente(db):
    processo, interessado = _processo_com_interessado(db)
    agora = datetime.now(timezone.utc)

    primeiro_total = anonimizar_interessados(db, processo, agora=agora, origem="automatico")
    db.refresh(interessado)
    anonimizado_em_primeira = interessado.anonimizado_em

    segundo_total = anonimizar_interessados(
        db, processo, agora=agora + timedelta(seconds=5), origem="automatico"
    )
    db.refresh(interessado)

    assert primeiro_total == 1
    assert segundo_total == 0
    assert interessado.anonimizado_em == anonimizado_em_primeira

    eventos = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.INTERESSADO_ANONIMIZADO)
        .all()
    )
    assert len(eventos) == 1


def test_identificador_anonimizado_nao_recupera_documento_original(db):
    processo, interessado = _processo_com_interessado(db)
    agora = datetime.now(timezone.utc)

    anonimizar_interessados(db, processo, agora=agora, origem="manual")
    db.refresh(interessado)

    assert interessado.documento != CPF_ORIGINAL
    # não é uma máscara do CPF original: formato hex, não os 11 dígitos do documento
    assert interessado.documento != CPF_ORIGINAL[:3] + "***" + CPF_ORIGINAL[-2:]
    assert not interessado.documento.isdigit()
