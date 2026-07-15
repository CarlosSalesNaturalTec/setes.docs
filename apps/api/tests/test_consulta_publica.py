"""Testes da Consulta Pública (Épico 7, US 7.1/7.2) — tasks 4.1 a 4.7.

Cobre LGPD (ausência de CPF/CNPJ e de nome de servidor) e sigilo
(indistinguibilidade de processo sigiloso e número inexistente), obrigatórios
por invariante de domínio, além de paginação e rate limiting.
"""

from __future__ import annotations

from datetime import date

from tests.helpers_processo import (
    CNPJ_VALIDO,
    auth,
    login,
    tipo_com_roteiro,
    unidade,
    usuario,
)

MSG_NAO_ENCONTRADO = "Nenhum processo encontrado com o número informado"
MSG_PESQUISA_VAZIA = "Nenhum processo encontrado para os filtros informados"


def _criar_processo(client, token, tipo, *, assunto="Assunto de teste", interessados=None):
    resp = client.post(
        "/processos",
        json={
            "assunto": assunto,
            "tipo_processo_id": str(tipo.id),
            "prazo_dias": 10,
            "interessados": interessados or [],
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_consulta_por_numero_de_processo_nao_sigiloso(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="serv1@ex.com")
    token = login(client, "serv1@ex.com")
    proc = _criar_processo(client, token, tipo, assunto="Solicitação de teste")

    resp = client.get(f"/publico/processos/{proc['numero']}")
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["numero"] == proc["numero"]
    assert corpo["assunto"] == "Solicitação de teste"
    assert corpo["tipo_processo"]
    assert corpo["status"] == "aberto"
    assert corpo["unidade_atual"]
    assert "criado_em" in corpo
    assert corpo["historico"] == []


def test_numero_inexistente_retorna_404_com_mensagem_padrao(client, db):
    resp = client.get("/publico/processos/2026/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == MSG_NAO_ENCONTRADO


def test_cpf_cnpj_do_interessado_nao_e_exposto(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="serv2@ex.com")
    token = login(client, "serv2@ex.com")
    proc = _criar_processo(
        client,
        token,
        tipo,
        interessados=[
            {"nome": "Empresa Teste", "documento": CNPJ_VALIDO, "tipo_documento": "cnpj"}
        ],
    )

    resp = client.get(f"/publico/processos/{proc['numero']}")
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["interessados"] == [{"nome": "Empresa Teste"}]
    assert CNPJ_VALIDO not in resp.text
    assert "documento" not in corpo["interessados"][0]
    assert "tipo_documento" not in corpo["interessados"][0]


def test_processo_sigiloso_pelo_numero_exato_e_indistinguivel_de_inexistente(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="serv3@ex.com")
    token = login(client, "serv3@ex.com")
    proc = _criar_processo(client, token, tipo)

    resp_sigilo = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token))
    assert resp_sigilo.status_code == 200, resp_sigilo.text

    resp = client.get(f"/publico/processos/{proc['numero']}")
    resp_inexistente = client.get("/publico/processos/2026/888888")

    assert resp.status_code == 404
    assert resp.json() == resp_inexistente.json() == {"detail": MSG_NAO_ENCONTRADO}


def test_pesquisa_por_assunto_exclui_processo_sigiloso(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="serv4@ex.com")
    token = login(client, "serv4@ex.com")
    termo = "TermoUnicoSigilo"
    proc = _criar_processo(client, token, tipo, assunto=f"Processo {termo}")
    client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token))

    resp = client.get("/publico/processos", params={"assunto": termo})
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["items"] == []
    assert corpo["mensagem_vazio"] == MSG_PESQUISA_VAZIA


def test_historico_simplificado_nao_expoe_responsavel_nem_eventos_de_sigilo(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    usuario(db, unidade_id=cofin.id, email="serv5@ex.com")
    token = login(client, "serv5@ex.com")
    proc = _criar_processo(client, token, tipo)

    # Gera um evento de despacho e outro de marcação de sigilo (interno).
    resp = client.post(f"/processos/{proc['id']}/despachar", json={}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token))
    client.delete(f"/processos/{proc['id']}/sigilo", headers=auth(token))

    resp = client.get(f"/publico/processos/{proc['numero']}")
    assert resp.status_code == 200, resp.text
    historico = resp.json()["historico"]
    assert len(historico) == 1
    evento = historico[0]
    assert set(evento.keys()) == {"criado_em", "unidade_origem", "unidade_destino", "status_resultante"}
    assert evento["unidade_origem"] == cofin.sigla
    assert evento["unidade_destino"] == ajur.sigla
    assert "responsavel_id" not in evento
    assert "Fulano" not in resp.text  # nome do servidor não aparece


def test_pesquisa_combinada_por_tipo_e_periodo_pagina_20_por_pagina(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    outro_tipo = tipo_com_roteiro(db, cofin, nome="Outro")
    usuario(db, unidade_id=cofin.id, email="serv6@ex.com")
    token = login(client, "serv6@ex.com")

    for i in range(21):
        _criar_processo(client, token, tipo, assunto=f"Processo paginação {i}")
    # Processo de outro tipo não deve casar com o filtro.
    _criar_processo(client, token, outro_tipo, assunto="Processo de outro tipo")

    hoje = date.today().isoformat()
    resp = client.get(
        "/publico/processos",
        params={"tipo_processo": tipo.nome, "data_inicio": hoje, "data_fim": hoje, "pagina": 1},
    )
    assert resp.status_code == 200, resp.text
    corpo = resp.json()
    assert corpo["total"] == 21
    assert len(corpo["items"]) == 20
    assert all(item["tipo_processo"] == tipo.nome for item in corpo["items"])

    resp_pagina_2 = client.get(
        "/publico/processos",
        params={"tipo_processo": tipo.nome, "data_inicio": hoje, "data_fim": hoje, "pagina": 2},
    )
    assert resp_pagina_2.status_code == 200, resp_pagina_2.text
    assert len(resp_pagina_2.json()["items"]) == 1


def test_rate_limit_60_por_minuto_no_publico(client, db):
    respostas = [client.get("/publico/processos/2026/000001").status_code for _ in range(61)]
    assert respostas[:60] == [404] * 60
    assert respostas[60] == 429

    ultima = client.get("/publico/processos/2026/000001")
    assert ultima.status_code == 429
    assert ultima.json()["detail"] == (
        "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente."
    )
