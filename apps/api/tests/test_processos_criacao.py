"""Testes de criação de processo (task 3.4 — obrigatório: dado pessoal de
interessado + número/histórico). US 2.1."""

from __future__ import annotations

from app.db.models import Processo, StatusProcesso
from tests.helpers_processo import (
    CNPJ_INVALIDO,
    CNPJ_VALIDO,
    CPF_INVALIDO,
    CPF_VALIDO,
    auth,
    login,
    tipo_com_roteiro,
    tipo_sem_roteiro,
    unidade,
    usuario,
)


def _servidor_logado(client, db):
    cofin = unidade(db, "COFIN")
    ajur = unidade(db, "AJUR")
    tipo = tipo_com_roteiro(db, cofin, ajur)
    serv = usuario(db, unidade_id=cofin.id, email="serv@example.com")
    token = login(client, "serv@example.com")
    return cofin, ajur, tipo, serv, token


def test_cria_processo_com_dados_obrigatorios(client, db):
    cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
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


def test_tipo_sem_roteiro_bloqueia_criacao(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_sem_roteiro(db)
    usuario(db, unidade_id=cofin.id, email="serv2@example.com")
    token = login(client, "serv2@example.com")
    resp = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    )
    assert resp.status_code == 422
    assert "não possui roteiro de tramitação configurado" in resp.text


def test_snapshot_de_roteiro_fixado_na_criacao(client, db):
    """US 8.2 Cen.2 — alterar o roteiro do tipo não afeta processo já criado."""
    from app.db.models import Roteiro, RoteiroEtapa

    cofin, ajur, tipo, _serv, token = _servidor_logado(client, db)
    numero = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    ).json()["numero"]
    processo = db.query(Processo).filter(Processo.numero == numero).one()
    roteiro_original = processo.roteiro_id

    # Nova versão do roteiro (a antiga deixa de ser vigente, mas permanece).
    antigo = db.query(Roteiro).filter(Roteiro.id == roteiro_original).one()
    antigo.vigente = False
    novo = Roteiro(tipo_processo_id=tipo.id, vigente=True)
    db.add(novo)
    db.commit()
    db.add(RoteiroEtapa(roteiro_id=novo.id, unidade_id=cofin.id, ordem=1))
    db.commit()

    db.refresh(processo)
    assert processo.roteiro_id == roteiro_original  # snapshot inalterado


def test_status_processo_e_aberto_apos_criacao(client, db):
    _cofin, _ajur, tipo, _serv, token = _servidor_logado(client, db)
    numero = client.post(
        "/processos",
        json={"assunto": "X", "tipo_processo_id": str(tipo.id), "prazo_dias": 5},
        headers=auth(token),
    ).json()["numero"]
    processo = db.query(Processo).filter(Processo.numero == numero).one()
    assert processo.status == StatusProcesso.ABERTO
