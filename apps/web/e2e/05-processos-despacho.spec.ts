import { expect, test } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { cadastrarSetor, cadastrarUsuario } from "./helpers/admin";
import { login, logout } from "./helpers/auth";
import { obterUltimoLink } from "./helpers/dev-inbox";

// Servidor exige setor da própria unidade (change setores-e-cadastro-usuario, D2).
const SETOR_PADRAO = { nome: "Gabinete", sigla: "GAB" };
const UNIDADE_PROCESSO = { nome: "Protocolo Central", sigla: "PROTC" };
const TIPO_PROCESSO = { nome: "Protocolo Simples" };
const SERVIDOR_A = {
  nome: "Servidor Protocolo A",
  email: "servidor.protocolo.a@example.com",
  senha: "SenhaProtocoloA1",
};

// Task 4.5 — E2E obrigatório da conclusão (US 2.1, 2.5, 2.4). A conclusão é
// ação própria (change tramitacao-manual) — não depende de despacho nem de
// "última etapa de roteiro": basta clicar "Concluir" e confirmar.
test("Servidor cria processo e conclui diretamente, com registro no histórico", async ({ page }) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_PROCESSO.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_PROCESSO.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_PROCESSO.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO.nome, exact: true })).toBeVisible();

  // Servidor vinculado à nova unidade.
  await cadastrarSetor(page, UNIDADE_PROCESSO.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_A.nome,
    email: SERVIDOR_A.email,
    unidadeNome: UNIDADE_PROCESSO.nome,
    setor: SETOR_PADRAO,
  });

  const link = await obterUltimoLink(SERVIDOR_A.email);
  await page.goto(link);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_A.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_A.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);

  await logout(page);
  await login(page, SERVIDOR_A.email, SERVIDOR_A.senha);

  // Criação do processo (US 2.1) — redireciona direto para o detalhe, nasce
  // atribuído ao criador (D1).
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill("Solicitação de protocolo simples");
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();

  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();
  await expect(page.getByText("Solicitação de protocolo simples")).toBeVisible();
  await expect(page.getByText("Aberto")).toBeVisible();

  // Kanban reflete o processo recém-criado na coluna "Aberto" (US 2.3).
  await page.goto("/processos");
  await expect(page.getByText("Solicitação de protocolo simples")).toBeVisible();

  // Conclusão direta a partir de "Aberto" — sem envio prévio (US 2.5 Cen.2).
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Concluir" }).click();
  const modal = page.getByRole("dialog", { name: "Confirmar conclusão" });
  await modal.getByRole("button", { name: "Concluir processo" }).click();

  await expect(page.getByText("Concluído")).toBeVisible();
  await expect(page.getByRole("button", { name: "Tramitar" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Concluir" })).toHaveCount(0);

  // Histórico registra o evento de conclusão (US 2.4).
  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Conclusão")).toBeVisible();
});

const UNIDADE_ORIGEM = { nome: "Coordenação de Origem", sigla: "CORIG" };
const UNIDADE_DESTINO = { nome: "Assessoria Jurídica Destino", sigla: "AJDES" };
const TIPO_PROCESSO_TRAMITACAO = { nome: "Protocolo com Tramitação" };
const SERVIDOR_ORIGEM = {
  nome: "Servidor Origem",
  email: "servidor.origem@example.com",
  senha: "SenhaOrigem1",
};
const SERVIDOR_DESTINO_B = {
  nome: "Servidor Destino B",
  email: "servidor.destino.b@example.com",
  senha: "SenhaDestinoB1",
};
const SERVIDOR_DESTINO_C = {
  nome: "Servidor Destino C",
  email: "servidor.destino.c@example.com",
  senha: "SenhaDestinoC1",
};
const ASSUNTO_TRAMITACAO = "Processo com tramitação completa";

async function abrirTramitacao(page: import("@playwright/test").Page) {
  await page.getByRole("button", { name: "Tramitar" }).click();
  return page.getByRole("dialog", { name: "Tramitar processo" });
}

// Task 8.2 — E2E obrigatório do fluxo completo de tramitação manual (change
// tramitacao-manual, design.md D1-D9): Servidor A cria (aparece no Kanban de
// A) → envia para o Servidor B de outra unidade → B devolve com motivo → A
// reenvia → B reatribui para C do mesmo setor → C conclui. Verifica em cada
// passo o histórico e a notificação do destinatário, incluindo o aviso de
// destino corrigido para A (D8).
test("Servidor A envia, B devolve, A reenvia, B reatribui para C e C conclui — com histórico e notificações", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);

  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_ORIGEM.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_ORIGEM.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_ORIGEM.nome })).toBeVisible();

  await page.getByLabel("Nome", { exact: true }).fill(UNIDADE_DESTINO.nome);
  await page.getByLabel("Sigla").fill(UNIDADE_DESTINO.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: UNIDADE_DESTINO.nome })).toBeVisible();

  await page.goto("/admin/tipos-processo");
  await page.getByLabel("Nome do tipo de processo").fill(TIPO_PROCESSO_TRAMITACAO.nome);
  await page.getByRole("button", { name: "Cadastrar tipo de processo" }).click();
  await expect(page.getByRole("cell", { name: TIPO_PROCESSO_TRAMITACAO.nome, exact: true })).toBeVisible();

  await cadastrarSetor(page, UNIDADE_ORIGEM.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_ORIGEM.nome,
    email: SERVIDOR_ORIGEM.email,
    unidadeNome: UNIDADE_ORIGEM.nome,
    setor: SETOR_PADRAO,
  });

  // B e C no MESMO setor da unidade destino (a Reatribuição de B para C
  // exige mesma unidade, D2 — e o cenário pede "do mesmo setor").
  await cadastrarSetor(page, UNIDADE_DESTINO.nome, SETOR_PADRAO);
  await cadastrarUsuario(page, {
    nome: SERVIDOR_DESTINO_B.nome,
    email: SERVIDOR_DESTINO_B.email,
    unidadeNome: UNIDADE_DESTINO.nome,
    setor: SETOR_PADRAO,
  });
  await cadastrarUsuario(page, {
    nome: SERVIDOR_DESTINO_C.nome,
    email: SERVIDOR_DESTINO_C.email,
    unidadeNome: UNIDADE_DESTINO.nome,
    setor: SETOR_PADRAO,
  });

  const linkOrigem = await obterUltimoLink(SERVIDOR_ORIGEM.email);
  await page.goto(linkOrigem);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_ORIGEM.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_ORIGEM.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  const linkB = await obterUltimoLink(SERVIDOR_DESTINO_B.email);
  await page.goto(linkB);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_DESTINO_B.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_DESTINO_B.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  const linkC = await obterUltimoLink(SERVIDOR_DESTINO_C.email);
  await page.goto(linkC);
  await page.getByLabel("Nova senha", { exact: true }).fill(SERVIDOR_DESTINO_C.senha);
  await page.getByLabel("Confirmar nova senha").fill(SERVIDOR_DESTINO_C.senha);
  await page.getByRole("button", { name: "Ativar conta" }).click();
  await expect(page).toHaveURL(/\/perfil$/);
  await logout(page);

  // Servidor A cria o processo — aparece no Kanban dele (D1: nasce atribuído ao criador).
  await login(page, SERVIDOR_ORIGEM.email, SERVIDOR_ORIGEM.senha);
  await page.goto("/processos/novo");
  await page.getByLabel("Assunto").fill(ASSUNTO_TRAMITACAO);
  await page.getByLabel("Tipo de processo").selectOption({ label: TIPO_PROCESSO_TRAMITACAO.nome });
  await page.getByLabel("Prazo (dias corridos)").fill("10");
  await page.getByRole("button", { name: "Criar processo" }).click();
  await expect(page).toHaveURL(/\/processos\/[0-9a-f-]+$/);
  const urlProcesso = page.url();

  await page.goto("/processos");
  await expect(page.getByText(ASSUNTO_TRAMITACAO)).toBeVisible();

  // A envia para B, de outra unidade (Envio com destino explícito).
  await page.goto(urlProcesso);
  const modalEnvio1 = await abrirTramitacao(page);
  await modalEnvio1.getByLabel("Unidade de destino").selectOption({ label: UNIDADE_DESTINO.nome });
  await modalEnvio1.getByLabel("Setor de destino").selectOption({ label: SETOR_PADRAO.nome });
  await modalEnvio1.getByLabel("Servidor de destino").selectOption({ label: SERVIDOR_DESTINO_B.nome });
  await modalEnvio1.getByLabel("Mensagem").fill("Segue para análise");
  await modalEnvio1.getByRole("button", { name: "Enviar" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo enviado para ${UNIDADE_DESTINO.sigla}.`)).toBeVisible();
  await logout(page);

  // B recebe a notificação de novo processo.
  await login(page, SERVIDOR_DESTINO_B.email, SERVIDOR_DESTINO_B.senha);
  await expect(page.getByTestId("notificacoes-contador")).toHaveText("1");
  await page.getByLabel("Notificações").click();
  await expect(page.getByRole("button", { name: new RegExp(ASSUNTO_TRAMITACAO) })).toBeVisible();

  // B abre o processo, vê o histórico com o Envio e a mensagem, e devolve com motivo.
  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Envio")).toBeVisible();
  await expect(page.getByText("Mensagem: Segue para análise")).toBeVisible();

  const modalDevolucao = await abrirTramitacao(page);
  await modalDevolucao.getByLabel("Tipo de ação").selectOption("devolver");
  await modalDevolucao.getByLabel("Motivo").selectOption({ label: "Documentação insuficiente" });
  await modalDevolucao.getByLabel("Justificativa (opcional)").fill("Faltam documentos");
  await modalDevolucao.getByRole("button", { name: "Confirmar devolução" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo devolvido para ${UNIDADE_ORIGEM.sigla}.`)).toBeVisible();
  await logout(page);

  // A reenvia o processo, de volta a B.
  await login(page, SERVIDOR_ORIGEM.email, SERVIDOR_ORIGEM.senha);
  await page.goto(urlProcesso);
  const modalEnvio2 = await abrirTramitacao(page);
  await modalEnvio2.getByLabel("Unidade de destino").selectOption({ label: UNIDADE_DESTINO.nome });
  await modalEnvio2.getByLabel("Setor de destino").selectOption({ label: SETOR_PADRAO.nome });
  await modalEnvio2.getByLabel("Servidor de destino").selectOption({ label: SERVIDOR_DESTINO_B.nome });
  await modalEnvio2.getByRole("button", { name: "Enviar" }).click();
  await expect(page).toHaveURL(/\/processos$/);
  await expect(page.getByText(`Processo enviado para ${UNIDADE_DESTINO.sigla}.`)).toBeVisible();
  await logout(page);

  // B reatribui para C, do mesmo setor — unidade fica travada (readonly, D2).
  await login(page, SERVIDOR_DESTINO_B.email, SERVIDOR_DESTINO_B.senha);
  await page.goto(urlProcesso);
  const modalReatribuicao = await abrirTramitacao(page);
  await modalReatribuicao.getByLabel("Tipo de ação").selectOption("reatribuir");
  await expect(modalReatribuicao.getByLabel("Unidade")).toBeDisabled();
  await expect(modalReatribuicao.getByLabel("Unidade")).toHaveValue(UNIDADE_DESTINO.nome);
  await modalReatribuicao.getByLabel("Setor de destino").selectOption({ label: SETOR_PADRAO.nome });
  await modalReatribuicao
    .getByLabel("Servidor de destino")
    .selectOption({ label: SERVIDOR_DESTINO_C.nome });
  await modalReatribuicao.getByLabel("Justificativa").fill("Processo é do C, não do B");
  await modalReatribuicao.getByRole("button", { name: "Reatribuir" }).click();

  // Reatribuição não muda de unidade — permanece na tela, com prazo mantido (D9).
  await expect(page.getByText("Processo reatribuído. O prazo foi mantido.")).toBeVisible();
  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Reatribuição")).toBeVisible();
  await expect(page.getByText("Justificativa: Processo é do C, não do B")).toBeVisible();
  await logout(page);

  // A (remetente original do segundo envio) recebe o aviso de destino corrigido (D8).
  await login(page, SERVIDOR_ORIGEM.email, SERVIDOR_ORIGEM.senha);
  await expect(page.getByTestId("notificacoes-contador")).toHaveText("1");
  await page.getByLabel("Notificações").click();
  const itemDestinoCorrigido = page.getByRole("button", { name: new RegExp(ASSUNTO_TRAMITACAO) });
  await expect(itemDestinoCorrigido.getByText("Destino da tramitação corrigido")).toBeVisible();
  await logout(page);

  // C recebe a notificação de reatribuição, abre o processo e conclui.
  await login(page, SERVIDOR_DESTINO_C.email, SERVIDOR_DESTINO_C.senha);
  await expect(page.getByTestId("notificacoes-contador")).toHaveText("1");
  await page.getByLabel("Notificações").click();
  const itemReatribuido = page.getByRole("button", { name: new RegExp(ASSUNTO_TRAMITACAO) });
  await expect(itemReatribuido.getByText("Reatribuído para você")).toBeVisible();

  await page.goto(urlProcesso);
  await page.getByRole("button", { name: "Concluir" }).click();
  await page
    .getByRole("dialog", { name: "Confirmar conclusão" })
    .getByRole("button", { name: "Concluir processo" })
    .click();
  await expect(page.getByText("Concluído")).toBeVisible();

  await page.getByRole("button", { name: "Histórico" }).click();
  await expect(page.getByText("Conclusão")).toBeVisible();
});
