# Tasks — dashboard-kpis-gestor (Épico 6, US 6.1)

Ordenadas por dependência: migration/schema → parâmetro de config → service de
agregação → endpoints → contrato → frontend → E2E. Cada tarefa é atômica (≤ 2h)
com critério de aceite explícito.

## 1. Migration e modelo (schema antes do endpoint)

- [x] 1.1 Adicionar coluna `dias_para_processo_parado` ao model `SistemaConfig`
  (`app/db/models.py`): `Mapped[int]`, `nullable=False`, `default=7`.
  **Aceite**: model importa sem erro; `SistemaConfig` expõe o atributo.
- [x] 1.2 Criar migration Alembic `0010_dias_para_processo_parado`: `add_column`
  em `sistema_config` com `server_default="7"` e `nullable=False`; `downgrade`
  faz `drop_column`. **Aceite**: `uv run alembic upgrade head` aplica sem erro
  em Postgres limpo e a linha singleton id=1 passa a ter valor 7; `downgrade -1`
  reverte.

## 2. Parâmetro configurável pelo Administrador (fatia da US 8.5)

- [x] 2.1 Estender `SistemaConfigResponse` e `AtualizarSistemaConfigRequest`
  (`app/schemas/sistema_config.py`) com `dias_para_processo_parado`
  (int opcional no request). **Aceite**: schema serializa o novo campo.
- [x] 2.2 Estender o router `sistema_config` (PUT) para persistir o novo
  parâmetro, aplicando a mesma validação inteiro-positivo dos demais (rejeita
  `< 1` com "O valor deve ser um número inteiro positivo"), Admin-only.
  **Aceite**: PUT com valor válido persiste; valor `<= 0` retorna erro de
  validação sem salvar.
- [x] 2.3 Teste pytest do parâmetro: Admin configura valor válido (persiste);
  valor inválido é rejeitado; não-Admin recebe rejeição e gera linha em
  `log_seguranca` (`tipo_evento=acesso_negado`). **Aceite**: 3 cenários da spec
  ("Parâmetro configurável") passam.

## 3. Service de agregação (fonte única das regras)

- [x] 3.1 Criar `app/services/dashboard.py` com helper de escopo: resolve as
  unidades geridas pelo Gestor (via `unidade_gestor`) e, dado `unidade_id`
  opcional, valida que pertence ao escopo (senão sinaliza acesso negado).
  **Aceite**: função retorna o conjunto de unidades; unidade fora do escopo é
  reportada como negada.
- [x] 3.2 Implementar cálculo dos KPIs no service: total de ativos; tempo médio
  de tramitação (dias corridos criação→conclusão, concluídos nos últimos 12
  meses); parados (ativos com última movimentação `MAX(tramitacao.criado_em)`
  além de `dias_para_processo_parado`, com `dias_parados`); produtividade por
  unidade (concluídos no mês corrente); lista de prazo em risco (vencido ou
  dentro de `dias_antecedencia_alerta_prazo`). **Aceite**: cada KPI computado só
  sobre o escopo; sem dados retorna zero/`null`.
- [x] 3.3 Teste pytest do service com dados de fixture cobrindo: escopo por
  unidade gerida (processos de unidade não gerida excluídos), tempo médio só de
  concluídos ≤ 12 meses, limiar de "parado" lido do config, borda de virada de
  mês na produtividade, e estado vazio. **Aceite**: cenários "Exibição com
  indicadores", "computado apenas sobre unidades geridas" e "Estado vazio"
  passam.

## 4. Endpoints do dashboard

- [x] 4.1 Criar schemas Pydantic de resposta: payload de KPIs e itens de
  drill-down (número, assunto, unidade atual, dias restantes / dias parados).
  **Aceite**: schemas serializam os campos exigidos pela spec.
- [x] 4.2 Criar router `app/routers/dashboard.py` com `GET /dashboard/kpis`
  (`unidade_id` opcional), sob `require_perfil(GESTOR)`; montar em `main.py`.
  **Aceite**: Gestor recebe 200 com KPIs do seu escopo.
- [x] 4.3 Adicionar drill-downs `GET /dashboard/processos-ativos` e
  `GET /dashboard/processos-parados` (mesmo escopo e filtro). Sem endpoint de
  drill-down para tempo médio/produtividade. **Aceite**: listas refletem o mesmo
  predicado dos KPIs correspondentes; contagem do KPI == tamanho da lista.
- [x] 4.4 Teste pytest de autorização: não-Gestor recebe 403 + `log_seguranca`;
  Gestor filtrando unidade não gerida recebe 403 + `log_seguranca`. **Aceite**:
  os dois cenários "Acesso negado" da spec passam.
- [x] 4.5 Regenerar contrato: `pnpm gen:types`; garantir `pnpm gen:types:check`
  verde. **Aceite**: snapshot de `packages/api-types` atualizado e commitado.

## 5. Frontend — tela Dashboard (Gestor)

- [x] 5.1 Criar rota `apps/web/app/dashboard/` protegida (perfil Gestor via
  `protected-shell`/`auth-provider`), consumindo `/dashboard/kpis` pelo cliente
  tipado `lib/api.ts`. **Aceite**: página carrega os cards para um Gestor
  autenticado; usuário sem perfil não acessa a rota.
- [x] 5.2 Renderizar os cards de KPI, o filtro por unidade gerida (recarrega com
  `unidade_id`) e o estado vazio ("Nenhum dado disponível para o período") por
  seção sem dados. **Aceite**: cenários Cen.2 e Cen.3 da US 6.1 refletidos na UI.
- [x] 5.3 Implementar drill-down clicável em "Processos Ativos" e "Processos
  Parados" navegando para listagem detalhada; "Tempo Médio" e "Produtividade"
  não são clicáveis. **Aceite**: Cen.4, Cen.5 e Cen.6 refletidos.
- [x] 5.4 Teste Vitest/RTL dos componentes: renderização de cards, estado vazio,
  e ausência de drill-down nos KPIs informativos. **Aceite**: testes passam.

## 6. Teste E2E (fluxo de leitura sensível a perfil/unidade)

- [x] 6.1 Playwright: Gestor faz login, acessa o Dashboard, vê os KPIs das suas
  unidades, aplica filtro por unidade e aciona o drill-down de "Processos
  Parados", chegando à listagem detalhada. **Aceite**: o fluxo completo passa
  contra api+web + Postgres local (seed mínimo de processos/tramitações).
- [x] 6.2 Playwright (caminho negado): usuário sem perfil de Gestor não acessa a
  rota `/dashboard`. **Aceite**: acesso é bloqueado/redirecionado.

## 7. Validação final

- [x] 7.1 Rodar `uv run pytest`, `uv run ruff check .`, `pnpm --filter @setes/web
  typecheck`, `pnpm --filter @setes/web test`, `pnpm gen:types:check` e o E2E.
  **Aceite**: todas as suítes verdes localmente antes do PR.
