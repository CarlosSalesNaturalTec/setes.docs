"""Testes de GET/POST /notificacoes (task 3.4). US 5.1 Cen.2/3/4/4b, acesso negado."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.db.models import LogSeguranca, Notificacao, TipoEventoLog, TipoNotificacao
from tests.helpers_processo import auth, login, servidor_com_setor, tipo_processo, unidade, usuario


def _processo_qualquer(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"criador-{uuid.uuid4().hex[:6]}@ex.com")
    token = login(client, criador.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Processo de teste", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"], cofin


def _notificacao(db, *, usuario_id, processo_id, unidade_id, lida_em=None, criado_em=None):
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
    if criado_em is not None:
        n.criado_em = criado_em
        db.commit()
    db.refresh(n)
    return n


def test_contador_nao_zera_ao_listar(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    servidor = usuario(db, unidade_id=cofin.id, email="dest@ex.com")
    for _ in range(3):
        _notificacao(db, usuario_id=servidor.id, processo_id=processo_id, unidade_id=cofin.id)

    token = login(client, servidor.email)
    resp_lista = client.get("/notificacoes", headers=auth(token))
    assert resp_lista.status_code == 200, resp_lista.text
    assert len(resp_lista.json()["items"]) == 3

    resp_contador = client.get("/notificacoes/contador", headers=auth(token))
    assert resp_contador.status_code == 200
    assert resp_contador.json()["nao_lidas"] == 3


def test_marcar_uma_decrementa_o_contador(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    servidor = usuario(db, unidade_id=cofin.id, email="dest2@ex.com")
    notifs = [
        _notificacao(db, usuario_id=servidor.id, processo_id=processo_id, unidade_id=cofin.id)
        for _ in range(3)
    ]
    token = login(client, servidor.email)

    resp = client.post(f"/notificacoes/{notifs[0].id}/ler", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["lida_em"] is not None

    resp_contador = client.get("/notificacoes/contador", headers=auth(token))
    assert resp_contador.json()["nao_lidas"] == 2


def test_marcar_todas_zera_o_contador(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    servidor = usuario(db, unidade_id=cofin.id, email="dest3@ex.com")
    for _ in range(3):
        _notificacao(db, usuario_id=servidor.id, processo_id=processo_id, unidade_id=cofin.id)
    token = login(client, servidor.email)

    resp = client.post("/notificacoes/marcar-todas-lidas", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["marcadas"] == 3

    resp_contador = client.get("/notificacoes/contador", headers=auth(token))
    assert resp_contador.json()["nao_lidas"] == 0


def test_acesso_negado_ao_ler_notificacao_de_outro_usuario(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    dono = usuario(db, unidade_id=cofin.id, email="dono@ex.com")
    intruso = usuario(db, unidade_id=cofin.id, email="intruso-notif@ex.com")
    notif = _notificacao(db, usuario_id=dono.id, processo_id=processo_id, unidade_id=cofin.id)

    token_intruso = login(client, intruso.email)
    resp = client.post(f"/notificacoes/{notif.id}/ler", headers=auth(token_intruso))
    assert resp.status_code == 403

    db.refresh(notif)
    assert notif.lida_em is None

    log = (
        db.query(LogSeguranca)
        .filter(
            LogSeguranca.usuario_id == intruso.id,
            LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO,
        )
        .first()
    )
    assert log is not None


def test_notificacao_lida_ha_mais_de_30_dias_nao_aparece_na_lista(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    servidor = usuario(db, unidade_id=cofin.id, email="dest4@ex.com")
    antiga = _notificacao(
        db,
        usuario_id=servidor.id,
        processo_id=processo_id,
        unidade_id=cofin.id,
        lida_em=datetime.now(timezone.utc) - timedelta(days=31),
    )
    recente = _notificacao(
        db,
        usuario_id=servidor.id,
        processo_id=processo_id,
        unidade_id=cofin.id,
        lida_em=datetime.now(timezone.utc) - timedelta(days=5),
    )

    token = login(client, servidor.email)
    resp = client.get("/notificacoes", headers=auth(token))
    ids = {item["id"] for item in resp.json()["items"]}
    assert str(antiga.id) not in ids
    assert str(recente.id) in ids


def test_notificacao_nao_lida_antiga_permanece_visivel(client, db):
    processo_id, cofin = _processo_qualquer(client, db)
    servidor = usuario(db, unidade_id=cofin.id, email="dest5@ex.com")
    antiga_nao_lida = _notificacao(
        db,
        usuario_id=servidor.id,
        processo_id=processo_id,
        unidade_id=cofin.id,
        criado_em=datetime.now(timezone.utc) - timedelta(days=45),
    )

    token = login(client, servidor.email)
    resp = client.get("/notificacoes", headers=auth(token))
    ids = {item["id"] for item in resp.json()["items"]}
    assert str(antiga_nao_lida.id) in ids

    resp_contador = client.get("/notificacoes/contador", headers=auth(token))
    assert resp_contador.json()["nao_lidas"] == 1
