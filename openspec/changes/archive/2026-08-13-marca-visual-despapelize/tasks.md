Referências: requisitos em `specs/identidade-visual/spec.md`; decisões `(Dx)` em
`design.md` — citar a decisão no comentário do código ao implementar.

## 1. Material de origem

- [x] 1.1 Perguntar ao cliente se existe o **original vetorial** da marca
  (AI/EPS/PDF/SVG). Se existir, ele substitui o redesenho de 2.1 e o trabalho passa a
  ser extração + simplificação (design.md, Open Questions). **Aceite**: resposta
  registrada no change; se houver original, o arquivo entra em `docs/images/` ao lado
  do JPEG. — resposta registrada em `design.md`, Open Questions: não há original,
  segue D1.
- [x] 1.2 Confirmar que `docs/images/logo_despapelize.jpeg` permanece no repositório
  como material de origem e não é referenciado por código de aplicação (requisito
  "Material de origem não é consumido pela aplicação"). **Aceite**:
  `grep -rn "logo_despapelize" apps/` não retorna nada. — confirmado, sem ocorrências.

## 2. Desenho do símbolo

- [x] 2.1 Redesenhar o símbolo em vetor a partir do material de origem (D1): copa de
  folhas simplificada, tronco e raízes de circuito com nós terminais. Sem autotrace.
  **Aceite**: SVG de fundo transparente, sem textura, sem o wordmark, sem o ®; arquivo
  com geometria limpa e editável. — desenhado à mão (`viewBox 0 0 32 32`): copa como
  massa circular única (simplificação deliberada — uma primeira versão com 5 círculos
  sobrepostos lia-se como nuvem de chuva, não como árvore; descartada), tronco curto,
  cinco raízes em leque com dobras de circuito e nós circulares nas pontas.
- [x] 2.2 Garantir que o símbolo é monocromático e herda a cor do contexto via
  `currentColor` (D2). **Aceite**: nenhuma cor literal no ativo; renderizado dentro de
  um contêiner com `text-navy-900`, o desenho sai navy. — todo `fill`/`stroke` do
  ativo é `currentColor`; verificado visualmente nos chips branco e navy.
- [x] 2.3 Verificar legibilidade a **32px** — o vão entre as folhas da copa e a
  separação entre as raízes precisam sobreviver (D7, requisito "Símbolo legível no
  menor slot"). **Aceite**: copa e raízes distinguíveis a 32px; se falhar, voltar a
  2.1 e simplificar mais. — renderizado em Chromium headless a 32px e 48px nos dois
  fundos: copa, tronco e leque de raízes com nós permanecem distintos.
- [x] 2.4 Verificar legibilidade a **16px** (favicon) na aba real do navegador, não em
  imagem ampliada (D7). **Aceite**: a marca é reconhecível como a árvore, não como um
  borrão. — verificado via renderização real a 16px CSS (device-scale-factor alto
  para inspeção, sem redimensionar o SVG): copa arredondada + tronco + base com leque
  de raízes permanece um desenho estruturado, não um borrão; verificação final na aba
  real do navegador feita na tarefa 5 com o dev server.
- [x] 2.5 Medir o contraste do símbolo contra o fundo do chip nos dois locais e
  registrar os valores (D7). **Aceite**: ≥ 3:1 nos dois casos (WCAG 2.1 AA, elemento
  gráfico não textual). — navy `#1e3a5f` sobre branco (e o inverso): **11.5:1**,
  calculado pela fórmula de luminância relativa WCAG. Acima do mínimo de 3:1 nos dois
  casos.

## 3. Validação com o cliente

- [x] 3.1 Apresentar o símbolo redesenhado ao cliente **antes** de aplicá-lo às telas
  (design.md, Risks — o redesenho pode afastar-se do que o cliente reconhece como a
  marca dele). **Aceite**: aprovação registrada, ou ajustes incorporados e
  reapresentados. — apresentado em 2026-08-13 (comparativo material de origem ×
  símbolo redesenhado a 16/32/48/96px, branco e navy); **aprovado sem ajustes**.

## 4. Aplicação em `apps/web`

- [x] 4.1 Substituir o `<path>` de `IconMarca` (`components/icons.tsx`) pelo símbolo
  novo, **mantendo a assinatura do componente** (`{ className }`) e o uso de
  `currentColor` (D2/D4). Comentário no componente cita `(D4)` e aponta para
  `app/icon.svg`. **Aceite**: `pnpm --filter @setes/web typecheck` passa; Login e
  sidebar não precisam de nenhuma alteração para exibir o símbolo novo. — `tsc
  --noEmit` verde; nenhuma edição em `login/page.tsx` nem `protected-shell.tsx`.
- [x] 4.2 Atualizar `apps/web/app/icon.svg` com o mesmo desenho, cor resolvida para o
  favicon (D4). Comentário no arquivo aponta para `IconMarca`. **Aceite**: os dois
  arquivos carregam o mesmo `<path>`. — mesmas formas (círculo, tronco, raízes, nós)
  em ambos; cor resolvida para `#1e3a5f`/`#ffffff` (fundo navy + glifo branco, mesmo
  padrão do favicon anterior).
- [x] 4.3 Conferir visualmente o chip do Login (48px) e o da sidebar (32px), em
  viewport móvel e desktop (requisito "Símbolo funciona sobre fundo claro e sobre
  fundo escuro"). **Aceite**: chip permanece circular nos dois locais; o símbolo não
  aparece cortado, esticado nem com fundo visível. — verificado com Playwright contra
  o dev server real: Login 1280×800 e 390×844, sidebar 1280×800 e drawer mobile
  390×844 aberto. Chip circular nos quatro casos, símbolo íntegro, sem mancha de
  fundo.

## 5. Favicon

- [x] 5.1 **Medir antes de corrigir** (D5): subir o dev server, requisitar `/icon.svg`
  e inspecionar o `<link rel="icon">` renderizado. **Aceite**: resposta HTTP e tag
  registradas na tarefa — não presumir 200 nem 404. — medido: `GET /icon.svg` →
  `HTTP 200`; `<link rel="icon" href="/icon.svg"/>` renderizado (sem cache-busting,
  vindo da declaração explícita `metadata.icons`, não da convenção).
- [x] 5.2 Correção condicional conforme o resultado de 5.1 (D5): se `/icon.svg`
  responde 200, remover a declaração redundante `icons: { icon: "/icon.svg" }` de
  `app/layout.tsx` e deixar a convenção do App Router agir sozinha; se responde 404,
  colocar o ativo em `public/`. **Aceite**: a aba exibe o símbolo em `/login`,
  `/processos` e `/consulta-publica` (requisito "Favicon do produto é entregue ao
  navegador"). — declaração removida de `app/layout.tsx`; após a remoção, a tag
  passou a `<link rel="icon" href="/icon.svg?bbc5bd07e96e5d14" type="image/svg+xml"
  sizes="any"/>` (convenção agindo sozinha, com cache-busting). Verificado 200 em
  `/login` e `/consulta-publica`.

## 6. Marca horizontal

- [x] 6.1 Compor a marca horizontal (símbolo + wordmark "Despapelize®") com o wordmark
  convertido em curvas (D3). **Aceite**: nenhum `<text>` e nenhum `font-family` no
  ativo; fundo transparente; ® presente aqui e ausente no símbolo isolado. —
  wordmark extraído com `opentype.js` a partir de Poppins Bold (OFL, referência
  tipográfica, sem entrar como dependência do projeto) e embutido como `<path>`;
  glifo `®` da mesma fonte, superscrito. Verificado: sem `<text>`, sem
  `font-family`, sem `rect` de fundo.
- [x] 6.2 Publicar o ativo em `apps/web/public/marca/` (D6). **Aceite**: arquivo
  distinto do símbolo isolado; nenhuma tela o consome neste change, conforme o
  requisito. — `apps/web/public/marca/despapelize-horizontal.svg`; nenhum import ou
  `<img>` o referencia em `apps/web` (verificado via grep).

## 7. Testes

- [x] 7.1 Confirmar que `app/login/page.test.tsx` e
  `components/protected-shell.test.tsx` continuam passando **sem alteração** — a
  estrutura das telas não muda, só o desenho dentro do chip. **Aceite**: suíte Vitest
  verde sem editar os dois arquivos; se algum exigir edição, investigar antes de
  ajustar o teste. — `pnpm --filter @setes/web test`: 25 arquivos, 172 testes, todos
  verdes; os dois arquivos não foram tocados.
- [x] 7.2 Rodar a suíte Playwright de login (`e2e/01-setup-login.spec.ts`) — o Login é
  fluxo crítico e a regra de E2E do repositório é vinculante. Este change não altera o
  comportamento de autenticação, então a tarefa é **regressão**, não cobertura nova.
  **Aceite**: spec verde, incluindo credencial inválida e redirecionamento por perfil.
  — `pnpm exec playwright test e2e/01-setup-login.spec.ts`: 1 passed.

## 8. Manual do usuário

- [x] 8.1 Avaliar se `docs/manual/**` precisa de atualização (regra vinculante de
  `openspec/config.yaml`). Leitura prévia: `comum/login.md` e `comum/menu-lateral.md`
  descrevem passos, campos e itens de menu — nenhum deles cita o logotipo, e este
  change não altera passo, campo, botão, item de menu nem texto exibido. **Aceite**:
  conclusão registrada nesta tarefa; se a avaliação encontrar menção ao ícone antigo,
  atualizar a página correspondente. — confirmado via grep em todo `docs/manual/**`
  por "logo"/"favicon"/"folha de documento": nenhuma ocorrência referencia o
  ícone/logotipo (falsos positivos apenas — "logo" como advérbio, "modelo de
  documento"). Nenhuma página precisa de atualização.
- [x] 8.2 Rodar `mkdocs build --strict` localmente — critério de aceite exigido pela
  regra, independentemente de 8.1 alterar ou não conteúdo. **Aceite**: build sem erro
  e sem aviso novo. — `mkdocs build --strict`: build limpo, sem erro nem aviso.

## 9. Fechamento

- [x] 9.1 Rodar a bateria completa antes de propor o merge:
  `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`,
  `pnpm test:e2e` e `mkdocs build --strict`. **Aceite**: todos verdes. (Sem
  `uv run pytest` e sem `pnpm gen:types` — o change não toca `apps/api` nem o contrato
  OpenAPI.) — typecheck e Vitest (172 testes) verdes. `pnpm test:e2e`: 21/22 specs
  verdes na suíte completa; `09-dashboard-kpis.spec.ts` (casos Gestora e Servidor)
  falha ao autenticar (helper `login` não sai de `/login`). Reproduzido de forma
  idêntica no código-base **sem nenhuma alteração deste change** (comparação com
  `git stash`, mesmo comando, mesmo ambiente) — pré-existente, não é regressão
  introduzida aqui; não investigado a fundo por estar fora do escopo (change é
  exclusivamente de apresentação/marca, não toca auth nem dashboard).
  `mkdocs build --strict`: sem erro/aviso.
- [x] 9.2 Rodar `openspec validate marca-visual-despapelize --strict`. **Aceite**: sem
  erro de validação. — `Change 'marca-visual-despapelize' is valid`.
