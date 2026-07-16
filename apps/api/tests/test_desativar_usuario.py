"""Teste de desativação de usuário — POST /usuarios/{id}/desativar (task 4.2 —
obrigatório, toca `log_seguranca` e histórico de tramitação)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    StatusProcesso,
    StatusUsuario,
    TipoEventoLog,
    TipoEventoTramitacao,
    Tramitacao,
)
from tests.helpers_processo import (
    auth,
    login,
    processo_ativo,
    processo_concluido,
    tipo_com_roteiro,
    unidade,
    usuario,
)


def _tramitacao(db, *, processo, responsavel, status_resultante):
    evento = Tramitacao(
        processo_id=processo.id,
        tipo_evento=TipoEventoTramitacao.DESPACHO,
        unidade_origem_id=processo.unidade_atual_id,
        unidade_destino_id=processo.unidade_atual_id,
        responsavel_id=responsavel.id,
        status_resultante=status_resultante,
    )
    db.add(evento)
    db.commit()
    return evento


def test_desativacao_sem_pendencias_registra_log(client, db):
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "admin@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/desativar", headers=auth(token))

    assert resp.status_code == 200
    assert resp.json()["status"] == "inativo"

    db.refresh(alvo)
    assert alvo.status == StatusUsuario.INATIVO
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 1
    assert logs[0].tipo_evento == TipoEventoLog.USUARIO_DESATIVADO
    assert logs[0].contexto["administrador_id"] == str(admin.id)


def test_desativacao_bloqueada_por_processos_em_andamento(client, db):
    cofin = unidade(db, "COFIN")
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id, email="alvo@example.com")
    tipo = tipo_com_roteiro(db, cofin)
    token = login(client, "admin@example.com")

    for _ in range(3):
        processo = processo_ativo(db, unidade=cofin, criador=alvo, tipo=tipo, prazo_em=date.today() + timedelta(days=10))
        _tramitacao(db, processo=processo, responsavel=alvo, status_resultante=StatusProcesso.EM_TRAMITACAO)

    resp = client.post(f"/usuarios/{alvo.id}/desativar", headers=auth(token))

    assert resp.status_code == 422
    assert "3 processo(s) em andamento" in resp.json()["detail"]

    db.refresh(alvo)
    assert alvo.status == StatusUsuario.ATIVO
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 0


def test_processo_concluido_ou_arquivado_nao_bloqueia_desativacao(client, db):
    cofin = unidade(db, "COFIN")
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, unidade_id=cofin.id, email="alvo@example.com")
    tipo = tipo_com_roteiro(db, cofin)
    token = login(client, "admin@example.com")

    agora = datetime.now(timezone.utc)
    processo_concluido(db, unidade=cofin, criador=alvo, tipo=tipo, concluido_em=agora, arquivar_em=agora)

    resp = client.post(f"/usuarios/{alvo.id}/desativar", headers=auth(token))

    assert resp.status_code == 200
    db.refresh(alvo)
    assert alvo.status == StatusUsuario.INATIVO


def test_desativacao_idempotente_de_usuario_ja_inativo(client, db):
    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    alvo.status = StatusUsuario.INATIVO
    db.commit()
    token = login(client, "admin@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/desativar", headers=auth(token))

    assert resp.status_code == 422
    assert "já está inativo" in resp.json()["detail"].lower()
    logs = db.query(LogSeguranca).filter(LogSeguranca.usuario_id == alvo.id).all()
    assert len(logs) == 0


def test_nao_admin_recebe_acesso_negado_ao_desativar(client, db):
    servidor = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="servidor@example.com")
    alvo = usuario(db, perfil=PerfilUsuario.SERVIDOR, email="alvo@example.com")
    token = login(client, "servidor@example.com")

    resp = client.post(f"/usuarios/{alvo.id}/desativar", headers=auth(token))

    assert resp.status_code == 403
    db.refresh(alvo)
    assert alvo.status == StatusUsuario.ATIVO
    logs = db.query(LogSeguranca).filter(
        LogSeguranca.usuario_id == servidor.id, LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO
    ).all()
    assert len(logs) == 1
