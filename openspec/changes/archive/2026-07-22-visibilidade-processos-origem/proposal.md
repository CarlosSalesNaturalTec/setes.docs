## Why

Hoje o Kanban do Servidor mostra apenas os processos **atualmente** na sua
unidade (US 1.4 Cen.1). Quando um processo é despachado para outra unidade, ele
some da tela da unidade que o abriu — o autor só reencontra metadados em "Meu
Perfil", e o detalhe responde "Acesso negado". Na prática, a unidade de origem
perde a capacidade de **acompanhar** o que protocolou: nunca vê seus processos
"Em Tramitação" em outras unidades, nem os "Concluído"/"Arquivado" (que ficam no
Kanban da última unidade do roteiro). Este change revisa conscientemente a regra
de visibilidade do PRD US 1.4: a tela de Processos passa a incluir, em modo
**somente leitura**, os processos cuja **unidade de origem** está no escopo do
usuário.

## What Changes

- **Escopo de visibilidade ampliado** no Kanban/Lista: além dos processos na
  unidade atual, o usuário vê os processos cuja `unidade_origem_id` pertence ao
  seu escopo (Servidor: própria unidade; Gestor: geridas; Administrador já vê
  tudo). A ampliação é **por unidade de origem**, não por autor — sobrevive a
  férias, transferência ou desativação do criador.
- **Read-only fora da unidade atual**: processos visíveis apenas por origem são
  exibidos com card **acinzentado** e abrem o detalhe em modo leitura (sem
  Despachar/Devolver/sigilo/documentos). O backend já bloqueia escrita fora da
  unidade atual; a leitura do detalhe passa a ser permitida para a unidade de
  origem.
- **Sigilo prevalece sobre o acompanhamento**: processo sigiloso que está em
  outra unidade **não aparece** no Kanban da unidade de origem e o detalhe segue
  negado ("Acesso restrito"). A regra de sigilo existente não é flexibilizada.
- **Destaque de devolução**: card destacado no Kanban/Lista enquanto o **último
  evento** do histórico for `DEVOLUCAO` e o processo estiver na unidade do
  usuário (o destaque apaga naturalmente no próximo despacho). Processo
  devolvido à unidade é acionável normalmente (não é read-only).
- **Checkbox "Exibir concluídos e arquivados"** no topo da tela de Processos,
  **desmarcado por padrão**, válido para todos os perfis, persistido em
  `localStorage`. Desmarcado, oculta as colunas/linhas de Concluído e Arquivado
  (o contador do cabeçalho reflete só o visível).
- **Contrato do card** (`CardProcessoResponse`) ganha campos aditivos
  `devolvido: bool` e `somente_leitura: bool` (processo fora da unidade atual do
  usuário, visível por origem). Mudança não-breaking; exige `pnpm gen:types` +
  commit de `packages/api-types`.
- **Revisão do PRD**: US 1.4 Cen.1 é atualizado para registrar a nova regra
  (visibilidade = unidade atual ∪ unidade de origem, read-only e sem sigilosos
  fora da unidade).

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a tela de Processos, o card e a primitiva de
acesso já existem — os requisitos deles é que mudam. -->

### Modified Capabilities

- `quadro-kanban`: o escopo do quadro do Servidor/Gestor passa a incluir
  processos da unidade de origem (read-only, acinzentados, sem sigilosos fora da
  unidade); novo destaque visual de devolução; novo checkbox "Exibir concluídos
  e arquivados" (default desmarcado, todos os perfis); card ganha `devolvido` e
  `somente_leitura`.
- `controle-acesso-por-unidade`: a **leitura** de detalhe/histórico passa a
  aceitar também o escopo da unidade de origem (exceto sigiloso); a **escrita**
  (despacho, devolução, sigilo, documentos) permanece estrita à unidade atual,
  com cenários explícitos de acesso negado.

## Impact

- **Dependências**: requer `processos-e-workflow`, `sigilo-de-processo` e
  `ajustar-visualizacao-processos` (todos arquivados). Nenhuma migration: usa a
  coluna existente `processo.unidade_origem_id` e a tabela `tramitacao` (último
  evento). Sem novo segredo no Secret Manager e sem novo bucket.
- **Backend** (`apps/api`): `services/processo_consulta.py` (`listar_kanban`,
  `buscar` — escopo `unidade_atual ∪ unidade_origem`, exclusão de sigilosos
  fora da unidade atual, cálculo de `devolvido`); `routers/processos.py`
  (`_exigir_leitura_ao_processo` aceita unidade de origem, mantendo negação +
  log para sigiloso); `schemas/processo.py` (`CardProcessoResponse.devolvido`,
  `.somente_leitura`).
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados
  (`pnpm gen:types`; CI `gen:types:check`).
- **Frontend** (`apps/web`): `app/processos/page.tsx` (checkbox, cards
  acinzentados, destaque de devolução), `app/processos/[id]/page.tsx` (modo
  leitura para visibilidade por origem, reutilizando o padrão read-only do
  Administrador), `lib/processo-ui.ts`.
- **LGPD**: nenhuma coleta nova de dado pessoal. A leitura do detalhe pela
  unidade de origem expõe dados já tratados (interessados CPF/CNPJ) a uma
  unidade que já teve o processo sob sua guarda — tratamento coberto pela base
  legal existente; processos sigilosos ficam de fora. Por tocar visibilidade de
  dados pessoais e histórico de tramitação, o change exige testes automatizados
  (pytest) incluindo cenários de acesso negado, e E2E Playwright do fluxo de
  despacho/acompanhamento (config OpenSpec vinculante).
- **PRD**: `docs/PRD.md` US 1.4 (Cen.1) atualizado como parte do change.
