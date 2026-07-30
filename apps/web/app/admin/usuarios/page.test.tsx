import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  listarUsuarios,
  listarUnidades,
  listarSetores,
  cadastrarUsuario,
  concederPermissaoAuditoria,
  revogarPermissaoAuditoria,
  desativarUsuario,
  usuarioAtual,
} = vi.hoisted(() => ({
  listarUsuarios: vi.fn(),
  listarUnidades: vi.fn(),
  listarSetores: vi.fn(),
  cadastrarUsuario: vi.fn(),
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
      listarSetores,
      cadastrarUsuario,
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
    listarSetores.mockReset().mockResolvedValue([]);
    cadastrarUsuario.mockReset().mockResolvedValue(SERVIDOR);
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
    await userEvent.click(screen.getByRole("button", { name: "Novo usuário" }));

    const select = screen.getByLabelText("Unidade") as HTMLSelectElement;
    expect(within(select).getByRole("option", { name: "COFIN" })).toBeInTheDocument();
    expect(within(select).queryByRole("option", { name: "AJUR" })).toBeNull();
  });

  it("não renderiza formulário de cadastro no índice — só após abrir o modal (D6)", async () => {
    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByLabelText("E-mail")).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Novo usuário" }));

    const modal = within(screen.getByRole("dialog"));
    expect(modal.getByLabelText("E-mail")).toBeInTheDocument();
    expect(modal.getByLabelText("Telefone")).toBeInTheDocument();
    expect(modal.getByLabelText("Cargo")).toBeInTheDocument();
    expect(modal.getByLabelText("Chefia direta")).toBeInTheDocument();
  });

  it("fecha o modal ao acionar Fechar", async () => {
    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");

    await userEvent.click(screen.getByRole("button", { name: "Novo usuário" }));
    await userEvent.click(screen.getByRole("button", { name: "Fechar" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("fecha o modal e recarrega a listagem após um cadastro bem-sucedido", async () => {
    listarUnidades.mockResolvedValue([{ id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true }]);
    listarSetores.mockResolvedValue([
      { id: "s-1", unidade_id: "un-1", nome: "Gabinete", sigla: "GAB", ativo: true },
    ]);

    render(<AdminUsuariosPage />);
    await screen.findByText("Servidor Um");
    await userEvent.click(screen.getByRole("button", { name: "Novo usuário" }));

    const modal = within(screen.getByRole("dialog"));
    await userEvent.type(modal.getByLabelText("Nome"), "Maria Silva");
    await userEvent.type(modal.getByLabelText("E-mail"), "maria@example.com");
    await userEvent.selectOptions(modal.getByLabelText("Unidade"), "un-1");
    await userEvent.selectOptions(await modal.findByLabelText(/^Setor/), "s-1");
    await userEvent.click(modal.getByRole("button", { name: "Cadastrar usuário" }));

    await waitFor(() => expect(cadastrarUsuario).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await waitFor(() => expect(listarUsuarios).toHaveBeenCalledTimes(2));
  });

  it("filtra por nome no backend após o debounce, sem recarregar a página", async () => {
    vi.useFakeTimers();
    // `delay: null` impede o userEvent de avançar os timers entre as teclas —
    // sem isso a digitação poderia estourar o debounce sozinha.
    const user = userEvent.setup({ delay: null, advanceTimers: vi.advanceTimersByTime });
    try {
      render(<AdminUsuariosPage />);
      await screen.findByText("Servidor Um");
      expect(listarUsuarios).toHaveBeenCalledWith(1, "");

      await user.type(screen.getByLabelText("Filtrar por nome"), "mari");
      // Antes do debounce, nenhuma requisição extra foi disparada.
      expect(listarUsuarios).toHaveBeenCalledTimes(1);

      await vi.advanceTimersByTimeAsync(300);

      await waitFor(() => expect(listarUsuarios).toHaveBeenCalledWith(1, "mari"));
      expect(listarUsuarios).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
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
