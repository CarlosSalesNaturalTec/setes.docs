import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { listarKanban, listarUnidades, listarTiposProcesso, replace } = vi.hoisted(() => ({
  listarKanban: vi.fn(),
  listarUnidades: vi.fn(),
  listarTiposProcesso: vi.fn(),
  replace: vi.fn(),
}));
let usuario: { perfil: string } = { perfil: "servidor" };
let searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  useSearchParams: () => searchParams,
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ usuario }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarKanban, listarUnidades, listarTiposProcesso },
  };
});

import ProcessosPage from "./page";

const CARD_BASE = {
  status: "aberto",
  unidade_atual_id: "un-1",
  unidade_atual_nome: "Coordenação de Finanças",
  servidor_atual_nome: "Fulano de Tal",
  tipo_processo_nome: "Licitação",
  criado_em: "2026-07-15T10:30:00Z",
  prazo_em: "2026-08-01",
  dias_restantes: 5,
  vencido: false,
  sigiloso: false,
  somente_leitura: false,
  devolvido: false,
  acao_requerida: true,
};

describe("ProcessosPage (Kanban)", () => {
  beforeEach(() => {
    listarKanban.mockReset();
    listarUnidades.mockReset();
    listarTiposProcesso.mockReset().mockResolvedValue([]);
    replace.mockReset();
    listarUnidades.mockResolvedValue([]);
    usuario = { perfil: "servidor" };
    searchParams = new URLSearchParams();
    window.localStorage.clear();
  });

  it("exibe a mensagem de Kanban vazio da unidade (PRD US 2.3 Cen.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);

    expect(
      await screen.findByText("Nenhum processo encontrado nesta unidade"),
    ).toBeInTheDocument();
  });

  it("agrupa os cards por coluna, exibe tipo/unidade/data e destaca vencidos (PRD US 2.3 Cen.1/4)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo em dia" },
        {
          ...CARD_BASE,
          id: "proc-2",
          numero: "2026/000002",
          assunto: "Processo vencido",
          prazo_em: "2026-07-01",
          dias_restantes: -5,
          vencido: true,
        },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const coluna = (await screen.findByText(/Aberto/)).closest("section");
    expect(coluna).not.toBeNull();
    const emDia = within(coluna as HTMLElement).getByText("2026/000001").closest("a");
    const vencido = within(coluna as HTMLElement).getByText("2026/000002").closest("a");

    expect(emDia?.className).not.toContain("border-l-red-600");
    expect(vencido?.className).toContain("border-l-red-600");
    expect(within(vencido as HTMLElement).getByText(/⏰/)).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText("Licitação")).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText("Coordenação de Finanças")).toBeInTheDocument();
    expect(within(emDia as HTMLElement).getByText(/Criado em 15\/07\/2026/)).toBeInTheDocument();
  });

  it("exibe o indicador de sigilo apenas no card sigiloso (PRD US 2.6 Cen.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo comum" },
        { ...CARD_BASE, id: "proc-2", numero: "2026/000002", assunto: "Processo sigiloso", sigiloso: true },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const comum = (await screen.findByText("2026/000001")).closest("a");
    const sigiloso = screen.getByText("2026/000002").closest("a");

    expect(within(comum as HTMLElement).queryByLabelText("Sigiloso")).not.toBeInTheDocument();
    expect(within(sigiloso as HTMLElement).getByLabelText("Sigiloso")).toBeInTheDocument();
  });

  it("exibe o filtro por unidade apenas para o Gestor (PRD US 2.8 Cen.2)", async () => {
    usuario = { perfil: "gestor" };
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nas unidades gerenciadas",
    });
    listarUnidades.mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: true },
    ]);

    render(<ProcessosPage />);

    const filtro = await screen.findByLabelText("Filtrar por unidade");
    await userEvent.selectOptions(filtro, "un-2");

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({
        filtro_unidade: "un-2",
        incluir_arquivados: false,
      }),
    );
  });

  it("não lista unidades inativas no filtro do Gestor", async () => {
    usuario = { perfil: "gestor" };
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nas unidades gerenciadas",
    });
    listarUnidades.mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: false },
    ]);

    render(<ProcessosPage />);

    const filtro = await screen.findByLabelText("Filtrar por unidade");
    expect(within(filtro).getByRole("option", { name: "COFIN" })).toBeInTheDocument();
    expect(within(filtro).queryByRole("option", { name: "AJUR" })).not.toBeInTheDocument();
  });

  it("não exibe o filtro por unidade para o Servidor", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);
    await screen.findByText("Nenhum processo encontrado nesta unidade");

    expect(screen.queryByLabelText("Filtrar por unidade")).not.toBeInTheDocument();
  });

  it("exibe o contador de processos no cabeçalho (PRD — contador corrigido)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        { ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "A" },
        { ...CARD_BASE, id: "proc-2", numero: "2026/000002", assunto: "B" },
      ],
      total: 2,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    expect(await screen.findByText("2 processo(s)")).toBeInTheDocument();
  });

  it("aplica cor por status no cabeçalho de cada coluna do Kanban", async () => {
    listarKanban.mockResolvedValue({
      items: [{ ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "A" }],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const aberto = (await screen.findByText(/Aberto/)).closest("h2");
    expect(aberto?.className).toContain("bg-status-aberto-bg");
    expect(aberto?.className).toContain("text-status-aberto");
  });

  it("exibe a confirmação de sucesso vinda do envio/devolução e limpa a query string", async () => {
    searchParams = new URLSearchParams({ acao: "envio", destino: "AJUR" });
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);

    expect(await screen.findByText("Processo enviado para AJUR.")).toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/processos");
  });

  it("alterna entre Kanban e Lista mantendo os mesmos processos (toggle)", async () => {
    listarKanban.mockResolvedValue({
      items: [{ ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "Processo único" }],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);
    await screen.findByText("2026/000001");

    // Kanban por padrão: card dentro de uma coluna ("section").
    expect(screen.getByText("2026/000001").closest("section")).not.toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Lista" }));

    // Lista: mesma numeração, agora como linha (fora de "section"), com a pill de status.
    const linha = screen.getByText("2026/000001").closest("a");
    expect(linha).not.toBeNull();
    expect(linha?.closest("section")).toBeNull();
    expect(within(linha as HTMLElement).getByText("Aberto")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Kanban" }));
    expect(screen.getByText("2026/000001").closest("section")).not.toBeNull();

    // Só uma chamada à API para ambos os modos — mesma resposta reaproveitada (D2).
    expect(listarKanban).toHaveBeenCalledTimes(1);
  });

  it('checkbox "Exibir Arquivados" desmarcado por padrão (change kanban-por-servidor, D4)', async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);
    await screen.findByText("Nenhum processo encontrado nesta unidade");

    const checkbox = screen.getByLabelText("Exibir Arquivados");
    expect(checkbox).not.toBeChecked();
    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ incluir_arquivados: false }),
    );
  });

  it("marcar o checkbox chama a API com incluir_arquivados=true e persiste a preferência", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: "Nenhum processo encontrado nesta unidade",
    });

    render(<ProcessosPage />);
    await screen.findByText("Nenhum processo encontrado nesta unidade");

    const checkbox = screen.getByLabelText("Exibir Arquivados");
    await userEvent.click(checkbox);

    expect(checkbox).toBeChecked();
    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ incluir_arquivados: true }),
    );
    expect(window.localStorage.getItem("setes:processos:exibir-arquivados")).toBe("true");
  });

  it("reaplica a preferência salva do checkbox na próxima visita", async () => {
    window.localStorage.setItem("setes:processos:exibir-arquivados", "true");
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ incluir_arquivados: true }),
    );
    expect(screen.getByLabelText("Exibir Arquivados")).toBeChecked();
  });

  it("não lê a chave antiga do checkbox (exibir-finalizados)", async () => {
    window.localStorage.setItem("setes:processos:exibir-finalizados", "true");
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ incluir_arquivados: false }),
    );
    expect(screen.getByLabelText("Exibir Arquivados")).not.toBeChecked();
  });

  it("o contador do cabeçalho reflete só o total retornado (arquivados ocultos)", async () => {
    listarKanban.mockResolvedValue({
      items: [{ ...CARD_BASE, id: "proc-1", numero: "2026/000001", assunto: "A" }],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    expect(await screen.findByText("1 processo(s)")).toBeInTheDocument();
  });

  it("exibe o card acinzentado quando somente_leitura (acompanhamento por origem)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        {
          ...CARD_BASE,
          id: "proc-1",
          numero: "2026/000001",
          assunto: "Despachado para AJUR",
          unidade_atual_nome: "Assessoria Jurídica",
          somente_leitura: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const card = (await screen.findByText("2026/000001")).closest("a");
    expect(card?.className).toContain("bg-gray-100");
    expect(card?.className).toContain("opacity-75");
  });

  it('exibe o badge "↩ Devolvido" com borda âmbar quando devolvido', async () => {
    listarKanban.mockResolvedValue({
      items: [
        {
          ...CARD_BASE,
          id: "proc-1",
          numero: "2026/000001",
          assunto: "Devolvido pela AJUR",
          devolvido: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const card = (await screen.findByText("2026/000001")).closest("a");
    expect(card?.className).toContain("border-l-amber-500");
    expect(within(card as HTMLElement).getByText("↩ Devolvido")).toBeInTheDocument();
  });

  it('exibe o card de ação com destaque e o badge "Ação necessária" (change kanban-por-servidor, D2)', async () => {
    listarKanban.mockResolvedValue({
      items: [
        {
          ...CARD_BASE,
          id: "proc-1",
          numero: "2026/000001",
          assunto: "Está comigo",
          acao_requerida: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const card = (await screen.findByText("2026/000001")).closest("a");
    expect(within(card as HTMLElement).getByText("Ação necessária")).toBeInTheDocument();
    expect(card?.className).toContain("ring-navy-400");
    expect(card?.className).not.toContain("border-dashed");
  });

  it("exibe o card de acompanhamento discreto com o nome do detentor (change kanban-por-servidor, D2)", async () => {
    listarKanban.mockResolvedValue({
      items: [
        {
          ...CARD_BASE,
          id: "proc-1",
          numero: "2026/000001",
          assunto: "Está com Maria",
          acao_requerida: false,
          servidor_atual_nome: "Maria Silva",
        },
      ],
      total: 1,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);

    const card = (await screen.findByText("2026/000001")).closest("a");
    expect(within(card as HTMLElement).queryByText("Ação necessária")).not.toBeInTheDocument();
    expect(within(card as HTMLElement).getByText(/Maria Silva/)).toBeInTheDocument();
    expect(card?.className).toContain("border-dashed");
  });

  it("filtra por tipo de processo e reflete na query (D5/6.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });
    listarTiposProcesso.mockResolvedValue([
      { id: "tp-1", nome: "Requerimento", ativo: true, prazo_anonimizacao_anos: 5 },
      { id: "tp-2", nome: "Licitação", ativo: true, prazo_anonimizacao_anos: 5 },
    ]);

    render(<ProcessosPage />);
    const filtro = await screen.findByLabelText("Filtrar por tipo de processo");
    await userEvent.selectOptions(filtro, "tp-1");

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({
        incluir_arquivados: false,
        tipo_processo_id: "tp-1",
      }),
    );
  });

  it("filtra por assunto com debounce de 300ms (D5/6.3)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    const user = userEvent.setup({ delay: null });
    render(<ProcessosPage />);
    await screen.findByLabelText("Filtrar por assunto");

    const campo = screen.getByLabelText("Filtrar por assunto");
    await user.type(campo, "diária");

    // Antes do debounce, ainda não filtrou por assunto.
    expect(listarKanban).not.toHaveBeenLastCalledWith(
      expect.objectContaining({ assunto: "diária" }),
    );

    vi.advanceTimersByTime(300);

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({
        incluir_arquivados: false,
        assunto: "diária",
      }),
    );
    vi.useRealTimers();
  });

  it("filtra por período de criação (D5/6.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });

    render(<ProcessosPage />);
    const inicio = await screen.findByLabelText("Data inicial");
    const fim = screen.getByLabelText("Data final");

    await userEvent.type(inicio, "2026-07-01");
    await userEvent.type(fim, "2026-07-31");

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({
        incluir_arquivados: false,
        data_inicial: "2026-07-01",
        data_final: "2026-07-31",
      }),
    );
  });

  it("combina os três filtros e o Limpar filtros restaura o quadro completo (D5/6.3)", async () => {
    listarKanban.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      mensagem_vazio: null,
    });
    listarTiposProcesso.mockResolvedValue([
      { id: "tp-1", nome: "Requerimento", ativo: true, prazo_anonimizacao_anos: 5 },
    ]);

    render(<ProcessosPage />);
    const filtroTipo = await screen.findByLabelText("Filtrar por tipo de processo");
    await userEvent.selectOptions(filtroTipo, "tp-1");
    await userEvent.type(screen.getByLabelText("Data inicial"), "2026-07-01");

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({
        incluir_arquivados: false,
        tipo_processo_id: "tp-1",
        data_inicial: "2026-07-01",
      }),
    );

    await userEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));

    await waitFor(() =>
      expect(listarKanban).toHaveBeenLastCalledWith({ incluir_arquivados: false }),
    );
  });
});
