## 1. Tokens de marca (fundação)

- [ ] 1.1 Estender `theme.extend` em `apps/web/tailwind.config.ts` com a escala
  `navy` (`50/600/700/900`, `900:#1e3a5f`), superfícies (`app`, `card`),
  `borderRadius.card` e `boxShadow.card`.
  **Aceite**: `pnpm --filter @setes/web typecheck` verde; classes `bg-navy-900`,
  `rounded-card`, `shadow-card` disponíveis (uso de teste removido em seguida).
- [ ] 1.2 Ajustar `apps/web/app/globals.css` para o fundo da aplicação usar a
  superfície de app (se necessário) sem introduzir CSS fora dos tokens.
  **Aceite**: fundo da app reflete o token; nenhuma regressão de layout.

## 2. Ícones de navegação e de Login

- [ ] 2.1 Adicionar em `apps/web/components/icons.tsx` os ícones de menu
  (`IconPainel`, `IconProcessos`, `IconNovoProcesso`, `IconConsultaPublica`,
  `IconRelatorios`, `IconUsuarios`, `IconPerfil`, `IconTiposProcesso`,
  `IconLgpd`, `IconDocumentos`) seguindo o padrão inline existente
  (`viewBox 0 0 24 24`, `stroke="currentColor"`, `aria-hidden`). Reusar
  `IconBuildings` para Unidades.
  **Aceite**: todos exportados, 18–20px, herdam `currentColor`; typecheck verde.
- [ ] 2.2 Adicionar `IconEnvelope` e `IconCadeado` no mesmo arquivo para os
  inputs do Login.
  **Aceite**: renderizam como decoração `aria-hidden`.

## 3. Login (`app/login/page.tsx`)

- [ ] 3.1 Reestilizar o markup de `LoginForm`: card branco centrado (`rounded-card`,
  `shadow-card`), logo navy arredondado, título "SETES.DOCS", subtítulo "Acesse
  sua conta", inputs de e-mail/senha com ícone interno, botão navy "Entrar", link
  "Esqueci minha senha". **Não** incluir botão Google nem divisor "ou". Preservar
  `onSubmit`, `useAuth().login`, `rotaInicial`, estados e `MENSAGENS_MOTIVO`, e os
  atributos `id`/`htmlFor`/`type`/textos.
  **Aceite**: nenhuma alteração de lógica; sem qualquer referência a Google/SSO.
- [ ] 3.2 Atualizar/rodar `apps/web/app/login/page.test.tsx` (Vitest + RTL) para
  cobrir: campos e botão presentes, ausência de opção de SSO, e o fluxo de
  submit inalterado.
  **Aceite**: `pnpm --filter @setes/web test -- login/page.test.tsx` verde.
- [ ] 3.3 Revalidar o E2E de login `apps/web/e2e/01-setup-login.spec.ts`
  (Playwright), ajustando seletores só se estritamente necessário — login altera
  a tela de autenticação, então o E2E é obrigatório.
  **Aceite**: `cd apps/web && pnpm test:e2e -- 01-setup-login` verde.

## 4. Shell / sidebar (`components/protected-shell.tsx`)

- [ ] 4.1 Modelar os itens de menu como dados (`{ href, label, Icon, visivel }`),
  computando `visivel` com **os mesmos predicados RBAC atuais** (servidor/gestor/
  administrador/`pode_auditar`). Sem adicionar nem remover regras de visibilidade.
  **Aceite**: a lista renderizada por perfil é idêntica à atual (mesmos itens).
- [ ] 4.2 Substituir a top-nav por layout de sidebar vertical à esquerda (logo +
  "SISTEMA ELETRÔNICO" no topo, itens com ícone) + header superior direito com
  `NotificacoesSino`, "Nome · perfil" e "Sair" (logout preservado). Manter a
  mensagem de acesso negado existente.
  **Aceite**: logout ainda redireciona para `/login`; acesso negado inalterado.
- [ ] 4.3 Destacar o item ativo via `usePathname()` (match por prefixo para
  subrotas), estado ativo = `bg-navy-50` + `text-navy-900`.
  **Aceite**: em `/processos`, o item "Processos" aparece ativo; demais normais.
- [ ] 4.4 Sidebar como **drawer** em telas estreitas: oculta por padrão, botão
  "hambúrguer" no header a abre, overlay fecha ao clicar fora. Não listar "Novo
  Processo" na sidebar.
  **Aceite**: em viewport móvel o drawer abre/fecha e o conteúdo permanece
  acessível; sidebar não contém item "Novo Processo".
- [ ] 4.5 Teste do shell (Vitest + RTL) cobrindo os cenários da spec: servidor vê
  só seus itens; item de auditoria oculto sem `pode_auditar`; administrador vê os
  itens administrativos; item ativo destacado.
  **Aceite**: `pnpm --filter @setes/web test -- protected-shell` verde.

## 5. Repaginação do conteúdo interno

- [ ] 5.1 Aplicar os tokens aos cards de `apps/web/app/dashboard/page.tsx`
  (superfície de card, `rounded-card`, `shadow-card`, cores de estado). Sem
  alterar dados nem KPIs exibidos.
  **Aceite**: cards com a nova casca; conjunto de dados idêntico; teste do
  dashboard (`app/dashboard/page.test.tsx`) verde.
- [ ] 5.2 Garantir na página `app/processos/page.tsx` um botão "Novo Processo"
  (estilizado com o token primário navy) apontando para `/processos/novo` — a
  criação vive aqui, não na sidebar (Q1). Se o botão já existir, apenas reestilizar.
  **Aceite**: botão visível em `/processos` leva a `/processos/novo`; sem novo
  item na sidebar; testes da tela verdes.
- [ ] 5.3 Aplicar os tokens às tabelas/contêineres das telas de admin
  (`app/admin/unidades`, `app/admin/usuarios`, `app/admin/tipos-processo`,
  `app/admin/documentos-removidos`, `app/admin/lgpd`) e de processos
  (`app/processos`, `app/processos/[id]`). Sem alterar colunas, ações ou RBAC.
  **Aceite**: mesmas colunas e ações por perfil; visual coerente com o tema;
  testes das telas afetadas verdes.

## 6. Verificação final

- [ ] 6.1 Rodar a suíte web completa e o lint.
  **Aceite**: `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`
  e `pnpm --filter @setes/web lint` verdes.
- [ ] 6.2 Confirmar que o contrato de API não mudou (nenhum schema/rota tocado):
  `pnpm gen:types:check`.
  **Aceite**: sem drift de tipos — este change não altera o contrato.
- [ ] 6.3 Revisão visual manual das telas-chave (Login, shell por perfil,
  dashboard, uma tela de admin) contra a referência da v1.
  **Aceite**: navy institucional, card de login, sidebar com item ativo e cards
  arredondados presentes; sem regressão funcional.
