import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { push, listarTiposProcesso, criarProcesso, listarModelos, gerarDocumento } = vi.hoisted(() => ({
  push: vi.fn(),
  listarTiposProcesso: vi.fn(),
  criarProcesso: vi.fn(),
  listarModelos: vi.fn(),
  gerarDocumento: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("@/components/protected-shell", () => ({
  ProtectedShell: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarTiposProcesso, criarProcesso, listarModelos, gerarDocumento },
  };
});

import NovoProcessoPage from "./page";

const TIPO = { id: "tipo-1", nome: "Licitação", ativo: true, prazo_anonimizacao_anos: 5 };
const MODELO = {
  id: "modelo-1",
  nome: "Requerimento padrão",
  categoria: "Pessoal",
  tipo: "requerimento" as const,
  descricao: null,
  conteudo: "<p><b>Requerimento</b> de [NOME DO SOLICITANTE]</p>",
  ativo: true,
  criado_por_id: "admin-1",
  criado_em: "2026-08-01T00:00:00Z",
};

describe("NovoProcessoPage", () => {
  beforeEach(() => {
    push.mockReset();
    criarProcesso.mockReset();
    listarTiposProcesso.mockReset();
    listarTiposProcesso.mockResolvedValue([TIPO]);
    listarModelos.mockReset();
    listarModelos.mockResolvedValue([MODELO]);
    gerarDocumento.mockReset();
    gerarDocumento.mockResolvedValue({
      id: "doc-1",
      processo_id: "proc-1",
      nome_exibicao: "Requerimento padrão.pdf",
      tipo_conteudo: "application/pdf",
      tamanho_bytes: 10,
      anexado_por_id: "u-1",
      anexado_em: "2026-08-01T00:00:00Z",
      modelo_id: MODELO.id,
    });
  });

  it("rejeita submissão sem assunto, tipo ou prazo (PRD US 2.1 Cen.2)", async () => {
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    expect(await screen.findByText("Informe o assunto.")).toBeInTheDocument();
    expect(screen.getByText("Selecione o tipo de processo.")).toBeInTheDocument();
    expect(screen.getByText("Informe um prazo em dias.")).toBeInTheDocument();
    expect(criarProcesso).not.toHaveBeenCalled();
  });

  it("cria o processo com dados válidos e navega para o detalhe", async () => {
    criarProcesso.mockResolvedValue({ id: "proc-1" });
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido de compra de material");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "30");
    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    await waitFor(() =>
      expect(criarProcesso).toHaveBeenCalledWith({
        assunto: "Pedido de compra de material",
        tipo_processo_id: TIPO.id,
        prazo_dias: 30,
        interessados: [],
      }),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos/proc-1"));
    // Criação de processo sem modelo continua disponível e inalterada (US 2.1).
    expect(gerarDocumento).not.toHaveBeenCalled();
  });

  it("ao escolher um modelo, o editor carrega seu conteúdo e o texto é enviado para gerar o documento", async () => {
    criarProcesso.mockResolvedValue({ id: "proc-1" });
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);
    await screen.findByText(MODELO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido com modelo");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "15");
    await userEvent.selectOptions(screen.getByLabelText("Modelo de documento (opcional)"), MODELO.id);

    const editor = screen.getByRole("textbox", { name: "Conteúdo do documento a gerar" });
    expect(editor).toHaveTextContent("Requerimento de [NOME DO SOLICITANTE]");

    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    await waitFor(() =>
      expect(gerarDocumento).toHaveBeenCalledWith("proc-1", {
        modelo_id: MODELO.id,
        conteudo: MODELO.conteudo,
      }),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos/proc-1"));
  });

  it("destaca lacuna pendente no modelo escolhido sem bloquear a geração", async () => {
    criarProcesso.mockResolvedValue({ id: "proc-1" });
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);
    await screen.findByText(MODELO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido com lacuna");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "5");
    await userEvent.selectOptions(screen.getByLabelText("Modelo de documento (opcional)"), MODELO.id);

    expect(screen.getByRole("status")).toHaveTextContent(/1 lacuna\(s\) ainda não preenchida/);

    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    await waitFor(() => expect(gerarDocumento).toHaveBeenCalled());
    await waitFor(() => expect(push).toHaveBeenCalledWith("/processos/proc-1"));
  });

  it("exibe o erro de CPF inválido retornado pela API (PRD US 2.1 Cen.3)", async () => {
    criarProcesso.mockRejectedValue(
      new ApiError(422, "CPF inválido — verifique o número informado"),
    );
    render(<NovoProcessoPage />);
    await screen.findByText(TIPO.nome);

    await userEvent.type(screen.getByLabelText("Assunto"), "Pedido de compra");
    await userEvent.selectOptions(screen.getByLabelText("Tipo de processo"), TIPO.id);
    await userEvent.type(screen.getByLabelText("Prazo (dias corridos)"), "10");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar interessado" }));
    await userEvent.type(screen.getByLabelText("Nome do interessado"), "Fulano de Tal");
    await userEvent.type(screen.getByLabelText("Documento do interessado"), "11111111111");
    await userEvent.click(screen.getByRole("button", { name: "Criar processo" }));

    expect(
      await screen.findByText("CPF inválido — verifique o número informado"),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });
});
