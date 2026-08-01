"""Testes de criação de processo (task 3.4 — obrigatório: dado pessoal de
interessado + número/histórico). US 2.1, change tramitacao-manual (sem
roteiro — processo nasce atribuído ao criador, D1)."""

from __future__ import annotations

from app.db.models import Processo, StatusProcesso
from tests.helpers_processo import (
    CNPJ_INVALIDO,
    CNPJ_VALIDO,
    CPF_INVALIDO,
    CPF_VALIDO,
    auth,
    login,
    servidor_com_setor,
    tipo_processo,
    unidade,
    usuario,
)


def _servidor_logado(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    tipo = tipo_processo(db)
    serv, _setor = servidor_com_setor(db, cofin, email="serv@example.com")
    token = login(client, "serv@example.com")
    return cofin, ajur, tipo, serv, token


def test_cria_processo_com_dados_obrigatorios(client, db):
    cofin, _ajur, tipo, serv, token = _servidor_logado(client, db)
    resp = client.post(
        "/processos",
        json={"assunto": "Compra de material", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "aberto"
    assert body["numero"].endswith("/000001")
    assert body["unidade_atual_id"] == str(cofin.id)
    assert body["setor_atual_id"] == str(serv.setor_id)
    assert body["servidor_atual_id"] == str(serv.id)
    # Aparece no Kanban da unidade (coluna Aberto).
    kanban = client.get("/processos", headers=auth(token))
    numeros = [c["numero"] for c in kanban.json()["items"]]
    assert body["numero"] in numeros


def test_numero_reinicia_por_ano_e_e_sequencial(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    n1 = client.post(
        "/processos",
        json={"assunto": "A", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    ).json()["numero"]
    n2 = client.post(
        "/processos",
        json={"assunto": "B", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    ).json()["numero"]
    assert n1.endswith("/000001")
    assert n2.endswith("/000002")


def test_criacao_sem_assunto_ou_tipo_e_422(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    resp = client.post(
        "/processos", json={"tipo_processo_id": str(tipo.id), "prazo_dias": 5}, headers=auth(token)
    )
    assert resp.status_code == 422
    campos = {e["loc"][-1] for e in resp.json()["detail"]}
    assert "assunto" in campos


def test_interessado_com_cpf_invalido(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    resp = client.post(
        "/processos",
        json={
            "assunto": "X",
            "tipo_processo_id": str(tipo.id),
            "prazo_dias": 5,
            "interessados": [{"nome": "João", "documento": CPF_INVALIDO, "tipo_documento": "cpf"}],
        },
        headers=auth(token),
    )
    assert resp.status_code == 422
    assert "CPF inválido — verifique o número informado" in resp.text


def test_interessado_com_cnpj_invalido(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    resp = client.post(
        "/processos",
        json={
            "assunto": "X",
            "tipo_processo_id": str(tipo.id),
            "prazo_dias": 5,
            "interessados": [
                {"nome": "Empresa", "documento": CNPJ_INVALIDO, "tipo_documento": "cnpj"}
            ],
        },
        headers=auth(token),
    )
    assert resp.status_code == 422
    assert "CNPJ inválido — verifique o número informado" in resp.text


def test_multiplos_interessados_validos_e_apenas_nome(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    resp = client.post(
        "/processos",
        json={
            "assunto": "X",
            "tipo_processo_id": str(tipo.id),
            "prazo_dias": 5,
            "interessados": [
                {
                    "nome": "Pessoa Física",
                    "documento": CPF_VALIDO,
                    "tipo_documento": "cpf",
                    "tipo_participacao": "requerente",
                },
                {
                    "nome": "Empresa",
                    "documento": CNPJ_VALIDO,
                    "tipo_documento": "cnpj",
                    "tipo_participacao": "terceiro",
                },
                {"nome": "Só Nome"},
            ],
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    interessados = resp.json()["interessados"]
    assert len(interessados) == 3
    docs = {i["documento"] for i in interessados if i["documento"]}
    assert "52998224725" in docs  # normalizado (sem máscara)


def test_criacao_nao_exige_roteiro_configurado(client, db):
    """Change tramitacao-manual: tipo de processo sem qualquer configuração de
    fluxo não bloqueia a criação — roteiros não existem mais no sistema."""
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    serv, _setor = servidor_com_setor(db, cofin, email="serv2@example.com")
    token = login(client, serv.email)
    resp = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text


def test_criacao_por_usuario_sem_setor_e_rejeitada(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    usuario(db, unidade_id=cofin.id, email="sem-setor@example.com")
    token = login(client, "sem-setor@example.com")
    resp = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    )
    assert resp.status_code == 422
    assert "setor" in resp.json()["detail"].lower()


def test_status_processo_e_aberto_apos_criacao(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    numero = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    ).json()["numero"]
    processo = db.query(Processo).filter(Processo.numero == numero).one()
    assert processo.status == StatusProcesso.ABERTO
