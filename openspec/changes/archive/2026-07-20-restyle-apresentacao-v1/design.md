## Context

O `apps/web` nasceu funcional mas sem identidade visual: `tailwind.config.ts`
tem `theme.extend: {}`, `globals.css` só carrega as camadas do Tailwind, e as
telas usam a paleta default (`blue-600`, `gray-*`). A navegação autenticada
(`components/protected-shell.tsx`) é uma top-nav horizontal com links de texto;
o Login (`app/login/page.tsx`) é um `<main max-w-sm>` sem card nem logo. A
referência aprovada ("versão 1") usa navy institucional, card de login centrado
e sidebar vertical com ícones.

Restrições que moldam o design:
- **Presentation-only**: sem tocar lógica de domínio, rotas, contrato de API ou
  banco. Nada de `pnpm gen:types`, nada de migration.
- **RBAC é invariante**: a visibilidade de itens de menu por perfil/permissão em
  `protected-shell.tsx` NÃO pode regredir (US 8.2; cenário de acesso negado).
- **A marca já existe**: o navy `#1e3a5f` do `app/icon.svg` é a cor-fonte.
- **Testes existentes verdes**: `app/login/page.test.tsx`,
  `components/*.test.tsx` e o E2E `e2e/01-setup-login.spec.ts` dependem de
  seletores/roles atuais.

## Goals / Non-Goals

**Goals:**
- Estabelecer tokens de marca no Tailwind, consumidos por toda a UI (fonte única).
- Reestilizar Login (card centrado, logo, inputs com ícone, botão navy) sem SSO.
- Trocar a top-nav por sidebar vertical com ícones e item ativo, preservando o RBAC.
- Repaginar cards do dashboard e tabelas de admin para herdar o tema.

**Non-Goals:**
- Reproduzir o Painel de KPIs completo da v1 (gráficos, cards com ícones
  coloridos) — Épico 6 (`dashboard-kpis`), change separado.
- Criar a tela "Modelos" da sidebar da v1 (não existe no MVP).
- Login com Google / qualquer SSO.
- Introduzir biblioteca de UI (shadcn, MUI) ou de ícones (lucide) — mantém-se a
  abordagem de ícones SVG inline já usada em `components/icons.tsx`.
- Dark mode / theming dinâmico.

## Decisions

### D1 — Tokens de marca via `tailwind.config.ts`, não CSS vars soltas
Estender `theme.extend.colors` com uma escala `navy` (`50`, `600`, `700`, `900`),
`superficie` (fundo da app + card) e reaproveitar `borderRadius`/`boxShadow` para
o card. Consumo por classes utilitárias (`bg-navy-900`, `rounded-card`,
`shadow-card`).

- **Por quê**: é a fonte única que o CLAUDE.md pressupõe ("theme" do Tailwind),
  mantém o consumo declarativo nas telas e evita divergência entre `blue-600`
  espalhado. Alternativa (CSS custom properties em `globals.css`) foi descartada
  por fragmentar a definição entre dois lugares e não tipar as classes.
- **Escala navy** (derivada de `#1e3a5f`): `900:#1e3a5f` (primária/logo/ativo),
  `700:#274b74` (hover), `600:#2f5a8a` (link/ação secundária), `50:#eef2f8`
  (fundo de item ativo / superfície suave). Valores exatos afináveis na
  implementação; o token é o contrato, não o hex.

### D2 — Layout do shell: sidebar fixa + área de conteúdo, header enxuto
Substituir o `<header>` top-nav por um grid de duas colunas: `<aside>` fixa
(~240px) à esquerda com logo+subtítulo e a lista de itens; à direita, um header
fino (usuário · perfil, `NotificacoesSino`, "Sair") sobre o `<main>`. O array de
itens de menu passa a ser dado — `{ href, label, Icon, visivel }` — e o mesmo
predicado de visibilidade de hoje decide `visivel`. **Nenhum predicado RBAC é
alterado**; só migram de JSX condicional para campo do item.

```
┌──────────────┬───────────────────────────────────────────┐
│  [logo]      │  header:  🔔  Nome · perfil     [ Sair ]   │
│  SETES.DOCS  ├───────────────────────────────────────────┤
│  SISTEMA…    │                                           │
│ ┌──────────┐ │                                           │
│ │▣ Painel  │ │   <main> (children)                       │
│ └──────────┘ │   cards / tabelas herdando tokens         │
│  🗀 Processos │                                           │
│  📊 Relat.   │                                           │
│  🏢 Unidades │                                           │
│  👤 Perfil   │                                           │
└──────────────┴───────────────────────────────────────────┘
   item ativo = fundo navy-50 + texto navy-900 (via usePathname)
```

- **Item ativo**: `usePathname()` comparado ao `href` do item (match por prefixo
  para subrotas). Client component — o shell já é `"use client"`.
- **Responsivo** (resolve Q3): em telas estreitas a sidebar vira um **drawer** —
  oculta por padrão, aberta por um botão "hambúrguer" no header, com overlay que
  a fecha ao clicar fora. O conteúdo nunca é bloqueado.

### D3 — Reconciliação dos itens de menu (sidebar da v1 × rotas reais da v2)
A sidebar da v1 lista itens que não mapeiam 1:1 nas rotas da v2. A lista final
adota o **layout** da v1 e o **conteúdo/visibilidade** da v2:

| Item (label)          | Rota                          | Condição de visibilidade (inalterada) |
|-----------------------|-------------------------------|----------------------------------------|
| Meu Perfil            | `/perfil`                     | qualquer sessão                        |
| Processos             | `/processos`                  | qualquer sessão                        |
| Dashboard             | `/dashboard`                  | `perfil === "gestor"`                  |
| Relatório de Auditoria| `/auditoria/relatorios`       | `pode_auditar`                         |
| Usuários              | `/admin/usuarios`             | `administrador` ou `gestor`            |
| Unidades              | `/admin/unidades`             | `administrador`                        |
| Tipos de Processo     | `/admin/tipos-processo`       | `administrador`                        |
| Documentos Removidos  | `/admin/documentos-removidos` | `administrador`                        |
| Solicitações LGPD     | `/admin/lgpd`                 | `administrador`                        |

- **"Painel" da v1 → "Dashboard"**: mantém-se o label/rota que existe. Não se
  cria uma rota `/painel`.
- **"Novo Processo" NÃO é item de sidebar** (resolve Q1): a criação continua
  como **botão dentro de `/processos`**, apontando para `/processos/novo`. A
  sidebar não lista esse item.
- **"Modelos" e "Relatórios" genéricos da v1**: fora — não há rota no MVP.
- **Itens administrativos ficam planos na sidebar** (resolve Q2): sem rótulo
  "Administração" agrupando — cada item é de primeiro nível, na ordem da tabela.

### D4 — Login: reestilizar o markup, congelar a lógica
Reescrever apenas a árvore JSX de `LoginForm` (card, logo, ícones nos inputs,
botão navy). `onSubmit`, `useAuth().login`, `rotaInicial`, estados `erro/enviando`
e as mensagens `MENSAGENS_MOTIVO` permanecem intactos. Os ícones de envelope e
cadeado entram como novos componentes em `components/icons.tsx`.

- **Acessibilidade/testes**: preservar `<label htmlFor>`, `id`, `type` e o texto
  do botão ("Entrar"/"Entrando…") para não quebrar `page.test.tsx` nem o E2E
  (que localizam por role/label). Ícones decorativos ficam `aria-hidden`.

### D5 — Ícones de navegação seguindo o padrão existente
Adicionar em `components/icons.tsx` os ícones de menu (`IconPainel`,
`IconProcessos`/pasta, `IconNovoProcesso`, `IconConsultaPublica`/globo,
`IconRelatorios`/gráfico, `IconUnidades` — já existe `IconBuildings`, reusar —,
`IconUsuarios`, `IconPerfil`, `IconTiposProcesso`, `IconLgpd`,
`IconDocumentos`), além de `IconEnvelope` e `IconCadeado` do Login. Mesmo padrão:
SVG inline, `viewBox 0 0 24 24`, `stroke="currentColor"`, `aria-hidden` — herdam
a cor do contexto.

- **Por quê inline e não lucide-react**: consistência com o que já existe, zero
  dependência nova, tree-shaking trivial. `IconBuildings` já cobre Unidades.

### D6 — Repaginação das páginas internas por herança de tokens
As páginas de conteúdo consomem os tokens via classes (`bg-superficie-card`,
`rounded-card`, `shadow-card`, `text-navy-900`). Prioridade: `app/dashboard`
(cards) e as tabelas de `app/admin/*`. Onde houver repetição de "casca de card",
extrair um utilitário/classe comum é aceitável, mas **não** é requisito criar uma
biblioteca de componentes neste change.

## Risks / Trade-offs

- **[Testes quebram por seletor/estrutura]** → Preservar roles, labels, `id`s e
  textos visíveis (D4). Rodar `pnpm --filter @setes/web test` e o E2E de login
  após cada bloco. Ajustar seletores só quando inevitável, documentando no commit.
- **[Regressão silenciosa no RBAC ao migrar JSX condicional → dados]** → Manter
  os predicados idênticos e cobrir com o teste do shell os três perfis + o caso
  `pode_auditar` (cenários da spec). Nenhum item novo é adicionado.
- **[Escopo "repaginar tabelas" incha]** → Limitar à casca (superfície, radius,
  sombra, cor primária); não redesenhar densidade, paginação ou colunas. Dados e
  ações permanecem idênticos (requisito da spec).
- **[Sidebar em telas estreitas]** → Fornecer colapso simples; não bloquear o
  conteúdo. Tratar como polimento, não como gate do change.
- **[Divergência de hex do navy vs. `icon.svg`]** → `#1e3a5f` é a fonte única;
  se afinar derivados, manter o `900` alinhado ao ícone para o logo casar.

## Migration Plan

Sem migration de banco. Deploy é o fluxo web padrão (Cloud Run, `apps/web`).
Rollout incremental sugerido, cada etapa verde antes da próxima:
1. Tokens no `tailwind.config.ts` (sem efeito visual até serem usados).
2. Ícones novos em `components/icons.tsx`.
3. Login reestilizado + revalidar `page.test.tsx` e E2E de login.
4. Shell → sidebar + teste do shell cobrindo os perfis (RBAC).
5. Cards do dashboard e tabelas de admin.

Rollback: reverter o commit da etapa — não há estado persistente afetado.

## Open Questions

Todas resolvidas (decisões do cliente, incorporadas às Decisions acima):

- **Q1 — "Novo Processo" na sidebar** → **RESOLVIDO**: não é item de sidebar;
  permanece como botão dentro de `/processos` (ver D3).
- **Q2 — Agrupar itens administrativos** → **RESOLVIDO**: não agrupar; itens
  administrativos ficam planos, de primeiro nível (ver D3).
- **Q3 — Responsivo da sidebar** → **RESOLVIDO**: drawer (oculta por padrão em
  telas estreitas, aberta por botão no header, com overlay) (ver D2).
