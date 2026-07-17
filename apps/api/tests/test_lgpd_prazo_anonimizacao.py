"""Testes obrigatórios do prazo de anonimização LGPD por tipo de processo
(US 10.3 Cen.2, tasks 6.2/6.3)."""

from __future__ import annotations

import pytest

from app.db.models import PerfilUsuario
from tests.helpers_processo import auth, login, tipo_com_roteiro, unidade, usuario


def test_configurar_prazo_valido_persiste_valor(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin-prazo@ex.com")
    token = login(client, admin.email)

    resp = client.patch(
        f"/tipos-processo/{tipo.id}", json={"prazo_anonimizacao_anos": 7}, headers=auth(token)
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["prazo_anonimizacao_anos"] == 7


@pytest.mark.parametrize("valor", [0, -1])
def test_valor_invalido_e_rejeitado(client, db, valor):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    admin = usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email=f"admin-prazo-inv{valor}@ex.com")
    token = login(client, admin.email)

    resp = client.patch(
        f"/tipos-processo/{tipo.id}", json={"prazo_anonimizacao_anos": valor}, headers=auth(token)
    )

    assert resp.status_code == 422


@pytest.mark.parametrize("perfil", [PerfilUsuario.SERVIDOR, PerfilUsuario.GESTOR])
def test_acesso_negado_nao_admin(client, db, perfil):
    cofin = unidade(db, "COFIN")
    tipo = tipo_com_roteiro(db, cofin)
    nao_admin = usuario(db, perfil=perfil, unidade_id=cofin.id, email=f"naoadmin-prazo-{perfil.value}@ex.com")
    token = login(client, nao_admin.email)

    resp = client.patch(
        f"/tipos-processo/{tipo.id}", json={"prazo_anonimizacao_anos": 3}, headers=auth(token)
    )

    assert resp.status_code == 403
    db.refresh(tipo)
    assert tipo.prazo_anonimizacao_anos == 5
