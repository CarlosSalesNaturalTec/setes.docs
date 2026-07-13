"""Sessão (D1): JWT + registro server-side em `sessao`.

Cada login cria uma linha em `sessao` e emite um JWT (jti=id da sessão). Toda
rota autenticada, além da assinatura/`exp` do JWT (checados por `decodificar_jwt`),
consulta `sessao` por `jti`: rejeita se `revogada_em` estiver preenchido ou se
`ultima_atividade` estiver a mais de `TIMEOUT_INATIVIDADE` — esse segundo
check é o que sustenta logout imediato e expiração por inatividade mesmo que
o `exp` do JWT ainda não tenha vencido (ex.: revogação após emissão do token).
Em toda validação bem-sucedida, `ultima_atividade` é atualizada e um novo JWT
é emitido com `exp = now() + TIMEOUT_INATIVIDADE` (sliding window).

Timeout de inatividade (30min) é constante hardcoded — parametrização é US 8.5,
fora de escopo deste change (design.md — Non-Goals).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import Sessao
from app.security.jwt import TokenInvalido, criar_jwt, decodificar_jwt

TIMEOUT_INATIVIDADE = timedelta(minutes=30)


class SessaoInvalida(Exception):
    """Sessão revogada, expirada por inatividade, ou token inválido."""


@dataclass(frozen=True)
class SessaoAtiva:
    sessao_id: uuid.UUID
    usuario_id: uuid.UUID
    jti: uuid.UUID
    token: str
    exp: datetime


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _com_tz(momento: datetime) -> datetime:
    return momento if momento.tzinfo is not None else momento.replace(tzinfo=timezone.utc)


def criar_sessao(
    db: Session,
    *,
    usuario_id: uuid.UUID,
    chave_jwt: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> SessaoAtiva:
    agora = _agora()
    jti = uuid.uuid4()
    sessao = Sessao(
        usuario_id=usuario_id,
        jti=jti,
        criada_em=agora,
        ultima_atividade=agora,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(sessao)
    db.flush()

    exp = agora + TIMEOUT_INATIVIDADE
    token = criar_jwt(usuario_id=usuario_id, jti=jti, expira_em=exp, chave=chave_jwt)
    return SessaoAtiva(sessao_id=sessao.id, usuario_id=usuario_id, jti=jti, token=token, exp=exp)


def validar_e_renovar_sessao(db: Session, *, token: str, chave_jwt: str) -> SessaoAtiva:
    try:
        claims = decodificar_jwt(token, chave=chave_jwt)
    except TokenInvalido as exc:
        raise SessaoInvalida("Sessão inválida.") from exc

    jti = uuid.UUID(claims["jti"])
    usuario_id = uuid.UUID(claims["sub"])

    sessao = db.query(Sessao).filter(Sessao.jti == jti).one_or_none()
    if sessao is None or sessao.revogada_em is not None:
        raise SessaoInvalida("Sessão expirada por inatividade.")

    agora = _agora()
    if agora - _com_tz(sessao.ultima_atividade) > TIMEOUT_INATIVIDADE:
        raise SessaoInvalida("Sessão expirada por inatividade.")

    sessao.ultima_atividade = agora
    db.flush()

    exp = agora + TIMEOUT_INATIVIDADE
    novo_token = criar_jwt(usuario_id=usuario_id, jti=jti, expira_em=exp, chave=chave_jwt)
    return SessaoAtiva(sessao_id=sessao.id, usuario_id=usuario_id, jti=jti, token=novo_token, exp=exp)


def revogar_sessao(db: Session, *, jti: uuid.UUID) -> None:
    sessao = db.query(Sessao).filter(Sessao.jti == jti).one_or_none()
    if sessao is not None and sessao.revogada_em is None:
        sessao.revogada_em = _agora()
        db.flush()
