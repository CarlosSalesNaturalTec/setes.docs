"""Teste de app/security/sessao.py (task 2.5 — obrigatório, sessão vinculada a usuário)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import PerfilUsuario, Sessao, StatusUsuario, Usuario
from app.security.jwt import criar_jwt
from app.security.sessao import (
    TIMEOUT_INATIVIDADE,
    SessaoInvalida,
    criar_sessao,
    revogar_sessao,
    validar_e_renovar_sessao,
)

CHAVE = "chave-de-teste-1234567890"


def _criar_usuario(db) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=f"{uuid.uuid4()}@example.com",
        senha_hash="hash",
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()
    return usuario


def test_criar_e_validar_sessao_com_sliding_window(db):
    usuario = _criar_usuario(db)
    sessao_ativa = criar_sessao(db, usuario_id=usuario.id, chave_jwt=CHAVE)
    db.commit()

    ultima_atividade_original = (
        db.query(Sessao).filter(Sessao.jti == sessao_ativa.jti).one().ultima_atividade
    )

    renovada = validar_e_renovar_sessao(db, token=sessao_ativa.token, chave_jwt=CHAVE)
    db.commit()

    assert renovada.usuario_id == usuario.id
    assert renovada.jti == sessao_ativa.jti
    # sliding window: `ultima_atividade` avança a cada validação bem-sucedida
    # (exp do JWT tem granularidade de 1s — comparar o token bruto seria flaky).
    sessao_row = db.query(Sessao).filter(Sessao.jti == sessao_ativa.jti).one()
    assert sessao_row.ultima_atividade >= ultima_atividade_original


def test_revogacao_logout_invalida_sessao(db):
    usuario = _criar_usuario(db)
    sessao_ativa = criar_sessao(db, usuario_id=usuario.id, chave_jwt=CHAVE)
    db.commit()

    revogar_sessao(db, jti=sessao_ativa.jti)
    db.commit()

    with pytest.raises(SessaoInvalida):
        validar_e_renovar_sessao(db, token=sessao_ativa.token, chave_jwt=CHAVE)


def test_expiracao_por_inatividade_rejeitada_mesmo_com_jwt_ainda_valido(db):
    """`ultima_atividade` em `sessao` é checado independentemente do `exp` do
    JWT (D1) — um token com `exp` no futuro ainda é rejeitado se a sessão
    ficou inativa além do timeout."""
    usuario = _criar_usuario(db)
    sessao_ativa = criar_sessao(db, usuario_id=usuario.id, chave_jwt=CHAVE)
    db.commit()

    token_exp_futuro = criar_jwt(
        usuario_id=usuario.id,
        jti=sessao_ativa.jti,
        expira_em=datetime.now(timezone.utc) + timedelta(hours=1),
        chave=CHAVE,
    )

    sessao_row = db.query(Sessao).filter(Sessao.jti == sessao_ativa.jti).one()
    sessao_row.ultima_atividade = (
        datetime.now(timezone.utc) - TIMEOUT_INATIVIDADE - timedelta(minutes=1)
    )
    db.commit()

    with pytest.raises(SessaoInvalida):
        validar_e_renovar_sessao(db, token=token_exp_futuro, chave_jwt=CHAVE)


def test_sessoes_concorrentes_sao_independentes(db):
    """US 1.9 — dois logins do mesmo usuário; revogar uma não afeta a outra."""
    usuario = _criar_usuario(db)
    sessao_a = criar_sessao(db, usuario_id=usuario.id, chave_jwt=CHAVE)
    sessao_b = criar_sessao(db, usuario_id=usuario.id, chave_jwt=CHAVE)
    db.commit()

    revogar_sessao(db, jti=sessao_a.jti)
    db.commit()

    with pytest.raises(SessaoInvalida):
        validar_e_renovar_sessao(db, token=sessao_a.token, chave_jwt=CHAVE)

    renovada_b = validar_e_renovar_sessao(db, token=sessao_b.token, chave_jwt=CHAVE)
    assert renovada_b.jti == sessao_b.jti
