"use client";

import { useRouter } from "next/navigation";

import { DefinirSenhaForm } from "@/components/definir-senha-form";
import { api } from "@/lib/api";

export function RedefinirSenhaClient({ token }: { token: string }) {
  const router = useRouter();

  async function redefinir(senha: string) {
    await api.redefinirSenha(token, { senha });
    router.push("/login?motivo=senha-redefinida");
  }

  return (
    <DefinirSenhaForm
      titulo="Redefinir senha"
      descricao="Defina sua nova senha. Se sua conta estava bloqueada por tentativas incorretas, ela será desbloqueada automaticamente."
      textoBotao="Redefinir senha"
      onSubmit={redefinir}
    />
  );
}
