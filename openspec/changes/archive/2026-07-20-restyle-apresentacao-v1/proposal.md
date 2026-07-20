## Why

O frontend atual (`apps/web`) não tem identidade visual: `tailwind.config.ts`
está com `theme.extend: {}` vazio, o `globals.css` só importa as camadas do
Tailwind e as telas usam a paleta default (`blue-600`, `gray-*`). O resultado é
uma UI utilitária, sem marca — enquanto a "versão 1" do produto (referência
aprovada pelo cliente) tem um visual coeso: navy institucional, cards com bordas
arredondadas e sombra, Login com card centrado e sidebar de navegação com ícones.
A marca já existe no repositório (o navy `#1e3a5f` do `app/icon.svg`), mas nunca
foi propagada para a UI. Este change estabelece essa identidade visual e a
aplica ao Login, ao shell de navegação e ao conteúdo das páginas internas.

Escopo **exclusivamente de apresentação**: não há lógica de domínio nova,
nenhuma rota nova, nenhuma mudança de contrato de API. O controle de acesso por
perfil (RBAC) exibido na navegação é preservado item a item.

## What Changes

- **Tokens de marca no Tailwind**: adicionar ao `tailwind.config.ts` a paleta
  navy (`#1e3a5f` e derivados 700/600/50), superfícies (fundo da app, superfície
  de card), radius padrão e sombra de card — consumidos por todas as telas.
- **Login (`app/login/page.tsx`)**: card branco centrado com borda e sombra;
  logo navy arredondado + título "SETES.DOCS" + subtítulo "Acesse sua conta";
  inputs de e-mail e senha com ícone interno (envelope/cadeado) e placeholder;
  botão primário navy. **Sem** botão "Continue with Google" (decisão explícita —
  o MVP não tem SSO; ver `autenticacao`).
- **Shell/navegação (`components/protected-shell.tsx`)**: substituir a top-nav
  horizontal por **sidebar vertical fixa à esquerda** — logo + subtítulo "SISTEMA
  ELETRÔNICO" no topo, cada item de menu com ícone, item ativo destacado; menu do
  usuário (nome · perfil, sino de notificações, "Sair") no cabeçalho superior
  direito. **A visibilidade condicional por perfil/permissão de cada item é
  mantida exatamente como está** (invariante de acesso por unidade/perfil).
- **Ícones de navegação (`components/icons.tsx`)**: adicionar os ícones inline
  usados pela sidebar (painel, pasta/processos, novo, globo/consulta pública,
  gráfico/relatórios, unidades, usuários, perfil, tipos, LGPD, documentos).
- **Repaginação do conteúdo interno**: cards do dashboard
  (`app/dashboard/page.tsx`) e tabelas das telas de admin (`app/admin/*`,
  `app/processos/*`, etc.) passam a herdar os tokens — superfícies de card com
  borda arredondada e sombra, cabeçalhos e cores de estado alinhados ao tema.

Fora de escopo (trabalho futuro, **não** neste change):
- Reproduzir o "Painel de Controle" completo da v1 (cards de KPI com ícones
  coloridos + gráficos de barras) — isso é feature do Épico 6 (`dashboard-kpis`).
- Adicionar a rota/tela "Modelos" que aparece na sidebar da v1 (não existe no MVP).
- Login com Google / qualquer SSO.

## Capabilities

### New Capabilities
- `identidade-visual`: define os tokens de marca (paleta, superfícies, radius,
  sombra) e os requisitos de apresentação de Login e shell de navegação
  (layout de sidebar, item ativo, menu do usuário) — preservando o RBAC de
  navegação já especificado em `controle-acesso-por-unidade` e `autenticacao`.

### Modified Capabilities
<!-- Nenhuma. Este change não altera requisitos de comportamento existentes;
     a visibilidade de itens de menu por perfil e o fluxo de login permanecem
     como especificados. Apenas a camada de apresentação muda. -->

## Impact

- **Código afetado (apenas `apps/web`)**:
  - `tailwind.config.ts` — tokens de marca (`theme.extend.colors/borderRadius/boxShadow`).
  - `app/login/page.tsx` — reestilização do formulário (sem mudança de lógica de login).
  - `components/protected-shell.tsx` — troca de top-nav por sidebar; RBAC preservado.
  - `components/icons.tsx` — novos ícones de navegação.
  - `app/dashboard/page.tsx` e telas `app/admin/*` / `app/processos/*` — cards e tabelas herdando o tema.
  - Possível `app/globals.css` — variáveis/estilos base do fundo da app.
- **Banco de dados**: nenhuma tabela nova ou afetada. Sem migrations.
- **Segredos / Cloud Storage**: nenhum segredo novo no Secret Manager, nenhum bucket novo.
- **LGPD**: não há coleta, retenção ou tratamento de dados pessoais — mudança
  puramente de apresentação.
- **Contrato de API / tipos gerados**: inalterado — nenhum schema/rota do FastAPI
  muda, `pnpm gen:types` não é necessário.
- **Dependência de change anterior**: requer `2026-07-18-redirect-login-por-perfil`
  arquivado (Login e shell atuais estáveis); o layout de navegação reestilizado
  reflete os itens já introduzidos até esse ponto.
- **Testes**: os testes de Login/shell existentes (`app/login/page.test.tsx`,
  `components/*.test.tsx`) precisam continuar verdes; ajustes de seletores podem
  ser necessários. Alteração em `app/login/page.tsx` (fluxo de login) exige
  revalidar o E2E Playwright de login (`e2e/01-setup-login.spec.ts`).
