"""Tipos de processo e roteiros de tramitação (seção 9 de tasks.md) — US 8.2."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Roteiro, RoteiroEtapa, TipoProcesso, Unidade, Usuario
from app.db.session import get_db
from app.schemas.tipos_processo import (
    AtualizarRoteiroRequest,
    CriarTipoProcessoRequest,
    EtapaRoteiroResponse,
    RoteiroResponse,
    TipoProcessoResponse,
    TipoProcessoUpdate,
)
from app.security.autorizacao import get_current_user, require_perfil
from app.services.roteiros import obter_roteiro_vigente

router = APIRouter(prefix="/tipos-processo", tags=["tipos-processo"])

MSG_ROTEIRO_VAZIO = "O roteiro deve conter ao menos uma unidade"
MSG_NOME_DUPLICADO = "Já existe um tipo de processo com este nome"

_require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)


def _roteiro_response(roteiro: Roteiro) -> RoteiroResponse:
    return RoteiroResponse(
        id=str(roteiro.id),
        vigente=roteiro.vigente,
        etapas=[
            EtapaRoteiroResponse(unidade_id=str(e.unidade_id), ordem=e.ordem)
            for e in sorted(roteiro.etapas, key=lambda e: e.ordem)
        ],
    )


def _validar_unidades(db: Session, unidade_ids: list[str]) -> list[uuid.UUID]:
    if not unidade_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_ROTEIRO_VAZIO)

    ids = [uuid.UUID(u) for u in unidade_ids]
    encontradas = db.query(Unidade.id).filter(Unidade.id.in_(ids)).count()
    if encontradas != len(set(ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unidade inválida no roteiro."
        )
    return ids


@router.get("", response_model=list[TipoProcessoResponse])
def listar_tipos_processo(
    _usuario: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TipoProcessoResponse]:
    """Catálogo de tipos de processo com o roteiro vigente de cada um.

    Leitura aberta a qualquer usuário autenticado (Servidor precisa listar o
    catálogo para criar processo — US 2.1); cadastro/edição de roteiro
    permanecem admin-only (US 8.2, `_require_admin` abaixo)."""
    tipos = db.query(TipoProcesso).order_by(TipoProcesso.nome).all()
    resultado = []
    for tipo in tipos:
        vigente = obter_roteiro_vigente(db, tipo.id)
        if vigente is None:
            continue  # nunca deveria acontecer (todo tipo nasce com um roteiro), defensivo
        resultado.append(
            TipoProcessoResponse(
                id=str(tipo.id),
                nome=tipo.nome,
                ativo=tipo.ativo,
                roteiro=_roteiro_response(vigente),
                prazo_anonimizacao_anos=tipo.prazo_anonimizacao_anos,
            )
        )
    return resultado


@router.post("", response_model=TipoProcessoResponse, status_code=status.HTTP_201_CREATED)
def criar_tipo_processo(
    payload: CriarTipoProcessoRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> TipoProcessoResponse:
    if db.query(TipoProcesso).filter(TipoProcesso.nome == payload.nome).first() is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_NOME_DUPLICADO)

    unidade_ids = _validar_unidades(db, payload.unidade_ids)

    tipo = TipoProcesso(nome=payload.nome, ativo=True)
    db.add(tipo)
    db.flush()

    roteiro = Roteiro(tipo_processo_id=tipo.id, vigente=True)
    db.add(roteiro)
    db.flush()
    for ordem, unidade_id in enumerate(unidade_ids, start=1):
        db.add(RoteiroEtapa(roteiro_id=roteiro.id, unidade_id=unidade_id, ordem=ordem))
    db.commit()
    db.refresh(roteiro)

    return TipoProcessoResponse(
        id=str(tipo.id),
        nome=tipo.nome,
        ativo=tipo.ativo,
        roteiro=_roteiro_response(roteiro),
        prazo_anonimizacao_anos=tipo.prazo_anonimizacao_anos,
    )


@router.patch("/{tipo_processo_id}", response_model=TipoProcessoResponse)
def atualizar_tipo_processo(
    tipo_processo_id: uuid.UUID,
    payload: TipoProcessoUpdate,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> TipoProcessoResponse:
    """US 10.3 Cen.2/3 — configura o prazo de anonimização LGPD (Admin-only);
    não retroativo (aplica-se só à avaliação seguinte da rotina/atendimento)."""
    tipo = db.get(TipoProcesso, tipo_processo_id)
    if tipo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de processo não encontrado.")

    tipo.prazo_anonimizacao_anos = payload.prazo_anonimizacao_anos
    db.commit()
    db.refresh(tipo)

    vigente = obter_roteiro_vigente(db, tipo.id)
    return TipoProcessoResponse(
        id=str(tipo.id),
        nome=tipo.nome,
        ativo=tipo.ativo,
        roteiro=_roteiro_response(vigente),
        prazo_anonimizacao_anos=tipo.prazo_anonimizacao_anos,
    )


@router.put("/{tipo_processo_id}/roteiro", response_model=RoteiroResponse)
def atualizar_roteiro(
    tipo_processo_id: uuid.UUID,
    payload: AtualizarRoteiroRequest,
    _admin: Annotated[Usuario, Depends(_require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> RoteiroResponse:
    """US 8.2 Cen.2 — cria nova versão vigente; a anterior fica congelada
    (`vigente=false`) e suas `roteiro_etapa` nunca são alteradas — processos já
    criados sob ela mantêm o roteiro do momento de sua criação.
    """
    tipo = db.get(TipoProcesso, tipo_processo_id)
    if tipo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de processo não encontrado.")

    unidade_ids = _validar_unidades(db, payload.unidade_ids)

    vigente_atual = obter_roteiro_vigente(db, tipo_processo_id)
    if vigente_atual is not None:
        vigente_atual.vigente = False
        db.flush()

    novo_roteiro = Roteiro(tipo_processo_id=tipo_processo_id, vigente=True)
    db.add(novo_roteiro)
    db.flush()
    for ordem, unidade_id in enumerate(unidade_ids, start=1):
        db.add(RoteiroEtapa(roteiro_id=novo_roteiro.id, unidade_id=unidade_id, ordem=ordem))
    db.commit()
    db.refresh(novo_roteiro)

    return _roteiro_response(novo_roteiro)
