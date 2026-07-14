"""Autenticação — login, sessão, logout (seção 4 de tasks.md).

Bloqueio por tentativas (D5): 3 falhas consecutivas bloqueiam a conta por 30
minutos (`usuario.bloqueado_ate`). Durante o bloqueio, qualquer tentativa —
mesmo com senha correta — é rejeitada sem alterar o contador nem reiniciar o
timer (PRD US 1.3 Cen.2b). Após o bloqueio expirar, a próxima tentativa
retoma normalmente: sucesso zera o contador (Cen.4), falha reinicia a
contagem do zero (a penalidade anterior já foi cumprida).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import SenhaHistorico, StatusUsuario, TipoTokenAutenticacao, Usuario
from app.db.session import get_db
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.rate_limit import RATE_LIMIT_AUTH_PUBLICO, limiter
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    MensagemResponse,
    PrimeiroAcessoRequest,
    RecuperarSenhaRequest,
    RedefinirSenhaRequest,
    TrocarSenhaRequest,
    UsuarioResumo,
)
from app.security.autorizacao import get_current_user
from app.security.senha import MENSAGEM_COMPLEXIDADE, hash_senha, senha_atende_complexidade, verificar_senha
from app.security.sessao import criar_sessao, revogar_sessao
from app.services.tokens import TokenInvalido, consumir_token, gerar_token

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_TENTATIVAS_LOGIN = 3
DURACAO_BLOQUEIO = timedelta(minutes=30)

MSG_CREDENCIAIS_INVALIDAS = "Credenciais inválidas."
MSG_CONTA_DESATIVADA = "Conta desativada. Entre em contato com o Administrador do sistema."
MSG_SENHA_ATUAL_INCORRETA = "Senha atual incorreta"
MSG_SENHA_REUTILIZADA = "A nova senha não pode ser igual à senha atual ou às 6 senhas anteriores"
HISTORICO_SENHAS_VERIFICADAS = 6


def _com_tz(momento: datetime) -> datetime:
    return momento if momento.tzinfo is not None else momento.replace(tzinfo=timezone.utc)


@router.post("/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMIT_AUTH_PUBLICO)
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).one_or_none()

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_CREDENCIAIS_INVALIDAS)

    if usuario.status == StatusUsuario.INATIVO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MSG_CONTA_DESATIVADA)

    agora = datetime.now(timezone.utc)
    bloqueio_ativo = usuario.bloqueado_ate is not None and _com_tz(usuario.bloqueado_ate) > agora
    if bloqueio_ativo:
        restante = _com_tz(usuario.bloqueado_ate) - agora
        minutos = max(1, int(restante.total_seconds() // 60) + 1)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Conta bloqueada temporariamente. Tente novamente em {minutos} minuto(s).",
        )

    senha_correta = verificar_senha(payload.senha, usuario.senha_hash)
    if not senha_correta:
        if usuario.bloqueado_ate is not None and _com_tz(usuario.bloqueado_ate) <= agora:
            usuario.tentativas_login_falhas = 0  # penalidade anterior já cumprida
        usuario.tentativas_login_falhas += 1
        if usuario.tentativas_login_falhas >= MAX_TENTATIVAS_LOGIN:
            usuario.bloqueado_ate = agora + DURACAO_BLOQUEIO
            db.commit()
            enqueue_email_seguro(
                EmailMessage(
                    to=usuario.email,
                    subject="SETES.DOCS — alerta de tentativas de login",
                    body=(
                        f"Olá {usuario.nome}, detectamos 3 tentativas de login incorretas na sua "
                        "conta. Ela foi bloqueada temporariamente por 30 minutos."
                    ),
                ),
                event_id=f"alerta-bloqueio:{usuario.id}:{int(agora.timestamp())}",
                config=config_from_settings(settings),
            )
        else:
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_CREDENCIAIS_INVALIDAS)

    usuario.tentativas_login_falhas = 0
    usuario.bloqueado_ate = None
    db.commit()

    sessao_ativa = criar_sessao(
        db,
        usuario_id=usuario.id,
        chave_jwt=settings.jwt_signing_key,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    return LoginResponse(token=sessao_ativa.token, exp=sessao_ativa.exp, usuario=UsuarioResumo.de(usuario))


@router.post("/logout", response_model=MensagemResponse)
def logout(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    _usuario: Annotated[Usuario, Depends(get_current_user)],
) -> MensagemResponse:
    jti: uuid.UUID = request.state.jti
    revogar_sessao(db, jti=jti)
    db.commit()
    return MensagemResponse(mensagem="Sessão encerrada.")


@router.get("/me", response_model=MeResponse)
def me(
    request: Request,
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> MeResponse:
    return MeResponse(usuario=UsuarioResumo.de(usuario), exp=request.state.sessao_exp)


@router.post("/primeiro-acesso/{token}", response_model=LoginResponse)
@limiter.limit(RATE_LIMIT_AUTH_PUBLICO)
def primeiro_acesso(
    request: Request,
    token: str,
    payload: PrimeiroAcessoRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """PRD US 1.6 Cen.1 — senha aceita, usuário é autenticado e status vira Ativo."""
    if not senha_atende_complexidade(payload.senha):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MENSAGEM_COMPLEXIDADE
        )

    try:
        registro = consumir_token(db, valor=token, tipo=TipoTokenAutenticacao.PRIMEIRO_ACESSO)
    except TokenInvalido as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    usuario = db.get(Usuario, registro.usuario_id)
    usuario.senha_hash = hash_senha(payload.senha)
    usuario.status = StatusUsuario.ATIVO
    db.commit()

    sessao_ativa = criar_sessao(
        db,
        usuario_id=usuario.id,
        chave_jwt=settings.jwt_signing_key,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    return LoginResponse(token=sessao_ativa.token, exp=sessao_ativa.exp, usuario=UsuarioResumo.de(usuario))


@router.post("/recuperar-senha", response_model=MensagemResponse)
@limiter.limit(RATE_LIMIT_AUTH_PUBLICO)
def recuperar_senha(
    request: Request,
    payload: RecuperarSenhaRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MensagemResponse:
    """PRD US 1.3 Cen.3/Cen.5 — nunca revela se o e-mail está cadastrado."""
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).one_or_none()

    if usuario is not None:
        gerado = gerar_token(db, usuario_id=usuario.id, tipo=TipoTokenAutenticacao.RECUPERACAO_SENHA)
        db.commit()
        link = f"{settings.frontend_base_url}/redefinir-senha/{gerado.valor}"
        enqueue_email_seguro(
            EmailMessage(
                to=usuario.email,
                subject="SETES.DOCS — recuperação de senha",
                body=(
                    f"Olá {usuario.nome}, use o link a seguir para redefinir sua senha "
                    f"(válido por 2 horas): {link}"
                ),
            ),
            event_id=f"recuperacao-senha:{gerado.token_id}",
            config=config_from_settings(settings),
        )

    return MensagemResponse(
        mensagem="Se o e-mail informado estiver cadastrado, um link de redefinição será enviado"
    )


@router.post("/redefinir-senha/{token}", response_model=MensagemResponse)
def redefinir_senha(
    token: str,
    payload: RedefinirSenhaRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MensagemResponse:
    """Zera bloqueio/tentativas na mesma transação (US 1.3 Cen.2c — desbloqueio automático)."""
    if not senha_atende_complexidade(payload.senha):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MENSAGEM_COMPLEXIDADE
        )

    try:
        registro = consumir_token(db, valor=token, tipo=TipoTokenAutenticacao.RECUPERACAO_SENHA)
    except TokenInvalido as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    usuario = db.get(Usuario, registro.usuario_id)
    usuario.senha_hash = hash_senha(payload.senha)
    usuario.tentativas_login_falhas = 0
    usuario.bloqueado_ate = None
    db.commit()

    return MensagemResponse(mensagem="Senha redefinida com sucesso.")


@router.post("/trocar-senha", response_model=MensagemResponse)
def trocar_senha(
    payload: TrocarSenhaRequest,
    usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MensagemResponse:
    """PRD US 1.7 — exige senha atual correta; impede reuso das últimas 6 senhas."""
    if not verificar_senha(payload.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_SENHA_ATUAL_INCORRETA
        )
    if not senha_atende_complexidade(payload.nova_senha):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MENSAGEM_COMPLEXIDADE
        )
    if verificar_senha(payload.nova_senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_SENHA_REUTILIZADA
        )

    historico = (
        db.query(SenhaHistorico)
        .filter(SenhaHistorico.usuario_id == usuario.id)
        .order_by(SenhaHistorico.criado_em.desc())
        .limit(HISTORICO_SENHAS_VERIFICADAS)
        .all()
    )
    for entrada in historico:
        if verificar_senha(payload.nova_senha, entrada.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_SENHA_REUTILIZADA
            )

    db.add(SenhaHistorico(usuario_id=usuario.id, senha_hash=usuario.senha_hash))
    usuario.senha_hash = hash_senha(payload.nova_senha)
    db.commit()

    return MensagemResponse(mensagem="Senha alterada com sucesso.")
