import { expect, test, type Page } from "@playwright/test";

import { ADMIN_ROOT } from "./fixtures";
import { login } from "./helpers/auth";

// Specs móveis rodam no projeto `mobile` (Pixel 5), depois do projeto
// `chromium` — sobre o banco já povoado pelos specs 01-16 (playwright.config.ts,
// D5). Este spec reaproveita o ADMIN_ROOT criado em 01 e não cria estado
// próprio: cobre apenas apresentação (login, gaveta, tabela rolável).
test.use({ viewport: { width: 360, height: 640 } });

/** "A página não rola horizontalmente" (design.md D6) — asserção mecânica. */
async function excedenteHorizontalDaPagina(page: Page): Promise<number> {
  return page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
}

// Task 5.1/5.2 — cobre os cenários "Página não rola horizontalmente" e
// "Tabela larga rola dentro do próprio contêiner" da spec identidade-visual.
test("Administrador loga em viewport de smartphone, abre a gaveta pelo hambúrguer e a tabela de usuários rola no próprio contêiner", async ({
  page,
}) => {
  await login(page, ADMIN_ROOT.email, ADMIN_ROOT.senha);
  expect(await excedenteHorizontalDaPagina(page)).toBeLessThanOrEqual(0);

  // Abaixo de 768 px a gaveta fica fechada por padrão, deslocada para fora do
  // viewport via `-translate-x-full` (components/protected-shell.tsx) — o
  // link continua no DOM (por isso não se usa toBeVisible aqui, que ignora a
  // posição), mas sua caixa fica com x negativo até o botão "Abrir menu" a
  // revelar.
  const linkUsuarios = page.getByRole("link", { name: "Usuários" });
  const caixaFechada = await linkUsuarios.boundingBox();
  expect(caixaFechada?.x).toBeLessThan(0);

  await page.getByRole("button", { name: "Abrir menu" }).click();
  // A gaveta desliza com `transition-transform` (protected-shell.tsx) — a
  // caixa só chega a x >= 0 depois que a transição termina, daí o poll.
  await expect.poll(async () => (await linkUsuarios.boundingBox())?.x).toBeGreaterThanOrEqual(0);
  await linkUsuarios.click();

  await expect(page).toHaveURL(/\/admin\/usuarios$/);
  expect(await excedenteHorizontalDaPagina(page)).toBeLessThanOrEqual(0);

  // A tabela (6 colunas: nome, e-mail, perfil, status, unidade, ações) excede
  // 360 px — o contêiner com overflow-x-auto é quem absorve o excedente (D1, D2).
  const tabela = page.getByRole("table");
  await expect(tabela).toBeVisible();
  const contêiner = tabela.locator("xpath=..");
  const excedenteContêiner = await contêiner.evaluate(
    (el) => el.scrollWidth - el.clientWidth,
  );
  expect(excedenteContêiner).toBeGreaterThan(0);

  await contêiner.evaluate((el) => {
    el.scrollLeft = 100;
  });
  const scrollLeftAposRolagem = await contêiner.evaluate((el) => el.scrollLeft);
  expect(scrollLeftAposRolagem).toBeGreaterThan(0);

  // A rolagem da tabela não vaza para a página.
  expect(await excedenteHorizontalDaPagina(page)).toBeLessThanOrEqual(0);
});
