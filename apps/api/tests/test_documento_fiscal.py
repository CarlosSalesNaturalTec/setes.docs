"""Teste do validador de CPF/CNPJ (task 2.2 — obrigatório, toca dado pessoal)."""

from __future__ import annotations

from app.services.documento_fiscal import (
    normalizar_documento,
    validar_cnpj,
    validar_cpf,
)


def test_cpf_valido_com_e_sem_mascara():
    assert validar_cpf("529.982.247-25")
    assert validar_cpf("52998224725")


def test_cpf_digito_verificador_invalido():
    assert not validar_cpf("529.982.247-24")
    assert not validar_cpf("11144477734")


def test_cpf_sequencia_trivial_rejeitada():
    assert not validar_cpf("00000000000")
    assert not validar_cpf("111.111.111-11")


def test_cpf_tamanho_incorreto():
    assert not validar_cpf("123")
    assert not validar_cpf("5299822472")  # 10 dígitos


def test_cnpj_valido_com_e_sem_mascara():
    assert validar_cnpj("11.222.333/0001-81")
    assert validar_cnpj("11222333000181")


def test_cnpj_digito_verificador_invalido():
    assert not validar_cnpj("11.222.333/0001-80")


def test_cnpj_sequencia_trivial_rejeitada():
    assert not validar_cnpj("00000000000000")


def test_cnpj_tamanho_incorreto():
    assert not validar_cnpj("112223330001")  # 12 dígitos


def test_normalizar_remove_mascara():
    assert normalizar_documento("529.982.247-25") == "52998224725"
    assert normalizar_documento("11.222.333/0001-81") == "11222333000181"
