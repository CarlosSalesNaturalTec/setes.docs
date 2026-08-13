## Why

O logo institucional na tela de Login hoje é um símbolo monocromático de 28px dentro
de um chip navy de 48px — discreto demais para a primeira impressão da marca que o
cliente pediu. O cliente forneceu a arte original (`docs/images/logo_despapelize.jpeg`)
com a árvore, o wordmark "Despapelize®" e as raízes de circuito, e quer essa arte
usada com destaque, exclusivamente na tela de Login — sem alterar sidebar, favicon ou
o restante da identidade visual já consolidada no change `marca-visual-despapelize`.

## What Changes

- Login passa a exibir uma cópia da imagem original do cliente
  (`apps/web/public/marca/login-hero.jpg`, derivada de
  `docs/images/logo_despapelize.jpeg`) em vez do chip circular navy +
  `IconMarca` atual — sem recorte, sem remoção do fundo texturizado, sem edição de
  cor.
- A imagem é exibida "solta" (sem container/chip circular), com largura máxima de
  260px, mantendo a proporção original (~0,59) da arte fornecida.
- O `<h1>{NOME_PRODUTO}</h1>` (texto "Despapelize") hoje renderizado abaixo do chip é
  **removido** do Login — duplicaria o wordmark "Despapelize®" que já está nos pixels
  da nova imagem. A imagem recebe `alt="Despapelize"` e fica envolvida por um `<h1>`,
  preservando o heading acessível no DOM sem duplicar texto visível. `SUBTITULO_CLIENTE`
  ("SETES") e "Acesse sua conta" continuam como texto, sem mudança.
- **BREAKING** (escopo de spec, não de dado/API): reabre, com exceção explícita e
  escopada só ao Login, três invariantes fixados pelo change
  `marca-visual-despapelize` — "material de origem não consumido pela aplicação",
  "fundo texturizado não aparece em nenhuma superfície" e "chip circular preservado
  nos dois locais [Login e sidebar]". Sidebar, favicon e `IconMarca` permanecem
  exatamente como estão hoje — nenhuma dessas três invariantes muda fora do Login.
- Sem cor fora da paleta navy institucional: nenhuma alteração de tom, filtro ou
  gradiente aplicada à imagem — ela é usada como fornecida pelo cliente, sem efeito
  adicional.
- Ajuste do teste `apps/web/app/login/page.test.tsx` para localizar o heading
  "Despapelize" pela imagem (via `alt`) em vez de por texto puro.

## Adendo (2026-08-13, mesmo dia) — três ajustes adicionais de destaque

Depois da primeira implementação (tasks 1–6, já commitadas em `9a30abc`), o
cliente pediu três ajustes adicionais na mesma tela, capturados aqui porque este
change ainda não foi arquivado (ver `design.md` D6–D8 para o raciocínio completo):

- **Logo 50% menor**: `login-hero.jpg` passa de `max-w-[260px]` (D2) para
  `max-w-[130px]` — metade do teto fixado em D2, mesma proporção original.
- **Fundo de página azul, no tom da imagem**: o `<main>` do Login troca
  `bg-superficie-app` (cinza claro, compartilhado com o resto da aplicação) por um
  novo token de marca (`marca.destaque`, `#126ced`) derivado do tom predominante de
  `login-hero.jpg` e escurecido o suficiente para manter contraste adequado contra
  o card branco (D7). Escopado exclusivamente ao `<main>` do Login — o restante da
  aplicação (shell autenticado, `globals.css`) continua em `bg-superficie-app`.
- **Remoção de "Acesse sua conta"**: o subtítulo de chamada de ação some do card —
  a imagem em destaque já comunica a marca, tornando o texto redundante.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `identidade-visual`: os requisitos "Apresentação do Login sem SSO", "Marca
  institucional exibe o ícone do favicon", "Símbolo derivado da marca fornecida pelo
  cliente" e "Material de origem não é consumido pela aplicação" ganham exceção
  explícita e escopada ao Login — chip circular, ausência de fundo texturizado e
  não-consumo do material de origem continuam valendo para a sidebar e o favicon,
  mas não mais para o hero do Login. O adendo (D6–D8) reduz o teto de largura do
  hero para 130px, remove "Acesse sua conta" do requisito "Apresentação do Login
  sem SSO" e acrescenta o requisito "Fundo de página do Login usa tom derivado da
  marca".

## Impact

- **Código afetado**: `apps/web/app/login/page.tsx` (troca do chip+`IconMarca`+`h1`
  pela nova imagem; adendo: `max-w-[130px]`, novo `bg-marca-destaque` no `<main>`,
  remoção do `<p>` "Acesse sua conta"), `apps/web/app/login/page.test.tsx` (ajuste
  de matcher do heading; adendo: remoção da asserção de "Acesse sua conta"),
  `apps/web/tailwind.config.ts` (adendo: novo token `colors.marca.destaque`).
  Nenhum outro arquivo de `apps/web` é tocado — `components/icons.tsx`,
  `components/protected-shell.tsx`, `app/globals.css` e `app/icon.svg` permanecem
  inalterados.
- **Novo asset estático**: `apps/web/public/marca/login-hero.jpg` (cópia de
  `docs/images/logo_despapelize.jpeg`, comentário apontando a origem).
  `docs/images/logo_despapelize.jpeg` continua intocado como material de origem.
- **Sem impacto em banco de dados**: nenhuma tabela PostgreSQL, migration ou schema
  afetado — mudança é exclusivamente de apresentação estática do frontend.
- **Sem novo segredo no Secret Manager nem novo bucket no Cloud Storage**: o asset é
  servido como arquivo estático do Next.js (`apps/web/public/`), não via
  Cloud Storage.
- **Sem dado pessoal envolvido**: a imagem é material de marca do cliente
  (logotipo institucional), não dado pessoal de interessado/usuário — não há
  tratamento LGPD aplicável a este change.
- **Depende de**: `marca-visual-despapelize` (arquivado em
  `openspec/changes/archive/2026-08-13-marca-visual-despapelize/`) — é o change que
  fixou os requisitos de `identidade-visual` que este change agora abre exceção.
