"""Tokens de uso único — primeiro acesso e recuperação de senha (D3).

O valor puro do token (`secrets.token_urlsafe`) só existe no e-mail enviado;
o banco guarda apenas seu hash sha256 (mesma lógica de defesa de um password
hash — se o banco vazar, tokens ainda ativos não são utilizáveis diretamente).
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import TipoTokenAutenticacao, TokenAutenticacao

TTL_PRIMEIRO_ACESSO = timedelta(hours=48)
TTL_RECUPERACAO_SENHA = timedelta(hours=2)

_TTL_POR_TIPO = {
    TipoTokenAutenticacao.PRIMEIRO_ACESSO: TTL_PRIMEIRO_ACESSO,
    TipoTokenAutenticacao.RECUPERACAO_SENHA: TTL_RECUPERACAO_SENHA,
}

MSG_LINK_EXPIRADO = "Link expirado. Solicite um novo link de acesso ao Administrador."
MSG_LINK_JA_UTILIZADO = 'Link já utilizado. Faça login ou use "Esqueci minha senha".'
MSG_LINK_INVALIDO = "Link inválido."


class TokenInvalido(Exception):
    """Token inexistente, expirado ou já utilizado — mensagem já pronta para o usuário."""


@dataclass(frozen=True)
class TokenGerado:
    token_id: uuid.UUID
    valor: str
    expira_em: datetime


def _hash_token(valor: str) -> str:
    return hashlib.sha256(valor.encode()).hexdigest()


def gerar_token(
    db: Session, *, usuario_id: uuid.UUID, tipo: TipoTokenAutenticacao
) -> TokenGerado:
    """Cria o registro em `token_autenticacao` e retorna o valor puro do token."""
    valor = secrets.token_urlsafe(32)
    agora = datetime.now(timezone.utc)
    expira_em = agora + _TTL_POR_TIPO[tipo]
    registro = TokenAutenticacao(
        usuario_id=usuario_id, tipo=tipo, token_hash=_hash_token(valor), expira_em=expira_em
    )
    db.add(registro)
    db.flush()
    return TokenGerado(token_id=registro.id, valor=valor, expira_em=expira_em)


def consumir_token(
    db: Session, *, valor: str, tipo: TipoTokenAutenticacao
) -> TokenAutenticacao:
    """Valida o token e marca `usado_em`. Levanta `TokenInvalido` com mensagem pronta para exibição."""
    registro = (
        db.query(TokenAutenticacao)
        .filter(TokenAutenticacao.token_hash == _hash_token(valor), TokenAutenticacao.tipo == tipo)
        .one_or_none()
    )
    if registro is None:
        raise TokenInvalido(MSG_LINK_INVALIDO)
    if registro.usado_em is not None:
        raise TokenInvalido(MSG_LINK_JA_UTILIZADO)

    agora = datetime.now(timezone.utc)
    expira_em = registro.expira_em
    if expira_em.tzinfo is None:
        expira_em = expira_em.replace(tzinfo=timezone.utc)
    if expira_em <= agora:
        raise TokenInvalido(MSG_LINK_EXPIRADO)

    registro.usado_em = agora
    db.flush()
    return registro
