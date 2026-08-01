"""Testes do escopo pessoal do quadro do Servidor (change kanban-por-servidor,
task 2.6 — obrigatório: visibilidade de dados pessoais). US 1.4, US 2.3, US 2.8
(design D1/D2/D3)."""

from __future__ import annotations

from tests.helpers_processo import (
    auth,
    enviar_para,
    gestor_de,
    login,
    servidor_com_setor,
    tipo_processo,
    unidade,
    usuario,
)


def _criar_processo(client, token, tipo, assunto="Processo"):
    resp = client.post(
        "/processos",
        json={"assunto": assunto, "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_servidor_ve_processo_criado_detido_e_participante_historico(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, email="a@ex.com")
    token_a = login(client, "a@ex.com")

    # P1: A cria e continua com ele (servidor_atual == criador == A).
    p1 = _criar_processo(client, token_a, tipo, "P1 - com A")

    # P2: A cria, envia para B (AJUR) e B envia adiante para C (DIRAD) — B foi
    # detentor (nem criador, nem responsável atual), deve ver P2 pelo ramo
    # "já detive" do escopo pessoal (D1).
    p2 = _criar_processo(client, token_a, tipo, "P2 - passou por B")
    _resp, servidor_b, _setor_b = enviar_para(
        client, db, processo_id=p2["id"], token_origem=token_a, unidade_destino=ajur,
        email_destino="b@ex.com",
    )
    token_b = login(client, "b@ex.com")
    enviar_para(
        client, db, processo_id=p2["id"], token_origem=token_b, unidade_destino=dirad,
        email_destino="c@ex.com",
    )

    # A: continua vendo P1 (responsável atual + criador) e P2 (criador).
    resp_a = client.get("/processos", headers=auth(token_a))
    numeros_a = {item["numero"] for item in resp_a.json()["items"]}
    assert {p1["numero"], p2["numero"]} <= numeros_a
    card_p2_a = next(i for i in resp_a.json()["items"] if i["numero"] == p2["numero"])
    assert card_p2_a["acao_requerida"] is False  # A não é mais o responsável atual de P2.

    # B: já não é responsável nem criador de P2, mas já o deteve — aparece.
    resp_b = client.get("/processos", headers=auth(token_b))
    numeros_b = {item["numero"] for item in resp_b.json()["items"]}
    assert p2["numero"] in numeros_b
    card_p2_b = next(i for i in resp_b.json()["items"] if i["numero"] == p2["numero"])
    assert card_p2_b["acao_requerida"] is False


def test_processo_da_propria_unidade_nunca_tocado_nao_aparece(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, email="colega1@ex.com")
    token_1 = login(client, "colega1@ex.com")
    _criar_processo(client, token_1, tipo, "Processo do colega")

    servidor_com_setor(db, cofin, email="colega2@ex.com")
    token_2 = login(client, "colega2@ex.com")

    resp = client.get("/processos", headers=auth(token_2))
    assert resp.json()["total"] == 0


def test_gestor_que_apenas_reatribuiu_nao_e_tratado_como_detentor(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, nome_setor="SetorB", email="servB@ex.com")
    token_b = login(client, "servB@ex.com")
    proc = _criar_processo(client, token_b, tipo, "Processo reatribuído")

    servidor_c, setor_c = servidor_com_setor(db, cofin, nome_setor="SetorC", email="servC@ex.com")
    gestor_de(db, cofin, email="gestorReat@ex.com")
    token_gestor = login(client, "gestorReat@ex.com")

    resp_reat = client.post(
        f"/processos/{proc['id']}/reatribuir",
        json={
            "setor_destino_id": str(setor_c.id),
            "servidor_destino_id": str(servidor_c.id),
            "justificativa": "Atribuição indevida",
        },
        headers=auth(token_gestor),
    )
    assert resp_reat.status_code == 200, resp_reat.text

    # O Gestor vê o processo pelo escopo de unidades geridas — não por
    # participação pessoal (seu quadro nunca foi pessoal) — e não é tratado
    # como o responsável atual só por ter agido sobre o processo.
    resp = client.get("/processos", headers=auth(token_gestor))
    card = next(i for i in resp.json()["items"] if i["numero"] == proc["numero"])
    assert card["acao_requerida"] is False
    assert card["servidor_atual_nome"] == servidor_c.nome


def test_sigiloso_em_outra_unidade_ausente_mesmo_para_ex_detentor(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, email="exdet@ex.com")
    token_a = login(client, "exdet@ex.com")
    proc = _criar_processo(client, token_a, tipo, "Vira sigiloso na AJUR")

    _resp, _servidor_b, _setor_b = enviar_para(
        client, db, processo_id=proc["id"], token_origem=token_a, unidade_destino=ajur,
        email_destino="ajurdet@ex.com",
    )
    token_ajur = login(client, "ajurdet@ex.com")
    marcar = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_ajur))
    assert marcar.status_code == 200, marcar.text

    # A criou o processo (branch "criei") e o deteve (branch "já detive"),
    # mas ele está sigiloso fora da própria unidade — some do quadro (D3).
    resp = client.get("/processos", headers=auth(token_a))
    assert resp.json()["total"] == 0


def test_gestor_mantem_escopo_por_unidades_geridas(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, email="gcofin2@ex.com")
    _criar_processo(client, login(client, "gcofin2@ex.com"), tipo, "P COFIN")
    servidor_com_setor(db, ajur, email="gajur2@ex.com")
    _criar_processo(client, login(client, "gajur2@ex.com"), tipo, "P AJUR")
    servidor_com_setor(db, dirad, email="gdirad2@ex.com")
    _criar_processo(client, login(client, "gdirad2@ex.com"), tipo, "P DIRAD")

    gestor_de(db, cofin, ajur, email="gestorunidades@ex.com")
    token_gestor = login(client, "gestorunidades@ex.com")

    resp = client.get("/processos", headers=auth(token_gestor))
    assert resp.json()["total"] == 2
    unidades_vistas = {item["unidade_atual_id"] for item in resp.json()["items"]}
    assert unidades_vistas == {str(cofin.id), str(ajur.id)}


def test_servidor_de_outra_unidade_nao_ve_processo_por_nenhum_ramo_do_escopo(client, db):
    cofin, dirad = unidade(db, "COFIN"), unidade(db, "DIRAD")
    tipo = tipo_processo(db)

    servidor_com_setor(db, cofin, email="dono@ex.com")
    token_dono = login(client, "dono@ex.com")
    proc = _criar_processo(client, token_dono, tipo, "Processo alheio")

    usuario(db, unidade_id=dirad.id, email="estranho@ex.com")
    token_estranho = login(client, "estranho@ex.com")

    resp = client.get("/processos", headers=auth(token_estranho))
    assert resp.json()["total"] == 0

    detalhe = client.get(f"/processos/{proc['id']}", headers=auth(token_estranho))
    assert detalhe.status_code == 403
