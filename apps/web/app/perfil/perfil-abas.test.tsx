import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { meuPerfil, atualizarMeuPerfil, recarregar, push } = vi.hoisted(() => ({
  meuPerfil: vi.fn(),
  atualizarMeuPerfil: vi.fn(),
  recarregar: vi.fn(),
  push: vi.fn(),
}));

let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ recarregar }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { meuPerfil, atualizarMeuPerfil },
  };
});

import PerfilPage from "./page";

const PERFIL = {
  usuario: {
    id: "u-1",
    nome: "Maria Souza",
    email: "maria@example.com",
    perfil: "servidor",
    status: "ativo",
    unidade_id: null,
    pode_auditar: false,
  },
  processos: [
    {
      processo_id: "p-1",
      numero: "2026/000042",
      assunto: "Solicitação de férias",
      data_acao: "2026-07-10T12:00:00Z",
      tipo_acao: "despacho",
    },
  ],
  documentos_assinados: [],
  mensagem_processos: "Nenhum processo registrado",
  mensagem_documentos: "Nenhum documento assinado",
};

describe("PerfilPage — abas (change perfil-em-abas)", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    meuPerfil.mockReset().mockResolvedValue(PERFIL);
    atualizarMeuPerfil.mockReset();
    recarregar.mockReset();
    push.mockReset();
  });

  it("renderiza as quatro abas, com 'Meu perfil' ativa por padrão", async () => {
    render(<PerfilPage />);

    await screen.findByRole("tablist", { name: "Meu Perfil" });
    const rotulos = screen.getAllByRole("tab").map((t) => t.textContent);
    expect(rotulos).toEqual(["Meu perfil", "Trocar senha", "Processos em que atuei", "Documentos assinados"]);

    expect(screen.getByRole("tab", { name: "Meu perfil" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByLabelText("Nome")).toBeInTheDocument();
  });

  it("abre a aba indicada em '?aba=processos' ao carregar", async () => {
    searchParams = new URLSearchParams("aba=processos");

    render(<PerfilPage />);

    expect(await screen.findByRole("tab", { name: "Processos em que atuei" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("2026/000042")).toBeInTheDocument();
    expect(screen.queryByLabelText("Nome")).toBeNull();
  });

  it("valor de aba desconhecido na URL cai no padrão 'Meu perfil'", async () => {
    searchParams = new URLSearchParams("aba=inexistente");

    render(<PerfilPage />);

    expect(await screen.findByRole("tab", { name: "Meu perfil" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByLabelText("Nome")).toBeInTheDocument();
  });

  it("trocar de aba atualiza a query string e não dispara nova chamada à API", async () => {
    render(<PerfilPage />);
    await screen.findByLabelText("Nome");

    await userEvent.click(screen.getByRole("tab", { name: "Trocar senha" }));

    expect(push).toHaveBeenCalledWith("/perfil?aba=senha", { scroll: false });
    expect(meuPerfil).toHaveBeenCalledTimes(1);
  });

  it("navegação por teclado ativa a aba seguinte com as setas", async () => {
    render(<PerfilPage />);
    const abaMeuPerfil = await screen.findByRole("tab", { name: "Meu perfil" });
    abaMeuPerfil.focus();

    await userEvent.keyboard("{ArrowRight}");

    expect(screen.getByRole("tab", { name: "Trocar senha" })).toHaveFocus();
    expect(push).toHaveBeenCalledWith("/perfil?aba=senha", { scroll: false });
  });

  it("aba 'Documentos assinados' mostra o aviso de fase futura, sem nenhum controle de assinatura", async () => {
    searchParams = new URLSearchParams("aba=assinados");

    render(<PerfilPage />);

    expect(
      await screen.findByText(/assinatura digital de documentos será disponibilizada em uma fase futura/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /assinar/i })).toBeNull();
    expect(screen.queryByLabelText(/certificado/i)).toBeNull();
  });
});
