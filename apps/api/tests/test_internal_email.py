"""Testes do endpoint interno OIDC-only (task 7.3, spec fila-notificacoes)."""

PAYLOAD = {
    "to": "user@example.com",
    "subject": "Prazo",
    "body": "Seu processo vence amanhã.",
    "event_id": "evt-1",
}


def test_rejeita_sem_token_oidc(client):
    # (a) chamada sem token OIDC é rejeitada com erro de autorização.
    resp = client.post("/internal/tasks/email", json=PAYLOAD)
    assert resp.status_code == 401


def test_rejeita_identidade_errada(client, monkeypatch):
    from app.security import oidc

    def _verify(token, audience):
        return {"email": "outra-sa@proj.iam.gserviceaccount.com", "email_verified": True}

    monkeypatch.setattr(oidc, "verify_google_oidc", _verify)
    resp = client.post(
        "/internal/tasks/email",
        json=PAYLOAD,
        headers={"Authorization": "Bearer qualquer"},
    )
    assert resp.status_code == 403


def test_falha_de_envio_loga_e_acka_sem_lancar(client, fake_valid_oidc, caplog):
    # (b) provedor falha (SENDGRID_API_KEY vazio) -> loga e retorna 200 (ACK), sem lançar.
    import logging

    with caplog.at_level(logging.ERROR, logger="setes.api"):
        resp = client.post(
            "/internal/tasks/email",
            json=PAYLOAD,
            headers={"Authorization": "Bearer valid-token"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"status": "acked"}
    assert any("email.falha" in r.message for r in caplog.records)


def test_envio_ok_acka(client, fake_valid_oidc, monkeypatch):
    # Caminho feliz: provedor aceita -> ACK.
    from app import main

    monkeypatch.setattr(main, "send_email", lambda *a, **k: None)
    resp = client.post(
        "/internal/tasks/email",
        json=PAYLOAD,
        headers={"Authorization": "Bearer valid-token"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "acked"}
