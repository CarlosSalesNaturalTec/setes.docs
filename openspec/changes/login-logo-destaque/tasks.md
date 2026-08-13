## 1. Asset de marca

- [x] 1.1 Copiar `docs/images/logo_despapelize.jpeg` para
      `apps/web/public/marca/login-hero.jpg`, sem edição (sem recorte, sem remoção
      de fundo, sem alteração de cor). Critério de aceite: arquivo binário idêntico
      ao original, só em novo caminho.
- [x] 1.2 Confirmar as dimensões reais do arquivo copiado (usadas depois no
      `width`/`height` do `next/image`, D2 do design.md). Confirmado: 438×740.

## 2. Implementação do Login

- [x] 2.1 Em `apps/web/app/login/page.tsx`, remover o bloco do chip circular
      (`div` navy + `IconMarca`) e o `<h1>{NOME_PRODUTO}</h1>`; remover o import de
      `IconMarca` deste arquivo (D2/D3 do design.md).
- [x] 2.2 Renderizar `next/image` com `src="/marca/login-hero.jpg"`,
      `alt="Despapelize"`, `width`/`height` das dimensões reais do arquivo (task
      1.2), `priority`, envolto em `<h1>` — sem chip, sem container circular,
      `className` limitando a `max-w-[260px]` mantendo a proporção original (D2/D3).
      Comentário no JSX apontando `docs/images/logo_despapelize.jpeg` como origem
      (D1).
- [x] 2.3 Confirmar que `SUBTITULO_CLIENTE` ("SETES") e "Acesse sua conta"
      continuam renderizados como texto, sem alteração de posição relativa à nova
      imagem.
- [x] 2.4 Confirmar visualmente que nenhum filtro, sombra colorida ou gradiente foi
      aplicado à imagem — ela aparece exatamente como o arquivo de origem (D4).

## 3. Testes automatizados

- [x] 3.1 Rodar `pnpm --filter @setes/web test -- page.test.tsx` (dentro de
      `apps/web`, Vitest) e verificar se
      `getByRole("heading", { name: "Despapelize" })` (linha 41 de
      `login/page.test.tsx`) continua passando sem alteração, já que o nome
      acessível do heading deve herdar o `alt` da imagem descendente (D3).
      Confirmado: passou sem alteração de matcher.
- [x] 3.2 Se 3.1 falhar, ajustar o matcher do teste para localizar a imagem por
      `alt` (ex. `within(getByRole("heading")).getByAltText("Despapelize")`) — sem
      reintroduzir um `<h1>` de texto. Não necessário — 3.1 passou.
- [x] 3.3 Confirmar que os demais testes de `login/page.test.tsx` (SSO ausente,
      login com sucesso, mensagem de erro, mensagem por `motivo`) continuam
      passando sem alteração — eles não dependem do logo. Confirmado: 5/5 testes
      passando.
- [x] 3.4 Estender `apps/web/e2e/01-setup-login.spec.ts` (ou spec de login
      equivalente) com uma verificação de que a imagem de marca (`alt="Despapelize"`)
      é visível na tela de Login — teste E2E Playwright obrigatório por esta tela
      tocar o fluxo de login.
- [x] 3.5 Rodar a suíte E2E do Login (`pnpm --filter @setes/web test:e2e`, ou o
      arquivo específico) localmente antes de abrir PR. Confirmado:
      `e2e/01-setup-login.spec.ts` passou (1/1), com API+Postgres locais e a nova
      asserção de imagem/heading do task 3.4.

## 4. Verificação de viewport e acessibilidade

- [x] 4.1 Verificar em viewport de 360px de largura (requisito de spec já vigente
      "Largura mínima de viewport suportada") que o card do Login — agora mais alto
      por causa da imagem — permanece operável: sem rolagem horizontal da página,
      com e-mail/senha/botão "Entrar" alcançáveis por rolagem vertical. Confirmado
      via Playwright headless em 360×640: `scrollWidth === clientWidth` (360px, sem
      rolagem horizontal) e os três campos com bounding box válida no eixo vertical.
- [x] 4.2 Verificar com leitor de tela (ou inspeção da árvore de acessibilidade) que
      a região da marca anuncia um heading "Despapelize" único, sem duplicação de
      texto. Confirmado: `getByRole("heading", { name: "Despapelize" })` retorna
      exatamente 1 elemento; não há nó de texto solto "Despapelize" (o `<h1>` só
      contém a imagem).

## 5. Documentação do manual

- [x] 5.1 Revisar `docs/manual/comum/login.md` (e qualquer outra página do manual
      que referencie a tela de Login) por menção ao logo/chip circular antigo; nenhum
      texto do manual descreve a logo hoje, mas a revisão é obrigatória por esta
      change alterar uma tela visível ao usuário. Confirmado: `docs/manual/comum/
      login.md` não menciona logo/chip; busca por "logo|chip|IconMarca|circular" em
      `docs/manual/` só encontrou falsos positivos ("logo abaixo", "catálogo").
- [x] 5.2 Rodar `mkdocs build --strict` localmente e confirmar que passa sem erro —
      critério de aceite desta tarefa, não a afirmação de que o manual foi revisado.
      Confirmado: build limpo, sem warnings/erros.

## 6. Verificação final

- [x] 6.1 `pnpm --filter @setes/web typecheck`. Confirmado: `tsc --noEmit` sem erros.
- [x] 6.2 Confirmar que nenhum arquivo fora de `apps/web/app/login/`,
      `apps/web/app/login/page.test.tsx`, `apps/web/e2e/`,
      `apps/web/public/marca/login-hero.jpg` e `docs/manual/**` foi alterado —
      sidebar, favicon, `IconMarca` e marca horizontal devem permanecer
      bit-a-bit idênticos ao estado anterior. Confirmado via `git status`: só
      `apps/web/app/login/page.tsx`, `apps/web/e2e/01-setup-login.spec.ts` e o
      novo `apps/web/public/marca/login-hero.jpg` foram tocados.
