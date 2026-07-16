import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const { listarDocumentosRemovidos, restaurarDocumento } = vi.hoisted(() => ({
  listarDocumentosRemovidos: vi.fn(),
  restaurarDocumento: vi.fn(),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: { listarDocumentosRemovidos, restaurarDocumento },
  };
});

import { DocumentosRemovidosConteudo } from "./page";

const DOC = {
  id: "doc-1",
  processo_id: "proc-1",
  processo_numero: "2026/000123",
  processo_assunto: "Aquisição de material",
  nome_exibicao: "parecer.pdf",
  removido_em: "2026-07-10T10:00:00Z",
  removido_por_id: "user-9",
};

beforeEach(() => {
  listarDocumentosRemovidos.mockReset();
  restaurarDocumento.mockReset();
});

describe("DocumentosRemovidosConteudo", () => {
  it("exibe o estado vazio quando não há documentos em retenção (US 8.7 Cen.3)", async () => {
    listarDocumentosRemovidos.mockResolvedValue({ items: [] });

    render(<DocumentosRemovidosConteudo />);

    expect(await screen.findByText("Nenhum documento em período de retenção")).toBeInTheDocument();
  });

  it("sempre exibe o rodapé de purga permanente (US 8.7 Cen.2)", async () => {
    listarDocumentosRemovidos.mockResolvedValue({ items: [] });

    render(<DocumentosRemovidosConteudo />);

    expect(
      await screen.findByText(
        "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados.",
      ),
    ).toBeInTheDocument();
  });

  it("lista os documentos com nome, processo e responsável", async () => {
    listarDocumentosRemovidos.mockResolvedValue({ items: [DOC] });

    render(<DocumentosRemovidosConteudo />);

    expect(await screen.findByText("parecer.pdf")).toBeInTheDocument();
    expect(screen.getByText("2026/000123")).toBeInTheDocument();
    expect(screen.getByText(/Aquisição de material/)).toBeInTheDocument();
    expect(screen.getByText("user-9")).toBeInTheDocument();
  });

  it("restaura com confirmação e o item some da lista (US 8.7 Cen.1)", async () => {
    listarDocumentosRemovidos
      .mockResolvedValueOnce({ items: [DOC] })
      .mockResolvedValue({ items: [] });
    restaurarDocumento.mockResolvedValue({ id: "doc-1" });

    render(<DocumentosRemovidosConteudo />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Restaurar" }));
    const modal = await screen.findByRole("dialog", { name: "Restaurar documento" });
    expect(restaurarDocumento).not.toHaveBeenCalled();

    await userEvent.click(within(modal).getByRole("button", { name: "Restaurar" }));

    await waitFor(() => expect(restaurarDocumento).toHaveBeenCalledWith("doc-1"));
    expect(await screen.findByText("Nenhum documento em período de retenção")).toBeInTheDocument();
  });

  it("cancelar a restauração não chama a API", async () => {
    listarDocumentosRemovidos.mockResolvedValue({ items: [DOC] });

    render(<DocumentosRemovidosConteudo />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Restaurar" }));
    const modal = await screen.findByRole("dialog", { name: "Restaurar documento" });
    await userEvent.click(within(modal).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog", { name: "Restaurar documento" })).not.toBeInTheDocument();
    expect(restaurarDocumento).not.toHaveBeenCalled();
  });

  it("exibe aviso quando o documento já foi purgado (404, US 8.7 Cen.2)", async () => {
    listarDocumentosRemovidos.mockResolvedValue({ items: [DOC] });
    restaurarDocumento.mockRejectedValue(new ApiError(404, "Documento não encontrado."));

    render(<DocumentosRemovidosConteudo />);
    await screen.findByText("parecer.pdf");

    await userEvent.click(screen.getByRole("button", { name: "Restaurar" }));
    const modal = await screen.findByRole("dialog", { name: "Restaurar documento" });
    await userEvent.click(within(modal).getByRole("button", { name: "Restaurar" }));

    expect(
      await screen.findByText(/não está mais disponível para restauração/),
    ).toBeInTheDocument();
  });
});
