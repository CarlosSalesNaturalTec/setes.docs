"""Validação de CPF/CNPJ por dígito verificador (D7).

Python puro, sem dependência externa. Aplicado no schema Pydantic do
interessado quando `documento` é informado (CPF/CNPJ são opcionais — só o nome
é obrigatório). Dado pessoal de terceiro (LGPD): a validação é estrutural, não
consulta base externa.
"""

from __future__ import annotations


def _apenas_digitos(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def _todos_iguais(digitos: str) -> bool:
    """Sequências triviais (000..., 111...) passam no dígito verificador mas são inválidas."""
    return len(set(digitos)) == 1


def _dv(digitos: str, pesos: list[int]) -> int:
    soma = sum(int(d) * p for d, p in zip(digitos, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def validar_cpf(valor: str) -> bool:
    """True se `valor` (com ou sem máscara) é um CPF com dígitos verificadores válidos."""
    cpf = _apenas_digitos(valor)
    if len(cpf) != 11 or _todos_iguais(cpf):
        return False
    dv1 = _dv(cpf[:9], list(range(10, 1, -1)))
    dv2 = _dv(cpf[:10], list(range(11, 1, -1)))
    return cpf[9] == str(dv1) and cpf[10] == str(dv2)


def validar_cnpj(valor: str) -> bool:
    """True se `valor` (com ou sem máscara) é um CNPJ com dígitos verificadores válidos."""
    cnpj = _apenas_digitos(valor)
    if len(cnpj) != 14 or _todos_iguais(cnpj):
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv1 = _dv(cnpj[:12], pesos1)
    dv2 = _dv(cnpj[:13], pesos2)
    return cnpj[12] == str(dv1) and cnpj[13] == str(dv2)


def normalizar_documento(valor: str) -> str:
    """Remove máscara, guardando só os dígitos (formato de persistência)."""
    return _apenas_digitos(valor)
