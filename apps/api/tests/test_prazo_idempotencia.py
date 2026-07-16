"""Idempotência/retomada da rotina diária de prazo e do expurgo de notificações
(task 5.4 — obrigatório: rotina automática + histórico). US 5.2 Cen.2, US 5.4,
US 5.1 Cen.4/4b."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import Notificacao, StatusProcesso, TipoNotificacao
from app.services.notificacao import expurgar_notificacoes_lidas
from app.services.prazo import verificar_prazos
from tests.helpers_processo import processo_ativo, tipo_com_roteiro, unidade, usuario

AGORA = datetime(2026, 7, 16, 3, 0, 0, tzinfo=timezone.utc)
HOJE = AGORA.date()


def _base(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)
    return cofin, criador, tipo


def test_gera_alerta_para_processo_dentro_da_janela_padrao(db, settings):
    cofin, criador, tipo = _base(db)
    servidor2 = usuario(db, unidade_id=cofin.id, email="serv2@ex.com")
    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=1))

    total = verificar_prazos(db, agora=AGORA, settings=settings)

    assert total == 2  # criador + servidor2, ambos servidores da unidade
    notifs = db.query(Notificacao).filter(Notificacao.processo_id == proc.id).all()
    assert {n.usuario_id for n in notifs} == {criador.id, servidor2.id}
    for n in notifs:
        assert n.tipo == TipoNotificacao.ALERTA_PRAZO
        assert n.prazo_referencia == proc.prazo_em
        assert n.unidade_id == cofin.id
        assert n.lida_em is None


def test_processo_fora_da_janela_nao_gera_alerta(db, settings):
    cofin, criador, tipo = _base(db)
    proc = processo_ativo(
        db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=10)
    )

    total = verificar_prazos(db, agora=AGORA, settings=settings)

    assert total == 0
    assert db.query(Notificacao).filter(Notificacao.processo_id == proc.id).count() == 0


def test_processo_concluido_nao_gera_alerta(db, settings):
    cofin, criador, tipo = _base(db)
    proc = processo_ativo(
        db,
        unidade=cofin,
        criador=criador,
        tipo=tipo,
        prazo_em=HOJE + timedelta(days=1),
        status=StatusProcesso.CONCLUIDO,
    )

    total = verificar_prazos(db, agora=AGORA, settings=settings)

    assert total == 0
    assert db.query(Notificacao).filter(Notificacao.processo_id == proc.id).count() == 0


def test_reexecucao_sobre_mesmo_estado_nao_duplica(db, settings):
    cofin, criador, tipo = _base(db)
    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=1))

    n1 = verificar_prazos(db, agora=AGORA, settings=settings)
    n2 = verificar_prazos(db, agora=AGORA, settings=settings)  # reexecução sobre o mesmo estado

    assert n1 == 1
    assert n2 == 0
    assert db.query(Notificacao).filter(Notificacao.processo_id == proc.id).count() == 1


def test_retomada_apos_indisponibilidade_cobre_a_janela(db, settings):
    cofin, criador, tipo = _base(db)
    procs = [
        processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE - timedelta(days=1)),
        processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE),
        processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=2)),
    ]

    total = verificar_prazos(db, agora=AGORA, settings=settings)

    assert total == len(procs)  # um servidor (criador) por processo
    assert db.query(Notificacao).filter(
        Notificacao.tipo == TipoNotificacao.ALERTA_PRAZO
    ).count() == len(procs)


def test_mudanca_do_prazo_vigente_permite_novo_ciclo_de_alerta(db, settings):
    """D3 — o guard é por `prazo_referencia`; se `prazo_em` mudar, um novo alerta é válido."""
    cofin, criador, tipo = _base(db)
    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=1))

    total1 = verificar_prazos(db, agora=AGORA, settings=settings)
    assert total1 == 1

    proc.prazo_em = HOJE + timedelta(days=2)
    db.commit()

    total2 = verificar_prazos(db, agora=AGORA, settings=settings)
    assert total2 == 1
    assert db.query(Notificacao).filter(Notificacao.processo_id == proc.id).count() == 2


def test_janela_configurada_pelo_admin_e_respeitada(db, settings):
    from app.db.models import SistemaConfig

    cofin, criador, tipo = _base(db)
    config = db.get(SistemaConfig, 1)
    config.dias_antecedencia_alerta_prazo = 5
    db.commit()

    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE + timedelta(days=5))

    total = verificar_prazos(db, agora=AGORA, settings=settings)

    assert total == 1
    assert db.query(Notificacao).filter(Notificacao.processo_id == proc.id).count() == 1


def _notificacao_lida(db, *, usuario_id, processo_id, unidade_id, lida_em):
    n = Notificacao(
        usuario_id=usuario_id,
        processo_id=processo_id,
        unidade_id=unidade_id,
        unidade_nome="COFIN",
        tipo=TipoNotificacao.NOVO_PROCESSO,
        numero_processo="2026/000001",
        assunto="Processo de teste",
        lida_em=lida_em,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def test_expurgo_remove_lidas_ha_mais_de_30_dias_preserva_nao_lidas(db):
    cofin, criador, _tipo = _base(db)
    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=_tipo, prazo_em=HOJE)

    lida_antiga = _notificacao_lida(
        db, usuario_id=criador.id, processo_id=proc.id, unidade_id=cofin.id,
        lida_em=AGORA - timedelta(days=31),
    )
    lida_recente = _notificacao_lida(
        db, usuario_id=criador.id, processo_id=proc.id, unidade_id=cofin.id,
        lida_em=AGORA - timedelta(days=5),
    )
    nao_lida_antiga = _notificacao_lida(
        db, usuario_id=criador.id, processo_id=proc.id, unidade_id=cofin.id, lida_em=None
    )
    nao_lida_antiga.criado_em = AGORA - timedelta(days=45)
    db.commit()

    total = expurgar_notificacoes_lidas(db, agora=AGORA)

    assert total == 1
    restantes = {n.id for n in db.query(Notificacao).filter(Notificacao.processo_id == proc.id).all()}
    assert lida_antiga.id not in restantes
    assert lida_recente.id in restantes
    assert nao_lida_antiga.id in restantes


def test_expurgo_reexecucao_sobre_mesmo_estado_nao_remove_de_novo(db):
    cofin, criador, tipo = _base(db)
    proc = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=HOJE)
    _notificacao_lida(
        db, usuario_id=criador.id, processo_id=proc.id, unidade_id=cofin.id,
        lida_em=AGORA - timedelta(days=31),
    )

    n1 = expurgar_notificacoes_lidas(db, agora=AGORA)
    n2 = expurgar_notificacoes_lidas(db, agora=AGORA)

    assert n1 == 1
    assert n2 == 0
