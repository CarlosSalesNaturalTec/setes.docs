// Espelha app/security/senha.py::senha_atende_complexidade (backend é a
// fonte de verdade; esta cópia só evita um round-trip para o feedback óbvio).
export function senhaAtendeComplexidade(senha: string): boolean {
  return /[A-Z]/.test(senha) && /[a-z]/.test(senha) && /[0-9]/.test(senha) && senha.length >= 8;
}

export const MENSAGEM_COMPLEXIDADE_SENHA =
  "A senha deve ter no mínimo 8 caracteres, incluindo letras maiúsculas, minúsculas e números";
