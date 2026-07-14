"""Teste de app/services/tokens.py (D3 — usado pelas tasks 5.2-5.4)."""

import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.db.models import PerfilUsuario, StatusUsuario, TipoTokenAutenticacao, TokenAutenticacao, Usuario
from app.services.tokens import (
    MSG_LINK_EXPIRADO,
    MSG_LINK_JA_UTILIZADO,
    TokenInvalido,
    consumir_token,
    gerar_token,
)


def _criar_usuario(db) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=f"{uuid.uuid4()}@example.com",
        senha_hash="hash",
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.PENDENTE_PRIMEIRO_ACESSO,
    )
    db.add(usuario)
    db.commit()
    return usuario


def test_valor_puro_nunca_e_persistido_apenas_o_hash(db):
    usuario = _criar_usuario(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    registro = db.query(TokenAutenticacao).filter(TokenAutenticacao.id == gerado.token_id).one()
    assert registro.token_hash != gerado.valor
    assert len(gerado.valor) > 20


def test_consumir_token_valido_marca_usado_em(db):
    usuario = _criar_usuario(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    registro = consumir_token(db, valor=gerado.valor, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    assert registro.usado_em is not None


def test_reuso_do_mesmo_token_e_rejeitado(db):
    usuario = _criar_usuario(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    consumir_token(db, valor=gerado.valor, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    with pytest.raises(TokenInvalido, match=re.escape(MSG_LINK_JA_UTILIZADO)):
        consumir_token(db, valor=gerado.valor, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)


def test_token_expirado_e_rejeitado(db):
    usuario = _criar_usuario(db)
    gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    db.commit()

    registro = db.query(TokenAutenticacao).filter(TokenAutenticacao.id == gerado.token_id).one()
    registro.expira_em = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    with pytest.raises(TokenInvalido, match=re.escape(MSG_LINK_EXPIRADO)):
        consumir_token(db, valor=gerado.valor, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)


def test_ttl_por_tipo_e_diferente():
    from app.services.tokens import TTL_PRIMEIRO_ACESSO, TTL_RECUPERACAO_SENHA

    assert TTL_PRIMEIRO_ACESSO == timedelta(hours=48)
    assert TTL_RECUPERACAO_SENHA == timedelta(hours=2)
