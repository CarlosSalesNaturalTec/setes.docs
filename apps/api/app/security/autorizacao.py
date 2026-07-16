"""Autorização por perfil e unidade (D4).

Composição: `get_current_user` → `require_perfil(*perfis)` → `require_acesso_unidade`.
Toda rejeição grava uma linha em `log_seguranca` (tipo_evento=`acesso_negado`),
cobrindo o cenário de acesso indevido do PRD (US 1.4 Cen.2).
"""

from __future__ import annotations

import uuid
from typing import Annotated, Callable

from fastapi import Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import LogSeguranca, PerfilUsuario, TipoEventoLog, Usuario, UnidadeGestor
from app.db.session import get_db
from app.security.sessao import SessaoInvalida, validar_e_renovar_sessao


def _extrair_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado."
        )
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    request: Request,
    response: Response,
    authorization: Annotated[str | None, Header()] = None,
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> Usuario:
    """Valida a sessão (JWT + `sessao`) e retorna o `Usuario` autenticado.

    Em toda chamada válida, reemite o JWT (sliding window, D1) no header
    `X-Renewed-Token` — o frontend troca o token silenciosamente.
    """
    token = _extrair_token(authorization)
    try:
        sessao_ativa = validar_e_renovar_sessao(db, token=token, chave_jwt=settings.jwt_signing_key)
    except SessaoInvalida as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    usuario = db.get(Usuario, sessao_ativa.usuario_id)
    if usuario is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")

    response.headers["X-Renewed-Token"] = sessao_ativa.token
    db.commit()

    request.state.jti = sessao_ativa.jti
    request.state.sessao_exp = sessao_ativa.exp
    return usuario


def registrar_acesso_negado(
    db: Session, *, usuario: Usuario | None, rota: str, contexto: dict | None = None
) -> None:
    db.add(
        LogSeguranca(
            usuario_id=usuario.id if usuario else None,
            tipo_evento=TipoEventoLog.ACESSO_NEGADO,
            contexto={"rota": rota, **(contexto or {})},
        )
    )
    db.commit()


def require_perfil(*perfis: PerfilUsuario) -> Callable[..., Usuario]:
    """Dependência FastAPI: exige que o usuário autenticado tenha um dos `perfis`."""

    def _dependency(
        request: Request,
        usuario: Annotated[Usuario, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> Usuario:
        if usuario.perfil not in perfis:
            registrar_acesso_negado(
                db,
                usuario=usuario,
                rota=request.url.path,
                contexto={
                    "perfil_exigido": [p.value for p in perfis],
                    "perfil_atual": usuario.perfil.value,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado para o seu perfil."
            )
        return usuario

    return _dependency


def require_pode_auditar(
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    """Dependência FastAPI (D6): exige `usuario.pode_auditar = true`.

    A permissão de auditoria é ortogonal ao perfil (Servidor/Gestor/
    Administrador) — não reutiliza `require_perfil`.
    """
    if not usuario.pode_auditar:
        registrar_acesso_negado(db, usuario=usuario, rota=request.url.path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado — permissão de auditoria necessária.",
        )
    return usuario


def tem_acesso_a_unidade(db: Session, *, usuario: Usuario, unidade_id: uuid.UUID) -> bool:
    """Servidor: só a própria unidade. Gestor: unidades geridas. Administrador: qualquer uma."""
    if usuario.perfil == PerfilUsuario.ADMINISTRADOR:
        return True
    if usuario.perfil == PerfilUsuario.SERVIDOR:
        return usuario.unidade_id == unidade_id
    if usuario.perfil == PerfilUsuario.GESTOR:
        return (
            db.query(UnidadeGestor)
            .filter(UnidadeGestor.gestor_id == usuario.id, UnidadeGestor.unidade_id == unidade_id)
            .first()
            is not None
        )
    return False


def require_acesso_unidade(
    db: Session, *, usuario: Usuario, unidade_id: uuid.UUID, rota: str
) -> None:
    """Levanta 403 (e grava `log_seguranca`) se `usuario` não tem acesso a `unidade_id`.

    Chamada explicitamente dentro dos endpoints — `unidade_id` normalmente vem
    do corpo da requisição (ex.: cadastro de usuário), não de um path param.
    """
    if not tem_acesso_a_unidade(db, usuario=usuario, unidade_id=unidade_id):
        registrar_acesso_negado(
            db, usuario=usuario, rota=rota, contexto={"unidade_solicitada": str(unidade_id)}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a esta unidade."
        )
