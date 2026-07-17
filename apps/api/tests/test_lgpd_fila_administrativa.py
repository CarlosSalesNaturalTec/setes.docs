"""Testes obrigatórios da fila administrativa LGPD (US 10.2, tasks
5.4/5.5/5.6/5.7) — acesso negado, dado pessoal, rejeição e estado terminal."""

from __future__ import annotations

from datetime import date

import pytest

from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    ProcessoInteressado,
    SolicitacaoLgpd,
    StatusSolicitacaoLgpd,
    TipoEventoLog,
)
from tests.helpers_processo import auth, login, processo_ativo, tipo_com_roteiro, unidade, usuario

CPF_VALIDO = "52998224725"


def _processo_com_interessado(db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    criador = usuario(db, unidade_id=cofin.id, email=f"criador-{cofin.id}@ex.com")
    processo = processo_ativo(db, unidade=cofin, criador=criador, tipo=tipo, prazo_em=date.today())
    interessado = ProcessoInteressado(processo_id=processo.id, nome="Fulano de Tal", documento=CPF_VALIDO)
    db.add(interessado)
    db.commit()
    return processo, interessado


def _solicitacao(db, processo, *, status_=StatusSolicitacaoLgpd.PENDENTE, sufixo="") -> SolicitacaoLgpd:
    s = SolicitacaoLgpd(
        protocolo=f"LGPD/2026/{abs(hash(sufixo)) % 999999:06d}",
        processo_id=processo.id,
        nome_solicitante="Fulano de Tal",
        cpf_solicitante=CPF_VALIDO,
        email_solicitante="fulano@example.com",
        tipo="exclusao",
        status=status_,
        documento_identificacao_chave="solicitacoes/fake",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _admin(db, sufixo="") -> object:
    return usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email=f"admin-lgpd{sufixo}@ex.com")


# --- 5.4 — acesso negado -----------------------------------------------------


@pytest.mark.parametrize("perfil", [PerfilUsuario.SERVIDOR, PerfilUsuario.GESTOR])
def test_acesso_negado_nao_admin(client, db, perfil):
    processo, _interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, sufixo="neg")
    cofin = unidade(db, "COFIN2")
    nao_admin = usuario(db, perfil=perfil, unidade_id=cofin.id, email=f"naoadmin-lgpd-{perfil.value}@ex.com")
    token = login(client, nao_admin.email)

    resp_lista = client.get("/lgpd/solicitacoes", headers=auth(token))
    assert resp_lista.status_code == 403

    resp_atender = client.post(
        f"/lgpd/solicitacoes/{solicitacao.id}/atender", headers=auth(token)
    )
    assert resp_atender.status_code == 403

    resp_rejeitar = client.post(
        f"/lgpd/solicitacoes/{solicitacao.id}/rejeitar",
        json={"justificativa": "não é o titular"},
        headers=auth(token),
    )
    assert resp_rejeitar.status_code == 403

    logs = db.query(LogSeguranca).filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO).all()
    assert len(logs) == 3


# --- 5.5 — atendimento anonimiza e muda status (dado pessoal) ---------------


def test_atender_anonimiza_interessados_e_muda_status(client, db):
    processo, interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, sufixo="atender")
    admin = _admin(db, "-atender")
    token = login(client, admin.email)

    resp = client.post(f"/lgpd/solicitacoes/{solicitacao.id}/atender", headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "atendida"
    db.refresh(interessado)
    assert interessado.nome == "Titular Anonimizado"
    assert interessado.anonimizado_em is not None
    db.refresh(solicitacao)
    assert solicitacao.status == StatusSolicitacaoLgpd.ATENDIDA
    assert solicitacao.atendido_por_id == admin.id
    assert solicitacao.atendido_em is not None


# --- 5.6 — rejeição ----------------------------------------------------------


def test_rejeitar_sem_justificativa_falha(client, db):
    processo, _interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, sufixo="semjust")
    admin = _admin(db, "-semjust")
    token = login(client, admin.email)

    resp = client.post(
        f"/lgpd/solicitacoes/{solicitacao.id}/rejeitar",
        json={"justificativa": ""},
        headers=auth(token),
    )

    assert resp.status_code == 422


def test_rejeitar_com_justificativa_muda_status_e_preserva_texto(client, db):
    processo, _interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, sufixo="comjust")
    admin = _admin(db, "-comjust")
    token = login(client, admin.email)

    resp = client.post(
        f"/lgpd/solicitacoes/{solicitacao.id}/rejeitar",
        json={"justificativa": "Solicitante não é o titular dos dados"},
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    db.refresh(solicitacao)
    assert solicitacao.status == StatusSolicitacaoLgpd.REJEITADA
    assert solicitacao.justificativa_rejeicao == "Solicitante não é o titular dos dados"


# --- 5.7 — estado terminal ---------------------------------------------------


@pytest.mark.parametrize("status_final", [StatusSolicitacaoLgpd.ATENDIDA, StatusSolicitacaoLgpd.REJEITADA])
def test_atender_ou_rejeitar_estado_terminal_falha(client, db, status_final):
    processo, _interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, status_=status_final, sufixo=f"terminal-{status_final.value}")
    admin = _admin(db, f"-terminal-{status_final.value}")
    token = login(client, admin.email)

    resp_atender = client.post(f"/lgpd/solicitacoes/{solicitacao.id}/atender", headers=auth(token))
    assert resp_atender.status_code == 409

    resp_rejeitar = client.post(
        f"/lgpd/solicitacoes/{solicitacao.id}/rejeitar",
        json={"justificativa": "qualquer"},
        headers=auth(token),
    )
    assert resp_rejeitar.status_code == 409


# --- 5.1 — listagem (protocolo/data/solicitante/processo/tipo/status) -------


def test_listar_fila_retorna_campos_esperados(client, db):
    processo, _interessado = _processo_com_interessado(db)
    solicitacao = _solicitacao(db, processo, sufixo="listagem")
    admin = _admin(db, "-listagem")
    token = login(client, admin.email)

    resp = client.get("/lgpd/solicitacoes", headers=auth(token))

    assert resp.status_code == 200, resp.text
    itens = resp.json()["items"]
    item = next(i for i in itens if i["id"] == str(solicitacao.id))
    assert item["protocolo"] == solicitacao.protocolo
    assert item["nome_solicitante"] == "Fulano de Tal"
    assert item["processo_numero"] == processo.numero
    assert item["tipo"] == "exclusao"
    assert item["status"] == "pendente"
