import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const {
  obterProcesso,
  historicoProcesso,
  listarUnidades,
  listarSetores,
  listarServidoresAtivosPorSetor,
  enviarProcesso,
  devolverProcesso,
  reatribuirProcesso,
  concluirProcesso,
  marcarSigilo,
  removerSigilo,
  push,
} = vi.hoisted(() => ({
  obterProcesso: vi.fn(),
  historicoProcesso: vi.fn(),
  listarUnidades: vi.fn(),
  listarSetores: vi.fn(),
  listarServidoresAtivosPorSetor: vi.fn(),
  enviarProcesso: vi.fn(),
  devolverProcesso: vi.fn(),
  reatribuirProcesso: vi.fn(),
  concluirProcesso: vi.fn(),
  marcarSigilo: vi.fn(),
  removerSigilo: vi.fn(),
  push: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "proc-1" }),
  useRouter: () => ({ push }),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

type UsuarioMock = {
  id: string;
  nome: string;
  email: string;
  perfil: string;
  unidade_id: string | null;
};

const USUARIO_SERVIDOR: UsuarioMock = {
  id: "u-1",
  nome: "Servidor",
  email: "s@example.com",
  perfil: "servidor",
  unidade_id: "un-1",
};
let usuarioAtual: UsuarioMock = USUARIO_SERVIDOR;

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ usuario: usuarioAtual }),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      obterProcesso,
      historicoProcesso,
      listarUnidades,
      listarSetores,
      listarServidoresAtivosPorSetor,
      enviarProcesso,
      devolverProcesso,
      reatribuirProcesso,
      concluirProcesso,
      marcarSigilo,
      removerSigilo,
    },
  };
});

import DetalheProcessoPage from "./page";

const PROCESSO_BASE = {
  id: "proc-1",
  numero: "2026/000001",
  assunto: "Pedido de compra de material",
  status: "em_tramitacao",
  unidade_atual_id: "un-1",
  unidade_origem_id: "un-1",
  tipo_processo_id: "tipo-1",
  setor_atual_id: "setor-1",
  servidor_atual_id: "u-1",
  prazo_dias: 10,
  prazo_em: "2026-08-01",
  criado_por_id: "user-1",
  criado_em: "2026-07-15T10:00:00Z",
  concluido_em: null,
  sigiloso: false,
  interessados: [],
};

const HISTORICO_VAZIO = {
  processo_id: "proc-1",
  criado_em: "2026-07-15T10:00:00Z",
  eventos: [],
  mensagem_vazio: "Nenhuma movimentação registrada",
};

const SETORES_AJUR = [{ id: "setor-2", unidade_id: "un-2", nome: "Análise", sigla: "ANL", ativo: true }];
const SERVIDORES_SETOR_2 = [{ id: "u-2", nome: "Maria Silva" }];

describe("DetalheProcessoPage", () => {
  beforeEach(() => {
    usuarioAtual = USUARIO_SERVIDOR;
    obterProcesso.mockReset();
    historicoProcesso.mockReset();
    listarUnidades.mockReset();
    listarSetores.mockReset();
    listarServidoresAtivosPorSetor.mockReset();
    enviarProcesso.mockReset();
    devolverProcesso.mockReset();
    reatribuirProcesso.mockReset();
    concluirProcesso.mockReset();
    marcarSigilo.mockReset();
    removerSigilo.mockReset();
    push.mockReset();
    listarUnidades.mockResolvedValue([
      { id: "un-1", nome: "COFIN", sigla: "COFIN", ativo: true },
      { id: "un-2", nome: "AJUR", sigla: "AJUR", ativo: true },
    ]);
    listarSetores.mockResolvedValue(SETORES_AJUR);
    listarServidoresAtivosPorSetor.mockResolvedValue(SERVIDORES_SETOR_2);
    historicoProcesso.mockResolvedValue(HISTORICO_VAZIO);
  });

  it("Servidor fora da unidade atual vê o detalhe em modo leitura, sem controles de ação (change visibilidade-processos-origem, D2/D5)", async () => {
    obterProcesso.mockResolvedValue({ ...PROCESSO_BASE, unidade_atual_id: "un-2" });

    render(<DetalheProcessoPage />);

    expect(
      await screen.findByText(
        "Acompanhamento em modo leitura — este processo está atualmente em outra unidade.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tramitar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Concluir" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar como Sigiloso" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remover Sigilo" })).not.toBeInTheDocument();
  });

  it("Servidor na própria unidade atual não vê o aviso de modo leitura", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);

    await screen.findByRole("button", { name: "Tramitar" });
    expect(
      screen.queryByText(
        "Acompanhamento em modo leitura — este processo está atualmente em outra unidade.",
      ),
    ).not.toBeInTheDocument();
  });

  it("cascata unidade→setor→servidor no Envio, e envia com destino explícito", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    enviarProcesso.mockResolvedValue({ ...PROCESSO_BASE, unidade_atual_id: "un-2" });

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));

    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    // Tipo de ação já inicia em "Envio" — cascata começa vazia.
    expect(within(modal).queryByLabelText("Setor de destino")).toBeDisabled();

    await userEvent.selectOptions(within(modal).getByLabelText("Unidade de destino"), "un-2");
    await waitFor(() => expect(listarSetores).toHaveBeenCalledWith("un-2", true));
    await userEvent.selectOptions(within(modal).getByLabelText("Setor de destino"), "setor-2");
    await waitFor(() => expect(listarServidoresAtivosPorSetor).toHaveBeenCalledWith("setor-2"));
    await userEvent.selectOptions(within(modal).getByLabelText("Servidor de destino"), "u-2");
    await userEvent.type(within(modal).getByLabelText("Mensagem"), "Segue para análise");
    await userEvent.click(within(modal).getByRole("button", { name: "Enviar" }));

    await waitFor(() =>
      expect(enviarProcesso).toHaveBeenCalledWith("proc-1", {
        unidade_destino_id: "un-2",
        setor_destino_id: "setor-2",
        servidor_destino_id: "u-2",
        mensagem: "Segue para análise",
      }),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos?acao=envio&destino=AJUR"));
  });

  it("bloqueia o envio para o próprio servidor atual antes de chamar a API", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    listarServidoresAtivosPorSetor.mockResolvedValue([{ id: "u-1", nome: "Eu mesmo" }]);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });

    await userEvent.selectOptions(within(modal).getByLabelText("Unidade de destino"), "un-2");
    await userEvent.selectOptions(within(modal).getByLabelText("Setor de destino"), "setor-2");
    await userEvent.selectOptions(within(modal).getByLabelText("Servidor de destino"), "u-1");
    await userEvent.click(within(modal).getByRole("button", { name: "Enviar" }));

    expect(
      within(modal).getByText("O destino deve ser um servidor diferente do responsável atual."),
    ).toBeInTheDocument();
    expect(enviarProcesso).not.toHaveBeenCalled();
  });

  it("campos condicionais mudam conforme o tipo de ação selecionado", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });

    expect(within(modal).getByLabelText("Unidade de destino")).toBeInTheDocument();

    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "devolver");
    expect(within(modal).queryByLabelText("Unidade de destino")).not.toBeInTheDocument();
    expect(within(modal).getByLabelText("Motivo")).toBeInTheDocument();
    expect(
      within(modal).getByText("O processo será devolvido automaticamente para quem o enviou."),
    ).toBeInTheDocument();

    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "reatribuir");
    expect(within(modal).queryByLabelText("Motivo")).not.toBeInTheDocument();
    expect(within(modal).getByLabelText("Justificativa")).toBeInTheDocument();
  });

  it("unidade fica travada (readonly) na Reatribuição — é sempre a unidade atual", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "reatribuir");

    const campoUnidade = within(modal).getByLabelText("Unidade") as HTMLInputElement;
    expect(campoUnidade).toBeDisabled();
    expect(campoUnidade.value).toBe("COFIN");
    await waitFor(() => expect(listarSetores).toHaveBeenCalledWith("un-1", true));
  });

  it("reatribuição preserva status/prazo e informa que o prazo foi mantido", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    listarSetores.mockResolvedValue([{ id: "setor-3", unidade_id: "un-1", nome: "Protocolo", sigla: "PROT", ativo: true }]);
    listarServidoresAtivosPorSetor.mockResolvedValue([{ id: "u-3", nome: "João Souza" }]);
    reatribuirProcesso.mockResolvedValue({ ...PROCESSO_BASE, setor_atual_id: "setor-3", servidor_atual_id: "u-3" });

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "reatribuir");
    await userEvent.selectOptions(within(modal).getByLabelText("Setor de destino"), "setor-3");
    await userEvent.selectOptions(within(modal).getByLabelText("Servidor de destino"), "u-3");
    await userEvent.type(within(modal).getByLabelText("Justificativa"), "Atribuído por engano");
    await userEvent.click(within(modal).getByRole("button", { name: "Reatribuir" }));

    await waitFor(() =>
      expect(reatribuirProcesso).toHaveBeenCalledWith("proc-1", {
        setor_destino_id: "setor-3",
        servidor_destino_id: "u-3",
        justificativa: "Atribuído por engano",
      }),
    );
    expect(await screen.findByText("Processo reatribuído. O prazo foi mantido.")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("exige seleção de motivo antes de confirmar a Devolução (PRD US 2.2b Cen.3)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "devolver");
    await userEvent.click(within(modal).getByRole("button", { name: "Confirmar devolução" }));

    expect(within(modal).getByText("Selecione um motivo para a devolução")).toBeInTheDocument();
    expect(devolverProcesso).not.toHaveBeenCalled();

    await userEvent.selectOptions(within(modal).getByLabelText("Motivo"), "documentacao_insuficiente");
    await userEvent.click(within(modal).getByRole("button", { name: "Confirmar devolução" }));

    await waitFor(() =>
      expect(devolverProcesso).toHaveBeenCalledWith("proc-1", {
        motivo: "documentacao_insuficiente",
        justificativa: null,
      }),
    );
  });

  it("devolução que muda a unidade exibe sucesso e navega ao Kanban (PRD US 2.2b)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    devolverProcesso.mockResolvedValue({
      ...PROCESSO_BASE,
      unidade_atual_id: "un-2",
      status: "em_tramitacao",
    });

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    await userEvent.selectOptions(within(modal).getByLabelText("Tipo de ação"), "devolver");
    await userEvent.selectOptions(within(modal).getByLabelText("Motivo"), "documentacao_insuficiente");
    await userEvent.click(within(modal).getByRole("button", { name: "Confirmar devolução" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos?acao=devolucao&destino=AJUR"));
  });

  it("botão Concluir abre confirmação própria e conclui o processo (US 2.5)", async () => {
    obterProcesso
      .mockResolvedValueOnce(PROCESSO_BASE)
      .mockResolvedValue({ ...PROCESSO_BASE, status: "concluido", concluido_em: "2026-07-16T10:00:00Z" });
    concluirProcesso.mockResolvedValue({ ...PROCESSO_BASE, status: "concluido" });

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Concluir" }));

    const modal = await screen.findByRole("dialog", { name: "Confirmar conclusão" });
    await userEvent.click(within(modal).getByRole("button", { name: "Concluir processo" }));

    await waitFor(() => expect(concluirProcesso).toHaveBeenCalledWith("proc-1"));
    expect(await screen.findByText("Concluído")).toBeInTheDocument();
  });

  it("Gestor vê Reatribuir e Concluir, mas não Envio/Devolução (tasks.md migracao-regiao-us-central1 6.5)", async () => {
    usuarioAtual = {
      id: "g-1",
      nome: "Gestora",
      email: "g@example.com",
      perfil: "gestor",
      unidade_id: null,
    };
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    listarSetores.mockResolvedValue([
      { id: "setor-3", unidade_id: "un-1", nome: "Protocolo", sigla: "PROT", ativo: true },
    ]);
    listarServidoresAtivosPorSetor.mockResolvedValue([{ id: "u-3", nome: "João Souza" }]);
    reatribuirProcesso.mockResolvedValue({
      ...PROCESSO_BASE,
      setor_atual_id: "setor-3",
      servidor_atual_id: "u-3",
    });

    render(<DetalheProcessoPage />);
    expect(await screen.findByRole("button", { name: "Reatribuir" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Concluir" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tramitar" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reatribuir" }));
    const modal = await screen.findByRole("dialog", { name: "Reatribuir processo" });
    expect(within(modal).queryByLabelText("Tipo de ação")).not.toBeInTheDocument();

    await userEvent.selectOptions(within(modal).getByLabelText("Setor de destino"), "setor-3");
    await userEvent.selectOptions(within(modal).getByLabelText("Servidor de destino"), "u-3");
    await userEvent.type(within(modal).getByLabelText("Justificativa"), "Atribuído por engano");
    await userEvent.click(within(modal).getByRole("button", { name: "Reatribuir" }));

    await waitFor(() =>
      expect(reatribuirProcesso).toHaveBeenCalledWith("proc-1", {
        setor_destino_id: "setor-3",
        servidor_destino_id: "u-3",
        justificativa: "Atribuído por engano",
      }),
    );
  });

  it("cancelar a confirmação de conclusão não altera nada (US 2.5)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Concluir" }));
    const modal = await screen.findByRole("dialog", { name: "Confirmar conclusão" });
    await userEvent.click(within(modal).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog", { name: "Confirmar conclusão" })).not.toBeInTheDocument();
    expect(concluirProcesso).not.toHaveBeenCalled();
    expect(screen.getByText("Em Tramitação")).toBeInTheDocument();
  });

  it("falha real do envio exibe erro sem navegar (PRD US 2.2)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    enviarProcesso.mockRejectedValue(
      new ApiError(403, "Acesso negado — você não tem permissão para realizar esta ação."),
    );

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Tramitar" }));
    const modal = await screen.findByRole("dialog", { name: "Tramitar processo" });
    await userEvent.selectOptions(within(modal).getByLabelText("Unidade de destino"), "un-2");
    await userEvent.selectOptions(within(modal).getByLabelText("Setor de destino"), "setor-2");
    await userEvent.selectOptions(within(modal).getByLabelText("Servidor de destino"), "u-2");
    await userEvent.click(within(modal).getByRole("button", { name: "Enviar" }));

    expect(
      await within(modal).findByText("Acesso negado — você não tem permissão para realizar esta ação."),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("exibe o estado vazio do histórico para processo recém-criado (PRD US 2.4 Cen.2)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await screen.findByRole("button", { name: "Tramitar" });
    await userEvent.click(screen.getByRole("button", { name: "Histórico" }));

    expect(await screen.findByText(/Nenhuma movimentação registrada/)).toBeInTheDocument();
  });

  it("renderiza o histórico distinguindo Envio, Devolução, Reatribuição e Conclusão (PRD US 2.4)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);
    historicoProcesso.mockResolvedValue({
      processo_id: "proc-1",
      criado_em: "2026-07-15T10:00:00Z",
      eventos: [
        {
          id: "ev-1",
          tipo_evento: "envio",
          unidade_origem_id: "un-1",
          unidade_destino_id: "un-2",
          setor_origem_id: "setor-1",
          setor_destino_id: "setor-2",
          servidor_origem_id: "u-1",
          servidor_destino_id: "u-2",
          responsavel_id: "u-1",
          status_resultante: "em_tramitacao",
          motivo: null,
          justificativa: null,
          mensagem: "Segue para análise",
          criado_em: "2026-07-15T11:00:00Z",
        },
        {
          id: "ev-2",
          tipo_evento: "devolucao",
          unidade_origem_id: "un-2",
          unidade_destino_id: "un-1",
          setor_origem_id: "setor-2",
          setor_destino_id: "setor-1",
          servidor_origem_id: "u-2",
          servidor_destino_id: "u-1",
          responsavel_id: "u-2",
          status_resultante: "em_tramitacao",
          motivo: "documentacao_insuficiente",
          justificativa: "Faltam anexos",
          mensagem: null,
          criado_em: "2026-07-15T12:00:00Z",
        },
        {
          id: "ev-3",
          tipo_evento: "reatribuicao",
          unidade_origem_id: "un-1",
          unidade_destino_id: "un-1",
          setor_origem_id: "setor-1",
          setor_destino_id: "setor-3",
          servidor_origem_id: "u-1",
          servidor_destino_id: "u-3",
          responsavel_id: "u-1",
          status_resultante: "em_tramitacao",
          motivo: null,
          justificativa: "Setor errado",
          mensagem: null,
          criado_em: "2026-07-15T13:00:00Z",
        },
      ],
      mensagem_vazio: null,
    });

    render(<DetalheProcessoPage />);
    await screen.findByRole("button", { name: "Tramitar" });
    await userEvent.click(screen.getByRole("button", { name: "Histórico" }));

    expect(await screen.findByText("Envio")).toBeInTheDocument();
    expect(screen.getByText("Devolução")).toBeInTheDocument();
    expect(screen.getByText("Reatribuição")).toBeInTheDocument();
    expect(screen.getByText("Mensagem: Segue para análise")).toBeInTheDocument();
    expect(screen.getByText("Motivo: documentacao_insuficiente")).toBeInTheDocument();
    expect(screen.getByText("Justificativa: Faltam anexos")).toBeInTheDocument();
    expect(screen.getByText("Justificativa: Setor errado")).toBeInTheDocument();
  });

  it("exibe o indicador de sigilo e a ação de remover quando o processo é sigiloso (PRD US 2.6 Cen.3)", async () => {
    obterProcesso.mockResolvedValue({ ...PROCESSO_BASE, sigiloso: true });

    render(<DetalheProcessoPage />);

    expect(await screen.findByLabelText("Sigiloso")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Remover Sigilo" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marcar como Sigiloso" })).not.toBeInTheDocument();
  });

  it("não exibe o indicador e mostra a ação de marcar quando o processo não é sigiloso (PRD US 2.6 Cen.1)", async () => {
    obterProcesso.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);

    await screen.findByRole("button", { name: "Marcar como Sigiloso" });
    expect(screen.queryByLabelText("Sigiloso")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remover Sigilo" })).not.toBeInTheDocument();
  });

  it("marcar como sigiloso atualiza o indicador e a ação sem recarregar a página (PRD US 2.6 Cen.1)", async () => {
    obterProcesso
      .mockResolvedValueOnce(PROCESSO_BASE)
      .mockResolvedValue({ ...PROCESSO_BASE, sigiloso: true });
    marcarSigilo.mockResolvedValue({ ...PROCESSO_BASE, sigiloso: true });

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Marcar como Sigiloso" }));

    await waitFor(() => expect(marcarSigilo).toHaveBeenCalledWith("proc-1"));
    expect(await screen.findByRole("button", { name: "Remover Sigilo" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Sigiloso")).toBeInTheDocument();
  });

  it("remover sigilo atualiza o indicador e a ação sem recarregar a página (PRD US 2.6 Cen.2)", async () => {
    obterProcesso
      .mockResolvedValueOnce({ ...PROCESSO_BASE, sigiloso: true })
      .mockResolvedValue(PROCESSO_BASE);
    removerSigilo.mockResolvedValue(PROCESSO_BASE);

    render(<DetalheProcessoPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Remover Sigilo" }));

    await waitFor(() => expect(removerSigilo).toHaveBeenCalledWith("proc-1"));
    expect(await screen.findByRole("button", { name: "Marcar como Sigiloso" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Sigiloso")).not.toBeInTheDocument();
  });
});
