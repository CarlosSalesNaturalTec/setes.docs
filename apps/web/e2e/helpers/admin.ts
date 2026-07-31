import { expect, type Page } from "@playwright/test";

// Cadastros administrativos usados por vários fluxos. Depois do change
// setores-e-cadastro-usuario, o cadastro de usuário vive num **modal** (D6) e
// o perfil Servidor exige **setor** da própria unidade (D2) — centralizar aqui
// evita repetir essa mecânica em cada spec.

export async function cadastrarUnidade(
  page: Page,
  unidade: { nome: string; sigla: string },
): Promise<void> {
  await page.goto("/admin/unidades");
  await page.getByLabel("Nome", { exact: true }).fill(unidade.nome);
  await page.getByLabel("Sigla", { exact: true }).fill(unidade.sigla);
  await page.getByRole("button", { name: "Cadastrar unidade" }).click();
  await expect(page.getByRole("cell", { name: unidade.nome, exact: true })).toBeVisible();
}

/**
 * Cadastra um setor na unidade indicada (Administrador). Idempotente: a sigla
 * é única dentro da unidade (D1), então recadastrar seria rejeitado — vários
 * fluxos chamam este helper para a mesma unidade.
 */
export async function cadastrarSetor(
  page: Page,
  unidadeNome: string,
  setor: { nome: string; sigla: string },
): Promise<void> {
  await page.goto("/admin/unidades");
  const linha = page
    .getByRole("row")
    .filter({ has: page.getByRole("cell", { name: unidadeNome, exact: true }) });
  await linha.getByRole("button", { name: "Setores" }).click();

  const jaExiste = page.getByRole("button", { name: `Editar setor ${setor.sigla}` });
  await expect(page.getByRole("button", { name: "Cadastrar setor" })).toBeVisible();
  if (await jaExiste.count()) return;

  await page.getByLabel("Nome do setor").fill(setor.nome);
  await page.getByLabel("Sigla do setor").fill(setor.sigla);
  await page.getByRole("button", { name: "Cadastrar setor" }).click();
  await expect(jaExiste).toBeVisible();
}

/**
 * Cadastra um usuário pelo modal "Novo usuário" e aguarda a confirmação de
 * envio do e-mail de primeiro acesso.
 */
export async function cadastrarUsuario(
  page: Page,
  usuario: {
    nome: string;
    email: string;
    perfil?: "servidor" | "gestor" | "administrador";
    unidadeNome?: string;
    setor?: { nome: string; sigla: string };
  },
): Promise<void> {
  await page.goto("/admin/usuarios");
  await page.getByRole("button", { name: "Novo usuário" }).click();

  const modal = page.getByRole("dialog", { name: "Novo usuário" });
  await modal.getByLabel("Nome", { exact: true }).fill(usuario.nome);
  await modal.getByLabel("E-mail").fill(usuario.email);
  if (usuario.perfil && usuario.perfil !== "servidor") {
    await modal.getByLabel("Perfil").selectOption(usuario.perfil);
  }
  if (usuario.unidadeNome) {
    await modal.getByLabel("Unidade", { exact: true }).selectOption({ label: usuario.unidadeNome });
  }
  if (usuario.setor) {
    // A cascata Unidade → Setor recarrega a lista; a opção só existe depois.
    await modal
      .getByLabel(/^Setor/)
      .selectOption({ label: `${usuario.setor.nome} (${usuario.setor.sigla})` });
  }
  await modal.getByRole("button", { name: "Cadastrar usuário" }).click();

  await expect(
    page.getByText(`Usuário cadastrado. Um e-mail de primeiro acesso foi enviado para ${usuario.email}.`),
  ).toBeVisible();
}
