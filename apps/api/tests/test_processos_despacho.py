"""Testes de despacho e devolução (task 4.4 — obrigatório: histórico de
tramitação). US 2.2, 2.2b, US 1.4 Cen.2."""

from __future__ import annotations

from app.db.models import (
    LogSeguranca,
    Processo,
    StatusProcesso,
    TipoEventoLog,
    TipoEventoTramitacao,
    Tramitacao,
)
from tests.helpers_processo import (
    auth,
    login,
    tipo_com_roteiro,
    unidade,
    usuario,
)


def _criar_processo(client, db, tipo, unidade_criacao):
    serv = usuario(db, unidade_id=unidade_criacao.id, email=f"criador-{unidade_criacao.sigla}@ex.com")
    token = login(client, serv.email)
    resp = client.post(
        "/processos",
        json={"assunto": "Fluxo", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json(), serv, token


def test_despacho_move_para_proxima_unidade(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    resp = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "em_tramitacao"
    assert body["unidade_atual_id"] == str(ajur.id)

    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).all()
    assert len(eventos) == 1
    assert eventos[0].tipo_evento == TipoEventoTramitacao.DESPACHO
    assert eventos[0].unidade_origem_id == cofin.id
    assert eventos[0].unidade_destino_id == ajur.id


def test_ultima_etapa_pede_confirmacao_e_conclui(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token_cofin = _criar_processo(client, db, tipo, cofin)

    # COFIN despacha para AJUR.
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    # Agora um Servidor de AJUR opera. Na última etapa: sem confirmar → 409.
    usuario(db, unidade_id=ajur.id, email="ajur@ex.com")
    token_ajur = login(client, "ajur@ex.com")
    r409 = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_ajur))
    assert r409.status_code == 409
    assert "destino final do roteiro" in r409.json()["detail"]

    # Confirmando, conclui.
    r_ok = client.post(
        f"/processos/{proc['id']}/despachar", json={"confirmar": True}, headers=auth(token_ajur)
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "concluido"
    processo = db.get(Processo, proc["id"])
    assert processo.concluido_em is not None
    eventos = db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).all()
    assert {e.tipo_evento for e in eventos} == {
        TipoEventoTramitacao.DESPACHO,
        TipoEventoTramitacao.CONCLUSAO,
    }


def test_cancelamento_da_conclusao_nao_altera_historico(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)  # roteiro de unidade única
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    # Não confirmar → 409, nada gravado.
    r409 = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert r409.status_code == 409
    assert db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).count() == 0
    processo = db.get(Processo, proc["id"])
    assert processo.status == StatusProcesso.ABERTO


def test_roteiro_de_unidade_unica_conclui_com_mensagem_propria(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    r409 = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert r409.status_code == 409
    assert "unidade de origem e destino final" in r409.json()["detail"]

    r_ok = client.post(
        f"/processos/{proc['id']}/despachar", json={"confirmar": True}, headers=auth(token)
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "concluido"


def test_devolucao_para_unidade_anterior(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token_cofin = _criar_processo(client, db, tipo, cofin)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=ajur.id, email="ajur2@ex.com")
    token_ajur = login(client, "ajur2@ex.com")
    resp = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "documentacao_insuficiente", "justificativa": "Faltam anexos"},
        headers=auth(token_ajur),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["unidade_atual_id"] == str(cofin.id)
    assert resp.json()["status"] == "em_tramitacao"
    evento = (
        db.query(Tramitacao)
        .filter(Tramitacao.tipo_evento == TipoEventoTramitacao.DEVOLUCAO)
        .one()
    )
    assert evento.unidade_destino_id == cofin.id
    assert evento.justificativa == "Faltam anexos"


def test_devolucao_bloqueada_na_primeira_unidade(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token = _criar_processo(client, db, tipo, cofin)

    resp = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "correcao_dados"},
        headers=auth(token),
    )
    assert resp.status_code == 409
    assert "unidade de origem do roteiro" in resp.json()["detail"]


def test_devolucao_sem_motivo_e_rejeitada(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, token_cofin = _criar_processo(client, db, tipo, cofin)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=ajur.id, email="ajur3@ex.com")
    token_ajur = login(client, "ajur3@ex.com")
    resp = client.post(
        f"/processos/{proc['id']}/devolver", json={}, headers=auth(token_ajur)
    )
    assert resp.status_code == 422
    assert "Selecione um motivo para a devolução" in resp.text


def test_servidor_de_outra_unidade_nao_despacha_e_loga(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    proc, _serv, _token = _criar_processo(client, db, tipo, cofin)

    # Servidor de AJUR tenta despachar processo que está na COFIN.
    usuario(db, unidade_id=ajur.id, email="intruso@ex.com")
    token_intruso = login(client, "intruso@ex.com")
    resp = client.post(
        f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_intruso)
    )
    assert resp.status_code == 403
    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO)
        .all()
    )
    assert len(logs) >= 1


def test_historico_e_append_only_apos_multiplas_transicoes(client, db):
    """Imutabilidade: cada transição é um novo INSERT; eventos anteriores não mudam."""
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_com_roteiro(db, cofin, ajur, dirad)
    proc, _serv, token_cofin = _criar_processo(client, db, tipo, cofin)

    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))
    primeiro = db.query(Tramitacao).filter(Tramitacao.processo_id == proc["id"]).one()
    id_primeiro, criado_primeiro = primeiro.id, primeiro.criado_em

    usuario(db, unidade_id=ajur.id, email="ajur4@ex.com")
    token_ajur = login(client, "ajur4@ex.com")
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_ajur))

    eventos = (
        db.query(Tramitacao)
        .filter(Tramitacao.processo_id == proc["id"])
        .order_by(Tramitacao.criado_em)
        .all()
    )
    assert len(eventos) == 2
    # O primeiro evento permanece inalterado.
    assert eventos[0].id == id_primeiro
    assert eventos[0].criado_em == criado_primeiro
