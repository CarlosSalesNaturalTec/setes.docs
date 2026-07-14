"""Teste de app/security/jwt.py (task 2.3)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.security.jwt import TokenInvalido, criar_jwt, decodificar_jwt

CHAVE = "chave-de-teste-1234567890"


def test_token_valido_decodifica_claims():
    usuario_id = uuid.uuid4()
    jti = uuid.uuid4()
    exp = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = criar_jwt(usuario_id=usuario_id, jti=jti, expira_em=exp, chave=CHAVE)

    claims = decodificar_jwt(token, chave=CHAVE)

    assert claims["sub"] == str(usuario_id)
    assert claims["jti"] == str(jti)


def test_token_expirado_e_rejeitado():
    token = criar_jwt(
        usuario_id=uuid.uuid4(),
        jti=uuid.uuid4(),
        expira_em=datetime.now(timezone.utc) - timedelta(seconds=1),
        chave=CHAVE,
    )
    with pytest.raises(TokenInvalido):
        decodificar_jwt(token, chave=CHAVE)


def test_assinatura_invalida_e_rejeitada():
    token = criar_jwt(
        usuario_id=uuid.uuid4(),
        jti=uuid.uuid4(),
        expira_em=datetime.now(timezone.utc) + timedelta(minutes=30),
        chave=CHAVE,
    )
    with pytest.raises(TokenInvalido):
        decodificar_jwt(token, chave="outra-chave-qualquer")
