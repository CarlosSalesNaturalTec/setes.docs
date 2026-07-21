"""Testes de Kanban e busca (task 6.4 — obrigatório: visibilidade por
unidade/perfil). US 2.3, 2.7, 2.8."""

from __future__ import annotations

from datetime import date

from sqlalchemy import event

from app.db.session import get_engine
from tests.helpers_processo import (
    auth,
    gestor_de,
    login,
    tipo_com_roteiro,
    unidade,
    usuario,
)


def _cria_processo(client, token, tipo, assunto="A", prazo=10):
    return client.post(
        "/processos",
        json={"assunto": assunto, "tipo_processo_id": str(tipo.id), "prazo_dias": prazo},
        headers=auth(token),
    ).json()


def _contar_queries(fn):
    """Executa `fn` contando as queries emitidas no engine — usado para
    validar ausência de N+1 (task 1.4, D1)."""
    queries: list[str] = []
    engine = get_engine()

    def _registrar(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", _registrar)
    try:
        resultado = fn()
    finally:
        event.remove(engine, "before_cursor_execute", _registrar)
    return resultado, len(queries)


def test_servidor_so_ve_processos_da_propria_unidade(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)

    usuario(db, unidade_id=cofin.id, email="c@ex.com")
    token_cofin = login(client, "c@ex.com")
    _cria_processo(client, token_cofin, tipo, "Processo COFIN")

    usuario(db, unidade_id=ajur.id, email="a@ex.com")
    token_ajur = login(client, "a@ex.com")

    resp = client.get("/processos", headers=auth(token_ajur))
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["mensagem_vazio"] == "Nenhum processo encontrado nesta unidade"


def test_kanban_vazio_servidor(client, db):
    cofin = unidade(db, "COFIN")
    usuario(db, unidade_id=cofin.id, email="v@ex.com")
    token = login(client, "v@ex.com")
    resp = client.get("/processos", headers=auth(token))
    assert resp.json()["items"] == []
    assert resp.json()["mensagem_vazio"] == "Nenhum processo encontrado nesta unidade"


def test_gestor_ve_consolidado_e_filtra_por_unidade(client, db):
    cofin, ajur, dirad = unidade(db, "COFIN"), unidade(db, "AJUR"), unidade(db, "DIRAD")
    tipo_c = tipo_com_roteiro(db, cofin, nome="TC")
    tipo_a = tipo_com_roteiro(db, ajur, nome="TA")

    usuario(db, unidade_id=cofin.id, email="sc@ex.com")
    _cria_processo(client, login(client, "sc@ex.com"), tipo_c, "P COFIN")
    usuario(db, unidade_id=ajur.id, email="sa@ex.com")
    _cria_processo(client, login(client, "sa@ex.com"), tipo_a, "P AJUR")

    gestor_de(db, cofin, ajur, email="gestor@ex.com")
    token_g = login(client, "gestor@ex.com")

    # Consolidado: vê os dois.
    todos = client.get("/processos", headers=auth(token_g))
    assert todos.json()["total"] == 2

    # Filtro por unidade gerida (US 2.8 Cen.2).
    so_cofin = client.get(f"/processos?filtro_unidade={cofin.id}", headers=auth(token_g))
    assert so_cofin.json()["total"] == 1
    assert so_cofin.json()["items"][0]["unidade_atual_id"] == str(cofin.id)

    # Filtro por unidade NÃO gerida (DIRAD) — não retorna nada (não amplia acesso).
    fora = client.get(f"/processos?filtro_unidade={dirad.id}", headers=auth(token_g))
    assert fora.json()["total"] == 0


def test_ordenacao_por_prazo_vencidos_primeiro(client, db):
    from app.db.models import Processo

    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="ord@ex.com")
    token = login(client, "ord@ex.com")

    _cria_processo(client, token, tipo, "Futuro", prazo=30)
    p_urgente = _cria_processo(client, token, tipo, "Urgente", prazo=1)

    # Força um vencimento no passado para "Urgente".
    proc = db.get(Processo, p_urgente["id"])
    proc.prazo_em = date(2000, 1, 1)
    db.commit()

    resp = client.get("/processos", headers=auth(token))
    itens = resp.json()["items"]
    assert itens[0]["numero"] == p_urgente["numero"]
    assert itens[0]["vencido"] is True


def test_busca_por_numero_exato(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    usuario(db, unidade_id=cofin.id, email="b@ex.com")
    token = login(client, "b@ex.com")
    proc = _cria_processo(client, token, tipo, "Alvo")

    resp = client.get(f"/processos/busca?numero={proc['numero']}", headers=auth(token))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    item = resp.json()["items"][0]
    assert item["numero"] == proc["numero"]
    assert item["tipo_processo_nome"] == tipo.nome
    assert item["unidade_atual_nome"] == cofin.nome
    assert item["criado_em"]


def test_card_do_kanban_traz_tipo_unidade_e_data_criacao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin, nome="Licitação")
    usuario(db, unidade_id=cofin.id, email="card@ex.com")
    token = login(client, "card@ex.com")
    proc = _cria_processo(client, token, tipo, "Processo card")

    resp = client.get("/processos", headers=auth(token))
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["numero"] == proc["numero"]
    assert item["tipo_processo_nome"] == tipo.nome
    assert item["unidade_atual_nome"] == cofin.nome
    assert item["criado_em"]


def test_listar_kanban_sem_n_mais_1_ao_incluir_tipo_e_unidade(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin, nome="Licitação")
    usuario(db, unidade_id=cofin.id, email="n1@ex.com")
    token = login(client, "n1@ex.com")
    _cria_processo(client, token, tipo, "P1")

    resp1, n1 = _contar_queries(lambda: client.get("/processos", headers=auth(token)))
    assert resp1.json()["total"] == 1

    for i in range(3):
        _cria_processo(client, token, tipo, f"P{i + 2}")

    resp2, n2 = _contar_queries(lambda: client.get("/processos", headers=auth(token)))
    assert resp2.json()["total"] == 4
    # Nº de queries não cresce com a quantidade de itens (eager loading, D1).
    assert n2 == n1


def test_busca_sem_n_mais_1_ao_incluir_tipo_e_unidade(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin, nome="Licitação")
    usuario(db, unidade_id=cofin.id, email="n2@ex.com")
    token = login(client, "n2@ex.com")
    _cria_processo(client, token, tipo, "Contrato 1")

    resp1, n1 = _contar_queries(
        lambda: client.get("/processos/busca?assunto=Contrato", headers=auth(token))
    )
    assert resp1.json()["total"] == 1

    for i in range(3):
        _cria_processo(client, token, tipo, f"Contrato {i + 2}")

    resp2, n2 = _contar_queries(
        lambda: client.get("/processos/busca?assunto=Contrato", headers=auth(token))
    )
    assert resp2.json()["total"] == 4
    assert n2 == n1


def test_busca_por_assunto_restrita_a_unidade(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo_c = tipo_com_roteiro(db, cofin, nome="TC")
    tipo_a = tipo_com_roteiro(db, ajur, nome="TA")

    usuario(db, unidade_id=cofin.id, email="bc@ex.com")
    _cria_processo(client, login(client, "bc@ex.com"), tipo_c, "Contrato especial")
    usuario(db, unidade_id=ajur.id, email="ba@ex.com")
    token_ajur = login(client, "ba@ex.com")
    _cria_processo(client, token_ajur, tipo_a, "Contrato especial")

    # AJUR busca "Contrato" — só vê o seu, nunca o da COFIN.
    resp = client.get("/processos/busca?assunto=Contrato", headers=auth(token_ajur))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["unidade_atual_id"] == str(ajur.id)


def test_busca_sem_resultados(client, db):
    cofin = unidade(db, "COFIN")
    usuario(db, unidade_id=cofin.id, email="sr@ex.com")
    token = login(client, "sr@ex.com")
    resp = client.get("/processos/busca?assunto=inexistente", headers=auth(token))
    assert resp.json()["total"] == 0
    assert resp.json()["mensagem_vazio"] == "Nenhum processo encontrado para os filtros informados"
