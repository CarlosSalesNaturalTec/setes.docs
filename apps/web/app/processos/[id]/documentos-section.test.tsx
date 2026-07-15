import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { listarDocumentos, anexarDocumento, removerDocumento, baixarDocumento, conteudoDocumento } =
  vi.hoisted(() => ({
    listarDocumentos: vi.fn(),
    anexarDocumento: vi.fn(),
    removerDocumento: vi.fn(),
    baixarDocumento: vi.fn(),
    conteudoDocumento: vi.fn(),
  }));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      listarDocumentos,
      anexarDocumento,
      removerDocumento,
      baixarDocumento,
      conteudoDocumento,
    },
  };
});

import { DocumentosSection, podeRemoverDocumento } from "./documentos-section";

const DOC_PDF = {
  id: "doc-1",
  processo_id: "proc-1",
  nome_exibicao: "parecer.pdf",
  tipo_conteudo: "application/pdf",
  tamanho_bytes: 2048,
  anexado_por_id: "user-1",
  anexado_em: "2026-07-15T10:00:00Z",
};

const EVENTO_DESPACHO = {
  id: "ev-1",
  tipo_evento: "despacho",
  unidade_origem_id: "un-1",
  unidade_destino_id: "un-2",
  responsavel_id: "user-1",
  status_resultante: "em_tramitacao",
  motivo: null,
  justificativa: null,
  criado_em: "2026-07-15T09:00:00Z",
};

const EVENTO_DEVOLUCAO = {
  id: "ev-2",
  tipo_evento: "devolucao",
  unidade_origem_id: "un-2",
  unidade_destino_id: "un-1",
  responsavel_id: "user-2",
  status_resultante: "em_tramitacao",
  motivo: "correcao_dados",
  justificativa: null,
  criado_em: "2026-07-15T10:00:00Z",
};

beforeEach(() => {
  listarDocumentos.mockReset();
  anexarDocumento.mockReset();
  removerDocumento.mockReset();
  baixarDocumento.mockReset();
  conteudoDocumento.mockReset();
  global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
  global.URL.revokeObjectURL = vi.fn();
});

describe("DocumentosSection", () => {
  it("mostra o estado vazio quando não há documentos", async () => {
    listarDocumentos.mockResolvedValue({ items: [] });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);

    expect(await screen.findByText("Nenhum documento anexado.")).toBeInTheDocument();
  });

  it("lista os documentos anexados com nome, tipo, tamanho e data (US 3.1 Cen.1)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);

    expect(await screen.findByText("parecer.pdf")).toBeInTheDocument();
    expect(screen.getByText(/2\.0 KB/)).toBeInTheDocument();
  });

  it("anexa um documento e recarrega a lista (US 3.1 Cen.1)", async () => {
    listarDocumentos.mockResolvedValueOnce({ items: [] }).mockResolvedValue({ items: [DOC_PDF] });
    anexarDocumento.mockResolvedValue(DOC_PDF);

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("Nenhum documento anexado.");

    const input = screen.getByLabelText("Anexar Documento");
    const arquivo = new File(["conteudo"], "parecer.pdf", { type: "application/pdf" });
    await userEvent.upload(input, arquivo);

    await waitFor(() => expect(anexarDocumento).toHaveBeenCalledWith("proc-1", arquivo));
    expect(await screen.findByText("parecer.pdf")).toBeInTheDocument();
  });

  it("exibe o erro do backend ao rejeitar o upload (US 3.1 Cen.2)", async () => {
    listarDocumentos.mockResolvedValue({ items: [] });
    anexarDocumento.mockRejectedValue(new ApiError(422, "Formato de arquivo não permitido"));

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("Nenhum documento anexado.");

    const input = screen.getByLabelText("Anexar Documento");
    const arquivo = new File(["MZ"], "virus.exe", { type: "application/octet-stream" });
    await userEvent.upload(input, arquivo);

    expect(await screen.findByText("Formato de arquivo não permitido")).toBeInTheDocument();
  });

  it("exige confirmação antes de remover e recarrega a lista (US 3.1 Cen.3)", async () => {
    listarDocumentos.mockResolvedValueOnce({ items: [DOC_PDF] }).mockResolvedValue({ items: [] });
    removerDocumento.mockResolvedValue({ ...DOC_PDF, removido_em: "2026-07-15T12:00:00Z" });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Remover" }));
    const modal = await screen.findByRole("dialog", { name: "Remover documento" });
    expect(removerDocumento).not.toHaveBeenCalled();

    await userEvent.click(within(modal).getByRole("button", { name: "Remover" }));

    await waitFor(() => expect(removerDocumento).toHaveBeenCalledWith("proc-1", "doc-1"));
    expect(await screen.findByText("Nenhum documento anexado.")).toBeInTheDocument();
  });

  it("cancelar a remoção não chama a API (US 3.1 Cen.3)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Remover" }));
    const modal = await screen.findByRole("dialog", { name: "Remover documento" });
    await userEvent.click(within(modal).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog", { name: "Remover documento" })).not.toBeInTheDocument();
    expect(removerDocumento).not.toHaveBeenCalled();
  });

  it("oculta a ação Remover quando o processo já foi despachado (US 3.1 Cen.4)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });

    render(
      <DocumentosSection
        processoId="proc-1"
        status="em_tramitacao"
        eventos={[EVENTO_DESPACHO]}
      />,
    );
    await screen.findByText("parecer.pdf");

    expect(screen.queryByRole("button", { name: "Remover" })).not.toBeInTheDocument();
  });

  it("mostra a ação Remover quando o processo voltou por devolução (US 3.1 Cen.4b)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });

    render(
      <DocumentosSection
        processoId="proc-1"
        status="em_tramitacao"
        eventos={[EVENTO_DESPACHO, EVENTO_DEVOLUCAO]}
      />,
    );
    await screen.findByText("parecer.pdf");

    expect(screen.getByRole("button", { name: "Remover" })).toBeInTheDocument();
  });

  it("oculta a ação Remover após redespacho pós-devolução (US 3.1 Cen.4c)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    const redespacho = { ...EVENTO_DESPACHO, id: "ev-3", criado_em: "2026-07-15T11:00:00Z" };

    render(
      <DocumentosSection
        processoId="proc-1"
        status="em_tramitacao"
        eventos={[EVENTO_DESPACHO, EVENTO_DEVOLUCAO, redespacho]}
      />,
    );
    await screen.findByText("parecer.pdf");

    expect(screen.queryByRole("button", { name: "Remover" })).not.toBeInTheDocument();
  });

  it("baixa o documento mantendo nome e formato (US 3.2 Cen.2)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    const blob = new Blob(["conteudo"], { type: "application/pdf" });
    baixarDocumento.mockResolvedValue({ blob, nomeArquivo: "parecer.pdf" });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Baixar" }));

    await waitFor(() => expect(baixarDocumento).toHaveBeenCalledWith("proc-1", "doc-1"));
  });

  it("clicar em DOC/DOCX avisa e dispara download automático (US 3.2 Cen.3)", async () => {
    const docx = {
      ...DOC_PDF,
      id: "doc-2",
      nome_exibicao: "oficio.docx",
      tipo_conteudo: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    };
    listarDocumentos.mockResolvedValue({ items: [docx] });
    const blob = new Blob(["conteudo"], { type: docx.tipo_conteudo });
    baixarDocumento.mockResolvedValue({ blob, nomeArquivo: "oficio.docx" });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("oficio.docx");

    await userEvent.click(screen.getByText("oficio.docx"));

    expect(
      await screen.findByText("Formato não permite visualização inline — o download será iniciado"),
    ).toBeInTheDocument();
    await waitFor(() => expect(baixarDocumento).toHaveBeenCalledWith("proc-1", "doc-2"));
  });

  it("clicar em PDF abre a visualização inline (US 3.2 Cen.1)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    const blob = new Blob(["conteudo"], { type: "application/pdf" });
    conteudoDocumento.mockResolvedValue({ blob, nomeArquivo: "parecer.pdf" });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByText("parecer.pdf"));

    expect(
      await screen.findByRole("dialog", { name: "Visualizar parecer.pdf" }),
    ).toBeInTheDocument();
  });
});

describe("podeRemoverDocumento", () => {
  it("permite quando o processo está aberto", () => {
    expect(podeRemoverDocumento("aberto", [])).toBe(true);
  });

  it("bloqueia quando concluído", () => {
    expect(podeRemoverDocumento("concluido", [])).toBe(false);
  });

  it("bloqueia quando arquivado", () => {
    expect(podeRemoverDocumento("arquivado", [])).toBe(false);
  });
});
