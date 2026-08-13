Referências: requisitos em `specs/identidade-visual/spec.md`; decisões `(Dx)` em
`design.md` — citar a decisão no comentário do código ao implementar.

## 1. Material de origem

- [ ] 1.1 Perguntar ao cliente se existe o **original vetorial** da marca
  (AI/EPS/PDF/SVG). Se existir, ele substitui o redesenho de 2.1 e o trabalho passa a
  ser extração + simplificação (design.md, Open Questions). **Aceite**: resposta
  registrada no change; se houver original, o arquivo entra em `docs/images/` ao lado
  do JPEG.
- [ ] 1.2 Confirmar que `docs/images/logo_despapelize.jpeg` permanece no repositório
  como material de origem e não é referenciado por código de aplicação (requisito
  "Material de origem não é consumido pela aplicação"). **Aceite**:
  `grep -rn "logo_despapelize" apps/` não retorna nada.

## 2. Desenho do símbolo

- [ ] 2.1 Redesenhar o símbolo em vetor a partir do material de origem (D1): copa de
  folhas simplificada, tronco e raízes de circuito com nós terminais. Sem autotrace.
  **Aceite**: SVG de fundo transparente, sem textura, sem o wordmark, sem o ®; arquivo
  com geometria limpa e editável.
- [ ] 2.2 Garantir que o símbolo é monocromático e herda a cor do contexto via
  `currentColor` (D2). **Aceite**: nenhuma cor literal no ativo; renderizado dentro de
  um contêiner com `text-navy-900`, o desenho sai navy.
- [ ] 2.3 Verificar legibilidade a **32px** — o vão entre as folhas da copa e a
  separação entre as raízes precisam sobreviver (D7, requisito "Símbolo legível no
  menor slot"). **Aceite**: copa e raízes distinguíveis a 32px; se falhar, voltar a
  2.1 e simplificar mais.
- [ ] 2.4 Verificar legibilidade a **16px** (favicon) na aba real do navegador, não em
  imagem ampliada (D7). **Aceite**: a marca é reconhecível como a árvore, não como um
  borrão.
- [ ] 2.5 Medir o contraste do símbolo contra o fundo do chip nos dois locais e
  registrar os valores (D7). **Aceite**: ≥ 3:1 nos dois casos (WCAG 2.1 AA, elemento
  gráfico não textual).

## 3. Validação com o cliente

- [ ] 3.1 Apresentar o símbolo redesenhado ao cliente **antes** de aplicá-lo às telas
  (design.md, Risks — o redesenho pode afastar-se do que o cliente reconhece como a
  marca dele). **Aceite**: aprovação registrada, ou ajustes incorporados e
  reapresentados.

## 4. Aplicação em `apps/web`

- [ ] 4.1 Substituir o `<path>` de `IconMarca` (`components/icons.tsx`) pelo símbolo
  novo, **mantendo a assinatura do componente** (`{ className }`) e o uso de
  `currentColor` (D2/D4). Comentário no componente cita `(D4)` e aponta para
  `app/icon.svg`. **Aceite**: `pnpm --filter @setes/web typecheck` passa; Login e
  sidebar não precisam de nenhuma alteração para exibir o símbolo novo.
- [ ] 4.2 Atualizar `apps/web/app/icon.svg` com o mesmo desenho, cor resolvida para o
  favicon (D4). Comentário no arquivo aponta para `IconMarca`. **Aceite**: os dois
  arquivos carregam o mesmo `<path>`.
- [ ] 4.3 Conferir visualmente o chip do Login (48px) e o da sidebar (32px), em
  viewport móvel e desktop (requisito "Símbolo funciona sobre fundo claro e sobre
  fundo escuro"). **Aceite**: chip permanece circular nos dois locais; o símbolo não
  aparece cortado, esticado nem com fundo visível.

## 5. Favicon

- [ ] 5.1 **Medir antes de corrigir** (D5): subir o dev server, requisitar `/icon.svg`
  e inspecionar o `<link rel="icon">` renderizado. **Aceite**: resposta HTTP e tag
  registradas na tarefa — não presumir 200 nem 404.
- [ ] 5.2 Correção condicional conforme o resultado de 5.1 (D5): se `/icon.svg`
  responde 200, remover a declaração redundante `icons: { icon: "/icon.svg" }` de
  `app/layout.tsx` e deixar a convenção do App Router agir sozinha; se responde 404,
  colocar o ativo em `public/`. **Aceite**: a aba exibe o símbolo em `/login`,
  `/processos` e `/consulta-publica` (requisito "Favicon do produto é entregue ao
  navegador").

## 6. Marca horizontal

- [ ] 6.1 Compor a marca horizontal (símbolo + wordmark "Despapelize®") com o wordmark
  convertido em curvas (D3). **Aceite**: nenhum `<text>` e nenhum `font-family` no
  ativo; fundo transparente; ® presente aqui e ausente no símbolo isolado.
- [ ] 6.2 Publicar o ativo em `apps/web/public/marca/` (D6). **Aceite**: arquivo
  distinto do símbolo isolado; nenhuma tela o consome neste change, conforme o
  requisito.

## 7. Testes

- [ ] 7.1 Confirmar que `app/login/page.test.tsx` e
  `components/protected-shell.test.tsx` continuam passando **sem alteração** — a
  estrutura das telas não muda, só o desenho dentro do chip. **Aceite**: suíte Vitest
  verde sem editar os dois arquivos; se algum exigir edição, investigar antes de
  ajustar o teste.
- [ ] 7.2 Rodar a suíte Playwright de login (`e2e/01-setup-login.spec.ts`) — o Login é
  fluxo crítico e a regra de E2E do repositório é vinculante. Este change não altera o
  comportamento de autenticação, então a tarefa é **regressão**, não cobertura nova.
  **Aceite**: spec verde, incluindo credencial inválida e redirecionamento por perfil.

## 8. Manual do usuário

- [ ] 8.1 Avaliar se `docs/manual/**` precisa de atualização (regra vinculante de
  `openspec/config.yaml`). Leitura prévia: `comum/login.md` e `comum/menu-lateral.md`
  descrevem passos, campos e itens de menu — nenhum deles cita o logotipo, e este
  change não altera passo, campo, botão, item de menu nem texto exibido. **Aceite**:
  conclusão registrada nesta tarefa; se a avaliação encontrar menção ao ícone antigo,
  atualizar a página correspondente.
- [ ] 8.2 Rodar `mkdocs build --strict` localmente — critério de aceite exigido pela
  regra, independentemente de 8.1 alterar ou não conteúdo. **Aceite**: build sem erro
  e sem aviso novo.

## 9. Fechamento

- [ ] 9.1 Rodar a bateria completa antes de propor o merge:
  `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`,
  `pnpm test:e2e` e `mkdocs build --strict`. **Aceite**: todos verdes. (Sem
  `uv run pytest` e sem `pnpm gen:types` — o change não toca `apps/api` nem o contrato
  OpenAPI.)
- [ ] 9.2 Rodar `openspec validate marca-visual-despapelize --strict`. **Aceite**: sem
  erro de validação.
