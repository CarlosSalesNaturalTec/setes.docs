"""Testes de GET /dashboard/* (task 4.4). US 6.1 — escopo, drill-down e acesso negado."""

from __future__ import annotations

from datetime import date, timedelta

from app.db.models import LogSeguranca, PerfilUsuario, TipoEventoLog
from tests.helpers_processo import (
    auth,
    gestor_de,
    login,
    processo_ativo,
    tipo_com_roteiro,
    unidade,
    usuario,
)


def test_gestor_recebe_kpis_do_escopo(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin, email="gestor-kpi@example.com")
    criador = usuario(db, unidade_id=cofin.id, email="criador-kpi@example.com")
    tipo_cofin = tipo_com_roteiro(db, cofin)
    tipo_ajur = tipo_com_roteiro(db, ajur)

    hoje = date.today()
    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo_cofin, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))

    token = login(client, gestor.email)
    resp = client.get("/dashboard/kpis", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total_processos_ativos"] == 1


def test_estado_vazio_gestor_sem_processos(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-vazio@example.com")

    token = login(client, gestor.email)
    resp = client.get("/dashboard/kpis", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total_processos_ativos"] == 0
    assert corpo["tempo_medio_tramitacao_dias"] is None
    assert corpo["total_processos_parados"] == 0
    assert corpo["produtividade_por_unidade"] == []
    assert corpo["prazos_em_risco"] == []


def test_drill_down_ativos_reflete_contagem_do_kpi(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-drill@example.com")
    criador = usuario(db, unidade_id=cofin.id, email="criador-drill@example.com")
    tipo = tipo_com_roteiro(db, cofin)

    hoje = date.today()
    p1 = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=5))
    p2 = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=8))

    token = login(client, gestor.email)
    resp_kpi = client.get("/dashboard/kpis", headers=auth(token))
    resp_drill = client.get("/dashboard/processos-ativos", headers=auth(token))

    assert resp_kpi.json()["total_processos_ativos"] == resp_drill.json()["total"]
    ids = {item["id"] for item in resp_drill.json()["items"]}
    assert ids == {str(p1.id), str(p2.id)}


def test_drill_down_parados_reflete_contagem_do_kpi(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-parado@example.com")

    token = login(client, gestor.email)
    resp_kpi = client.get("/dashboard/kpis", headers=auth(token))
    resp_drill = client.get("/dashboard/processos-parados", headers=auth(token))

    assert resp_kpi.json()["total_processos_parados"] == resp_drill.json()["total"] == 0


def test_filtro_por_unidade_gerida_restringe_calculo(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin, ajur, email="gestor-filtro@example.com")
    criador = usuario(db, unidade_id=cofin.id, email="criador-filtro@example.com")
    tipo_cofin = tipo_com_roteiro(db, cofin)
    tipo_ajur = tipo_com_roteiro(db, ajur)

    hoje = date.today()
    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo_cofin, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))

    token = login(client, gestor.email)
    resp = client.get("/dashboard/kpis", params={"unidade_id": str(cofin.id)}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_processos_ativos"] == 1


def test_nao_gestor_recebe_acesso_negado_e_loga(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor-dash@example.com")
    token = login(client, servidor.email)

    resp = client.get("/dashboard/kpis", headers=auth(token))
    assert resp.status_code == 403

    log = (
        db.query(LogSeguranca)
        .filter(
            LogSeguranca.usuario_id == servidor.id,
            LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO,
        )
        .first()
    )
    assert log is not None


def test_gestor_consulta_unidade_nao_gerida_recebe_acesso_negado_e_loga(client, db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin, email="gestor-negado@example.com")

    token = login(client, gestor.email)
    resp = client.get("/dashboard/kpis", params={"unidade_id": str(dirad.id)}, headers=auth(token))
    assert resp.status_code == 403

    log = (
        db.query(LogSeguranca)
        .filter(
            LogSeguranca.usuario_id == gestor.id,
            LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO,
        )
        .first()
    )
    assert log is not None


def test_gestor_consulta_unidade_nao_gerida_nos_drill_downs_recebe_acesso_negado(client, db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin, email="gestor-negado2@example.com")

    token = login(client, gestor.email)
    resp_ativos = client.get(
        "/dashboard/processos-ativos", params={"unidade_id": str(dirad.id)}, headers=auth(token)
    )
    resp_parados = client.get(
        "/dashboard/processos-parados", params={"unidade_id": str(dirad.id)}, headers=auth(token)
    )
    assert resp_ativos.status_code == 403
    assert resp_parados.status_code == 403


def test_gestor_recebe_distribuicoes_do_escopo(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin, email="gestor-dist@example.com")
    criador = usuario(db, unidade_id=cofin.id, email="criador-dist@example.com")
    tipo_cofin = tipo_com_roteiro(db, cofin)
    tipo_ajur = tipo_com_roteiro(db, ajur)

    hoje = date.today()
    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo_cofin, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))

    token = login(client, gestor.email)
    resp = client.get("/dashboard/distribuicoes", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["por_unidade"] == [{"rotulo": cofin.nome, "quantidade": 1}]
    assert corpo["por_tipo"] == [{"rotulo": tipo_cofin.nome, "quantidade": 1}]
    assert corpo["por_usuario"] == [{"rotulo": criador.nome, "quantidade": 1}]


def test_filtro_por_unidade_restringe_distribuicoes(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin, ajur, email="gestor-dist-filtro@example.com")
    criador = usuario(db, unidade_id=cofin.id, email="criador-dist-filtro@example.com")
    tipo_cofin = tipo_com_roteiro(db, cofin)
    tipo_ajur = tipo_com_roteiro(db, ajur)

    hoje = date.today()
    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo_cofin, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))

    token = login(client, gestor.email)
    resp = client.get(
        "/dashboard/distribuicoes", params={"unidade_id": str(cofin.id)}, headers=auth(token)
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["por_unidade"] == [{"rotulo": cofin.nome, "quantidade": 1}]


def test_distribuicoes_estado_vazio(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-dist-vazio@example.com")

    token = login(client, gestor.email)
    resp = client.get("/dashboard/distribuicoes", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["por_unidade"] == []
    assert corpo["por_tipo"] == []
    assert corpo["por_usuario"] == []


def test_gestor_consulta_distribuicoes_unidade_nao_gerida_recebe_acesso_negado_e_loga(client, db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin, email="gestor-dist-negado@example.com")

    token = login(client, gestor.email)
    resp = client.get(
        "/dashboard/distribuicoes", params={"unidade_id": str(dirad.id)}, headers=auth(token)
    )
    assert resp.status_code == 403

    log = (
        db.query(LogSeguranca)
        .filter(
            LogSeguranca.usuario_id == gestor.id,
            LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO,
        )
        .first()
    )
    assert log is not None


def test_nao_gestor_recebe_acesso_negado_nas_distribuicoes(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor-dist@example.com")
    token = login(client, servidor.email)

    resp = client.get("/dashboard/distribuicoes", headers=auth(token))
    assert resp.status_code == 403
