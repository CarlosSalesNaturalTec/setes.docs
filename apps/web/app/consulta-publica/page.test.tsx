import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "@/lib/api";
import ConsultaPublicaPage from "./page";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      consultarProcessoPublico: vi.fn(),
      pesquisarProcessosPublico: vi.fn(),
    },
  };
});

describe("ConsultaPublicaPage", () => {
  beforeEach(() => {
    vi.mocked(api.consultarProcessoPublico).mockReset();
    vi.mocked(api.pesquisarProcessosPublico).mockReset();
  });

  it("exibe o resultado da consulta por número sem renderizar CPF/CNPJ mesmo se presente nos dados", async () => {
    vi.mocked(api.consultarProcessoPublico).mockResolvedValue({
      numero: "2026/000123",
      assunto: "Solicitação de teste",
      tipo_processo: "Licitação",
      status: "aberto",
      unidade_atual: "COFIN",
      criado_em: "2026-01-01T00:00:00Z",
      interessados: [
        // Simula um vazamento hipotético — o componente não deve renderizar
        // esses campos mesmo que estivessem presentes no payload.
        { nome: "Fulano de Tal", documento: "529.982.247-25", tipo_documento: "cpf" } as never,
      ],
      historico: [],
    });

    render(<ConsultaPublicaPage />);
    await userEvent.type(screen.getByLabelText("Número do processo"), "2026/000123");
    await userEvent.click(screen.getByRole("button", { name: "Consultar" }));

    expect(await screen.findByText("Solicitação de teste")).toBeInTheDocument();
    expect(screen.getByText("Fulano de Tal")).toBeInTheDocument();
    expect(screen.queryByText("529.982.247-25")).not.toBeInTheDocument();
    expect(screen.queryByText(/cpf/i)).not.toBeInTheDocument();
  });

  it("exibe a mensagem de vazio quando o número não corresponde a nenhum processo", async () => {
    vi.mocked(api.consultarProcessoPublico).mockRejectedValue(
      new ApiError(404, "Nenhum processo encontrado com o número informado"),
    );

    render(<ConsultaPublicaPage />);
    await userEvent.type(screen.getByLabelText("Número do processo"), "2026/999999");
    await userEvent.click(screen.getByRole("button", { name: "Consultar" }));

    expect(
      await screen.findByText("Nenhum processo encontrado com o número informado"),
    ).toBeInTheDocument();
  });

  it("exibe a mensagem de vazio quando a pesquisa não retorna resultados", async () => {
    vi.mocked(api.pesquisarProcessosPublico).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      mensagem_vazio: "Nenhum processo encontrado para os filtros informados",
    });

    render(<ConsultaPublicaPage />);
    await userEvent.type(screen.getByLabelText("Assunto"), "termo qualquer");
    await userEvent.click(screen.getByRole("button", { name: "Pesquisar" }));

    expect(
      await screen.findByText("Nenhum processo encontrado para os filtros informados"),
    ).toBeInTheDocument();
  });

  it("exibe a mensagem de rate limit quando a API recusa por excesso de requisições", async () => {
    vi.mocked(api.consultarProcessoPublico).mockRejectedValue(
      new ApiError(429, "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente."),
    );

    render(<ConsultaPublicaPage />);
    await userEvent.type(screen.getByLabelText("Número do processo"), "2026/000001");
    await userEvent.click(screen.getByRole("button", { name: "Consultar" }));

    expect(
      await screen.findByText(
        "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente.",
      ),
    ).toBeInTheDocument();
  });
});
