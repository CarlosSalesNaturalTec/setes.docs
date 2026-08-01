"""Testes dos cards de contagem por status do dashboard (change
kanban-por-servidor, task 4.3 — obrigatório: acesso negado). US 6.1 (design D8)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.db.models import LogSeguranca, PerfilUsuario, StatusProcesso, TipoEventoLog
from tests.helpers_processo import (
    auth,
    gestor_de,
    login,
    processo_ativo,
    processo_concluido,
    servidor_com_setor,
    tipo_processo,
    unidade,
    usuario,
)


def test_contagens_refletem_distribuicao_por_status(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-contagem@example.com")
    criador, _setor = servidor_com_setor(db, cofin, email="criador-contagem@example.com")
    tipo = tipo_processo(db)
    hoje = date.today()

    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=5),
                    status=StatusProcesso.ABERTO)
    for _ in range(2):
        processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=5),
                        status=StatusProcesso.EM_TRAMITACAO)
    processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=datetime.utcnow(), arquivar_em=datetime.utcnow() + timedelta(days=30),
    )
    for _ in range(3):
        processo_concluido(
            db, unidade=cofin, criador=criador, tipo=tipo,
            concluido_em=datetime.utcnow(), arquivar_em=datetime.utcnow() + timedelta(days=30),
            status=StatusProcesso.ARQUIVADO,
        )

    token = login(client, gestor.email)
    resp = client.get("/dashboard/contagens", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["abertos"] == 1
    assert corpo["em_tramitacao"] == 2
    assert corpo["concluidos"] == 1
    assert corpo["arquivados"] == 3
    assert corpo["total"] == 7


def test_total_e_sempre_a_soma_das_parcelas(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-soma@example.com")
    criador, _setor = servidor_com_setor(db, cofin, email="criador-soma@example.com")
    tipo = tipo_processo(db)
    hoje = date.today()

    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=5))
    processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=datetime.utcnow(), arquivar_em=datetime.utcnow() + timedelta(days=30),
        status=StatusProcesso.ARQUIVADO,
    )

    token = login(client, gestor.email)
    corpo = client.get("/dashboard/contagens", headers=auth(token)).json()
    soma = corpo["abertos"] + corpo["em_tramitacao"] + corpo["concluidos"] + corpo["arquivados"]
    assert corpo["total"] == soma


def test_escopo_vazio_zera_os_cards(client, db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin, email="gestor-zero@example.com")

    token = login(client, gestor.email)
    resp = client.get("/dashboard/contagens", headers=auth(token))
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo == {"total": 0, "abertos": 0, "em_tramitacao": 0, "concluidos": 0, "arquivados": 0}


def test_contagens_restritas_as_unidades_geridas(client, db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin, email="gestor-restrito@example.com")
    criador_cofin, _s1 = servidor_com_setor(db, cofin, email="criador-restrito-cofin@example.com")
    criador_dirad, _s2 = servidor_com_setor(db, dirad, email="criador-restrito-dirad@example.com")
    tipo = tipo_processo(db)
    hoje = date.today()

    processo_ativo(db, unidade=cofin, criador=criador_cofin, tipo=tipo, prazo_em=hoje + timedelta(days=5))
    processo_ativo(db, unidade=dirad, criador=criador_dirad, tipo=tipo, prazo_em=hoje + timedelta(days=5))

    token = login(client, gestor.email)
    resp = client.get("/dashboard/contagens", headers=auth(token))
    assert resp.json()["total"] == 1


def test_gestor_nao_obtem_contagens_de_unidade_nao_gerida(client, db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin, email="gestor-negado-contagem@example.com")

    token = login(client, gestor.email)
    resp = client.get(
        "/dashboard/contagens", params={"unidade_id": str(dirad.id)}, headers=auth(token)
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


def test_servidor_nao_acessa_contagens(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor-contagem@example.com")
    token = login(client, servidor.email)

    resp = client.get("/dashboard/contagens", headers=auth(token))
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
