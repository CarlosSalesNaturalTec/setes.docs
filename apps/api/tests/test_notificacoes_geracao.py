"""Testes de geração de notificação interna nos eventos de despacho/conclusão
(task 2.5, Épico 5 — obrigatório: histórico de tramitação). US 5.1, 5.3."""

from __future__ import annotations

from app.db.models import Notificacao, TipoNotificacao
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario

ASSUNTO = "Licitação de equipamentos"


def _criar_processo(client, db, tipo, unidade_criacao):
    serv = usuario(db, unidade_id=unidade_criacao.id, email=f"criador-{unidade_criacao.sigla}@ex.com")
    token = login(client, serv.email)
    resp = client.post(
        "/processos",
        json={"assunto": ASSUNTO, "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json(), serv, token


def test_despacho_gera_notificacao_para_cada_servidor_do_destino(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    serv_ajur_1 = usuario(db, unidade_id=ajur.id, email="ajur1@ex.com")
    serv_ajur_2 = usuario(db, unidade_id=ajur.id, email="ajur2@ex.com")

    resp = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert resp.status_code == 200, resp.text

    notificacoes = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"],
            Notificacao.tipo == TipoNotificacao.NOVO_PROCESSO,
        )
        .all()
    )
    assert {n.usuario_id for n in notificacoes} == {serv_ajur_1.id, serv_ajur_2.id}
    for n in notificacoes:
        assert n.lida_em is None
        assert n.unidade_id == ajur.id
        assert n.unidade_origem_id == cofin.id
        assert n.numero_processo == proc["numero"]
        assert n.assunto == ASSUNTO


def test_conclusao_gera_notificacao_para_servidores_da_unidade_de_conclusao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)  # roteiro de unidade única
    proc, serv_criador, token = _criar_processo(client, db, tipo, cofin)
    outro_servidor_cofin = usuario(db, unidade_id=cofin.id, email="outro-cofin@ex.com")

    resp = client.post(
        f"/processos/{proc['id']}/despachar", json={"confirmar": True}, headers=auth(token)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "concluido"

    notificacoes = (
        db.query(Notificacao)
        .filter(
            Notificacao.processo_id == proc["id"], Notificacao.tipo == TipoNotificacao.CONCLUIDO
        )
        .all()
    )
    assert {n.usuario_id for n in notificacoes} == {serv_criador.id, outro_servidor_cofin.id}
    for n in notificacoes:
        assert n.lida_em is None
        assert n.unidade_id == cofin.id
        assert n.unidade_origem_id is None


def test_despacho_para_unidade_sem_servidores_nao_gera_notificacao(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    resp = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert resp.status_code == 200, resp.text

    assert db.query(Notificacao).filter(Notificacao.processo_id == proc["id"]).count() == 0
