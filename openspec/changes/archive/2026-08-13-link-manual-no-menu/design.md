## Context

`components/protected-shell.tsx` define `ITENS_MENU: ItemMenu[]`, onde
`ItemMenu.href: string` é sempre uma rota interna do Next.js renderizada com
`<Link href={href}>` (`next/link`). O destaque de item ativo compara
`pathname` (de `usePathname()`) com cada `href` via `itemAtivo()`. A
visibilidade de cada item é um predicado `visivel: (usuario: Usuario) =>
boolean`, testado em `protected-shell.test.tsx`.

O manual já está publicado (change `manual-mkdocs`, arquivado) no GitHub
Pages do repositório `CarlosSalesNaturalTec/setes.docs`, sem `site_url`
customizado em `mkdocs.yml` — a URL efetiva é a default do Pages para esse
repositório: `https://carlossalesnaturaltec.github.io/setes.docs/`.

Ver proposal.md — Why para a análise que descartou hospedar o manual junto à
aplicação ou atrás de login.

## Goals / Non-Goals

**Goals:**
- Tornar o item de menu capaz de representar tanto uma rota interna quanto um
  link externo, sem duplicar a estrutura de `ITENS_MENU` nem o componente de
  renderização.
- Adicionar o item "Manual" visível a todos os perfis, abrindo o site do
  manual em nova aba.
- Manter um único ponto de definição para a URL do manual.

**Non-Goals:**
- Não alterar o RBAC de nenhum item existente.
- Não tornar o manual privado nem mudar onde ele é hospedado — decisão D5 de
  `manual-mkdocs` permanece válida (ver proposal.md).
- Não adicionar um mecanismo genérico de plugins/links configuráveis em
  runtime — a lista de itens continua estática em código, como hoje.

## Decisions

### D1 — `ItemMenu` distingue rota interna de link externo por um campo opcional `href` vs `hrefExterno`

`ItemMenu` ganha um campo opcional `hrefExterno?: string`, mantendo `href`
como estava. Um item é de rota interna quando só `href` está presente (caso
de hoje, sem alteração); é externo quando `hrefExterno` está presente — nesse
caso `href` continua obrigatório e serve apenas como `key` estável do React
e como valor que `itemAtivo()` nunca vai casar (nenhuma rota real da
aplicação usa essa string), preservando a assinatura de `itemAtivo(pathname,
href)` sem overload.

Na renderização, o item mapeia para `<a href={hrefExterno} target="_blank"
rel="noopener noreferrer">` em vez de `<Link href={href}>`, e o cálculo de
`ativo` é pulado (sempre `false`) quando `hrefExterno` está presente — sem
precisar de um branch redundante em `itemAtivo`, que continua puro e só
lida com rotas internas.

**Alternativas consideradas:**
- *Um array separado `ITENS_MENU_EXTERNOS` renderizado depois do `<nav>`
  principal.* Rejeitado: duplica o JSX de item (ícone + label + estilo ativo)
  e obriga a spec/teste a verificar dois lugares para "todos os itens
  visíveis", quando o requisito de RBAC trata a sidebar como uma lista única.
- *`href` sempre absoluto, e o componente decide interno vs externo testando
  se a string começa com `http`.* Rejeitado: acopla o comportamento de
  navegação a uma heurística de parsing de string em vez de um campo
  explícito — mais frágil e mais difícil de testar (o teste teria que
  inspecionar a URL renderizada em vez de checar a prop que determinou o
  comportamento).

### D2 — Item "Manual" usa `visivel: () => true`, sem novo predicado

O predicado de visibilidade dos itens comuns (`Processos`, `Meu Perfil`) já é
`() => true`. O item "Manual" reaproveita o mesmo predicado — não introduz
um terceiro conceito de visibilidade (ex.: "sempre visível, mas não é
rota") na função `itensVisiveis = ITENS_MENU.filter(...)`, que continua
sendo o único filtro de RBAC da sidebar.

### D3 — URL do manual centralizada em `lib/manual.ts`

Novo arquivo `apps/web/lib/manual.ts`, exportando `URL_MANUAL`, no mesmo
espírito de `lib/marca.ts` (`NOME_PRODUTO`, `SUBTITULO_CLIENTE`) — um módulo
minúsculo, sem lógica, cujo único papel é ser o ponto único de uma string
usada pela UI. `protected-shell.tsx` importa dali em vez de embutir a URL
literal no array `ITENS_MENU`.

**Alternativa considerada:** literal direto em `ITENS_MENU`. Rejeitado pelo
próprio texto do proposal.md ("a URL do manual fica num ponto único") — o
projeto já tem o precedente de `lib/marca.ts` para constantes de apresentação
consumidas por mais de uma tela ou reescritas eventualmente sem tocar
lógica de componente.

### D4 — Novo ícone `IconManual` segue o padrão SVG inline de `icons.tsx`

Adicionado a `components/icons.tsx` como `IconManual({ className })`,
seguindo a mesma assinatura `IconProps` e o mesmo padrão de `stroke`
monocromático (herda `currentColor`) dos demais ícones de menu
(`IconProcessos`, `IconPerfil`, …) — nenhuma dependência nova de ícones.

## Risks / Trade-offs

- **[Risco]** O link para `github.io` quebra silenciosamente se o repositório
  for renomeado ou o Pages desabilitado, e nada no frontend detectaria isso —
  é um link estático para fora da aplicação, sem healthcheck.
  **Mitigação**: nenhuma automática; é o mesmo risco que qualquer link
  externo tem, e o custo de monitorá-lo (ex.: checar disponibilidade em CI)
  é desproporcional a um item de menu. Registrado aqui para não ser
  redescoberto como surpresa.
- **[Trade-off]** `hrefExterno` opcional em `ItemMenu` deixa o tipo permitir,
  em tese, um item com `hrefExterno` mas sem `href` só por erro de leitura —
  TypeScript não impede porque `href` continua obrigatório e independente.
  Como há um único item externo hoje (`Manual`) e ele é definido estaticamente
  em `ITENS_MENU`, o teste de `protected-shell.test.tsx` cobre o caso real; um
  tipo discriminado (union de duas formas de `ItemMenu`) resolveria isso com
  mais rigor, mas foi descartado por ser complexidade desproporcional a um
  único item externo — revisitar se um segundo item externo for adicionado.

## Migration Plan

Mudança de apresentação, sem estado, sem migration de banco, sem dado a
migrar. Deploy normal do `apps/web` via `deploy.yml` (push em `main`); nenhum
passo de rollback além de reverter o commit — não há efeito colateral
persistente.
