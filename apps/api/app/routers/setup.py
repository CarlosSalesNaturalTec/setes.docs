"""Inicialização do sistema (US 8.0) — D7.

`POST /setup` só produz efeito uma vez: `UPDATE sistema_config ... WHERE
inicializado=false RETURNING id` é atômico no nível de linha do Postgres, então
duas requisições concorrentes produzem exatamente um Administrador root
(task 3.1 aceite) — a segunda vê `inicializado=true` e recebe 409 sem criar nada.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import PerfilUsuario, StatusUsuario, Unidade, Usuario
from app.db.session import get_db
from app.email.provider import EmailMessage
from app.email.queue import config_from_settings, enqueue_email_seguro
from app.schemas.setup import SetupRequest, SetupResponse, SetupStatusResponse
from app.security.senha import MENSAGEM_COMPLEXIDADE, hash_senha, senha_atende_complexidade

router = APIRouter(tags=["setup"])


@router.post("/setup", response_model=SetupResponse, status_code=status.HTTP_201_CREATED)
def inicializar_sistema(
    payload: SetupRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SetupResponse:
    if not senha_atende_complexidade(payload.administrador.senha):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MENSAGEM_COMPLEXIDADE
        )

    resultado = db.execute(
        text(
            "UPDATE sistema_config SET inicializado = true "
            "WHERE id = 1 AND inicializado = false RETURNING id"
        )
    ).first()
    if resultado is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Sistema já inicializado"
        )

    unidade = Unidade(nome=payload.unidade.nome, sigla=payload.unidade.sigla, ativo=True)
    db.add(unidade)
    db.flush()

    admin = Usuario(
        nome=payload.administrador.nome,
        email=payload.administrador.email,
        senha_hash=hash_senha(payload.administrador.senha),
        perfil=PerfilUsuario.ADMINISTRADOR,
        status=StatusUsuario.ATIVO,
        unidade_id=None,
    )
    db.add(admin)
    db.flush()
    admin_id, unidade_id = admin.id, unidade.id

    db.commit()

    enqueue_email_seguro(
        EmailMessage(
            to=admin.email,
            subject="SETES.DOCS — sistema inicializado",
            body=f"Olá {admin.nome}, o sistema foi inicializado com sucesso. Você já pode fazer login.",
        ),
        event_id=f"setup-confirmacao:{admin_id}",
        config=config_from_settings(settings),
    )

    return SetupResponse(usuario_id=str(admin_id), unidade_id=str(unidade_id))


@router.get("/setup/status", response_model=SetupStatusResponse)
def status_inicializacao(db: Annotated[Session, Depends(get_db)]) -> SetupStatusResponse:
    inicializado = db.execute(
        text("SELECT inicializado FROM sistema_config WHERE id = 1")
    ).scalar()
    return SetupStatusResponse(inicializado=bool(inicializado))
