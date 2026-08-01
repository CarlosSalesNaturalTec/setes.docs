import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "@/lib/api";
import { NotificacoesSino } from "./notificacoes-sino";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      contarNotificacoes: vi.fn(),
      listarNotificacoes: vi.fn(),
      marcarNotificacaoLida: vi.fn(),
      marcarTodasNotificacoesLidas: vi.fn(),
    },
  };
});

const NOTIFICACAO_BASE = {
  id: "n1",
  tipo: "novo_processo",
  processo_id: "p1",
  numero_processo: "2026/000123",
  assunto: "Licitação de equipamentos",
  unidade_id: "u1",
  unidade_nome: "AJUR",
  unidade_origem_id: "u2",
  unidade_origem_nome: "COFIN",
  justificativa: null,
  prazo_referencia: null,
  lida_em: null,
  criado_em: "2026-07-16T10:00:00Z",
};

describe("NotificacoesSino", () => {
  beforeEach(() => {
    vi.mocked(api.contarNotificacoes).mockReset().mockResolvedValue({ nao_lidas: 0 });
    vi.mocked(api.listarNotificacoes).mockReset().mockResolvedValue({ items: [], mensagem_vazio: null });
    vi.mocked(api.marcarNotificacaoLida).mockReset();
    vi.mocked(api.marcarTodasNotificacoesLidas).mockReset();
  });

  it("não exibe o contador quando não há notificações não lidas", async () => {
    render(<NotificacoesSino />);
    await waitFor(() => expect(api.contarNotificacoes).toHaveBeenCalled());
    expect(screen.queryByTestId("notificacoes-contador")).not.toBeInTheDocument();
  });

  it("exibe o contador de não lidas", async () => {
    vi.mocked(api.contarNotificacoes).mockResolvedValue({ nao_lidas: 3 });
    render(<NotificacoesSino />);
    expect(await screen.findByTestId("notificacoes-contador")).toHaveTextContent("3");
  });

  it("abre o painel e lista as notificações sem zerar o contador (US 5.1 Cen.2)", async () => {
    vi.mocked(api.contarNotificacoes).mockResolvedValue({ nao_lidas: 1 });
    vi.mocked(api.listarNotificacoes).mockResolvedValue({
      items: [NOTIFICACAO_BASE],
      mensagem_vazio: null,
    });
    render(<NotificacoesSino />);
    expect(await screen.findByTestId("notificacoes-contador")).toHaveTextContent("1");

    await userEvent.click(screen.getByLabelText("Notificações"));

    expect(await screen.findByText("2026/000123")).toBeInTheDocument();
    expect(screen.getByText("Licitação de equipamentos")).toBeInTheDocument();
    expect(screen.getByText(/Novo processo recebido, vindo de COFIN/)).toBeInTheDocument();
    expect(screen.getByTestId("notificacoes-contador")).toHaveTextContent("1");
  });

  it("marcar uma notificação como lida decrementa o contador", async () => {
    vi.mocked(api.contarNotificacoes).mockResolvedValue({ nao_lidas: 1 });
    vi.mocked(api.listarNotificacoes).mockResolvedValue({
      items: [NOTIFICACAO_BASE],
      mensagem_vazio: null,
    });
    vi.mocked(api.marcarNotificacaoLida).mockResolvedValue({
      ...NOTIFICACAO_BASE,
      lida_em: "2026-07-16T11:00:00Z",
    });
    render(<NotificacoesSino />);
    await userEvent.click(screen.getByLabelText("Notificações"));
    const item = await screen.findByText("2026/000123");

    await userEvent.click(item);

    await waitFor(() => expect(api.marcarNotificacaoLida).toHaveBeenCalledWith("n1"));
    await waitFor(() =>
      expect(screen.queryByTestId("notificacoes-contador")).not.toBeInTheDocument(),
    );
  });

  it("marcar todas como lidas zera o contador", async () => {
    vi.mocked(api.contarNotificacoes).mockResolvedValue({ nao_lidas: 2 });
    vi.mocked(api.listarNotificacoes).mockResolvedValue({
      items: [NOTIFICACAO_BASE, { ...NOTIFICACAO_BASE, id: "n2", numero_processo: "2026/000124" }],
      mensagem_vazio: null,
    });
    vi.mocked(api.marcarTodasNotificacoesLidas).mockResolvedValue({ marcadas: 2 });
    render(<NotificacoesSino />);
    await userEvent.click(screen.getByLabelText("Notificações"));
    await screen.findByText("2026/000123");

    await userEvent.click(screen.getByRole("button", { name: "Marcar todas como lidas" }));

    await waitFor(() => expect(api.marcarTodasNotificacoesLidas).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.queryByTestId("notificacoes-contador")).not.toBeInTheDocument(),
    );
  });

  it("exibe rótulo e justificativa das notificações de reatribuição (change tramitacao-manual, D8)", async () => {
    vi.mocked(api.contarNotificacoes).mockResolvedValue({ nao_lidas: 2 });
    vi.mocked(api.listarNotificacoes).mockResolvedValue({
      items: [
        {
          ...NOTIFICACAO_BASE,
          id: "n3",
          tipo: "reatribuido_para_voce",
          justificativa: "Setor errado",
        },
        {
          ...NOTIFICACAO_BASE,
          id: "n4",
          tipo: "destino_corrigido",
          justificativa: "Reatribuído para João Souza.",
        },
      ],
      mensagem_vazio: null,
    });
    render(<NotificacoesSino />);
    await userEvent.click(screen.getByLabelText("Notificações"));

    expect(await screen.findByText("Reatribuído para você")).toBeInTheDocument();
    expect(screen.getByText("Setor errado")).toBeInTheDocument();
    expect(screen.getByText("Destino da tramitação corrigido")).toBeInTheDocument();
    expect(screen.getByText("Reatribuído para João Souza.")).toBeInTheDocument();
  });
});
