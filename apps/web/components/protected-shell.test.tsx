import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { URL_MANUAL } from "@/lib/manual";

import { ProtectedShell } from "./protected-shell";

const replace = vi.fn();
let pathname = "/processos";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => pathname,
}));

vi.mock("./notificacoes-sino", () => ({
  NotificacoesSino: () => null,
}));

vi.mock("./session-watcher", () => ({
  SessionWatcher: () => null,
}));

const logout = vi.fn();
let usuarioMock: {
  nome: string;
  perfil: "servidor" | "gestor" | "administrador";
  pode_auditar: boolean;
} | null = null;

vi.mock("./auth-provider", () => ({
  useAuth: () => ({ usuario: usuarioMock, carregando: false, logout }),
}));

function usuario(
  perfil: "servidor" | "gestor" | "administrador",
  pode_auditar = false,
): typeof usuarioMock {
  return { nome: "Fulano", perfil, pode_auditar };
}

describe("ProtectedShell — sidebar (RBAC)", () => {
  beforeEach(() => {
    replace.mockReset();
    logout.mockReset();
    pathname = "/processos";
  });

  it("topo da sidebar exibe o nome do produto e o subtítulo de cliente (change renomear-sistema-despapelize)", () => {
    usuarioMock = usuario("servidor");
    render(<ProtectedShell>conteúdo</ProtectedShell>);

    expect(screen.getByText("Despapelize")).toBeInTheDocument();
    expect(screen.getByText("SETES")).toBeInTheDocument();
  });

  it("servidor vê apenas os itens do seu perfil", () => {
    usuarioMock = usuario("servidor");
    render(<ProtectedShell>conteúdo</ProtectedShell>);

    expect(screen.getByRole("link", { name: "Meu Perfil" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Processos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Manual" })).toBeInTheDocument();

    expect(screen.queryByRole("link", { name: "Dashboard" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Relatório de Auditoria" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuários" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Unidades" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Tipos de Processo" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Solicitações LGPD" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Documentos Removidos" })).not.toBeInTheDocument();
  });

  it.each([["servidor"], ["gestor"], ["administrador"]] as const)(
    "item Manual aparece para o perfil %s, abrindo em nova aba com rel=noopener noreferrer",
    (perfil) => {
      usuarioMock = usuario(perfil);
      render(<ProtectedShell>conteúdo</ProtectedShell>);

      const link = screen.getByRole("link", { name: "Manual" });
      expect(link).toHaveAttribute("href", URL_MANUAL);
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    },
  );

  it("item de auditoria fica oculto sem a permissão pode_auditar", () => {
    usuarioMock = usuario("servidor", false);
    render(<ProtectedShell>conteúdo</ProtectedShell>);
    expect(screen.queryByRole("link", { name: "Relatório de Auditoria" })).not.toBeInTheDocument();
  });

  it("usuário com pode_auditar vê o item de Relatório de Auditoria", () => {
    usuarioMock = usuario("servidor", true);
    render(<ProtectedShell>conteúdo</ProtectedShell>);
    expect(screen.getByRole("link", { name: "Relatório de Auditoria" })).toBeInTheDocument();
  });

  it("administrador vê os itens administrativos", () => {
    usuarioMock = usuario("administrador");
    render(<ProtectedShell>conteúdo</ProtectedShell>);

    expect(screen.getByRole("link", { name: "Unidades" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Tipos de Processo" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Usuários" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Documentos Removidos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Solicitações LGPD" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Dashboard" })).not.toBeInTheDocument();
  });

  it("destaca o item ativo correspondente à rota atual", () => {
    pathname = "/processos";
    usuarioMock = usuario("servidor");
    render(<ProtectedShell>conteúdo</ProtectedShell>);

    expect(screen.getByRole("link", { name: "Processos" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Meu Perfil" })).not.toHaveAttribute("aria-current");
  });

  it("item Manual nunca recebe o destaque de item ativo, independentemente da rota corrente", () => {
    pathname = "/processos";
    usuarioMock = usuario("servidor");
    render(<ProtectedShell>conteúdo</ProtectedShell>);

    expect(screen.getByRole("link", { name: "Manual" })).not.toHaveAttribute("aria-current");
  });
});
