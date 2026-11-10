import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

const {
  listarDocumentos,
  anexarDocumento,
  removerDocumento,
  baixarDocumento,
  conteudoDocumento,
  verificarAssinatura,
} = vi.hoisted(() => ({
  listarDocumentos: vi.fn(),
  anexarDocumento: vi.fn(),
  removerDocumento: vi.fn(),
  baixarDocumento: vi.fn(),
  conteudoDocumento: vi.fn(),
  verificarAssinatura: vi.fn(),
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
      verificarAssinatura,
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
  tipo_evento: "envio",
  unidade_origem_id: "un-1",
  unidade_destino_id: "un-2",
  setor_origem_id: "setor-1",
  setor_destino_id: "setor-2",
  servidor_origem_id: "user-1",
  servidor_destino_id: "user-2",
  responsavel_id: "user-1",
  status_resultante: "em_tramitacao",
  motivo: null,
  justificativa: null,
  mensagem: null,
  criado_em: "2026-07-15T09:00:00Z",
};

const EVENTO_DEVOLUCAO = {
  id: "ev-2",
  tipo_evento: "devolucao",
  unidade_origem_id: "un-2",
  unidade_destino_id: "un-1",
  setor_origem_id: "setor-2",
  setor_destino_id: "setor-1",
  servidor_origem_id: "user-2",
  servidor_destino_id: "user-1",
  responsavel_id: "user-2",
  status_resultante: "em_tramitacao",
  motivo: "correcao_dados",
  justificativa: null,
  mensagem: null,
  criado_em: "2026-07-15T10:00:00Z",
};

beforeEach(() => {
  listarDocumentos.mockReset();
  anexarDocumento.mockReset();
  removerDocumento.mockReset();
  baixarDocumento.mockReset();
  conteudoDocumento.mockReset();
  verificarAssinatura.mockReset();
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

  it("oculta anexar/remover quando somenteLeitura (change visibilidade-processos-origem, D2/D5)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });

    render(
      <DocumentosSection
        processoId="proc-1"
        status="em_tramitacao"
        eventos={[EVENTO_DESPACHO, EVENTO_DEVOLUCAO]}
        somenteLeitura
      />,
    );
    await screen.findByText("parecer.pdf");

    expect(screen.queryByLabelText("Anexar Documento")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remover" })).not.toBeInTheDocument();
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

// --- Verificar Assinatura (change assinatura-verificacao-fundacao, D9) -------

const AVISO_OFICIAL =
  "Esta conferência é feita pelo Despapelize e não substitui o verificador oficial. " +
  "Para o veredito oficial, envie o arquivo ao Verificador de Conformidade do ITI.";

function assinatura(veredito: string, mensagem: string, extra: Record<string, unknown> = {}) {
  return {
    ordem: 1,
    veredito,
    mensagem,
    signatario_nome: "MARIA DE TESTE DA SILVA",
    signatario_cpf: "12345678909",
    autoridade_certificadora: "AC Intermediaria de Teste",
    data_assinatura: "2026-11-10T14:00:00Z",
    origem_data: "declarada",
    autoridade_carimbo: null,
    certificado_expirado_em: null,
    ...extra,
  };
}

function resultado(assinaturas: ReturnType<typeof assinatura>[], resumo: string) {
  return {
    documento_id: "doc-1",
    situacao: "assinado",
    resumo,
    mensagem_resumo: assinaturas.find((a) => a.veredito === resumo)?.mensagem ?? "",
    assinaturas,
    aviso_veredito_oficial: AVISO_OFICIAL,
    url_verificador_oficial: "https://validar.iti.gov.br",
  };
}

async function abrirVerificacao() {
  render(<DocumentosSection processoId="proc-1" status="em_tramitacao" eventos={[]} />);
  await screen.findByText("parecer.pdf");
  await userEvent.click(screen.getByRole("button", { name: "Verificar Assinatura" }));
  return screen.findByRole("region", { name: /Verificação de assinatura/ });
}

describe("Verificar Assinatura", () => {
  it("só oferece a ação para PDF — DOCX e PNG não têm o botão", async () => {
    listarDocumentos.mockResolvedValue({
      items: [
        DOC_PDF,
        {
          ...DOC_PDF,
          id: "doc-2",
          nome_exibicao: "oficio.docx",
          tipo_conteudo: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        },
        { ...DOC_PDF, id: "doc-3", nome_exibicao: "foto.png", tipo_conteudo: "image/png" },
      ],
    });

    render(<DocumentosSection processoId="proc-1" status="aberto" eventos={[]} />);
    await screen.findByText("oficio.docx");

    expect(screen.getAllByRole("button", { name: "Verificar Assinatura" })).toHaveLength(1);
  });

  it("mostra carregamento e depois os dados da assinatura válida com o link do ITI", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    let resolver: (v: unknown) => void = () => {};
    verificarAssinatura.mockReturnValue(new Promise((r) => (resolver = r)));

    const painel = await abrirVerificacao();
    expect(within(painel).getByText("Verificando assinatura…")).toBeInTheDocument();
    resolver(resultado([assinatura("valida", "Assinatura válida — documento íntegro")], "valida"));

    expect(
      await within(painel).findByText("Assinatura válida — documento íntegro"),
    ).toBeInTheDocument();
    expect(verificarAssinatura).toHaveBeenCalledWith("proc-1", "doc-1");
    expect(within(painel).getByText("MARIA DE TESTE DA SILVA")).toBeInTheDocument();
    expect(within(painel).getByText("12345678909")).toBeInTheDocument();
    expect(within(painel).getByText("AC Intermediaria de Teste")).toBeInTheDocument();
    expect(
      within(painel).getByText(/declarada pelo signatário, sem carimbo de tempo/),
    ).toBeInTheDocument();
    const link = within(painel).getByRole("link", { name: "Abrir o verificador oficial do ITI" });
    expect(link).toHaveAttribute("href", "https://validar.iti.gov.br");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(
      within(painel).getByText(new RegExp("não substitui o verificador oficial")),
    ).toBeInTheDocument();
  });

  it.each([
    [
      "invalida",
      "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado",
      "Alerta",
    ],
    [
      "inconclusiva",
      "Verificação inconclusiva — não foi possível confirmar agora a situação do certificado.",
      "Inconclusiva",
    ],
    [
      "fora_icp_brasil",
      "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil — não é uma assinatura qualificada.",
      "Atenção",
    ],
    [
      "alterada_apos_assinatura",
      "Assinatura válida, mas o documento recebeu alterações depois de assinado.",
      "Atenção",
    ],
  ])(
    "renderiza o veredito %s com a mensagem da API e o ícone correspondente",
    async (veredito, mensagem, rotulo) => {
      listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
      verificarAssinatura.mockResolvedValue(resultado([assinatura(veredito, mensagem)], veredito));

      const painel = await abrirVerificacao();

      expect(await within(painel).findByText(mensagem)).toBeInTheDocument();
      expect(within(painel).getByRole("img", { name: rotulo })).toBeInTheDocument();
    },
  );

  it("exibe carimbo de tempo e CPF ausente como não informado", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    verificarAssinatura.mockResolvedValue(
      resultado(
        [
          assinatura("valida", "Assinatura válida — documento íntegro", {
            signatario_cpf: null,
            origem_data: "carimbo",
            autoridade_carimbo: "ACT de Teste",
          }),
        ],
        "valida",
      ),
    );

    const painel = await abrirVerificacao();

    expect(
      await within(painel).findByText(/comprovada por carimbo de tempo — ACT de Teste/),
    ).toBeInTheDocument();
    expect(within(painel).getByText("não informado no certificado")).toBeInTheDocument();
  });

  it("com várias assinaturas mostra o resumo do documento", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    const invalida =
      "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado";
    verificarAssinatura.mockResolvedValue(
      resultado(
        [
          assinatura("valida", "Assinatura válida — documento íntegro"),
          { ...assinatura("invalida", invalida), ordem: 2 },
        ],
        "invalida",
      ),
    );

    const painel = await abrirVerificacao();

    expect(await within(painel).findByTestId("resumo-verificacao")).toHaveTextContent(invalida);
    expect(within(painel).getAllByRole("listitem")).toHaveLength(2);
  });

  it("PDF sem assinatura mostra só a mensagem, sem link do ITI", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    verificarAssinatura.mockResolvedValue({
      documento_id: "doc-1",
      situacao: "sem_assinatura",
      resumo: null,
      mensagem_resumo: "Este documento não contém assinatura digital.",
      assinaturas: [],
      aviso_veredito_oficial: null,
      url_verificador_oficial: null,
    });

    const painel = await abrirVerificacao();

    expect(
      await within(painel).findByText("Este documento não contém assinatura digital."),
    ).toBeInTheDocument();
    expect(within(painel).queryByRole("link")).not.toBeInTheDocument();
  });

  it("exibe o erro da API (ex.: acesso negado)", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    verificarAssinatura.mockRejectedValue(new ApiError(403, "Acesso negado"));

    const painel = await abrirVerificacao();

    expect(await within(painel).findByText("Acesso negado")).toBeInTheDocument();
  });

  it("fechar descarta o resultado e não guarda nada no localStorage", async () => {
    listarDocumentos.mockResolvedValue({ items: [DOC_PDF] });
    verificarAssinatura.mockResolvedValue(
      resultado([assinatura("valida", "Assinatura válida — documento íntegro")], "valida"),
    );
    const setItem = vi.spyOn(Storage.prototype, "setItem");

    const painel = await abrirVerificacao();
    await within(painel).findByText("Assinatura válida — documento íntegro");
    await userEvent.click(within(painel).getByRole("button", { name: "Fechar" }));

    expect(
      screen.queryByRole("region", { name: /Verificação de assinatura/ }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("12345678909")).not.toBeInTheDocument();
    expect(setItem).not.toHaveBeenCalled();
    setItem.mockRestore();
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
