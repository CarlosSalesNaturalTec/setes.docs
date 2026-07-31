## Why

Após a primeira entrega, o cliente avaliou o sistema e pediu um conjunto de
ajustes — vários estruturais (`docs/Ajustes SETES DOCS.pdf`). A estrutura
organizacional atual só tem um nível (**Unidade**), e o Servidor é vinculado
apenas a ela. O cliente precisa de um segundo nível — **Setor** — porque a
tramitação manual (change `tramitacao-manual`) exige escolher explicitamente
unidade **e setor** **e servidor** de destino. Sem Setor no modelo, a tela de
tramitação não fecha.

Junto vêm os ajustes de cadastro de usuário pedidos no mesmo documento
(telefone, cargo, chefia direta, setor), a substituição do formulário inline por
um modal, e a troca do espaço liberado no índice por um filtro de busca por
nome.

Este é o **primeiro** dos seis changes que implementam os ajustes pós-avaliação.
É a fundação: não altera workflow nem visibilidade, apenas adiciona a estrutura
de que os changes seguintes dependem.

## What Changes

- **Nova entidade `Setor`**, vinculada a uma Unidade (1:N): nome, sigla, ativo.
  CRUD restrito ao Administrador, no mesmo padrão de `unidades-administrativas`
  (cadastrar, editar, desativar/reativar — nunca excluir).
- **`Usuario` ganha `setor_id`**, FK para `setor`. **Obrigatório para o perfil
  Servidor** (decisão do cliente); Gestor e Administrador seguem opcionais. O
  setor escolhido SHALL pertencer à unidade do usuário — não há setor
  "solto" nem setor de outra unidade.
- **Novos campos de cadastro de usuário**: `telefone`, `cargo`, `chefia_direta`
  (texto livre — pode nomear chefia externa ao sistema, decisão do cliente).
- **Modal de cadastro de novo usuário** substitui o formulário inline hoje
  renderizado no índice de `/admin/usuarios`.
- **Filtro por nome** ocupa, no índice, o espaço antes usado pelo formulário —
  busca parcial, case-insensitive, aplicada no backend.
- **Desativação de unidade cascateia coerência**: desativar uma Unidade SHALL
  desativar seus Setores; um Setor não pode ser desativado enquanto houver
  Servidor ativo vinculado a ele (mesma guarda já usada para Unidade).

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: Setor é um segundo nível da estrutura
organizacional já coberta por `unidades-administrativas`, e os campos/telas de
usuário pertencem a `gestao-usuarios`. -->

### Modified Capabilities

- `unidades-administrativas`: passa a cobrir o cadastro de **Setores** vinculados
  à Unidade (CRUD do Administrador, desativação em cascata, guarda de setor com
  servidores ativos).
- `gestao-usuarios`: cadastro ganha `setor` (obrigatório para Servidor,
  restrito à unidade do usuário), `telefone`, `cargo` e `chefia_direta`; o
  formulário inline vira **modal**; o índice ganha **filtro por nome**.

## Impact

- **Dependências**: requer `identidade-e-estrutura-organizacional` e
  `administracao-usuario-auditoria` (ambos arquivados). É **pré-requisito** de
  `tramitacao-manual`, que consome `setor` no destino da tramitação.
- **Tabelas PostgreSQL**: **nova** tabela `setor` (`id` uuid PK, `unidade_id`
  FK→`unidade`, `nome`, `sigla`, `ativo`); **alterada** `usuario`
  (+`setor_id` FK→`setor` nullable no schema, obrigatoriedade do Servidor
  validada na aplicação; +`telefone`, +`cargo`, +`chefia_direta`).
- **Migrations**: `0020_setor`, `0021_usuario_setor_e_campos`.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket
  novo no Cloud Storage.
- **Backend** (`apps/api`): `db/models.py` (`Setor`, campos de `Usuario`),
  `services/unidades.py` (+setores), `routers/unidades.py` (rotas de setor),
  `routers/usuarios.py` (filtro por nome, novos campos),
  `schemas/unidades.py`, `schemas/usuarios.py`, `db/dev_reset.py`.
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados
  (`pnpm gen:types`; CI `gen:types:check`).
- **Frontend** (`apps/web`): `app/admin/unidades/page.tsx` (setores da unidade),
  `app/admin/usuarios/page.tsx` (modal de cadastro, filtro por nome, novos
  campos), `app/perfil/page.tsx` (exibir setor/cargo/telefone/chefia).
- **LGPD**: `telefone`, `cargo` e `chefia_direta` são **dados pessoais de
  servidor** (não de interessado/cidadão). Coleta com finalidade de identificação
  funcional e roteamento de tramitação; retenção acompanha o ciclo de vida da
  conta do usuário; sem exposição em consulta pública e sem inclusão no fluxo de
  anonimização de interessados (Épico 10, que trata de terceiros). Por tocar
  dados pessoais, o change **exige** testes automatizados pytest, incluindo
  cenários de acesso negado ao CRUD de setor por perfil não-Administrador.
- **PRD**: `docs/PRD.md` — Épico 1 (US 1.1/1.3) e Épico 8 (US 8.1/8.2)
  atualizados com Setor e os novos campos de cadastro.
