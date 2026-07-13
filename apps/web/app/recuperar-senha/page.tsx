"use client";

import { useState } from "react";

import { ApiError, api } from "@/lib/api";

export default function RecuperarSenhaPage() {
  const [email, setEmail] = useState("");
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    try {
      const resp = await api.recuperarSenha({ email });
      setMensagem(resp.mensagem);
    } catch (err) {
      // A rota nunca deve revelar se o e-mail existe (US 1.3 Cen.5); em caso
      // de erro de rede/servidor, ainda assim mostramos a mensagem genérica.
      setMensagem(
        err instanceof ApiError
          ? err.detail
          : "Se o e-mail informado estiver cadastrado, um link de redefinição será enviado",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="mx-auto max-w-sm p-8">
      <h1 className="text-2xl font-semibold">Recuperar senha</h1>
      <p className="mt-1 text-sm text-gray-600">
        Informe o e-mail cadastrado. Se existir, enviaremos um link de redefinição válido por 2 horas.
      </p>

      {mensagem ? (
        <p className="mt-6 rounded bg-blue-50 p-3 text-sm text-blue-800">{mensagem}</p>
      ) : (
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={enviando}
            className="w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {enviando ? "Enviando…" : "Enviar link de redefinição"}
          </button>
        </form>
      )}
    </main>
  );
}
