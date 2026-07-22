"""Testes de visibilidade por unidade de origem (change
visibilidade-processos-origem, task 2.5 — obrigatório: histórico de
tramitação/dados pessoais). US 1.4 (revisada), US 2.3, US 2.7, US 2.8."""

from __future__ import annotations

from tests.helpers_processo import auth, gestor_de, login, tipo_com_roteiro, unidade, usuario


def _criar_processo(client, token, tipo, assunto="Origem"):
    resp = client.post(
        "/processos",
        json={"assunto": assunto, "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_processo_despachado_visivel_por_origem_como_somente_leitura(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="origem@ex.com")
    token_cofin = login(client, "origem@ex.com")
    proc = _criar_processo(client, token_cofin, tipo)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    resp = client.get("/processos", headers=auth(token_cofin))
    assert resp.status_code == 200
    itens = resp.json()["items"]
    assert len(itens) == 1
    assert itens[0]["unidade_atual_id"] == str(ajur.id)
    assert itens[0]["somente_leitura"] is True

    busca = client.get(f"/processos/busca?numero={proc['numero']}", headers=auth(token_cofin))
    assert busca.json()["items"][0]["somente_leitura"] is True


def test_sigiloso_fora_da_unidade_ausente_do_kanban_e_da_busca(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="sigorigem@ex.com")
    token_cofin = login(client, "sigorigem@ex.com")
    proc = _criar_processo(client, token_cofin, tipo, "Sigiloso")
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=ajur.id, email="destino@ex.com")
    token_ajur = login(client, "destino@ex.com")
    marcar = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_ajur))
    assert marcar.status_code == 200, marcar.text

    resp = client.get("/processos", headers=auth(token_cofin))
    assert resp.json()["total"] == 0

    busca = client.get(f"/processos/busca?numero={proc['numero']}", headers=auth(token_cofin))
    assert busca.json()["total"] == 0


def test_devolvido_verdadeiro_apos_devolucao_e_falso_apos_novo_despacho(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="devcofin@ex.com")
    token_cofin = login(client, "devcofin@ex.com")
    proc = _criar_processo(client, token_cofin, tipo)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=ajur.id, email="devajur@ex.com")
    token_ajur = login(client, "devajur@ex.com")
    dev = client.post(
        f"/processos/{proc['id']}/devolver",
        json={"motivo": "documentacao_insuficiente"},
        headers=auth(token_ajur),
    )
    assert dev.status_code == 200, dev.text

    resp = client.get("/processos", headers=auth(token_cofin))
    card = resp.json()["items"][0]
    assert card["devolvido"] is True
    assert card["somente_leitura"] is False

    # Novo despacho da COFIN — o destaque de devolução cessa (D3: derivado do
    # último evento, sem estado adicional); o processo volta a ser somente
    # leitura por origem para a COFIN.
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))
    resp2 = client.get("/processos", headers=auth(token_cofin))
    card2 = resp2.json()["items"][0]
    assert card2["devolvido"] is False
    assert card2["somente_leitura"] is True


def test_incluir_finalizados_filtra_status(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="fin@ex.com")
    token = login(client, "fin@ex.com")
    proc = _criar_processo(client, token, tipo)
    client.post(f"/processos/{proc['id']}/despachar", json={"confirmar": True}, headers=auth(token))

    resp_default = client.get("/processos", headers=auth(token))
    assert resp_default.json()["total"] == 0

    resp_incluir = client.get("/processos?incluir_finalizados=true", headers=auth(token))
    assert resp_incluir.json()["total"] == 1
    assert resp_incluir.json()["items"][0]["status"] == "concluido"


def test_gestor_ve_origem_das_unidades_geridas(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_com_roteiro(db, cofin, dirad)
    usuario(db, unidade_id=cofin.id, email="gcofin@ex.com")
    token_cofin = login(client, "gcofin@ex.com")
    proc = _criar_processo(client, token_cofin, tipo)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    gestor_de(db, cofin, ajur, email="gestorX@ex.com")
    token_gestor = login(client, "gestorX@ex.com")
    resp = client.get("/processos", headers=auth(token_gestor))
    assert resp.json()["total"] == 1
    card = resp.json()["items"][0]
    assert card["unidade_atual_id"] == str(dirad.id)
    assert card["somente_leitura"] is True


def test_servidor_de_terceira_unidade_nao_ve_processo_alheio(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="c3@ex.com")
    token_cofin = login(client, "c3@ex.com")
    proc = _criar_processo(client, token_cofin, tipo)
    client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token_cofin))

    usuario(db, unidade_id=dirad.id, email="d3@ex.com")
    token_dirad = login(client, "d3@ex.com")
    resp = client.get("/processos", headers=auth(token_dirad))
    assert resp.json()["total"] == 0

    busca = client.get(f"/processos/busca?numero={proc['numero']}", headers=auth(token_dirad))
    assert busca.json()["total"] == 0
