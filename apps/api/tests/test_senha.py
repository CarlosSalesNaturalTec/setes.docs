"""Teste de app/security/senha.py (task 2.2 — obrigatório, toca dado pessoal)."""

import pytest

from app.security.senha import hash_senha, senha_atende_complexidade, verificar_senha


def test_hash_de_duas_chamadas_para_mesma_senha_difere():
    h1 = hash_senha("SenhaForte@123")
    h2 = hash_senha("SenhaForte@123")
    assert h1 != h2  # salt aleatório por chamada


def test_verificar_senha_confirma_ambos_os_hashes():
    h1 = hash_senha("SenhaForte@123")
    h2 = hash_senha("SenhaForte@123")
    assert verificar_senha("SenhaForte@123", h1)
    assert verificar_senha("SenhaForte@123", h2)


def test_verificar_senha_rejeita_senha_errada():
    h = hash_senha("SenhaForte@123")
    assert not verificar_senha("SenhaErrada@123", h)


@pytest.mark.parametrize(
    "senha,esperado",
    [
        ("SenhaForte1", True),
        ("curta1A", False),  # menos de 8 caracteres
        ("semmaiuscula1", False),  # sem maiúscula
        ("SEMMINUSCULA1", False),  # sem minúscula
        ("SemNumeroAqui", False),  # sem número
    ],
)
def test_senha_atende_complexidade(senha: str, esperado: bool):
    assert senha_atende_complexidade(senha) is esperado
