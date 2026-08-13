# Tarefas — responsividade-mobile

Referências: comportamento esperado em `specs/identidade-visual/spec.md`;
decisões técnicas (D1–D7) em `design.md`. Todo comentário acrescentado ao código
por estas tarefas cita a decisão de origem no formato `(Dx)`, conforme a
convenção do projeto.

> **`pnpm gen:types` não se aplica** a este change (D7): nenhuma rota ou schema
> do FastAPI é tocada, portanto o job de drift do CI não é afetado e
> `packages/api-types` não muda. Registrado aqui porque a regra de tarefas do
> projeto exige a decisão explícita, não o silêncio.

## 1. Tabelas de administração — contêiner rolável (D1, D2)

Padrão-alvo em todas as tarefas deste grupo, copiado de
`app/admin/tipos-processo/page.tsx:148-149`: o `<div>` externo recebe
`overflow-x-auto` **e** a identidade visual (`rounded-card border border-navy-50
bg-superficie-card shadow-card`) mais a margem que hoje está na tabela; a
`<table>` fica com `w-full min-w-[<N>px] text-left text-sm` e perde
`overflow-hidden`, `rounded-card`, `border` e `shadow-card`.

Critério de aceite comum a 1.1–1.5, verificado no navegador a 360 px de largura:
a tabela rola horizontalmente dentro da própria caixa; a página **não** rola
horizontalmente; borda, radius e sombra do card continuam visíveis; nenhuma
coluna, registro ou ação some ou muda de lugar em relação ao desktop.

- [x] 1.1 `app/admin/usuarios/page.tsx:378` — envolver a tabela no contêiner
  rolável e aplicar `min-w-[720px]` (6 colunas: nome, e-mail, perfil, status,
  unidade, ações). *Aceite:* além do critério comum, `pnpm --filter @setes/web test`
  continua passando sem alteração nos testes existentes.
- [x] 1.2 `app/admin/unidades/page.tsx:360` (tabela de unidades) — mesmo padrão;
  contar as colunas e dimensionar o `min-w` pela regra de ~120 px por coluna (D2).
  *Aceite:* critério comum.
- [x] 1.3 `app/admin/unidades/page.tsx:413` (tabela de setores) — mesmo padrão e
  mesma regra de dimensionamento. *Aceite:* critério comum; as duas tabelas da
  mesma página rolam de forma independente uma da outra.
- [x] 1.4 `app/admin/lgpd/solicitacoes-lgpd-content.tsx:147` — mesmo padrão.
  *Aceite:* critério comum; nenhum dado pessoal exibido é acrescentado, removido
  ou reordenado (a tela lista solicitações LGPD — a adaptação é só de viewport).
- [x] 1.5 `app/admin/documentos-removidos/documentos-removidos-content.tsx:129` —
  mesmo padrão. *Aceite:* critério comum e
  `pnpm --filter @setes/web test documentos-removidos-content` passando — este é
  o único dos cinco com teste de componente colocado ao lado
  (`documentos-removidos-content.test.tsx`).
- [x] 1.6 Conferir que nenhuma outra `<table>` do repositório mantém
  `overflow-hidden` na própria tag: `grep -rn "<table" apps/web/app apps/web/components`.
  *Aceite:* a busca não retorna nenhuma `<table>` com `overflow-hidden`, e
  `admin/tipos-processo` permanece intocado (3 colunas curtas cabem em 360 px, D2).

## 2. Detalhe do processo — modais e grade (D3, D4)

- [x] 2.1 `app/processos/[id]/page.tsx:202` (modal de tramitação) — trocar
  `items-center … p-4` por `items-start … overflow-y-auto p-4 sm:p-8`, idêntico a
  `components/modal.tsx:34`, com comentário citando `(D3)`. *Aceite:* em viewport
  de 360 × 640 px, com a ação "Enviar" selecionada (unidade, setor, servidor e
  mensagem visíveis), os botões "Confirmar" e "Cancelar" são alcançáveis por
  rolagem do diálogo.
- [x] 2.2 `app/processos/[id]/page.tsx:32` (modal de conclusão) — mesmo contêiner
  do 2.1, pelo mesmo motivo e com a mesma citação. *Aceite:* o diálogo de
  confirmação permanece inteiramente visível e operável a 360 × 640 px.
- [x] 2.3 `app/processos/[id]/page.tsx:674` — `grid-cols-[auto_1fr]` passa a
  `grid-cols-1 sm:grid-cols-[auto_1fr]`. *Aceite:* a 360 px os pares rótulo/valor
  (Status, Unidade atual, Prazo) aparecem empilhados; a partir de `sm` a
  apresentação em duas colunas é a de hoje, sem diferença visual.
- [x] 2.4 `app/processos/[id]/page.tsx:648` — acrescentar `overflow-x-auto` à
  barra de abas (D4). *Aceite:* as abas Detalhes / Documentos / Histórico
  permanecem acionáveis a 360 px, sem provocar rolagem horizontal da página.
- [ ] 2.5 Verificar as três abas a 360 px sem alterar código: Detalhes,
  Documentos e Histórico. *Aceite:* nenhuma delas produz rolagem horizontal do
  documento; os cards do histórico (`<ol>`, já empilhados) permanecem legíveis.
  Se esta verificação revelar problema fora do previsto em D3/D4, registrar antes
  de corrigir — o escopo é ajuste de viewport, não redesenho.

## 3. Consulta pública (D4)

- [x] 3.1 `app/consulta-publica/page.tsx:18` — `grid-cols-2` passa a
  `grid-cols-1 sm:grid-cols-2`. *Aceite:* a 360 px, tipo de processo, status,
  unidade atual e data de criação aparecem empilhados e legíveis; o conjunto de
  campos exibidos é idêntico ao do desktop — nenhum dado a mais é revelado.
- [x] 3.2 Verificar os dois modos da tela (consulta por número e pesquisa por
  assunto/tipo/período) a 360 px, **sem autenticação**. *Aceite:* os formulários
  já usam `flex-wrap` e permanecem utilizáveis; nenhuma rolagem horizontal da
  página. `bg-blue-600` na linha 105 **não** é corrigido aqui — está fora de
  escopo por decisão registrada (design.md, Non-Goals e Open Questions).

## 4. Infraestrutura de teste em viewport móvel (D5)

- [x] 4.1 `apps/web/playwright.config.ts` — acrescentar o projeto `mobile`
  (`devices["Pixel 5"]`, `testMatch: /.*\.mobile\.spec\.ts/`) e, no projeto
  `chromium` existente, `testIgnore: /.*\.mobile\.spec\.ts/`. Comentar o motivo do
  par `testMatch`/`testIgnore` citando `(D5)`: a suíte é serial e com estado
  encadeado, então os conjuntos de specs precisam ser disjuntos — sem o
  `testIgnore`, o desktop rodaria os specs móveis em viewport largo; sem o
  `testMatch`, o projeto móvel repetiria os 16 specs contra um banco já povoado.
  *Aceite:* `cd apps/web && pnpm test:e2e` executa os 16 specs existentes
  **uma única vez** cada, e nenhum deles roda no projeto `mobile`.

## 5. Specs E2E em viewport móvel (D6)

Os três specs autenticam com `ADMIN_ROOT` (`e2e/fixtures.ts`) via
`helpers/auth.ts` — que já zera o rate limit de `/auth/*` antes de cada login — e
criam o próprio estado com nomes e e-mails **distintos** dos usados em `01`–`16`,
porque rodam sobre o banco já povoado pela passada desktop (D5).

- [x] 5.1 `e2e/17-login-mobile.mobile.spec.ts` — login em viewport de smartphone,
  abertura da gaveta de navegação pelo botão de menu, e navegação até
  Admin › Usuários. *Aceite:* o login conclui e sai de `/login`; a gaveta abre e
  fecha; a asserção de ausência de rolagem horizontal
  (`documentElement.scrollWidth - clientWidth <= 0`) passa nas telas visitadas.
- [x] 5.2 No mesmo spec, asserção da tabela rolável (cenário "Tabela larga rola
  dentro do próprio contêiner"). *Aceite:* o contêiner da tabela de usuários tem
  `scrollWidth > clientWidth`, `scrollLeft` assume valor positivo após rolagem
  programática, e o documento continua sem rolagem horizontal.
- [x] 5.3 `e2e/18-tramitacao-mobile.mobile.spec.ts` — **E2E obrigatório de
  tramitação** (regra do projeto): criar unidade, setor, servidor e processo
  próprios, abrir o modal de tramitação em viewport móvel, selecionar "Enviar",
  preencher unidade/setor/servidor/mensagem e confirmar. *Aceite:* o botão
  "Confirmar" é alcançável por rolagem do diálogo (cenário do modal alto); o
  envio é registrado; o histórico exibe o novo evento **acrescentado** aos
  anteriores, nenhum substituído.
- [x] 5.4 `e2e/19-consulta-publica-mobile.mobile.spec.ts` — **E2E obrigatório de
  consulta pública** (regra do projeto): consulta por número em viewport móvel,
  **sem autenticação**. *Aceite:* o resultado exibe os pares rótulo/valor
  empilhados e legíveis; nenhuma rolagem horizontal da página; os campos exibidos
  são os mesmos do desktop.
- [x] 5.5 Rodar a suíte E2E completa (desktop + móvel) e confirmar que a passada
  móvel não interfere no estado dos specs anteriores. *Aceite:*
  `cd apps/web && pnpm test:e2e` verde de ponta a ponta, sem `retries`.

## 6. Manual do usuário (regra vinculante do projeto)

O change altera a apresentação de telas ao usuário final em dispositivos móveis,
o que dispara a regra de atualização de `docs/manual/**`. Hoje o manual menciona
o assunto uma única vez, de passagem, em `comum/menu-lateral.md` ("em telas
estreitas ele vira uma gaveta") — não há orientação de uso em celular ou tablet.

- [x] 6.1 Criar `docs/manual/comum/celular-tablet.md`: acesso pelo navegador do
  aparelho (não há aplicativo a instalar), a gaveta de navegação, a rolagem
  lateral das tabelas administrativas e a nota de que **todas as funções e todos
  os dados são os mesmos do computador** — não existe versão reduzida.
  *Aceite:* a página não descreve nenhuma tela ou função que não exista.
- [x] 6.2 Registrar a página no `nav` do `mkdocs.yml`, em "Para todos os perfis".
  *Aceite:* a página aparece no `nav`; `docs_dir` **permanece** `docs/manual`
  (nunca `docs/` — controle de segurança documentado no próprio `mkdocs.yml`).
- [x] 6.3 Referenciar a nova página em `docs/manual/comum/menu-lateral.md`, junto
  da menção existente à gaveta. *Aceite:* o link resolve no build.
- [x] 6.4 Rodar `mkdocs build --strict` localmente. *Aceite:* build sem erro nem
  aviso — é este comando, e não a afirmação de que o manual foi atualizado, que
  encerra o grupo 6. É também o mesmo comando que o job `manual` do CI executa em
  PR que toque `docs/manual/**`.

## 7. Verificação final

- [x] 7.1 `pnpm --filter @setes/web typecheck` e `pnpm --filter @setes/web test`.
  *Aceite:* ambos verdes; nenhum teste Vitest precisou ser alterado — os testes
  de componente não asseguram classes de layout, e a proteção contra regressão de
  layout é o projeto móvel do Playwright (design.md, Risks).
- [x] 7.2 Conferência de escopo antes de abrir PR. *Aceite:* o diff toca apenas
  `apps/web/app/**`, `apps/web/playwright.config.ts`, `apps/web/e2e/**`,
  `docs/manual/**` e `mkdocs.yml`; **nenhum** arquivo em `apps/api/**`,
  `packages/api-types/**`, `migrations/**` ou `infra/**` foi modificado (D7).
