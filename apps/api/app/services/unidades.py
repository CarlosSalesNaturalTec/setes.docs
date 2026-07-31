"""Serviços de unidade administrativa e de setor (seção 8 de tasks.md;
change setores-e-cadastro-usuario, design.md D1/D3)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import PerfilUsuario, Setor, StatusUsuario, Usuario
from app.services.processo_consulta import contar_em_andamento

MSG_SETOR_NAO_ENCONTRADO = "Setor não encontrado."
MSG_UNIDADE_NAO_ENCONTRADA = "Unidade não encontrada."


def contar_processos_em_andamento(db: Session, unidade_id: uuid.UUID) -> int:
    """Quantos processos em andamento (Aberto/Em Tramitação) a unidade possui
    (US 8.1 Cen.3). Agora que a tabela `processo` existe, a contagem é efetiva
    (proposal — fecha a pendência de `unidades-administrativas`)."""
    return contar_em_andamento(db, unidade_id)


# --- Setor (D1, D3) ---------------------------------------------------------


def _msg_sigla_duplicada(sigla: str) -> str:
    return f"Já existe um setor com a sigla '{sigla}' nesta unidade."


def _msg_servidores_ativos(quantidade: int) -> str:
    return (
        f"Este setor possui {quantidade} servidor(es) ativo(s) vinculado(s). "
        "Transfira-os para outro setor antes de desativá-lo."
    )


def obter_setor(db: Session, setor_id: uuid.UUID) -> Setor:
    setor = db.get(Setor, setor_id)
    if setor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_SETOR_NAO_ENCONTRADO
        )
    return setor


def listar_setores(db: Session, unidade_id: uuid.UUID, *, apenas_ativos: bool = False) -> list[Setor]:
    query = db.query(Setor).filter(Setor.unidade_id == unidade_id)
    if apenas_ativos:
        query = query.filter(Setor.ativo.is_(True))
    return query.order_by(Setor.nome).all()


def _sigla_ja_usada(
    db: Session, *, unidade_id: uuid.UUID, sigla: str, exceto_id: uuid.UUID | None = None
) -> bool:
    query = db.query(Setor).filter(Setor.unidade_id == unidade_id, Setor.sigla == sigla)
    if exceto_id is not None:
        query = query.filter(Setor.id != exceto_id)
    return query.first() is not None


def cadastrar_setor(db: Session, *, unidade_id: uuid.UUID, nome: str, sigla: str) -> Setor:
    """Cadastra um setor ativo na unidade. A sigla é única *dentro* da unidade
    (D1) — a mesma sigla em outra unidade é aceita."""
    nome, sigla = nome.strip(), sigla.strip()
    if _sigla_ja_usada(db, unidade_id=unidade_id, sigla=sigla):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=_msg_sigla_duplicada(sigla)
        )

    setor = Setor(unidade_id=unidade_id, nome=nome, sigla=sigla, ativo=True)
    db.add(setor)
    db.commit()
    return setor


def editar_setor(
    db: Session, *, setor_id: uuid.UUID, nome: str | None, sigla: str | None
) -> Setor:
    setor = obter_setor(db, setor_id)

    if sigla is not None:
        sigla = sigla.strip()
        if _sigla_ja_usada(db, unidade_id=setor.unidade_id, sigla=sigla, exceto_id=setor.id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=_msg_sigla_duplicada(sigla),
            )
        setor.sigla = sigla
    if nome is not None:
        setor.nome = nome.strip()

    db.commit()
    return setor


def contar_servidores_ativos_do_setor(db: Session, setor_id: uuid.UUID) -> int:
    return (
        db.query(Usuario)
        .filter(
            Usuario.setor_id == setor_id,
            Usuario.perfil == PerfilUsuario.SERVIDOR,
            Usuario.status != StatusUsuario.INATIVO,
        )
        .count()
    )


def desativar_setor(db: Session, setor_id: uuid.UUID) -> Setor:
    """Desativa (nunca exclui, D3). Bloqueado enquanto houver Servidor ativo
    vinculado — a mensagem informa a contagem."""
    setor = obter_setor(db, setor_id)

    vinculados = contar_servidores_ativos_do_setor(db, setor.id)
    if vinculados > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_msg_servidores_ativos(vinculados),
        )

    setor.ativo = False
    db.commit()
    return setor


def reativar_setor(db: Session, setor_id: uuid.UUID) -> Setor:
    """Reativação é ação administrativa explícita, item a item (D3); idempotente."""
    setor = obter_setor(db, setor_id)
    setor.ativo = True
    db.commit()
    return setor


def desativar_setores_da_unidade(db: Session, unidade_id: uuid.UUID) -> int:
    """Cascata de contenção ao desativar a Unidade (D3): desativa todos os
    setores ativos dela e devolve quantos foram afetados. A reativação da
    unidade NÃO desfaz esta cascata — cada setor é reativado explicitamente.
    Sem commit: o chamador commita junto com a desativação da unidade."""
    return (
        db.query(Setor)
        .filter(Setor.unidade_id == unidade_id, Setor.ativo.is_(True))
        .update({"ativo": False}, synchronize_session=False)
    )
