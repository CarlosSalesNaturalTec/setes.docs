"""Testes do histórico de tramitação (task 5.2 — obrigatório: histórico). US 2.4."""

from __future__ import annotations

from tests.helpers_processo import auth, login, servidor_com_setor, setor, tipo_processo, unidade, usuario


def _criar(client, db, tipo, u, email):
    serv, _setor = servidor_com_setor(db, u, email=email)
    token = login(client, email)
    proc = client.post(
        "/processos",
        json={"assunto": "H", "tipo_processo_id": str(tipo.id), "prazo_dias": 7},
        headers=auth(token),
    ).json()
    return proc, token


def test_historico_vazio_de_processo_recem_criado(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    proc, token = _criar(client, db, tipo, cofin, "h1@ex.com")

    resp = client.get(f"/processos/{proc['id']}/historico", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["eventos"] == []
    assert body["mensagem_vazio"] == "Nenhuma movimentação registrada"
    assert body["criado_em"] is not None


def test_historico_em_ordem_cronologica(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)
    proc, token_cofin = _criar(client, db, tipo, cofin, "h2@ex.com")

    setor_ajur = setor(db, ajur, "Análise")
    serv_ajur = usuario(db, unidade_id=ajur.id, setor_id=setor_ajur.id, email="h2ajur@ex.com")
    client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(ajur.id),
            "setor_destino_id": str(setor_ajur.id),
            "servidor_destino_id": str(serv_ajur.id),
        },
        headers=auth(token_cofin),
    )

    setor_dirad = setor(db, dirad, "Julgamento")
    serv_dirad = usuario(db, unidade_id=dirad.id, setor_id=setor_dirad.id, email="h2dirad@ex.com")
    token_ajur = login(client, "h2ajur@ex.com")
    client.post(
        f"/processos/{proc['id']}/enviar",
        json={
            "unidade_destino_id": str(dirad.id),
            "setor_destino_id": str(setor_dirad.id),
            "servidor_destino_id": str(serv_dirad.id),
        },
        headers=auth(token_ajur),
    )

    # O processo agora está na DIRAD — só um Servidor da DIRAD tem acesso ao detalhe.
    token_dirad = login(client, "h2dirad@ex.com")
    resp = client.get(f"/processos/{proc['id']}/historico", headers=auth(token_dirad))
    eventos = resp.json()["eventos"]
    assert len(eventos) == 2
    datas = [e["criado_em"] for e in eventos]
    assert datas == sorted(datas)
    assert eventos[0]["unidade_origem_id"] == str(cofin.id)
    assert eventos[0]["unidade_destino_id"] == str(ajur.id)
