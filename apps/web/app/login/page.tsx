"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { IconCadeado, IconEnvelope } from "@/components/icons";
import { ApiError } from "@/lib/api";
import { rotaInicial } from "@/lib/rota-inicial";

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
      const usuario = await login(email, senha);
      router.push(rotaInicial(usuario));
    } catch (err) {
      setErro(err instanceof ApiError ? err.detail : "Falha ao entrar.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-superficie-app p-4">
      <div className="w-full max-w-sm rounded-card border border-navy-50 bg-superficie-card p-8 shadow-card">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-navy-900 text-lg font-semibold text-white">
            S
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-navy-900">SETES.DOCS</h1>
          <p className="mt-1 text-sm text-gray-600">Acesse sua conta</p>
        </div>

        {motivo && MENSAGENS_MOTIVO[motivo] && (
          <p className="mt-4 rounded bg-navy-50 p-3 text-sm text-navy-900">{MENSAGENS_MOTIVO[motivo]}</p>
        )}

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm">
              E-mail
            </label>
            <div className="relative mt-1">
              <IconEnvelope className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="seu.email@setes.gov.br"
                className="w-full rounded-card border px-3 py-2 pl-9 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
              />
            </div>
          </div>
          <div>
            <label htmlFor="senha" className="block text-sm">
              Senha
            </label>
            <div className="relative mt-1">
              <IconCadeado className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                id="senha"
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full rounded-card border px-3 py-2 pl-9 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
              />
            </div>
          </div>

          {erro && <p className="text-sm text-red-600">{erro}</p>}

          <button
            type="submit"
            disabled={enviando}
            className="w-full rounded-card bg-navy-900 px-4 py-2 text-sm font-medium text-white hover:bg-navy-700 disabled:opacity-50"
          >
            {enviando ? "Entrando…" : "Entrar"}
          </button>
        </form>

        <Link href="/recuperar-senha" className="mt-4 inline-block text-sm text-navy-600">
          Esqueci minha senha
        </Link>
      </div>
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
