## Why

O manual do usuário já está publicado como site MkDocs no GitHub Pages desde o
change `manual-mkdocs` (arquivado em 2026-08-04). O que falta é o caminho até ele:
**nenhuma tela do produto aponta para o manual**. Quem usa o sistema precisa
conhecer a URL do site por fora — o que na prática significa que o manual existe e
ninguém o encontra.

Foi avaliada a alternativa de **hospedar a documentação junto à própria aplicação**,
e ela foi descartada com fundamento no código:

- Servir o manual como estático do Next (`apps/web/public/manual/`, que o
  `apps/web/Dockerfile:33` já copia para a imagem) funcionaria e unificaria o
  domínio — mas **não tornaria o manual privado**, apenas mudaria o endereço. Em
  troca, acoplaria a publicação da documentação ao deploy da imagem web: um commit
  que só toca `docs/manual/**` passaria a exigir rebuild e redeploy do serviço.
- Servir o manual **atrás do login** esbarra numa decisão fundacional: a sessão é
  **Bearer token guardado em `localStorage`** (`apps/web/lib/session-store.ts`,
  decisão D1 de sessão), **não** cookie — e não existe `middleware.ts` no projeto.
  Uma navegação de browser para uma página estática não envia header
  `Authorization`, de modo que o servidor não teria como autenticá-la. Proteger o
  manual exigiria converter a sessão inteira para cookie, tocando
  `security/sessao.py`, `security/autorizacao.py`, o CORS
  (`allow_credentials=False` → `True`), `lib/api.ts`, `session-store.ts` e
  `session-watcher.tsx`. É risco desproporcional ao objetivo.

A decisão **D5** do change `manual-mkdocs` — publicar no GitHub Pages, desacoplado
do deploy da aplicação — **permanece válida**. Este change trata apenas da lacuna
real: tornar o manual alcançável de dentro do produto.

## What Changes

- **Um item "Manual" é adicionado à navegação lateral** do shell autenticado
  (`components/protected-shell.tsx`), apontando para o site do manual no GitHub
  Pages e abrindo em **nova aba** (`target="_blank"`), para não descartar o
  contexto de trabalho do usuário.
- **O tipo `ItemMenu` passa a suportar destino externo.** Hoje todos os itens são
  rotas internas renderizadas com `next/link` (`ItemMenu.href: string` →
  `<Link>`). Um destino externo precisa de `<a>` com `href` absoluto,
  `target="_blank"` e `rel="noopener noreferrer"` — o componente passa a distinguir
  os dois casos.
- **O item é visível para todos os perfis.** O manual documenta os três perfis e a
  navegação do site é por perfil; não há razão para restringir o acesso a ele.
  Nenhuma regra de visibilidade por perfil existente é alterada.
- **O item não participa do destaque de rota ativa.** O realce de item ativo
  (`itemAtivo(pathname, href)`) compara com a rota corrente do Next; um link
  externo nunca é a rota corrente e não deve ser marcado como ativo.
- **A URL do manual fica num ponto único**, no mesmo espírito de `lib/marca.ts` —
  não literal espalhado por componente.

## Capabilities

### New Capabilities

<!-- Nenhuma. -->

### Modified Capabilities

- **`identidade-visual`** — o requisito "Navegação em sidebar preservando o RBAC
  por perfil" é estendido para admitir **item de navegação externo**, visível a
  todos os perfis, aberto em nova aba e excluído do destaque de item ativo. Os
  cenários existentes de RBAC — incluindo os de **acesso negado** (servidor não vê
  itens administrativos; usuário sem `pode_auditar` não vê Relatório de Auditoria)
  — permanecem **inalterados** e devem continuar valendo.

## Impact

- **Dependências**: **requer `manual-mkdocs` arquivado** (já está, desde
  2026-08-04) — o site precisa estar publicado para que o link tenha destino. Com o
  Pages já habilitado, a URL de destino é o site do repositório
  `CarlosSalesNaturalTec/setes.docs`.
- **Tabelas PostgreSQL**: **nenhuma**.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: **nenhum**.
- **Backend**: **nenhuma alteração**. Nenhum endpoint, schema ou rota é tocado.
- **Contrato**: **nenhuma regeneração de tipos**.
- **Frontend**: `components/protected-shell.tsx` (tipo `ItemMenu`, lista
  `ITENS_MENU`, renderização do item), um ícone novo em `components/icons.tsx` e o
  ponto único da URL.
- **Testes**: `components/protected-shell.test.tsx` já verifica a composição do
  menu por perfil — precisa acompanhar o item novo. O teste deve cobrir que o item
  aparece para os três perfis, que abre em nova aba com
  `rel="noopener noreferrer"`, e que **nenhum item restrito passou a aparecer para
  perfil sem acesso** (regressão de RBAC).
- **LGPD**: **não aplicável** — nenhum dado pessoal é tratado. Vale registrar que o
  link leva a um site **público**, hospedado fora da infraestrutura GCP do produto;
  isso não expõe dado algum, já que o manual não contém dados reais (garantido pelo
  `docs_dir` restrito, D1 de `manual-mkdocs`).
- **PRD**: nenhuma alteração.

> **Trade-off herdado e reafirmado**: o manual continua sendo um site **público**
> num domínio `github.io`, e o produto continua sendo interno. É exatamente o
> trade-off registrado em "Risks / Trade-offs" do design de `manual-mkdocs`, agora
> reafirmado com conhecimento do custo da alternativa. Se a privacidade do manual
> vier a se tornar requisito, o caminho é uma change de sessão por cookie — não um
> ajuste neste change.
