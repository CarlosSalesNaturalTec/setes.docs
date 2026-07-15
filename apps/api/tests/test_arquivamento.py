"""Idempotência/retomada do arquivamento automático contra Postgres real
(task 4.3/4.4 — obrigatório: histórico de tramitação e transição de estado).
US 2.5 Cen.1/3/4."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.models import PerfilUsuario, StatusProcesso, TipoEventoTramitacao, Tramitacao
from app.services.arquivamento import arquivar_vencidos
from tests.helpers_processo import auth, login, processo_concluido, tipo_com_roteiro, unidade, usuario

AGORA = datetime(2026, 7, 15, 3, 0, 0, tzinfo=timezone.utc)


def _base(db):
    cofin = unidade(db, "COFIN")
    criador = usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id)
    tipo = tipo_com_roteiro(db, cofin)
    return cofin, criador, tipo


def test_vencidos_sao_arquivados_e_geram_um_evento_cada(db):
    cofin, criador, tipo = _base(db)
    p1 = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=31), arquivar_em=AGORA - timedelta(days=1),
    )
    p2 = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=40), arquivar_em=AGORA - timedelta(days=10),
    )
    nao_vencido = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=1), arquivar_em=AGORA + timedelta(days=29),
    )

    total = arquivar_vencidos(db, agora=AGORA)

    assert total == 2
    for p in (p1, p2):
        db.refresh(p)
        assert p.status == StatusProcesso.ARQUIVADO
        eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == p.id).all()
        assert len(eventos) == 1
        assert eventos[0].tipo_evento == TipoEventoTramitacao.ARQUIVAMENTO_AUTOMATICO
        assert eventos[0].responsavel_id is None
        assert eventos[0].status_resultante == StatusProcesso.ARQUIVADO

    db.refresh(nao_vencido)
    assert nao_vencido.status == StatusProcesso.CONCLUIDO
    assert db.query(Tramitacao).filter(Tramitacao.processo_id == nao_vencido.id).count() == 0


def test_reexecucao_sobre_mesmo_estado_nao_duplica_efeito(db):
    cofin, criador, tipo = _base(db)
    p1 = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=31), arquivar_em=AGORA - timedelta(days=1),
    )

    n1 = arquivar_vencidos(db, agora=AGORA)
    n2 = arquivar_vencidos(db, agora=AGORA)  # reexecução sobre o mesmo estado

    assert n1 == 1
    assert n2 == 0
    assert db.query(Tramitacao).filter(Tramitacao.processo_id == p1.id).count() == 1


def test_retomada_apos_indisponibilidade_captura_tudo_que_venceu(db):
    cofin, criador, tipo = _base(db)
    processos = [
        processo_concluido(
            db, unidade=cofin, criador=criador, tipo=tipo,
            concluido_em=AGORA - timedelta(days=33), arquivar_em=AGORA - timedelta(days=3),
        ),
        processo_concluido(
            db, unidade=cofin, criador=criador, tipo=tipo,
            concluido_em=AGORA - timedelta(days=32), arquivar_em=AGORA - timedelta(days=2),
        ),
        processo_concluido(
            db, unidade=cofin, criador=criador, tipo=tipo,
            concluido_em=AGORA - timedelta(days=31), arquivar_em=AGORA - timedelta(days=1),
        ),
    ]

    total = arquivar_vencidos(db, agora=AGORA)

    assert total == 3
    for p in processos:
        db.refresh(p)
        assert p.status == StatusProcesso.ARQUIVADO
    assert db.query(Tramitacao).filter(
        Tramitacao.tipo_evento == TipoEventoTramitacao.ARQUIVAMENTO_AUTOMATICO
    ).count() == 3


def test_historico_http_serializa_responsavel_id_nulo_como_null(client, db):
    """Regressão: `EventoHistoricoResponse.responsavel_id` era `str` obrigatório
    e serializava o evento de sistema como a string "None" em vez de `null`."""
    cofin, criador, tipo = _base(db)
    p = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=31), arquivar_em=AGORA - timedelta(days=1),
    )
    arquivar_vencidos(db, agora=AGORA)

    token = login(client, criador.email)
    resp = client.get(f"/processos/{p.id}/historico", headers=auth(token))
    assert resp.status_code == 200
    evento = resp.json()["eventos"][0]
    assert evento["tipo_evento"] == "arquivamento_automatico"
    assert evento["responsavel_id"] is None


def test_evento_de_arquivamento_nao_altera_dados_de_interessados(db):
    """Histórico imutável (LGPD): o arquivamento só transiciona status e
    insere evento — não toca `processo_interessado`."""
    cofin, criador, tipo = _base(db)
    p = processo_concluido(
        db, unidade=cofin, criador=criador, tipo=tipo,
        concluido_em=AGORA - timedelta(days=31), arquivar_em=AGORA - timedelta(days=1),
    )

    arquivar_vencidos(db, agora=AGORA)

    db.refresh(p)
    assert p.status == StatusProcesso.ARQUIVADO
    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == p.id).all()
    assert len(eventos) == 1
    assert eventos[0].unidade_origem_id is None
    assert eventos[0].unidade_destino_id is None
    assert eventos[0].justificativa is None
    assert eventos[0].motivo is None
