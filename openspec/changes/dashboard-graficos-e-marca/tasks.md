## 1. Backend — agregações de distribuição (services)

- [ ] 1.1 Em `apps/api/app/services/dashboard.py`, adicionar `distribuicao_por_unidade(db, unidades)` — `GROUP BY unidade_atual_id` sobre `_query_ativos`, retornando `[(nome_unidade, quantidade)]` ordenado por quantidade desc
- [ ] 1.2 Adicionar `distribuicao_por_tipo(db, unidades)` — `GROUP BY tipo_processo_id`, resolvendo `TipoProcesso.nome`, ordenado por quantidade desc
- [ ] 1.3 Adicionar `distribuicao_por_usuario(db, unidades)` — `GROUP BY criado_por_id`, resolvendo `Usuario.nome` (autor), ordenado por quantidade desc
- [ ] 1.4 Garantir que as três funções reusam a base de ativos (`_query_ativos`) e retornam listas vazias quando `unidades` vazio, sem filtrar sigilosos

## 2. Backend — schema e endpoint

- [ ] 2.1 Em `apps/api/app/schemas/dashboard.py`, criar `DistribuicaoItem { rotulo: str, quantidade: int }` e `DistribuicoesResponse { por_unidade, por_tipo, por_usuario: list[DistribuicaoItem] }`
- [ ] 2.2 Em `apps/api/app/routers/dashboard.py`, adicionar `GET /dashboard/distribuicoes` (perfil Gestor), com `unidade_id` opcional, chamando `resolver_escopo_gestor` e as três agregações
- [ ] 2.3 No endpoint, tratar `EscopoNegado` → HTTP 403 + `log_seguranca` (`acesso_negado`), no mesmo padrão de `GET /dashboard/kpis`

## 3. Backend — testes (pytest, Postgres real)

- [ ] 3.1 Em `apps/api/tests/test_dashboard_service.py`, testar as três agregações: só ativos contam (concluído/arquivado ficam de fora), sigiloso é contado, agrupamento por autor correto, ordenação desc
- [ ] 3.2 Em `apps/api/tests/test_dashboard_endpoints.py`, testar `GET /dashboard/distribuicoes`: caminho feliz do Gestor, filtro `unidade_id`, e estado vazio (listas vazias)
- [ ] 3.3 Teste de **acesso negado** (obrigatório): Gestor pedindo `unidade_id` fora do escopo → 403 + registro `acesso_negado` em `log_seguranca`; e perfil não-Gestor barrado pelo RBAC

## 4. Contrato front-back

- [ ] 4.1 Exportar OpenAPI e rodar `pnpm gen:types`; commitar `packages/api-types` (`openapi.json` + `schema.ts`) atualizados
- [ ] 4.2 Confirmar `pnpm gen:types:check` verde (sem drift de contrato)

## 5. Frontend — gráficos no Dashboard

- [ ] 5.1 Adicionar dependência `recharts` em `apps/web` (`package.json` + lockfile)
- [ ] 5.2 Em `apps/web/lib/api.ts`, adicionar `obterDashboardDistribuicoes(query?)` consumindo `@setes/api-types` (sem `any`)
- [ ] 5.3 Criar componente de gráfico de barras horizontais (recharts `BarChart` + `ResponsiveContainer`) recebendo `DistribuicaoItem[]`, com cores dos tokens de marca
- [ ] 5.4 Em `apps/web/app/dashboard/page.tsx`, fazer a 2ª chamada e renderizar os três gráficos ("Processos por Unidade", "por Tipo", "por Usuário") **abaixo** dos KPIs
- [ ] 5.5 Estado vazio por gráfico: exibir "Nenhum dado disponível para o período" quando a lista vier vazia
- [ ] 5.6 Atualizar/estender `apps/web/app/dashboard/page.test.tsx` (Vitest) cobrindo render dos gráficos e estado vazio

## 6. Frontend — marca institucional (favicon)

- [ ] 6.1 Em `apps/web/components/icons.tsx`, adicionar `IconMarca` com o SVG do favicon (`app/icon.svg`)
- [ ] 6.2 Em `apps/web/components/protected-shell.tsx`, substituir o "S" do chip circular da sidebar por `<IconMarca/>`, mantendo o chip `rounded-full`
- [ ] 6.3 Em `apps/web/app/login/page.tsx`, substituir o "S" do chip circular por `<IconMarca/>`, mantendo o chip `rounded-full`
- [ ] 6.4 Ajustar/adicionar testes de componente afetados (login/protected-shell) se referenciarem o "S"; conferir contraste do ícone nos dois fundos (chip branco no login, chip na sidebar)

## 7. Verificação final

- [ ] 7.1 `cd apps/api && uv run ruff check . && uv run pytest` verdes
- [ ] 7.2 `pnpm --filter @setes/web typecheck && pnpm --filter @setes/web test` verdes
- [ ] 7.3 Rodar `openspec verify --change dashboard-graficos-e-marca` (ou `/opsx:verify`) antes de arquivar
