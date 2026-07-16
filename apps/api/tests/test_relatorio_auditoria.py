"""Relatório consolidado de auditoria (US 9.2, task 3.4 — obrigatório: toca
dado pessoal e `log_seguranca`). Cobre D4/D5/D6 de
`openspec/changes/auditoria-e-relatorios/design.md`."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from app.db.models import LogSeguranca, PerfilUsuario, Processo, StatusProcesso, TipoEventoLog
from app.services import relatorio_auditoria as relatorio_service
from app.services.roteiros import obter_roteiro_vigente
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario

HOJE = date(2026, 7, 16)


def _processo(
    db,
    *,
    unidade_obj,
    criador,
    tipo,
    criado_em: datetime,
    status: StatusProcesso = StatusProcesso.ABERTO,
    concluido_em: datetime | None = None,
) -> Processo:
    roteiro = obter_roteiro_vigente(db, tipo.id)
    processo = Processo(
        numero=f"2026/{uuid.uuid4().int % 999999:06d}",
        assunto="Processo de teste",
        tipo_processo_id=tipo.id,
        roteiro_id=roteiro.id,
        status=status,
        unidade_atual_id=unidade_obj.id,
        unidade_origem_id=unidade_obj.id,
        ordem_atual=0,
        prazo_dias=30,
        prazo_em=criado_em.date() + timedelta(days=30),
        criado_por_id=criador.id,
        criado_em=criado_em,
        concluido_em=concluido_em,
    )
    db.add(processo)
    db.commit()
    return processo


def _auditor(db, *, unidade_obj) -> object:
    auditor = usuario(db, unidade_id=unidade_obj.id, email=f"auditor-{uuid.uuid4()}@ex.com")
    auditor.pode_auditar = True
    db.commit()
    return auditor


# --- 3.1 — service (funções puras) -------------------------------------------


def test_gerar_relatorio_totaliza_e_calcula_tempo_medio_no_periodo(db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)

    _processo(
        db,
        unidade_obj=cofin,
        criador=criador,
        tipo=tipo,
        criado_em=datetime(2026, 6, 1, tzinfo=timezone.utc),
        status=StatusProcesso.CONCLUIDO,
        concluido_em=datetime(2026, 6, 11, tzinfo=timezone.utc),
    )
    _processo(
        db,
        unidade_obj=cofin,
        criador=criador,
        tipo=tipo,
        criado_em=datetime(2026, 6, 5, tzinfo=timezone.utc),
        status=StatusProcesso.CONCLUIDO,
        concluido_em=datetime(2026, 6, 25, tzinfo=timezone.utc),
    )
    # Fora do período — não deve entrar no total.
    _processo(
        db,
        unidade_obj=cofin,
        criador=criador,
        tipo=tipo,
        criado_em=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status=StatusProcesso.CONCLUIDO,
        concluido_em=datetime(2026, 1, 5, tzinfo=timezone.utc),
    )

    total, tempo_medio, processos = relatorio_service.gerar_relatorio(
        db, inicio=date(2026, 6, 1), fim=date(2026, 6, 30)
    )

    assert total == 2
    assert tempo_medio == 15.0  # (10 + 20) / 2
    assert len(processos) == 2


def test_gerar_relatorio_filtra_por_unidade_e_tipo(db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    tipo_cofin = tipo_com_roteiro(db, cofin, nome="TipoCofin")
    tipo_ajur = tipo_com_roteiro(db, ajur, nome="TipoAjur")
    criador = usuario(db, unidade_id=cofin.id)

    _processo(db, unidade_obj=cofin, criador=criador, tipo=tipo_cofin, criado_em=datetime.now(timezone.utc))
    _processo(db, unidade_obj=ajur, criador=criador, tipo=tipo_ajur, criado_em=datetime.now(timezone.utc))

    total_unidade, _, _ = relatorio_service.gerar_relatorio(db, unidade_id=cofin.id)
    assert total_unidade == 1

    total_tipo, _, _ = relatorio_service.gerar_relatorio(db, tipo_processo_id=tipo_ajur.id)
    assert total_tipo == 1


def test_gerar_relatorio_tempo_medio_none_sem_concluidos(db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)

    _processo(
        db,
        unidade_obj=cofin,
        criador=criador,
        tipo=tipo,
        criado_em=datetime.now(timezone.utc),
        status=StatusProcesso.EM_TRAMITACAO,
    )

    total, tempo_medio, _ = relatorio_service.gerar_relatorio(db)
    assert total == 1
    assert tempo_medio is None


def test_gerar_relatorio_sem_processos_retorna_vazio(db):
    total, tempo_medio, processos = relatorio_service.gerar_relatorio(
        db, inicio=date(2020, 1, 1), fim=date(2020, 1, 2)
    )
    assert total == 0
    assert tempo_medio is None
    assert processos == []


# --- 3.3 — endpoint ------------------------------------------------------


def test_auditor_gera_relatorio_com_filtros(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    _processo(
        db,
        unidade_obj=cofin,
        criador=criador,
        tipo=tipo,
        criado_em=datetime(2026, 6, 10, tzinfo=timezone.utc),
        status=StatusProcesso.CONCLUIDO,
        concluido_em=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    auditor = _auditor(db, unidade_obj=cofin)
    token = login(client, auditor.email)

    resp = client.get(
        "/auditoria/relatorio",
        params={"inicio": "2026-06-01", "fim": "2026-06-30"},
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_processos"] == 1
    assert body["tempo_medio_tramitacao_dias"] == 5.0
    assert body["mensagem_vazio"] is None
    assert body["items"][0]["status"] == "concluido"


def test_relatorio_sem_resultado_retorna_mensagem_vazio(client, db):
    cofin = unidade(db, "COFIN")
    auditor = _auditor(db, unidade_obj=cofin)
    token = login(client, auditor.email)

    resp = client.get(
        "/auditoria/relatorio",
        params={"inicio": "2020-01-01", "fim": "2020-01-02"},
        headers=auth(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_processos"] == 0
    assert body["mensagem_vazio"] == "Nenhum dado encontrado para os filtros informados"


def test_nao_auditor_recebe_acesso_negado_e_loga(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor-relatorio@ex.com")
    token = login(client, servidor.email)

    resp = client.get("/auditoria/relatorio", headers=auth(token))

    assert resp.status_code == 403
    logs = db.query(LogSeguranca).filter(
        LogSeguranca.usuario_id == servidor.id, LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO
    ).all()
    assert len(logs) == 1
