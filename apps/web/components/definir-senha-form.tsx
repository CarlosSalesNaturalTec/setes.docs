"use client";

// Formulário compartilhado por /primeiro-acesso/[token] e /redefinir-senha/[token]
// — mesma UX: nova senha + confirmação, validação de complexidade no client
// (US 1.6 Cen.1b), tratamento de link expirado/usado repassado pelo backend.
import { useState } from "react";

import { ApiError } from "@/lib/api";
import { MENSAGEM_COMPLEXIDADE_SENHA, senhaAtendeComplexidade } from "@/lib/validacao";

interface DefinirSenhaFormProps {
  titulo: string;
  descricao: string;
  textoBotao: string;
  onSubmit: (senha: string) => Promise<void>;
}

export function DefinirSenhaForm({ titulo, descricao, textoBotao, onSubmit }: DefinirSenhaFormProps) {
  const [senha, setSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);

    if (!senhaAtendeComplexidade(senha)) {
      setErro(MENSAGEM_COMPLEXIDADE_SENHA);
      return;
    }
    if (senha !== confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }

    setEnviando(true);
    try {
      await onSubmit(senha);
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível concluir a operação.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="mx-auto max-w-sm p-8">
      <h1 className="text-2xl font-semibold">{titulo}</h1>
      <p className="mt-1 text-sm text-gray-600">{descricao}</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="senha" className="block text-sm">
            Nova senha
          </label>
          <input
            id="senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-gray-500">{MENSAGEM_COMPLEXIDADE_SENHA}</p>
        </div>
        <div>
          <label htmlFor="confirmar-senha" className="block text-sm">
            Confirmar nova senha
          </label>
          <input
            id="confirmar-senha"
            type="password"
            value={confirmarSenha}
            onChange={(e) => setConfirmarSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Enviando…" : textoBotao}
        </button>
      </form>
    </main>
  );
}
