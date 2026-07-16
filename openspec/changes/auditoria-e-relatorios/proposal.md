## Why

O Épico 9 (Auditoria e Relatórios) é o **consumidor** de uma permissão que já foi
construída, mas hoje não faz nada. O change anterior `administracao-usuario-auditoria`
entregou de propósito **apenas o mecanismo**: a flag `usuario.pode_auditar` (ortogonal ao
perfil), concedível/revogável pelo Administrador e registrada em `log_seguranca`. O
próprio `proposal.md` daquele change declara que "o **consumo** dessa permissão — ver
processos sigilosos (US 9.1), gerar relatórios consolidados (US 9.2) — é o Épico 9 e fica
**fora deste escopo**". Enquanto esse consumo não existir, `pode_auditar` é um gancho sem
consumidor: um Auditor autorizado continua limitado à visibilidade por unidade como
qualquer Servidor, e não há relatório consolidado algum.

Este change fecha esse laço entregando as duas histórias do épico — US 9.1 (leitura
irrestrita mediante permissão) e US 9.2 (relatório consolidado de tramitação, em tela) —
sem introduzir tabelas novas nem geração de arquivo.

## What Changes

- **US 9.1 — Leitura irrestrita do Auditor:** um usuário autenticado com `pode_auditar =
  true` passa a visualizar **qualquer** processo do sistema — de qualquer unidade,
  inclusive **sigilosos** — completo: detalhe, histórico de tramitação e documentos
  anexados (com respectivas assinaturas, quando o Épico 4 existir). O acesso **não**
  depende de `require_acesso_unidade`: a flag de auditoria é um caminho de autorização
  paralelo à visibilidade por unidade, consumido nos endpoints de leitura de processo
  (`GET /processos/{id}`, `/historico`, e leitura de documentos).
- **US 9.1 — Acesso negado (cenário de rejeição):** usuário autenticado **sem**
  `pode_auditar` que tente acessar um processo **sigiloso** fora do seu escopo de unidade
  recebe a mensagem específica do PRD — `"Acesso restrito — solicite autorização ao
  Administrador"` — e a rejeição é registrada em `log_seguranca`
  (`tipo_evento=acesso_negado`). Distingue-se da rejeição genérica de unidade
  (`MSG_ACESSO_NEGADO_PROCESSO`): sigiloso sem permissão de auditoria tem mensagem própria.
- **Rastro de auditoria (decisão de design, não exigida pelo PRD):** todo acesso
  **bem-sucedido** de um Auditor a um processo via permissão de auditoria é registrado
  como evento imutável em `log_seguranca` (novo `tipo_evento=acesso_auditoria`), guardando
  quem auditou qual processo e quando — coerente com a invariante de histórico imutável e
  com a razão de existir do perfil Auditor (fiscalização rastreável).
- **US 9.2 — Relatório consolidado (em tela):** nova rota Auditor-only que retorna, para
  filtros de **período**, **unidade** e **tipo de processo**: total de processos no
  período, tempo médio de tramitação e a lista de processos com status atual e unidade
  atual. **Sem exportação** — o PRD define explicitamente que "o relatório é visualizado
  na própria interface. A exportação em PDF estará disponível em versão futura". Filtros
  sem resultado retornam a mensagem `"Nenhum dado encontrado para os filtros informados"`.
  As agregações (total, tempo médio de tramitação) **reaproveitam** a lógica já existente
  em `app/services/dashboard.py`, mudando o recorte de acesso: o dashboard filtra pelas
  unidades geridas pelo Gestor; o relatório de auditoria enxerga todas as unidades.
- **Frontend:** nova rota autenticada de relatório de auditoria (formulário de filtros +
  relatório consolidado em tela + estado vazio), visível apenas a usuários com
  `pode_auditar`. A leitura de processo existente passa a ser acessível ao Auditor.
- **Contrato:** há rotas/schemas novos no FastAPI → **regenerar** `packages/api-types`
  (`pnpm gen:types`); o CI `types-drift` falha se defasado.
- **Escopo negativo (explícito):** este change **não** implementa exportação de relatório
  (PDF/CSV — Fase futura), **não** altera o mecanismo de concessão da permissão (já
  entregue em `administracao-usuario-auditoria`) e **não** toca o Épico 10 (LGPD) nem o
  Épico 4 (assinatura). Onde a leitura menciona assinaturas, apenas expõe o que já existir.

## Capabilities

### New Capabilities
- `auditoria-processos`: leitura irrestrita de qualquer processo (inclusive sigiloso) por
  usuário com `pode_auditar`, com caminho de autorização paralelo à visibilidade por
  unidade, mensagem de acesso negado específica para não-autorizado e registro imutável do
  acesso de auditoria bem-sucedido. Cobre US 9.1.
- `relatorios-auditoria`: relatório consolidado de tramitação (em tela, sem exportação)
  por período/unidade/tipo, reaproveitando agregações do dashboard, com estado vazio.
  Cobre US 9.2.

### Modified Capabilities
- `sigilo-processo`: acrescenta o cenário em que a ocultação por sigilo é **suspensa** para
  usuário com permissão de auditoria (US 9.1 Cen.1) e o cenário de rejeição específico para
  quem tenta ver sigiloso sem a permissão (US 9.1 Cen.2).

## Impact

- **Requer (arquivados):** `administracao-usuario-auditoria` (flag `usuario.pode_auditar`,
  eventos de `log_seguranca`), `processos-e-workflow` (`processo`, `tramitacao`,
  `StatusProcesso`, leitura de detalhe/histórico), `sigilo-de-processo` (flag `sigiloso` e
  sua ocultação), `gestao-documental` (leitura de documentos anexados) e
  `dashboard-kpis-gestor` (agregações reaproveitadas em `services/dashboard.py`).
- **Tabelas PostgreSQL afetadas:**
  - **Nenhuma tabela nova e nenhuma coluna nova.** `usuario.pode_auditar` já existe.
  - `log_seguranca` — sem colunas novas; **novo valor** no enum `TipoEventoLog`:
    `acesso_auditoria` (`ALTER TYPE ... ADD VALUE`, não retroativo). A rejeição usa o
    `acesso_negado` já existente.
  - Leitura sobre `processo` / `tramitacao` / `documento` — sem alteração de schema.
- **Migrations Alembic:** uma migration apenas para o novo valor de enum
  (`acesso_auditoria`). Sem alteração estrutural de tabela.
- **API (FastAPI):**
  - `routers/processos.py` — `_exigir_acesso_ao_processo` passa a liberar acesso quando
    `usuario.pode_auditar`, registrando `acesso_auditoria`; a rejeição a sigiloso sem
    permissão usa a mensagem específica do PRD.
  - Novo `routers/auditoria.py` (ou rota em módulo dedicado) — `GET` de relatório
    consolidado, Auditor-only (gate por `pode_auditar`), com filtros período/unidade/tipo.
  - `services/dashboard.py` — funções de agregação (`tempo_medio_tramitacao_dias`,
    contagem de processos) reutilizadas/estendidas para escopo global sem unidades geridas.
  - Novos schemas Pydantic para o relatório e seus filtros.
- **Contrato:** muda schema/rotas do FastAPI → **regenerar** `packages/api-types`.
- **Frontend (Next.js):** nova rota autenticada de relatório de auditoria (filtros +
  relatório em tela + estado vazio), gated por `pode_auditar`; a leitura de processo
  existente torna-se acessível ao Auditor.
- **Segredos/buckets:** nenhum novo segredo no Secret Manager, nenhum novo bucket.
- **Endpoints públicos:** nenhum — todas as rotas deste change exigem autenticação e
  permissão de auditoria; não há canal público, logo sem rate limiting novo.
- **LGPD:** o Auditor **enxerga** dados pessoais de interessados (CPF/CNPJ, nome) inerentes
  ao processo — é o propósito legítimo da auditoria/fiscalização, com base legal distinta
  da consulta pública (que os oculta). Este change **não coleta** novos dados pessoais nem
  cria retenção nova: apenas concede leitura a um perfil autorizado e registra o acesso em
  `log_seguranca` (trilha de segurança, retenção conforme política de log já vigente). A
  anonimização de dados de titular é responsabilidade do Épico 10, fora deste escopo.
