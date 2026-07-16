## Context

O Épico 6 (US 6.1) entrega ao Gestor um dashboard de KPIs operacionais das
unidades que gerencia. Diferente do Kanban (visualização de estado atual, US
2.8), o dashboard é uma camada de **leitura agregada** sobre dados que já
existem, sem novas tabelas de negócio:

- `processo` — `status`, `criado_em`, `concluido_em`, `prazo_em`,
  `unidade_atual_id` (change `processos-e-workflow`).
- `tramitacao` — histórico imutável; a última movimentação de um processo é o
  evento com maior `criado_em` (change `processos-e-workflow`).
- `unidade_gestor` — vínculo Gestor↔unidades geridas (change
  `identidade-e-estrutura-organizacional`).
- `sistema_config` — singleton id=1; já expõe `prazo_arquivamento_dias` e
  `dias_antecedencia_alerta_prazo` via router `sistema_config` (GET/PUT,
  Admin-only). Ganha o novo `dias_para_processo_parado`.

Composição de autorização já disponível em `app/security/autorizacao.py`:
`get_current_user → require_perfil(GESTOR) → tem_acesso_a_unidade` +
`registrar_acesso_negado` (grava `log_seguranca`). O padrão de config Admin-only
já está em `app/routers/sistema_config.py`. Não há tela de "Configurações do
Sistema" no `apps/web` ainda — os parâmetros existentes são editáveis só via
API; este change mantém esse padrão para o novo parâmetro.

## Goals / Non-Goals

**Goals:**
- Endpoint único de KPIs (`GET /dashboard/kpis`) escopado por unidades geridas,
  com filtro opcional por uma unidade, retornando os 5 indicadores da US 6.1 +
  a lista de prazos em risco, e sinalização de estado vazio.
- Dois endpoints de drill-down (ativos, parados) que reutilizam o mesmo escopo.
- Novo parâmetro operacional `dias_para_processo_parado` (default 7),
  configurável em runtime pelo Admin, lido pelo cálculo de "parados".
- Tela Dashboard no `apps/web` (Gestor), com cards, filtro de unidade, estado
  vazio e drill-down navegando para listagem detalhada.
- Regenerar o contrato (`pnpm gen:types`).

**Non-Goals:**
- Tela web de "Configurações do Sistema" completa (US 8.5 integral) — segue em
  change futuro; aqui só se adiciona o campo ao endpoint existente.
- Persistência/materialização de métricas (views materializadas, cache): o MVP
  calcula on-the-fly. Otimização fica para quando o volume justificar.
- Dashboards de Administrador/Auditor consolidados de todas as unidades — o
  escopo da US 6.1 é o Gestor sobre suas unidades geridas.
- Exportação de relatórios (Épico 9).

## Decisions

### D1 — `dias_para_processo_parado` como coluna em `sistema_config` (não constante)
**Migration antes do endpoint.** A invariante "parâmetros operacionais são
configuráveis em runtime, não hardcoded" exige coluna, não constante. Segue o
precedente `prazo_arquivamento_dias`.

- **Migration Alembic `0010_dias_para_processo_parado`**: `add_column` em
  `sistema_config` → `dias_para_processo_parado INTEGER NOT NULL DEFAULT 7`.
  O default no servidor cobre a linha singleton já existente (id=1) sem
  backfill manual. `downgrade` = `drop_column`.
- Model `SistemaConfig` ganha o `Mapped[int]` correspondente; o router
  `sistema_config` (GET/PUT) e os schemas `SistemaConfigResponse` /
  `AtualizarSistemaConfigRequest` ganham o campo, com a **mesma** validação
  inteiro-positivo já aplicada aos outros parâmetros (rejeita `< 1` com "O valor
  deve ser um número inteiro positivo").

*Alternativa descartada:* constante em código — viola a invariante e impede
ajuste sem deploy.

### D2 — Um endpoint de KPIs + dois de drill-down, todos sob o mesmo escopo
`GET /dashboard/kpis?unidade_id=<opcional>` retorna o payload agregado.
`GET /dashboard/processos-ativos` e `GET /dashboard/processos-parados` retornam
as listas de drill-down (número, assunto, unidade atual, e — respectivamente —
dias restantes / dias parados). Os três compartilham o **mesmo helper de
escopo**: resolve o conjunto de unidades geridas do Gestor autenticado; se
`unidade_id` for informado, valida que pertence a esse conjunto (senão →
`registrar_acesso_negado` + 403). "Tempo médio" e "produtividade" **não** têm
endpoint de drill-down (US 6.1 Cen.6).

*Alternativa descartada:* embutir as listas completas de ativos/parados dentro
do payload de KPIs — infla a resposta e acopla contagem a listagem; o drill-down
sob demanda espelha o comportamento clicável da UI.

### D3 — Regras de cálculo (fonte única no service de agregação)
Um `services/dashboard.py` concentra as queries, para o cálculo ser testável
isoladamente e consistente entre KPI e drill-down:

- **Ativos**: `status IN ('aberto','em_tramitacao')` nas unidades do escopo.
- **Tempo médio de tramitação**: média de `EXTRACT(day FROM concluido_em -
  criado_em)` sobre processos com `concluido_em >= now() - 12 meses`. Dias
  **corridos**. Sem concluídos no período → `null`/0 + estado vazio (US 6.1
  Cen.2).
- **Parados**: entre os ativos, aqueles cujo `MAX(tramitacao.criado_em)` (última
  movimentação) é anterior a `now() - dias_para_processo_parado` dias corridos.
  `dias_parados` = dias corridos desde essa última movimentação. Processo sem
  nenhuma tramitação usa `processo.criado_em` como referência.
- **Produtividade por unidade**: contagem de `concluido_em` dentro do mês
  corrente, `GROUP BY unidade`.
- **Prazo em risco**: ativos com `prazo_em < hoje` (vencido) ou `prazo_em <=
  hoje + dias_antecedencia_alerta_prazo` (a vencer) — reaproveita o parâmetro do
  change de notificações.

### D4 — Estado vazio como sinalização estrutural, não string do back
O back retorna zeros/`null` e contagens vazias; o front decide exibir "Nenhum
dado disponível para o período". Mantém o texto de UI no front e o back livre de
copy. (US 6.1 Cen.2.)

### Diagrama de sequência — carregamento do dashboard com drill-down

```
Gestor        apps/web (Dashboard)      FastAPI /dashboard         Postgres
  |                  |                        |                        |
  |-- abre página -->|                        |                        |
  |                  |-- GET /kpis (Bearer)-->|                        |
  |                  |                        |-- require_perfil(GESTOR)|
  |                  |                        |-- resolve unidades geridas ->|
  |                  |                        |-- agrega KPIs ---------->|
  |                  |                        |<-- linhas agregadas -----|
  |                  |<-- 200 KPIs -----------|                        |
  |<-- cards + filtro|                        |                        |
  |                  |                        |                        |
  |-- clica "Parados 7" ->                    |                        |
  |                  |-- GET /processos-parados?unidade_id -->         |
  |                  |                        |-- valida unidade ∈ geridas
  |                  |                        |     (senão: log_seguranca+403)
  |                  |                        |-- lista parados -------->|
  |                  |<-- 200 lista ----------|                        |
  |<-- listagem parados                       |                        |
```

## Risks / Trade-offs

- **[Custo das agregações on-the-fly cresce com o volume de processos]** →
  Mitigação: queries indexadas por `unidade_atual_id`/`status`/`concluido_em`
  (índices já existentes do change de processos onde aplicável); materialização
  fica como Non-Goal explícito até haver evidência de gargalo.
- **["Última movimentação" via `MAX(tramitacao.criado_em)` pode ser custoso]** →
  Mitigação: subquery agrupada por `processo_id` restrita ao conjunto de ativos
  do escopo (não a tabela inteira); avaliar índice `(processo_id, criado_em)` em
  `tramitacao` na task de implementação se o plano de execução justificar.
- **[Fuso horário no corte "mês corrente" e "12 meses"]** → Mitigação: usar o
  fuso de operação do órgão (America/Bahia) de forma consistente com o restante
  do sistema; cobrir a borda de virada de mês em teste.
- **[Divergência entre contagem do KPI e tamanho da lista de drill-down]** →
  Mitigação: KPI e drill-down derivam do mesmo predicado no `services/dashboard.py`
  — nunca duplicar a regra no router.

## Migration Plan

1. Migration `0010_dias_para_processo_parado` (`add_column` com default 7 no
   servidor) — aplicada pelo Cloud Run Job de migrations **antes** da troca do
   serviço, conforme pipeline de deploy. Rollback: `downgrade` (`drop_column`);
   o dashboard tolera ausência do parâmetro apenas se revertido junto com o
   código (deploy atômico).
2. Model + schemas + router `sistema_config` estendidos com o novo parâmetro.
3. `services/dashboard.py` + router `dashboard` + schemas; montar router em
   `main.py`.
4. `pnpm gen:types` — snapshot do contrato atualizado e commitado.
5. Tela `apps/web/app/dashboard/` + guarda de rota (Gestor).
6. Testes: pytest (agregações, escopo, acesso negado, config inválida) + E2E
   Playwright do fluxo de dashboard/drill-down (fluxo de leitura sensível a
   perfil/unidade).

## Open Questions

- **Admin/Auditor também acessam o dashboard?** A US 6.1 fala do Gestor. Decisão
  atual: restringir a Gestor (mais simples e aderente à US). Se o órgão pedir
  visão de Admin, entra como extensão futura — não bloqueia este change.
- **"Produtividade por unidade" e "processos concluídos no mês": mês-calendário
  corrente ou últimos 30 dias?** A US 6.1 diz "no mês" — assumindo
  mês-calendário corrente. Confirmar com o cliente antes do fechamento da task.
