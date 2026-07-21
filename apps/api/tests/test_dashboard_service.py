"""Testes do service de agregação do dashboard (task 3.3, US 6.1)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.db.models import SistemaConfig, StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services import dashboard as dashboard_service
from tests.helpers_processo import (
    gestor_de,
    processo_ativo,
    processo_concluido,
    tipo_com_roteiro,
    unidade,
    usuario,
)


def _tramitacao(db, *, processo, responsavel, criado_em):
    evento = Tramitacao(
        processo_id=processo.id,
        tipo_evento=TipoEventoTramitacao.DESPACHO,
        unidade_origem_id=processo.unidade_atual_id,
        unidade_destino_id=processo.unidade_atual_id,
        responsavel_id=responsavel.id,
        status_resultante=processo.status,
        criado_em=criado_em,
    )
    db.add(evento)
    db.commit()
    return evento


def test_escopo_exclui_unidade_nao_gerida(db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo_cofin = tipo_com_roteiro(db, cofin)
    tipo_ajur = tipo_com_roteiro(db, ajur)

    hoje = date.today()
    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo_cofin, prazo_em=hoje + timedelta(days=10))
    processo_ativo(db, unidade=ajur, criador=criador, tipo=tipo_ajur, prazo_em=hoje + timedelta(days=10))

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    assert unidades == [cofin.id]
    assert dashboard_service.total_ativos(db, unidades) == 1


def test_unidade_id_fora_do_escopo_levanta_escopo_negado(db):
    cofin = unidade(db, "COFIN")
    dirad = unidade(db, "DIRAD")
    gestor = gestor_de(db, cofin)

    with pytest.raises(dashboard_service.EscopoNegado):
        dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=dirad.id)


def test_unidade_id_dentro_do_escopo_restringe_a_uma_unidade(db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    gestor = gestor_de(db, cofin, ajur)

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=cofin.id)
    assert unidades == [cofin.id]


def test_tempo_medio_considera_apenas_concluidos_ultimos_12_meses(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    agora = datetime.now(timezone.utc)
    dentro = processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=agora - timedelta(days=30),
        arquivar_em=agora,
    )
    dentro.criado_em = agora - timedelta(days=40)
    db.commit()

    fora = processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=agora - timedelta(days=400),
        arquivar_em=agora,
    )
    fora.criado_em = agora - timedelta(days=430)
    db.commit()

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    media = dashboard_service.tempo_medio_tramitacao_dias(db, unidades, hoje=date.today())
    assert media == 10.0


def test_parados_usa_limiar_do_config_e_criado_em_sem_tramitacao(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    hoje = date.today()
    agora = datetime.now(timezone.utc)

    parado_com_tramitacao = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10)
    )
    _tramitacao(db, processo=parado_com_tramitacao, responsavel=criador, criado_em=agora - timedelta(days=10))

    ativo_recente = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10)
    )
    _tramitacao(db, processo=ativo_recente, responsavel=criador, criado_em=agora - timedelta(days=3))

    parado_sem_tramitacao = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10)
    )
    parado_sem_tramitacao.criado_em = agora - timedelta(days=15)
    db.commit()

    config = db.get(SistemaConfig, 1)
    config.dias_para_processo_parado = 7
    db.commit()

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    limiar = dashboard_service.dias_para_processo_parado(db)
    parados = dashboard_service.listar_parados(db, unidades, dias_limiar=limiar, hoje=hoje)

    ids = {p.id for p, _ in parados}
    assert ids == {parado_com_tramitacao.id, parado_sem_tramitacao.id}
    assert dashboard_service.total_parados(db, unidades, dias_limiar=limiar, hoje=hoje) == 2


def test_produtividade_conta_apenas_mes_corrente(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    dentro_dt = datetime.combine(inicio_mes, datetime.min.time(), tzinfo=timezone.utc)
    fora_dt = dentro_dt - timedelta(days=1)  # último instante do mês anterior

    processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo, concluido_em=dentro_dt, arquivar_em=dentro_dt
    )
    processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo, concluido_em=fora_dt, arquivar_em=fora_dt
    )

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    produtividade = dashboard_service.produtividade_por_unidade(db, unidades, hoje=hoje)

    assert len(produtividade) == 1
    unidade_resultado, quantidade = produtividade[0]
    assert unidade_resultado.id == cofin.id
    assert quantidade == 1


def test_prazos_em_risco_vencido_e_a_vencer(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)
    hoje = date.today()

    vencido = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje - timedelta(days=1))
    a_vencer = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=1))
    fora_da_janela = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=30)
    )

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    itens = dashboard_service.prazos_em_risco(db, unidades, dias_antecedencia=2, hoje=hoje)

    ids = {p.id for p in itens}
    assert ids == {vencido.id, a_vencer.id}
    assert fora_da_janela.id not in ids


def test_estado_vazio_gestor_sem_processos(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    hoje = date.today()

    assert dashboard_service.total_ativos(db, unidades) == 0
    assert dashboard_service.tempo_medio_tramitacao_dias(db, unidades, hoje=hoje) is None
    assert dashboard_service.listar_parados(db, unidades, dias_limiar=7, hoje=hoje) == []
    assert dashboard_service.produtividade_por_unidade(db, unidades, hoje=hoje) == []
    assert dashboard_service.prazos_em_risco(db, unidades, dias_antecedencia=2, hoje=hoje) == []


def test_distribuicoes_contam_apenas_ativos(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)
    hoje = date.today()

    for _ in range(5):
        processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10))
    processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=datetime.now(timezone.utc),
        arquivar_em=datetime.now(timezone.utc),
    )
    processo_concluido(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        concluido_em=datetime.now(timezone.utc),
        arquivar_em=datetime.now(timezone.utc),
        status=StatusProcesso.ARQUIVADO,
    )

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)

    por_unidade = dashboard_service.distribuicao_por_unidade(db, unidades)
    assert por_unidade == [(cofin.nome, 5)]

    por_tipo = dashboard_service.distribuicao_por_tipo(db, unidades)
    assert por_tipo == [(tipo.nome, 5)]

    por_usuario = dashboard_service.distribuicao_por_usuario(db, unidades)
    assert por_usuario == [(criador.nome, 5)]


def test_distribuicao_conta_sigiloso(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)
    hoje = date.today()

    processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10))
    sigiloso = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=hoje + timedelta(days=10))
    sigiloso.sigiloso = True
    db.commit()

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    por_unidade = dashboard_service.distribuicao_por_unidade(db, unidades)
    assert por_unidade == [(cofin.nome, 2)]


def test_distribuicao_por_usuario_agrupa_por_autor_e_ordena_desc(db):
    cofin = unidade(db, "COFIN")
    gestor = gestor_de(db, cofin)
    ricardo = usuario(db, unidade_id=cofin.id, email="ricardo@example.com")
    ricardo.nome = "Ricardo Pita"
    ana = usuario(db, unidade_id=cofin.id, email="ana@example.com")
    ana.nome = "Ana Souza"
    db.commit()
    tipo = tipo_com_roteiro(db, cofin)
    hoje = date.today()

    for _ in range(5):
        processo_ativo(db, unidade=cofin, criador=ricardo, tipo=tipo, prazo_em=hoje + timedelta(days=10))
    for _ in range(2):
        processo_ativo(db, unidade=cofin, criador=ana, tipo=tipo, prazo_em=hoje + timedelta(days=10))

    unidades = dashboard_service.resolver_escopo_gestor(db, gestor=gestor, unidade_id=None)
    por_usuario = dashboard_service.distribuicao_por_usuario(db, unidades)
    assert por_usuario == [("Ricardo Pita", 5), ("Ana Souza", 2)]


def test_distribuicoes_vazias_quando_sem_unidades(db):
    assert dashboard_service.distribuicao_por_unidade(db, []) == []
    assert dashboard_service.distribuicao_por_tipo(db, []) == []
    assert dashboard_service.distribuicao_por_usuario(db, []) == []
