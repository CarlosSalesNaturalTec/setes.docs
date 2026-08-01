"""Testes dos filtros do quadro (tipo, assunto, data) e do desdobramento do
checkbox de arquivados (change kanban-por-servidor, task 3.4 — obrigatório:
não pode ampliar o escopo autorizado). US 2.3, US 2.8 (design D4/D5)."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.db.models import Processo, StatusProcesso
from tests.helpers_processo import auth, login, servidor_com_setor, tipo_processo, unidade


def _criar_processo(client, token, tipo, assunto="Processo"):
    resp = client.post(
        "/processos",
        json={"assunto": assunto, "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _marcar_status(db, processo_id: str, status: StatusProcesso) -> None:
    processo = db.get(Processo, processo_id)
    processo.status = status
    if status in (StatusProcesso.CONCLUIDO, StatusProcesso.ARQUIVADO):
        processo.concluido_em = datetime.utcnow()
    db.commit()


def test_concluidos_sempre_exibidos_arquivados_ocultos_por_padrao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="arq@ex.com")
    token = login(client, "arq@ex.com")

    aberto = _criar_processo(client, token, tipo, "Aberto")
    concluido = _criar_processo(client, token, tipo, "Concluído")
    arquivado = _criar_processo(client, token, tipo, "Arquivado")
    _marcar_status(db, concluido["id"], StatusProcesso.CONCLUIDO)
    _marcar_status(db, arquivado["id"], StatusProcesso.ARQUIVADO)

    resp_default = client.get("/processos", headers=auth(token))
    numeros_default = {item["numero"] for item in resp_default.json()["items"]}
    assert aberto["numero"] in numeros_default
    assert concluido["numero"] in numeros_default
    assert arquivado["numero"] not in numeros_default
    assert resp_default.json()["total"] == 2

    resp_arquivados = client.get("/processos?incluir_arquivados=true", headers=auth(token))
    numeros_arquivados = {item["numero"] for item in resp_arquivados.json()["items"]}
    assert {aberto["numero"], concluido["numero"], arquivado["numero"]} == numeros_arquivados
    assert resp_arquivados.json()["total"] == 3


def test_filtro_por_tipo_processo(client, db):
    cofin = unidade(db, "COFIN")
    tipo_a = tipo_processo(db, nome="Requerimento")
    tipo_b = tipo_processo(db, nome="Licitação")
    servidor_com_setor(db, cofin, email="tipo@ex.com")
    token = login(client, "tipo@ex.com")

    p_a = _criar_processo(client, token, tipo_a, "Do tipo A")
    _criar_processo(client, token, tipo_b, "Do tipo B")

    resp = client.get(f"/processos?tipo_processo_id={tipo_a.id}", headers=auth(token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["numero"] == p_a["numero"]


def test_filtro_por_assunto_parcial(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="assunto@ex.com")
    token = login(client, "assunto@ex.com")

    alvo = _criar_processo(client, token, tipo, "Solicitação de diária para capacitação")
    _criar_processo(client, token, tipo, "Compra de material de escritório")

    resp = client.get("/processos?assunto=di%C3%A1ria", headers=auth(token))
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["numero"] == alvo["numero"]


def test_filtro_por_periodo_de_criacao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="periodo@ex.com")
    token = login(client, "periodo@ex.com")

    dentro = _criar_processo(client, token, tipo, "Dentro do período")
    fora = _criar_processo(client, token, tipo, "Fora do período")
    proc_fora = db.get(Processo, fora["id"])
    proc_fora.criado_em = datetime.utcnow() - timedelta(days=60)
    db.commit()

    hoje = date.today()
    inicio = hoje - timedelta(days=5)
    resp = client.get(
        f"/processos?data_inicial={inicio.isoformat()}&data_final={hoje.isoformat()}",
        headers=auth(token),
    )
    numeros = {item["numero"] for item in resp.json()["items"]}
    assert dentro["numero"] in numeros
    assert fora["numero"] not in numeros


def test_filtros_combinados_com_incluir_arquivados(client, db):
    cofin = unidade(db, "COFIN")
    tipo_a = tipo_processo(db, nome="Requerimento")
    tipo_b = tipo_processo(db, nome="Licitação")
    servidor_com_setor(db, cofin, email="comb@ex.com")
    token = login(client, "comb@ex.com")

    alvo = _criar_processo(client, token, tipo_a, "Diária de viagem")
    _marcar_status(db, alvo["id"], StatusProcesso.ARQUIVADO)
    _criar_processo(client, token, tipo_a, "Outro assunto qualquer")
    _criar_processo(client, token, tipo_b, "Diária de viagem também")

    hoje = date.today()
    resp = client.get(
        "/processos"
        f"?tipo_processo_id={tipo_a.id}&assunto=di%C3%A1ria"
        f"&data_inicial={hoje.isoformat()}&data_final={hoje.isoformat()}"
        "&incluir_arquivados=true",
        headers=auth(token),
    )
    numeros = {item["numero"] for item in resp.json()["items"]}
    assert numeros == {alvo["numero"]}

    # Sem incluir_arquivados, o mesmo conjunto de filtros não retorna nada
    # (o único que satisfaz tipo+assunto está arquivado).
    resp_sem_arquivados = client.get(
        "/processos"
        f"?tipo_processo_id={tipo_a.id}&assunto=di%C3%A1ria"
        f"&data_inicial={hoje.isoformat()}&data_final={hoje.isoformat()}",
        headers=auth(token),
    )
    assert resp_sem_arquivados.json()["total"] == 0


def test_filtro_nao_amplia_escopo_pessoal_do_servidor(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="alheio@ex.com")
    token_alheio = login(client, "alheio@ex.com")
    processo_alheio = _criar_processo(client, token_alheio, tipo, "Diária de terceiro")

    servidor_com_setor(db, cofin, email="filtroescopo@ex.com")
    token = login(client, "filtroescopo@ex.com")

    resp = client.get("/processos?assunto=Di%C3%A1ria", headers=auth(token))
    assert resp.json()["total"] == 0
    numeros = {item["numero"] for item in resp.json()["items"]}
    assert processo_alheio["numero"] not in numeros
