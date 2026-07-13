"use client";

import { useRouter } from "next/navigation";

import { DefinirSenhaForm } from "@/components/definir-senha-form";
import { api } from "@/lib/api";
import { setToken } from "@/lib/session-store";

export function PrimeiroAcessoClient({ token }: { token: string }) {
  const router = useRouter();

  async function ativarConta(senha: string) {
    // PRD US 1.6 Cen.1 — a senha é aceita e o usuário já sai autenticado.
    const resp = await api.primeiroAcesso(token, { senha });
    setToken(resp.token);
    router.push("/perfil");
  }

  return (
    <DefinirSenhaForm
      titulo="Ativar sua conta"
      descricao="Defina sua senha para concluir o primeiro acesso ao SETES.DOCS."
      textoBotao="Ativar conta"
      onSubmit={ativarConta}
    />
  );
}
