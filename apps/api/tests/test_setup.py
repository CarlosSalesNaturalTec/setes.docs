"""Teste de POST /setup e GET /setup/status (task 3.4 — obrigatório, Administrador root)."""

from __future__ import annotations

import threading

PAYLOAD = {
    "administrador": {"nome": "Root Admin", "email": "admin@example.com", "senha": "SenhaForte1"},
    "unidade": {"nome": "Unidade Central", "sigla": "UC"},
}


def test_setup_em_banco_vazio_cria_administrador_e_unidade(client, db, monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        "app.routers.setup.enqueue_email_seguro",
        lambda message, *, event_id, config: chamadas.append(event_id) or True,
    )

    resp = client.post("/setup", json=PAYLOAD)

    assert resp.status_code == 201
    body = resp.json()
    assert body["usuario_id"]
    assert body["unidade_id"]
    # e-mail de confirmação enfileirado após o commit, com o event_id do design (D10)
    assert chamadas == [f"setup-confirmacao:{body['usuario_id']}"]

    status_resp = client.get("/setup/status")
    assert status_resp.json() == {"inicializado": True}


def test_setup_apos_inicializado_retorna_409(client, db, monkeypatch):
    monkeypatch.setattr("app.routers.setup.enqueue_email_seguro", lambda *a, **k: True)

    primeiro = client.post("/setup", json=PAYLOAD)
    assert primeiro.status_code == 201

    segundo = client.post("/setup", json=PAYLOAD)
    assert segundo.status_code == 409


def test_status_em_banco_vazio_retorna_false(client, db):
    resp = client.get("/setup/status")
    assert resp.json() == {"inicializado": False}


def test_senha_fraca_e_rejeitada(client, db):
    payload = {**PAYLOAD, "administrador": {**PAYLOAD["administrador"], "senha": "fraca"}}
    resp = client.post("/setup", json=payload)
    assert resp.status_code == 422


def test_corrida_de_duas_requisicoes_simultaneas_produz_um_unico_administrador(
    client, db, monkeypatch
):
    monkeypatch.setattr("app.routers.setup.enqueue_email_seguro", lambda *a, **k: True)

    resultados: list[int] = []
    lock = threading.Lock()

    def _post() -> None:
        resp = client.post("/setup", json=PAYLOAD)
        with lock:
            resultados.append(resp.status_code)

    t1 = threading.Thread(target=_post)
    t2 = threading.Thread(target=_post)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert sorted(resultados) == [201, 409]

    from app.db.models import PerfilUsuario, Usuario

    admins = db.query(Usuario).filter(Usuario.perfil == PerfilUsuario.ADMINISTRADOR).all()
    assert len(admins) == 1
