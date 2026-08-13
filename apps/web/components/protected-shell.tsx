"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { type Schemas } from "@/lib/api";
import { NOME_PRODUTO, SUBTITULO_CLIENTE } from "@/lib/marca";
import { URL_MANUAL } from "@/lib/manual";

import { useAuth } from "./auth-provider";
import {
  IconBuildings,
  IconDocumentos,
  IconFechar,
  IconLgpd,
  IconManual,
  IconMarca,
  IconMenu,
  IconPainel,
  IconPerfil,
  IconProcessos,
  IconRelatorios,
  IconTiposProcesso,
  IconUsuarios,
} from "./icons";
import { NotificacoesSino } from "./notificacoes-sino";
import { SessionWatcher } from "./session-watcher";

type Perfil = Schemas["UsuarioResumo"]["perfil"];
type Usuario = Schemas["UsuarioResumo"];

type ItemMenu = {
  href: string;
  /** Quando presente, o item aponta para fora da aplicação (design.md D1 do
   * change link-manual-no-menu): renderiza `<a target="_blank">` em vez de
   * `<Link>`, e `href` deixa de ser navegado — serve só de `key` estável e
   * nunca casa com `itemAtivo()`. */
  hrefExterno?: string;
  label: string;
  Icon: (props: { className?: string }) => React.ReactNode;
  visivel: (usuario: Usuario) => boolean;
};

// Predicados de visibilidade preservados da versão anterior — só a ordem de
// exibição muda. Nenhuma regra de RBAC é adicionada ou removida.
const ITENS_MENU: ItemMenu[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    Icon: IconPainel,
    visivel: (u) => u.perfil === "gestor",
  },
  { href: "/processos", label: "Processos", Icon: IconProcessos, visivel: () => true },
  {
    href: "/admin/documentos-removidos",
    label: "Documentos Removidos",
    Icon: IconDocumentos,
    visivel: (u) => u.perfil === "administrador",
  },
  {
    href: "/admin/lgpd",
    label: "Solicitações LGPD",
    Icon: IconLgpd,
    visivel: (u) => u.perfil === "administrador",
  },
  {
    href: "/admin/unidades",
    label: "Unidades",
    Icon: IconBuildings,
    visivel: (u) => u.perfil === "administrador",
  },
  {
    href: "/admin/tipos-processo",
    label: "Tipos de Processo",
    Icon: IconTiposProcesso,
    visivel: (u) => u.perfil === "administrador",
  },
  {
    href: "/admin/modelos",
    label: "Modelos de Documento",
    Icon: IconDocumentos,
    visivel: (u) => u.perfil === "administrador",
  },
  {
    href: "/admin/usuarios",
    label: "Usuários",
    Icon: IconUsuarios,
    visivel: (u) => u.perfil === "administrador" || u.perfil === "gestor",
  },
  {
    href: "/auditoria/relatorios",
    label: "Relatório de Auditoria",
    Icon: IconRelatorios,
    visivel: (u) => u.pode_auditar,
  },
  { href: "/perfil", label: "Meu Perfil", Icon: IconPerfil, visivel: () => true },
  {
    href: "manual-externo",
    hrefExterno: URL_MANUAL,
    label: "Manual",
    Icon: IconManual,
    visivel: () => true,
  },
];

function itemAtivo(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

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
  const pathname = usePathname();
  const [drawerAberto, setDrawerAberto] = useState(false);

  useEffect(() => {
    if (!carregando && !usuario) router.replace("/login");
  }, [carregando, usuario, router]);

  useEffect(() => {
    setDrawerAberto(false);
  }, [pathname]);

  if (carregando) {
    return <p className="p-8 text-sm text-gray-500">Carregando…</p>;
  }
  if (!usuario) return null;

  const acessoNegadoPerfil = perfisPermitidos != null && !perfisPermitidos.includes(usuario.perfil);
  const acessoNegadoAuditoria = exigirAuditoria === true && !usuario.pode_auditar;
  const acessoNegado = acessoNegadoPerfil || acessoNegadoAuditoria;

  const itensVisiveis = ITENS_MENU.filter((item) => item.visivel(usuario));

  async function sair() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-superficie-app md:grid md:grid-cols-[240px_1fr]">
      <SessionWatcher />

      {drawerAberto && (
        <button
          type="button"
          aria-label="Fechar menu"
          onClick={() => setDrawerAberto(false)}
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[240px] flex-col bg-navy-900 text-white transition-transform md:sticky md:top-0 md:z-auto md:h-screen md:translate-x-0 ${
          drawerAberto ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-sm font-semibold text-navy-900">
                <IconMarca className="h-5 w-5" />
              </div>
              <span className="text-sm font-semibold">{NOME_PRODUTO}</span>
            </div>
            <p className="mt-1 text-[10px] uppercase tracking-wide text-navy-50/70">
              {SUBTITULO_CLIENTE}
            </p>
          </div>
          <button
            type="button"
            aria-label="Fechar menu"
            onClick={() => setDrawerAberto(false)}
            className="rounded p-1 hover:bg-navy-700 md:hidden"
          >
            <IconFechar />
          </button>
        </div>

        <nav className="mt-2 flex-1 space-y-1 overflow-y-auto px-2 pb-4 text-sm">
          {itensVisiveis.map(({ href, hrefExterno, label, Icon }) => {
            if (hrefExterno != null) {
              return (
                <a
                  key={href}
                  href={hrefExterno}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 rounded-card px-3 py-2 text-white hover:bg-navy-700"
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {label}
                </a>
              );
            }

            const ativo = itemAtivo(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={ativo ? "page" : undefined}
                className={`flex items-center gap-3 rounded-card px-3 py-2 ${
                  ativo ? "bg-navy-50 font-medium text-navy-900" : "text-white hover:bg-navy-700"
                }`}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="flex min-h-screen flex-col">
        <header className="border-b bg-superficie-card">
          <div className="flex items-center justify-between gap-3 p-4 text-sm">
            <button
              type="button"
              aria-label="Abrir menu"
              onClick={() => setDrawerAberto(true)}
              className="rounded p-1.5 hover:bg-gray-100 md:hidden"
            >
              <IconMenu />
            </button>
            <div className="flex flex-1 items-center justify-end gap-3">
              <NotificacoesSino />
              <span className="text-gray-500">
                {usuario.nome} · {usuario.perfil}
              </span>
              <button
                type="button"
                onClick={() => void sair()}
                className="rounded-card border px-2 py-1"
              >
                Sair
              </button>
            </div>
          </div>
        </header>
        <main className="flex-1 p-6">
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
    </div>
  );
}
