"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { ApiError } from "@/lib/api";

const MENSAGENS_MOTIVO: Record<string, string> = {
  inatividade: "Sua sessão expirou por inatividade. Faça login novamente.",
  "setup-concluido": "Sistema inicializado com sucesso. Faça login para continuar.",
  "senha-redefinida": "Senha redefinida com sucesso. Faça login com a nova senha.",
};

function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const searchParams = useSearchParams();
  const motivo = searchParams.get("motivo");

  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await login(email, senha);
      router.push("/perfil");
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Falha ao entrar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="mx-auto max-w-sm p-8">
      <h1 className="text-2xl font-semibold">SETES.DOCS</h1>
      <p className="mt-1 text-sm text-gray-600">Entre com suas credenciais.</p>

      {motivo && MENSAGENS_MOTIVO[motivo] && (
        <p className="mt-4 rounded bg-blue-50 p-3 text-sm text-blue-800">{MENSAGENS_MOTIVO[motivo]}</p>
      )}

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
        <div>
          <label htmlFor="senha" className="block text-sm">
            Senha
          </label>
          <input
            id="senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
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
          {enviando ? "Entrando…" : "Entrar"}
        </button>
      </form>

      <Link href="/recuperar-senha" className="mt-4 inline-block text-sm text-blue-600">
        Esqueci minha senha
      </Link>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<p className="p-8 text-sm text-gray-500">Carregando…</p>}>
      <LoginForm />
    </Suspense>
  );
}
