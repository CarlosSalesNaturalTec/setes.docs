"""Teste de app/security/autorizacao.py (task 2.7 — obrigatório, visibilidade
por unidade/perfil)."""

import uuid

import pytest
from fastapi import HTTPException

from app.db.models import (
    LogSeguranca,
    PerfilUsuario,
    StatusUsuario,
    TipoEventoLog,
    Unidade,
    UnidadeGestor,
    Usuario,
)
from app.security.autorizacao import require_acesso_unidade, tem_acesso_a_unidade


def _unidade(db, nome="Unidade X") -> Unidade:
    unidade = Unidade(nome=nome, sigla=nome[:3].upper(), ativo=True)
    db.add(unidade)
    db.commit()
    return unidade


def _usuario(db, perfil: PerfilUsuario, unidade_id=None) -> Usuario:
    usuario = Usuario(
        nome="Fulano",
        email=f"{uuid.uuid4()}@example.com",
        senha_hash="hash",
        perfil=perfil,
        status=StatusUsuario.ATIVO,
        unidade_id=unidade_id,
    )
    db.add(usuario)
    db.commit()
    return usuario


def test_administrador_acessa_qualquer_unidade(db):
    unidade = _unidade(db)
    admin = _usuario(db, PerfilUsuario.ADMINISTRADOR)
    assert tem_acesso_a_unidade(db, usuario=admin, unidade_id=unidade.id)


def test_servidor_so_acessa_a_propria_unidade(db):
    unidade_a = _unidade(db, "Unidade A")
    unidade_b = _unidade(db, "Unidade B")
    servidor = _usuario(db, PerfilUsuario.SERVIDOR, unidade_id=unidade_a.id)

    assert tem_acesso_a_unidade(db, usuario=servidor, unidade_id=unidade_a.id)
    assert not tem_acesso_a_unidade(db, usuario=servidor, unidade_id=unidade_b.id)


def test_gestor_so_acessa_unidades_geridas(db):
    unidade_a = _unidade(db, "Unidade A")
    unidade_b = _unidade(db, "Unidade B")
    gestor = _usuario(db, PerfilUsuario.GESTOR)
    db.add(UnidadeGestor(gestor_id=gestor.id, unidade_id=unidade_a.id))
    db.commit()

    assert tem_acesso_a_unidade(db, usuario=gestor, unidade_id=unidade_a.id)
    assert not tem_acesso_a_unidade(db, usuario=gestor, unidade_id=unidade_b.id)


def test_servidor_de_unidade_a_negado_em_recurso_da_unidade_b_e_log_gravado(db):
    unidade_a = _unidade(db, "Unidade A")
    unidade_b = _unidade(db, "Unidade B")
    servidor = _usuario(db, PerfilUsuario.SERVIDOR, unidade_id=unidade_a.id)

    with pytest.raises(HTTPException) as exc_info:
        require_acesso_unidade(db, usuario=servidor, unidade_id=unidade_b.id, rota="/teste")

    assert exc_info.value.status_code == 403
    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO)
        .all()
    )
    assert len(logs) == 1
    assert logs[0].usuario_id == servidor.id
    assert logs[0].contexto["unidade_solicitada"] == str(unidade_b.id)
