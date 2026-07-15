"""Builders compartilhados dos testes de processo/workflow (Épico 2)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models import (
    PerfilUsuario,
    Roteiro,
    RoteiroEtapa,
    StatusUsuario,
    TipoProcesso,
    Unidade,
    UnidadeGestor,
    Usuario,
)
from app.security.senha import hash_senha

SENHA = "SenhaForte1"

# CPF/CNPJ válidos (dígitos verificadores corretos) para os testes.
CPF_VALIDO = "529.982.247-25"
CPF_INVALIDO = "529.982.247-24"
CNPJ_VALIDO = "11.222.333/0001-81"
CNPJ_INVALIDO = "11.222.333/0001-80"


def unidade(db: Session, nome: str = "COFIN") -> Unidade:
    u = Unidade(nome=nome, sigla=nome[:5].upper(), ativo=True)
    db.add(u)
    db.commit()
    return u


def usuario(
    db: Session, *, perfil=PerfilUsuario.SERVIDOR, unidade_id=None, email: str | None = None
) -> Usuario:
    u = Usuario(
        nome="Fulano",
        email=email or f"{uuid.uuid4()}@example.com",
        senha_hash=hash_senha(SENHA),
        perfil=perfil,
        status=StatusUsuario.ATIVO,
        unidade_id=unidade_id,
    )
    db.add(u)
    db.commit()
    return u


def gestor_de(db: Session, *unidades: Unidade, email: str | None = None) -> Usuario:
    g = usuario(db, perfil=PerfilUsuario.GESTOR, email=email)
    for u in unidades:
        db.add(UnidadeGestor(gestor_id=g.id, unidade_id=u.id))
    db.commit()
    return g


def tipo_com_roteiro(db: Session, *unidades: Unidade, nome: str = "Licitação") -> TipoProcesso:
    """Cria um tipo de processo e um roteiro vigente com as `unidades` na ordem dada."""
    tipo = TipoProcesso(nome=f"{nome}-{uuid.uuid4().hex[:6]}", ativo=True)
    db.add(tipo)
    db.commit()
    roteiro = Roteiro(tipo_processo_id=tipo.id, vigente=True)
    db.add(roteiro)
    db.commit()
    for ordem, u in enumerate(unidades, start=1):
        db.add(RoteiroEtapa(roteiro_id=roteiro.id, unidade_id=u.id, ordem=ordem))
    db.commit()
    return tipo


def tipo_sem_roteiro(db: Session, nome: str = "SemRoteiro") -> TipoProcesso:
    tipo = TipoProcesso(nome=f"{nome}-{uuid.uuid4().hex[:6]}", ativo=True)
    db.add(tipo)
    db.commit()
    return tipo


def login(client, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "senha": SENHA})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
