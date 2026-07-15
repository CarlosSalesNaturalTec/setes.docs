"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "./auth-provider";
import { SessionWatcher } from "./session-watcher";

export function ProtectedShell({ children }: { children: React.ReactNode }) {
  const { usuario, carregando, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!carregando && !usuario) router.replace("/login");
  }, [carregando, usuario, router]);

  if (carregando) {
    return <p className="p-8 text-sm text-gray-500">Carregando…</p>;
  }
  if (!usuario) return null;

  return (
    <div className="min-h-screen">
      <SessionWatcher />
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3 p-4 text-sm">
          <div className="flex flex-wrap gap-4">
            <Link href="/perfil" className="font-medium">
              Meu Perfil
            </Link>
            <Link href="/processos">Processos</Link>
            {(usuario.perfil === "administrador" || usuario.perfil === "gestor") && (
              <Link href="/admin/usuarios">Usuários</Link>
            )}
            {usuario.perfil === "administrador" && (
              <>
                <Link href="/admin/unidades">Unidades</Link>
                <Link href="/admin/tipos-processo">Tipos de Processo</Link>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-gray-500">
              {usuario.nome} · {usuario.perfil}
            </span>
            <button
              type="button"
              onClick={() => {
                void (async () => {
                  await logout();
                  router.replace("/login");
                })();
              }}
              className="rounded border px-2 py-1"
            >
              Sair
            </button>
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl p-6">{children}</main>
    </div>
  );
}
