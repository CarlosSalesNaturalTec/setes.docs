"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { type Schemas } from "@/lib/api";

import { useAuth } from "./auth-provider";
import { NotificacoesSino } from "./notificacoes-sino";
import { SessionWatcher } from "./session-watcher";

type Perfil = Schemas["UsuarioResumo"]["perfil"];

export function ProtectedShell({
  children,
  perfisPermitidos,
  exigirAuditoria,
}: {
  children: React.ReactNode;
  /** Restringe o conteúdo da página aos perfis informados. Um usuário
   * autenticado mas fora da lista continua vendo o shell (cabeçalho/menu),
   * porém no lugar do conteúdo recebe "Acesso negado para o seu perfil." —
   * o cenário de rejeição explícito exigido para toda regra de visibilidade
   * por perfil (US 8.2). Sem a prop, a página fica aberta a qualquer sessão. */
  perfisPermitidos?: Perfil[];
  /** Restringe o conteúdo a usuários com `pode_auditar = true` — ortogonal ao
   * perfil (Épico 9, US 9.1/9.2), ex.: o relatório de auditoria. */
  exigirAuditoria?: boolean;
}) {
  const { usuario, carregando, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!carregando && !usuario) router.replace("/login");
  }, [carregando, usuario, router]);

  if (carregando) {
    return <p className="p-8 text-sm text-gray-500">Carregando…</p>;
  }
  if (!usuario) return null;

  const acessoNegadoPerfil = perfisPermitidos != null && !perfisPermitidos.includes(usuario.perfil);
  const acessoNegadoAuditoria = exigirAuditoria === true && !usuario.pode_auditar;
  const acessoNegado = acessoNegadoPerfil || acessoNegadoAuditoria;

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
            {usuario.perfil === "gestor" && <Link href="/dashboard">Dashboard</Link>}
            {usuario.pode_auditar && (
              <Link href="/auditoria/relatorios">Relatório de Auditoria</Link>
            )}
            {(usuario.perfil === "administrador" || usuario.perfil === "gestor") && (
              <Link href="/admin/usuarios">Usuários</Link>
            )}
            {usuario.perfil === "administrador" && (
              <>
                <Link href="/admin/unidades">Unidades</Link>
                <Link href="/admin/tipos-processo">Tipos de Processo</Link>
                <Link href="/admin/documentos-removidos">Documentos Removidos</Link>
                <Link href="/admin/lgpd">Solicitações LGPD</Link>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <NotificacoesSino />
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
      <main className="mx-auto max-w-4xl p-6">
        {acessoNegado ? (
          <p className="text-sm text-red-600">
            {acessoNegadoAuditoria
              ? "Acesso negado — permissão de auditoria necessária."
              : "Acesso negado para o seu perfil."}
          </p>
        ) : (
          children
        )}
      </main>
    </div>
  );
}
