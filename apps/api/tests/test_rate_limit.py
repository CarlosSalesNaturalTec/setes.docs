"""Teste de rate limiting (D6, task 2.9) — 11ª requisição no mesmo minuto/IP
recebe 429 em `/auth/login`."""

from __future__ import annotations

from app.db.models import PerfilUsuario, StatusUsuario, Usuario
from app.security.senha import hash_senha


def test_decima_primeira_tentativa_de_login_no_minuto_recebe_429(client, db):
    usuario = Usuario(
        nome="Fulano",
        email="ratelimit@example.com",
        senha_hash=hash_senha("SenhaForte1"),
        perfil=PerfilUsuario.SERVIDOR,
        status=StatusUsuario.ATIVO,
    )
    db.add(usuario)
    db.commit()

    payload = {"email": "ratelimit@example.com", "senha": "errada"}
    respostas = [client.post("/auth/login", json=payload).status_code for _ in range(11)]

    # 3 falhas -> 401; a partir da 4ª a conta já está bloqueada -> 403;
    # a 11ª chamada no mesmo minuto/IP é barrada pelo rate limit -> 429.
    assert respostas[:3] == [401, 401, 401]
    assert respostas[3:10] == [403] * 7
    assert respostas[10] == 429
