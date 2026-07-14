"use client";

import { useState } from "react";

import { ApiError, api } from "@/lib/api";
import { MENSAGEM_COMPLEXIDADE_SENHA, senhaAtendeComplexidade } from "@/lib/validacao";

export function TrocarSenhaForm() {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setMensagem(null);

    if (!senhaAtendeComplexidade(novaSenha)) {
      setErro(MENSAGEM_COMPLEXIDADE_SENHA);
      return;
    }
    if (novaSenha !== confirmarSenha) {
      setErro("As senhas não coincidem.");
      return;
    }

    setEnviando(true);
    try {
      const resp = await api.trocarSenha({ senha_atual: senhaAtual, nova_senha: novaSenha });
      setMensagem(resp.mensagem);
      setSenhaAtual("");
      setNovaSenha("");
      setConfirmarSenha("");
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Não foi possível trocar a senha.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="mt-8 rounded border p-4">
      <h2 className="text-lg font-medium">Trocar senha</h2>
      <form onSubmit={onSubmit} className="mt-4 max-w-sm space-y-3">
        <div>
          <label htmlFor="senha-atual" className="block text-sm">
            Senha atual
          </label>
          <input
            id="senha-atual"
            type="password"
            value={senhaAtual}
            onChange={(e) => setSenhaAtual(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="nova-senha" className="block text-sm">
            Nova senha
          </label>
          <input
            id="nova-senha"
            type="password"
            value={novaSenha}
            onChange={(e) => setNovaSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="confirmar-nova-senha" className="block text-sm">
            Confirmar nova senha
          </label>
          <input
            id="confirmar-nova-senha"
            type="password"
            value={confirmarSenha}
            onChange={(e) => setConfirmarSenha(e.target.value)}
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}
        {mensagem && <p className="text-sm text-green-700">{mensagem}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {enviando ? "Salvando…" : "Trocar senha"}
        </button>
      </form>
    </section>
  );
}
