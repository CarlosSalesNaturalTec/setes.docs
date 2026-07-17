## Why

O Épico 10 (Conformidade LGPD e Privacidade) é o único épico não-condicional do MVP ainda
em zero. Todos os demais épicos aplicáveis já foram entregues (1, 2, 3, 5, 6, 7, 8, 9); o
Épico 4 (assinatura ICP-Brasil) segue condicionado a Discovery Técnico e fica fora deste
change. A invariante de domínio do projeto é explícita: "LGPD é requisito, não opcional" —
hoje, no entanto, o sistema coleta dado pessoal de interessado (`processo_interessado`)
sem nenhum canal para o titular exercer seus direitos, nenhuma fila para o Administrador
processar pedidos, e nenhuma anonimização automática de processos arquivados há anos. O
próprio `bootstrap-infraestrutura` já reservou a infraestrutura para isso: o Cloud Run Job
`job-anonimizacao-lgpd` está provisionado com Cloud Scheduler trimestral (spec
`rotinas-agendadas`), mas roda o mesmo entrypoint placeholder do job diário — nenhuma
lógica de negócio foi implementada.

## What Changes

- **US 10.1 — Canal público de solicitação:** novo endpoint público (sem autenticação,
  sob rate limiting), onde qualquer titular (ou representante) informa número do
  processo, nome completo, CPF, e-mail, tipo de solicitação ("Exclusão de dados" ou
  "Anonimização de dados") e anexa documento de identificação (PDF/JPG/PNG). O sistema
  gera um protocolo, confirma na tela e envia e-mail de confirmação. Valida: campos
  obrigatórios, formato do anexo, e existência do número de processo informado.
- **US 10.2 — Fila administrativa de solicitações:** o Administrador vê a lista de
  solicitações (protocolo, data, solicitante, processo, tipo, status:
  Pendente/Em análise/Atendida/Rejeitada) e pode **atender** (dispara anonimização
  irreversível dos dados do interessado indicado no processo e notifica por e-mail) ou
  **rejeitar** (com justificativa obrigatória, notifica por e-mail). A operação de
  anonimização usada aqui é a **mesma rotina de anonimização** que a rotina automática
  (US 10.3) — um único serviço, dois gatilhos (manual vs. agendado).
- **US 10.3 — Anonimização automática trimestral:** o job `job-anonimizacao-lgpd`
  (infraestrutura já provisionada, entrypoint placeholder) ganha lógica de negócio real:
  seleciona processos `Arquivado` cujo prazo legal de anonimização (configurável **por
  tipo de processo**) já expirou desde o arquivamento, e anonimiza os dados pessoais de
  todos os interessados vinculados (nome → "Titular Anonimizado", CPF/CNPJ →
  identificador irreversível), preservando número, datas, unidades, status e histórico de
  tramitação. Segue o contrato de idempotência já estabelecido em `rotinas-agendadas`
  (seleção por estado atual, sem reprocessar processo já anonimizado).
- **Parâmetro novo (US 10.3 Cen.2):** `tipo_processo` ganha o campo configurável "Prazo
  de anonimização LGPD" (anos), editável pelo Administrador, aplicado apenas a processos
  arquivados a partir da alteração (não retroativo — mesmo padrão de `sistema_config`).

## Capabilities

### New Capabilities
- `solicitacao-lgpd`: canal público de solicitação (US 10.1), fila administrativa de
  atendimento/rejeição (US 10.2) e o serviço compartilhado de anonimização irreversível
  de interessado, reutilizado pela rotina automática. Inclui os cenários de "acesso
  negado" para operações administrativas por perfil não-Administrador.
- `anonimizacao-lgpd`: seleção e execução da anonimização automática trimestral de
  processos arquivados vencidos (US 10.3), consumindo o serviço de `solicitacao-lgpd` e
  o job já provisionado por `rotinas-agendadas`.

### Modified Capabilities
- `rotinas-agendadas`: o job `job-anonimizacao-lgpd`, hoje placeholder (mesmo entrypoint
  do job diário), passa a executar a lógica real de `anonimizacao-lgpd` — novo entrypoint
  próprio, mantendo o contrato de idempotência já especificado.
- `tipos-processo-e-roteiros`: adiciona o parâmetro configurável "Prazo de anonimização
  LGPD" (anos) por tipo de processo, com validação de valor inteiro positivo e aplicação
  não retroativa (US 10.3 Cen.2).

## Impact

- **Requer (arquivados):** `processos-e-workflow` (`processo`, `processo_interessado`,
  `StatusProcesso.ARQUIVADO`), `arquivamento-automatico` (processo já chega a
  `Arquivado` com `concluido_em`/`arquivado_em` datados), `tipos-processo-e-roteiros`
  (`tipo_processo`), `consulta-publica` (padrão de lookup público de processo por
  número + rate limiting `slowapi`), `administracao-usuario-auditoria` /
  `restauracao-documento` (padrão de fila administrativa com estados e ações), a
  infraestrutura de `rotinas-agendadas` (Cloud Scheduler + `job-anonimizacao-lgpd` já
  provisionados no bootstrap).
- **Tabelas PostgreSQL:**
  - **Nova** `solicitacao_lgpd`: protocolo (único, gerado), `processo_id` (FK
    `processo.id`), nome/CPF/e-mail do solicitante, tipo de solicitação (enum), status
    (enum: pendente/em_analise/atendida/rejeitada), justificativa de rejeição (nullable),
    chave do documento de identificação anexado, `criado_em`, `atendido_em`/`atendido_por_id`
    (FK `usuario.id`, nullable).
  - `tipo_processo` — **nova coluna** `prazo_anonimizacao_anos INTEGER NOT NULL DEFAULT 5`.
  - `processo_interessado` — **nova coluna** `anonimizado_em TIMESTAMPTZ NULL` (guard de
    idempotência explícito para a rotina automática — string-matching em `nome` seria
    frágil). Quando preenchida, `nome` e `documento` já foram sobrescritos com os
    marcadores irreversíveis ("Titular Anonimizado" / identificador anonimizado).
  - `log_seguranca` — **novos valores** no enum `TipoEventoLog`: `interessado_anonimizado`
    (usado tanto pelo atendimento manual quanto pela rotina automática, com
    `solicitacao_lgpd_id` nulo neste último caso).
- **Segredos/buckets:** **novo bucket** Cloud Storage para o documento de identificação
  anexado ao formulário LGPD (dado sensível de identidade civil — não deve compartilhar
  bucket com anexos de processo, que têm retenção/acesso próprios). Nenhum segredo novo.
- **API (FastAPI):** novo `routers/lgpd.py` — `POST /publico/lgpd/solicitacoes` (público,
  rate-limited), `GET /lgpd/solicitacoes` e `POST /lgpd/solicitacoes/{id}/atender` /
  `.../rejeitar` (Admin-only). Novo `services/lgpd.py` com `anonimizar_interessados(processo)`
  compartilhado entre atendimento manual e job. `tipos_processo.py` (router e schema) passa
  a aceitar `prazo_anonimizacao_anos`.
- **Contrato:** muda schema/rotas do FastAPI → regenerar `packages/api-types`
  (`pnpm gen:types`).
- **Frontend (Next.js):** nova página pública de solicitação LGPD; nova página
  `apps/web/app/admin/lgpd/page.tsx` com a fila administrativa; `admin/tipos-processo`
  ganha o campo de prazo de anonimização.
- **Jobs:** novo `app/jobs/entrypoint_lgpd.py`, e `infra/jobs_scheduler.tf` atualizado
  para apontar `job-anonimizacao-lgpd` a esse entrypoint (troca de `command`, sem mudança
  de schedule/service account/infra já provisionada).
- **LGPD (tratamento explícito):** este change **é** o mecanismo de conformidade LGPD —
  coleta dado pessoal do solicitante (nome, CPF, e-mail, documento de identificação) só
  para validar a titularidade do pedido, com retenção mínima necessária; a anonimização
  aplicada (manual ou automática) é **irreversível por design** (sem coluna ou tabela de
  "valor original"); o documento de identificação do solicitante não é anexado ao
  processo nem exposto na consulta pública.
