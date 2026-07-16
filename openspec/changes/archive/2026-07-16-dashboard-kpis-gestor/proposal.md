## Why

O Gestor precisa de visão tática da eficiência operacional das unidades que
gerencia, mas hoje só dispõe do Kanban consolidado (US 2.8) — que mostra o
estado atual dos processos, não os indicadores agregados de desempenho. Sem
tempo médio de tramitação, contagem de processos parados e produtividade por
unidade, não há como identificar gargalos nem priorizar intervenções. Este
change entrega o Épico 6 (US 6.1), fechando a lacuna de métricas do MVP. Toda
a base de dados necessária já existe (histórico imutável de tramitação, datas
de criação/conclusão e prazo do processo), então é predominantemente uma
camada de leitura agregada.

## What Changes

- Novo endpoint de **KPIs do dashboard** (`GET /dashboard/kpis`), restrito ao
  perfil **Gestor**, escopado às unidades que ele gerencia (via `unidade_gestor`),
  com filtro opcional por uma unidade gerida. Retorna: total de processos
  ativos (Aberto + Em Tramitação), tempo médio de tramitação (dias corridos,
  criação→conclusão, apenas concluídos nos últimos 12 meses), quantidade de
  processos parados (sem movimentação há mais que o parâmetro configurável),
  produtividade por unidade (processos concluídos no mês corrente) e lista de
  processos com prazo vencido ou próximo do vencimento.
- Novos endpoints de **drill-down** para os KPIs clicáveis: lista de processos
  **ativos** e lista de processos **parados** (com `dias_parados` por item).
  "Tempo médio" e "produtividade" são apenas informativos — sem drill-down.
- Novo **parâmetro operacional configurável em runtime** `dias_para_processo_parado`
  (padrão: 7 dias corridos), gerido pelo Administrador, seguindo o precedente
  de "fatia mínima da US 8.5" já usado pelo prazo de arquivamento. Define o
  limiar do KPI "Processos parados" (PRD US 8.5, linha 703; afeta US 6.1).
- Nova tela **Dashboard** no `apps/web` para o Gestor: cards de KPI, filtro por
  unidade, estado vazio ("Nenhum dado disponível para o período") e drill-down
  navegando para listagem detalhada.
- Cenário de **acesso negado** explícito (não-Gestor, ou Gestor consultando
  unidade que não gerencia) com registro em `log_seguranca`.

## Capabilities

### New Capabilities
- `dashboard-kpis`: Dashboard de indicadores operacionais do Gestor — cálculo
  e exposição dos KPIs (ativos, tempo médio de tramitação, parados,
  produtividade por unidade, processos com prazo em risco), escopo de
  visibilidade por unidade gerida com acesso negado, drill-down de ativos e
  parados, estado vazio, e o parâmetro operacional `dias_para_processo_parado`
  (limiar de "processo parado", configurável pelo Administrador).

### Modified Capabilities
<!-- Nenhuma. O novo parâmetro dias_para_processo_parado segue o padrão de
     "cada change é dono da sua fatia da US 8.5" (precedente: prazo de
     arquivamento na capability arquivamento-automatico), então pertence à
     nova capability dashboard-kpis, não altera requisitos de spec existente. -->

## Impact

- **Depende de** (changes arquivados): `processos-e-workflow` (tabelas
  `processo` e `tramitacao`, máquina de estados, número do processo) e
  `notificacoes-e-alertas` (parâmetro `dias_antecedencia_alerta_prazo` e a
  noção de prazo em risco). Reaproveita `identidade-e-estrutura-organizacional`
  (perfis, `unidade_gestor`, `require_perfil`/escopo por unidade).
- **Tabelas PostgreSQL**:
  - *Afetada*: `sistema_config` (singleton id=1) — nova coluna
    `dias_para_processo_parado INTEGER NOT NULL DEFAULT 7`. Migration Alembic.
  - *Somente leitura (agregação)*: `processo` (status, `criado_em`,
    `concluido_em`, `prazo_em`, `unidade_atual_id`), `tramitacao` (última
    movimentação por processo via `MAX(criado_em)`), `unidade`, `unidade_gestor`,
    `tipo_processo`. Sem tabelas novas.
- **API**: novos schemas Pydantic (KPIs e itens de drill-down), novo router
  `dashboard`, novo service de agregação. Contrato OpenAPI muda → `pnpm gen:types`
  obrigatório (`packages/api-types`).
- **Frontend**: nova rota `apps/web/app/dashboard/`, protegida (Gestor);
  extensão da tela de configurações do Admin para o novo parâmetro.
- **Segredos/buckets**: nenhum novo segredo no Secret Manager, nenhum bucket
  no Cloud Storage.
- **LGPD**: o dashboard é superfície **autenticada e escopada por unidade** —
  não é consulta pública. As listagens (ativos, parados, prazo em risco) exibem
  número, assunto, unidade atual e prazos; não introduzem exposição de dados
  pessoais de interessado (CPF/CNPJ/nome) além do que o Gestor já acessa nos
  processos da sua unidade. Nenhuma nova coleta, retenção ou anonimização.
