"""Regras de vínculo organizacional do usuário (change
setores-e-cadastro-usuario, design.md D2)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Setor

MSG_SETOR_OBRIGATORIO_SERVIDOR = (
    "Setor é obrigatório para o perfil Servidor — selecione um setor da unidade do usuário."
)
MSG_SETOR_INEXISTENTE = "Setor inválido ou inativo — selecione um setor ativo da unidade."
MSG_SETOR_DE_OUTRA_UNIDADE = (
    "O setor informado não pertence à unidade do usuário — selecione um setor da própria unidade."
)


def validar_vinculo_setor(
    db: Session,
    *,
    perfil: PerfilUsuario,
    unidade_id: uuid.UUID | None,
    setor_id: uuid.UUID | None,
    exigir_ativo: bool = True,
) -> None:
    """Valida o par (unidade, setor) de um usuário — no cadastro e em **toda**
    edição, inclusive transferência de unidade (D2).

    Regras:
    - Servidor SHALL ter setor; Gestor e Administrador podem não ter.
    - O setor SHALL pertencer à unidade do próprio usuário.

    Um setor de outra unidade é **dado inconsistente** (422), não acesso negado
    — não é questão de permissão: Setor não é fronteira de autorização.
    """
    if setor_id is None:
        if perfil == PerfilUsuario.SERVIDOR:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=MSG_SETOR_OBRIGATORIO_SERVIDOR,
            )
        return

    setor = db.get(Setor, setor_id)
    if setor is None or (exigir_ativo and not setor.ativo):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_SETOR_INEXISTENTE
        )

    if unidade_id is None or setor.unidade_id != unidade_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=MSG_SETOR_DE_OUTRA_UNIDADE
        )
