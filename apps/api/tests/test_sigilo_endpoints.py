"""Teste de permissão e acesso negado dos endpoints de sigilo (task 3.3 —
obrigatório: visibilidade por unidade/perfil, com cenário de acesso negado).
US 2.6 Cen.1/1b/2/3."""

from __future__ import annotations

from app.db.models import LogSeguranca, PerfilUsuario, TipoEventoLog
from tests.helpers_processo import auth, gestor_de, login, servidor_com_setor, tipo_processo, unidade, usuario


def _criar_processo(client, token, tipo):
    resp = client.post(
        "/processos",
        json={"assunto": "Sigilo", "tipo_processo_id": str(tipo.id), "prazo_dias": 10},
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_servidor_da_unidade_atual_marca_e_remove_sigilo(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv@ex.com")
    token = login(client, "serv@ex.com")
    proc = _criar_processo(client, token, tipo)

    resp = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["sigiloso"] is True

    resp = client.delete(f"/processos/{proc['id']}/sigilo", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["sigiloso"] is False


def test_gestor_da_unidade_marca_sigilo(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv2@ex.com")
    proc = _criar_processo(client, login(client, "serv2@ex.com"), tipo)

    gestor_de(db, cofin, email="gestor@ex.com")
    token_gestor = login(client, "gestor@ex.com")
    resp = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_gestor))
    assert resp.status_code == 200, resp.text
    assert resp.json()["sigiloso"] is True


def test_administrador_marca_sigilo_em_qualquer_unidade(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv3@ex.com")
    proc = _criar_processo(client, login(client, "serv3@ex.com"), tipo)

    usuario(db, perfil=PerfilUsuario.ADMINISTRADOR, email="admin@ex.com")
    token_admin = login(client, "admin@ex.com")
    resp = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_admin))
    assert resp.status_code == 200, resp.text
    assert resp.json()["sigiloso"] is True


def test_servidor_de_outra_unidade_recebe_acesso_negado_e_loga(client, db):
    cofin, ajur = unidade(db, "COFIN"), unidade(db, "AJUR")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv4@ex.com")
    proc = _criar_processo(client, login(client, "serv4@ex.com"), tipo)

    usuario(db, unidade_id=ajur.id, email="intruso@ex.com")
    token_intruso = login(client, "intruso@ex.com")

    resp = client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token_intruso))
    assert resp.status_code == 403
    assert "Acesso negado" in resp.json()["detail"]

    logs = (
        db.query(LogSeguranca)
        .filter(LogSeguranca.tipo_evento == TipoEventoLog.ACESSO_NEGADO)
        .all()
    )
    assert len(logs) >= 1


def test_processo_sigiloso_continua_no_kanban_da_unidade(client, db):
    cofin = unidade(db, "COFIN")
    tipo = tipo_processo(db)
    servidor_com_setor(db, cofin, email="serv5@ex.com")
    token = login(client, "serv5@ex.com")
    proc = _criar_processo(client, token, tipo)

    client.post(f"/processos/{proc['id']}/sigilo", headers=auth(token))

    resp = client.get("/processos", headers=auth(token))
    assert resp.status_code == 200
    cards = resp.json()["items"]
    card = next(c for c in cards if c["id"] == proc["id"])
    assert card["sigiloso"] is True
