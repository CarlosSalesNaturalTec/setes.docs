import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  listarUsuarios,
  listarUnidades,
  concederPermissaoAuditoria,
  revogarPermissaoAuditoria,
  desativarUsuario,
  usuarioAtual,
} = vi.hoisted(() => ({
  listarUsuarios: vi.fn(),
  listarUnidades: vi.fn(),
  concederPermissaoAuditoria: vi.fn(),
  revogarPermissaoAuditoria: vi.fn(),
  desativarUsuario: vi.fn(),
  usuarioAtual: { value: { id: "admin-1", nome: "Admin", email: "admin@example.com", perfil: "administrador" } },
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ usuario: usuarioAtual.value }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      listarUsuarios,
      listarUnidades,
      concederPermissaoAuditoria,
      revogarPermissaoAuditoria,
      desativarUsuario,
    },
  };
});

import AdminUsuariosPage from "./page";

const SERVIDOR = {
  id: "u-1",
  nome: "Servidor Um",
  email: "servidor@example.com",
  perfil: "servidor" as const,
  status: "ativo",
  unidade_id: null,
  pode_auditar: false,
};

function linhaDoServidor() {
  return screen.getByText("Servidor Um").closest("tr") as HTMLElement;
}

describe("AdminUsuariosPage — ações de auditoria e desativação (US 8.3/8.4)", () => {
  beforeEach(() => {
    usuarioAtual.value = { id: "admin-1", nome: "Admin", email: "admin@example.com", perfil: "administrador" };
    listarUsuarios.mockReset().mockResolvedValue({ items: [SERVIDOR], total: 1, page: 1, page_size: 20 });
    listarUnidades.mockReset().mockResolvedValue([]);
    concederPermissaoAuditoria.mockReset();
    revogarPermissaoAuditoria.mockReset();
    desativarUsuario.mockReset();
  });

  it("Administrador vê e aciona 'Conceder Permissão de Auditoria' sobre um usuário sem a flag", async () => {
    concederPermissaoAuditoria.mockResolvedValue({ ...SERVIDOR, pode_auditar: true });

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    const linha = within(linhaDoServidor());
    const botao = linha.getByRole("button", { name: "Conceder Permissão de Auditoria" });
    await userEvent.click(botao);

    await waitFor(() => expect(concederPermissaoAuditoria).toHaveBeenCalledWith("u-1"));
    await waitFor(() => expect(listarUsuarios).toHaveBeenCalledTimes(2));
  });

  it("alterna para 'Revogar Permissão de Auditoria' quando pode_auditar já é true", async () => {
    listarUsuarios.mockResolvedValue({
      items: [{ ...SERVIDOR, pode_auditar: true }],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    expect(within(linhaDoServidor()).getByRole("button", { name: "Revogar Permissão de Auditoria" })).toBeInTheDocument();
  });

  it("aciona 'Desativar Usuário' e recarrega a lista em caso de sucesso", async () => {
    desativarUsuario.mockResolvedValue({ ...SERVIDOR, status: "inativo" });

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    const linha = within(linhaDoServidor());
    await userEvent.click(linha.getByRole("button", { name: "Desativar Usuário" }));

    await waitFor(() => expect(desativarUsuario).toHaveBeenCalledWith("u-1"));
    await waitFor(() => expect(listarUsuarios).toHaveBeenCalledTimes(2));
  });

  it("exibe a mensagem de guarda de processos pendentes quando a desativação é bloqueada", async () => {
    const { ApiError } = await import("@/lib/api");
    desativarUsuario.mockRejectedValue(
      new ApiError(422, "Este usuário possui 3 processo(s) em andamento. Reatribua os processos antes de desativar."),
    );

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    const linha = within(linhaDoServidor());
    await userEvent.click(linha.getByRole("button", { name: "Desativar Usuário" }));

    expect(
      await linha.findByText(/Este usuário possui 3 processo\(s\) em andamento/),
    ).toBeInTheDocument();
  });

  it("não exibe a ação 'Desativar Usuário' quando o status já é inativo", async () => {
    listarUsuarios.mockResolvedValue({
      items: [{ ...SERVIDOR, status: "inativo" }],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    expect(within(linhaDoServidor()).queryByRole("button", { name: "Desativar Usuário" })).toBeNull();
  });

  it("não oferece unidades inativas no select de cadastro de usuário", async () => {
    listarUnidades.mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: false },
    ]);

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    const select = screen.getByLabelText("Unidade") as HTMLSelectElement;
    expect(within(select).getByRole("option", { name: "COFIN" })).toBeInTheDocument();
    expect(within(select).queryByRole("option", { name: "AJUR" })).toBeNull();
  });

  it("não exibe as ações de auditoria/desativação para um Gestor (não-Administrador)", async () => {
    usuarioAtual.value = { id: "gestor-1", nome: "Gestor", email: "gestor@example.com", perfil: "gestor" };

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    const linha = within(linhaDoServidor());
    expect(linha.queryByRole("button", { name: /Permissão de Auditoria/ })).toBeNull();
    expect(linha.queryByRole("button", { name: "Desativar Usuário" })).toBeNull();
  });
});
