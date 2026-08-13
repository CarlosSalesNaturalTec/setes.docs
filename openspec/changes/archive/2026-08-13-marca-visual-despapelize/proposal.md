## Why

A marca do produto existe hoje apenas como **texto**. Onde a interface deveria
exibir a logomarca, ela exibe `IconMarca` (`apps/web/components/icons.tsx:84`) —
um desenho genérico de folha de documento com três linhas, sem nenhuma relação com
a identidade real da Despapelize. O mesmo desenho é o favicon (`apps/web/app/icon.svg`).

O cliente forneceu a marca em `docs/images/logo_despapelize.jpeg`. O arquivo **não é
um asset de marca utilizável**, e essa é a razão de existir deste change:

```
docs/images/logo_despapelize.jpeg
  438 × 740 px   → retrato, proporção 0,59
  JPEG           → sem canal alfa
  fundo azul texturizado "craquelado"  → CHAPADO na imagem, não removível por CSS
  conteúdo: símbolo (árvore com raízes de circuito) + wordmark "Despapelize®"
```

Os dois lugares onde a marca precisa entrar são **chips circulares pequenos** —
32×32 na sidebar (`protected-shell.tsx:163`) e 48×48 no Login
(`login/page.tsx`). Inserir o JPEG em qualquer um deles produz um retângulo azul
texturizado recortado: sobre o `bg-navy-900` da sidebar e sobre o card branco do
Login, o fundo chapado fica visível como uma mancha. A proporção retrato também
não cabe em slot quadrado sem cortar o wordmark.

Some-se a isso que `apps/web/public/` está **vazio** — o frontend não tem hoje
nenhum pipeline de imagem, nenhum uso de `next/image`, nenhum asset binário.

Portanto: o trabalho não é "inserir a imagem nas telas", é **derivar um asset de
marca próprio para interface** a partir do material fornecido, e então aplicá-lo.

## What Changes

- **A marca é vetorizada para SVG**, com fundo transparente, a partir do material
  em `docs/images/logo_despapelize.jpeg`. O fundo texturizado do pôster é
  descartado — ele é arte de peça gráfica, não parte da marca.
- **Dois SVGs, não um**, porque os slots têm necessidades diferentes:
  - **símbolo isolado** (a árvore com raízes de circuito), para os chips circulares
    da sidebar e do Login e para o favicon — legível a 32 px;
  - **marca horizontal** (símbolo + wordmark "Despapelize"), para superfícies com
    largura disponível.
- **A marca usa `currentColor` onde for possível**, ou variantes explícitas para
  fundo claro e fundo escuro. O símbolo precisa funcionar sobre `bg-navy-900`
  (sidebar) **e** sobre superfície de card branca (Login) — hoje o `IconMarca` faz
  isso por ser traço monocromático, e essa propriedade não pode ser perdida.
- **`IconMarca` passa a renderizar o símbolo real da Despapelize**, mantendo a
  assinatura de componente e o ponto único de consumo já estabelecidos pela
  capability `identidade-visual` (requisito "Marca institucional exibe o ícone do
  favicon"). Login e sidebar continuam **sem duplicar markup SVG**.
- **`apps/web/app/icon.svg` passa a ser o símbolo real**, alinhando favicon e
  interface — que hoje já são o mesmo desenho, e devem continuar sendo.
- **O `docs/images/logo_despapelize.jpeg` permanece no repositório** como material
  de origem da marca, não é referenciado por código de aplicação.
- **Verificação do favicon**: `app/layout.tsx:9` declara
  `icons: { icon: "/icon.svg" }` enquanto o arquivo real é `apps/web/app/icon.svg`
  (convenção de metadata do App Router) e `apps/web/public/` está vazio. O caminho
  absoluto `/icon.svg` aponta para `public/`. Este change **verifica se o favicon
  está sendo servido ou retornando 404** e corrige se for o caso.

## Capabilities

### New Capabilities

<!-- Nenhuma. -->

### Modified Capabilities

- **`identidade-visual`** — o requisito "Marca institucional exibe o ícone do
  favicon" é atualizado: o chip do Login e o da sidebar passam a exibir o **símbolo
  da marca Despapelize**, não o ícone genérico de documento. O formato circular, o
  componente único `IconMarca` e a ausência de duplicação de SVG são **preservados**
  como estão especificados hoje. Os cenários de "acesso negado" e de preservação de
  comportamento da capability não são tocados.

## Impact

- **Dependências**: nenhuma. `renomear-sistema-despapelize` (arquivado) já
  estabeleceu `lib/marca.ts` como fonte única do nome do produto; este change é o
  equivalente visual e consome os mesmos slots.
- **Tabelas PostgreSQL**: **nenhuma**.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: **nenhum**.
- **Backend**: **nenhuma alteração**. Nenhum endpoint, schema ou rota é tocado.
- **Contrato**: **nenhuma regeneração de tipos** — `pnpm gen:types` não se aplica.
- **Frontend**: `components/icons.tsx` (`IconMarca`), `app/icon.svg`, possivelmente
  `app/layout.tsx` (metadata de ícone) e novos arquivos SVG. Login e
  `protected-shell` **não mudam de estrutura** — consomem o mesmo componente.
- **Testes**: `app/login/page.test.tsx` e `components/protected-shell.test.tsx` já
  cobrem a marca; devem continuar passando. Não há teste E2E obrigatório aqui — a
  regra de Playwright cobre login/tramitação/documentos/consulta pública quanto ao
  **comportamento**, e este change é exclusivamente de apresentação, sem alterar o
  fluxo de autenticação.
- **LGPD**: **não aplicável** — nenhum dado pessoal é tratado, exibido ou
  armazenado.
- **PRD**: nenhuma alteração.

> **Ponto em aberto para o design**: a vetorização fiel de um JPEG com textura
> exige decidir quanto de fidelidade se persegue. O símbolo (árvore + raízes de
> circuito) tem geometria limpa e vetoriza bem; o wordmark "Despapelize®" é
> tipografia — reproduzi-lo como caminho vetorial preserva a forma exata, mas
> impede ajuste posterior. A decisão pertence ao `design.md`.
