## Why

Testes em produção revelaram um conjunto de ajustes de acabamento e duas
correções de comportamento nas telas administrativas e de perfil: o favicon
retorna 500, "Meu Perfil" não permite editar o próprio nome, unidades inativas
não têm como ser reativadas, o cadastro de tipo de processo aceita unidades
inativas no roteiro (bug de invariante de domínio) e o Administrador vê
controles de ação de processo que não pode executar. São refinamentos pós-MVP
que não introduzem épico novo — recortam gestão de usuários/unidades/tipos e
controle de acesso já entregues.

## What Changes

- **Favicon (500 → OK)**: adicionar ativo de ícone (`app/icon.svg`) e declarar
  `metadata.icons` no `layout.tsx`. Correção de asset, sem contrato.
- **Design das tabelas de admin**: refinar as tabelas de `admin/usuarios` e
  `admin/unidades` e substituir as ações em texto por ícones com `aria-label`/
  `title` (acessibilidade preservada). Apenas UI.
- **Editar o próprio Nome em "Meu Perfil"**: novo endpoint self-service
  (`PATCH /usuarios/me/perfil`) que altera **apenas o nome** do usuário
  autenticado; edição livre, limite de 200 caracteres (conforme `String(200)`
  do modelo). Form de edição em `perfil/page.tsx`. E-mail e perfil continuam
  não-editáveis pelo próprio usuário.
- **Reativação de unidade inativa**: novo endpoint
  `POST /unidades/{id}/reativar` (Admin-only) e botão "Reativar" quando
  `!ativo`. A reativação **não** repovoa `unidade_id` dos servidores que foram
  desvinculados na desativação — o revínculo continua manual.
- **Remoção do campo "Gestor responsável" do cadastro de unidade**: o campo é
  hoje decorativo — o acesso do Gestor a uma unidade vem exclusivamente da M2M
  `UnidadeGestor` ("Unidades geridas"). Remoção **apenas de UI**; a coluna
  `Unidade.gestor_responsavel_id` fica dormente, sem migration.
- **Administrador com acesso read-only a Processos**: mantém o link "Processos"
  e a visão consolidada do Kanban (Admin já enxerga todas as unidades), mas
  oculta para o Administrador os controles de ação (Novo processo, Despachar,
  Devolver, alternar sigilo). O backend já rejeita essas ações (são
  SERVIDOR-only) — o ajuste é de front, para não exibir controle inútil.
- **Bug — unidade inativa em roteiro**: `_validar_unidades` passa a rejeitar
  unidades inativas (em `criar_tipo_processo` e `atualizar_roteiro`) e o
  dropdown de montagem do roteiro passa a listar somente unidades ativas.
  Espelha o precedente já existente no cadastro de usuário ("Unidade
  inexistente ou inativa").

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: todos os ajustes recortam capabilities já existentes. -->

### Modified Capabilities
- `gestao-usuarios`: novo requisito de auto-serviço — o usuário autenticado
  altera o próprio nome (US 1.5), sem poder alterar e-mail/perfil.
- `unidades-administrativas`: novo requisito de **reativação** de unidade
  inativa (Admin-only, sem revínculo automático de servidores); e remoção do
  vínculo de "gestor responsável" da superfície de cadastro/edição de unidade
  (o vínculo de gestão passa a viver só em `UnidadeGestor`).
- `tipos-processo-e-roteiros`: a validação de roteiro passa a **rejeitar
  unidades inativas**, tanto na criação quanto no versionamento do roteiro.
- `quadro-kanban`: o Administrador tem acesso **read-only** ao Kanban
  consolidado de todas as unidades — visualiza, mas não dispõe de controles de
  ação (criar/despachar/devolver/sigilo).

## Impact

- **Depende de**: `identidade-e-estrutura-organizacional`,
  `administracao-usuario-auditoria`, `processos-e-workflow` e
  `tipos-processo-e-roteiros` (todos arquivados). Nenhuma dependência de change
  em aberto.
- **Tabelas PostgreSQL**: nenhuma nova nem alterada. `Unidade.gestor_responsavel_id`
  permanece na tabela `unidade` porém sem uso (sem migration de remoção neste
  change). Sem novas FKs.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager nem bucket no
  Cloud Storage.
- **Contrato OpenAPI**: novos endpoints `PATCH /usuarios/me/perfil` e
  `POST /unidades/{id}/reativar` → exige `pnpm gen:types` e commit do snapshot
  em `packages/api-types` (o CI roda `gen:types:check`).
- **Backend**: `app/routers/usuarios.py`, `app/routers/unidades.py`,
  `app/routers/tipos_processo.py`, `app/schemas/*` correspondentes.
- **Frontend**: `app/layout.tsx` + `app/icon.svg`, `app/perfil/page.tsx`,
  `app/admin/usuarios/page.tsx`, `app/admin/unidades/page.tsx`,
  `app/admin/tipos-processo/page.tsx`, `app/processos/page.tsx`,
  `app/processos/[id]/page.tsx`, `lib/api.ts`.
- **LGPD**: o único dado pessoal tocado é o **nome do próprio usuário
  autenticado**, editado por ele mesmo — não há dado de interessado/terceiro
  nem exposição em consulta pública. Sem impacto em anonimização ou retenção.
