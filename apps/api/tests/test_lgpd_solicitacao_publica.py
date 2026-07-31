"""Testes obrigatórios do canal público de solicitação LGPD (US 10.1, tasks
4.5/4.6/4.7/4.8) — dado pessoal do solicitante."""

from __future__ import annotations

from datetime import date

from app.db.models import SolicitacaoLgpd
from tests.helpers_processo import processo_ativo, servidor_com_setor, tipo_processo, unidade

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF"

CPF_VALIDO = "529.982.247-25"


def _processo(db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    criador, _setor_criador = servidor_com_setor(db, cofin, email=f"criador-{cofin.id}@ex.com")
    return processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today())


def _form(numero_processo: str, **overrides) -> dict:
    dados = {
        "numero_processo": numero_processo,
        "nome": "Fulano de Tal",
        "cpf": CPF_VALIDO,
        "email": "fulano@example.com",
        "tipo": "exclusao",
    }
    dados.update(overrides)
    return dados


def test_solicitacao_valida_gera_protocolo_unico(client, db):
    processo = _processo(db)

    resp = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form(processo.numero),
        files={"arquivo": ("id.pdf", PDF, "application/pdf")},
    )

    assert resp.status_code == 201, resp.text
    protocolo = resp.json()["protocolo"]
    assert protocolo.startswith("LGPD/")

    registro = db.query(SolicitacaoLgpd).filter(SolicitacaoLgpd.protocolo == protocolo).first()
    assert registro is not None
    assert registro.processo_id == processo.id
    assert registro.nome_solicitante == "Fulano de Tal"
    assert registro.email_solicitante == "fulano@example.com"

    resp2 = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form(processo.numero),
        files={"arquivo": ("id.pdf", PDF, "application/pdf")},
    )
    assert resp2.json()["protocolo"] != protocolo


def test_campos_obrigatorios_ausentes(client, db):
    processo = _processo(db)

    resp = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form(processo.numero, nome=""),
        files={"arquivo": ("id.pdf", PDF, "application/pdf")},
    )

    assert resp.status_code == 422
    assert resp.json()["detail"] == "Preencha todos os campos obrigatórios"


def test_documento_formato_invalido_rejeitado(client, db):
    processo = _processo(db)

    resp = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form(processo.numero),
        files={"arquivo": ("id.txt", b"conteudo", "text/plain")},
    )

    assert resp.status_code == 422
    assert "PDF, JPG ou PNG" in resp.json()["detail"]


def test_documento_vazio_rejeitado(client, db):
    processo = _processo(db)

    resp = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form(processo.numero),
        files={"arquivo": ("id.pdf", b"", "application/pdf")},
    )

    assert resp.status_code == 422


def test_numero_processo_inexistente(client, db):
    resp = client.post(
        "/publico/lgpd/solicitacoes",
        data=_form("2026/999999"),
        files={"arquivo": ("id.pdf", PDF, "application/pdf")},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == (
        "Nenhum processo encontrado com o número informado. Verifique o número e tente novamente."
    )
