"""Teste da geração do número de processo (task 2.4 — obrigatório, invariante
de número do processo)."""

from __future__ import annotations

from sqlalchemy import text

from app.db.models import LogSeguranca, TipoEventoLog
from app.services.numero_processo import alocar_numero


def test_primeiro_numero_do_ano_com_seis_digitos(db):
    numero = alocar_numero(db, 2026)
    db.commit()
    assert numero == "2026/000001"


def test_sequencial_incrementa_no_mesmo_ano(db):
    n1 = alocar_numero(db, 2026)
    n2 = alocar_numero(db, 2026)
    n3 = alocar_numero(db, 2026)
    db.commit()
    assert [n1, n2, n3] == ["2026/000001", "2026/000002", "2026/000003"]


def test_reinicio_por_ano(db):
    alocar_numero(db, 2025)
    alocar_numero(db, 2025)
    n_2026 = alocar_numero(db, 2026)
    db.commit()
    assert n_2026 == "2026/000001"


def test_expansao_de_digitos_ao_cruzar_um_milhao(db):
    # Pré-posiciona o contador em 999.999 (Cen. de expansão da US 2.1 Cen.1).
    db.execute(
        text("INSERT INTO processo_contador_ano (ano, ultimo_sequencial) VALUES (2026, 999999)")
    )
    numero = alocar_numero(db, 2026)
    db.commit()
    assert numero == "2026/1000000"  # 7 dígitos, sem limite superior

    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.EXPANSAO_NUMERO_PROCESSO)
        .all()
    )
    assert len(logs) == 1
    assert logs[0].contexto["digitos"] == 7


def test_sem_gap_apos_rollback(db):
    n1 = alocar_numero(db, 2026)
    db.commit()
    assert n1 == "2026/000001"

    # Aloca e desfaz — o incremento vive na transação, então o rollback o desfaz.
    alocar_numero(db, 2026)  # seria 000002
    db.rollback()

    n_apos_rollback = alocar_numero(db, 2026)
    db.commit()
    assert n_apos_rollback == "2026/000002"  # reaproveita, sem buraco


def test_unicidade_sob_alocacoes_concorrentes_simuladas(db):
    from app.db.session import get_session_factory

    # Duas sessões (transações) distintas alocando no mesmo ano: o lock de
    # linha do upsert serializa; nenhum número colide.
    numeros = set()
    factory = get_session_factory()
    s1 = factory()
    s2 = factory()
    try:
        numeros.add(alocar_numero(s1, 2026))
        s1.commit()
        numeros.add(alocar_numero(s2, 2026))
        s2.commit()
    finally:
        s1.close()
        s2.close()
    assert numeros == {"2026/000001", "2026/000002"}
