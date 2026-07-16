## 1. Schema e migrations (antes dos endpoints)

- [ ] 1.1 Adicionar model `Notificacao` em `db/models.py` (PK UUID app; FKs `usuario_id`,
  `processo_id`, `unidade_id`; `tipo` enum `novo_processo|concluido|alerta_prazo`;
  `prazo_referencia` DATE nullable; snapshot mínimo de render; `lida_em` nullable;
  `criado_em`) e o enum `TipoNotificacao`.
- [ ] 1.2 Migration Alembic `create_notificacao` com índices `(usuario_id, lida_em)`,
  `(processo_id, usuario_id, tipo, prazo_referencia)` e `(lida_em)`. Aplicar `upgrade head`
  contra Postgres local e conferir o `downgrade`.
- [ ] 1.3 Adicionar coluna `dias_antecedencia_alerta_prazo INT NOT NULL DEFAULT 2` ao model
  `SistemaConfig` e migration `add_dias_antecedencia_alerta_prazo` com backfill do singleton
  id=1.

## 2. Serviço de geração de notificações + e-mail (US 5.1, 5.3)

- [ ] 2.1 `services/notificacao.py`: função para resolver servidores de uma unidade e gerar
  N notificações (INSERT) para um dado tipo/evento, recebendo a `Session` da transação em
  curso.
- [ ] 2.2 Ligar geração de `novo_processo` dentro de `services/processo.py::despachar` (ramo
  de despacho para próxima etapa), na mesma transação da `Tramitacao(DESPACHO)`.
- [ ] 2.3 Ligar geração de `concluido` no ramo de conclusão de `despachar`, na mesma
  transação da `Tramitacao(CONCLUSAO)`.
- [ ] 2.4 Após o commit do despacho/conclusão, enfileirar e-mails (`enqueue_email` com
  `event_id` determinístico) de "Novo processo recebido" aos servidores do destino, em modo
  best-effort (falha só loga — não propaga).
- [ ] 2.5 Teste pytest (Postgres real) do serviço: despacho gera N notificações não lidas na
  unidade destino e evento imutável correspondente; conclusão gera na unidade de conclusão.
  (Obrigatório — toca histórico de tramitação.)

## 3. Endpoints de notificação (US 5.1 Cen.2/Cen.3)

- [ ] 3.1 `routers/notificacoes.py`: `GET /notificacoes` (próprias, aplicando retenção de 30d
  para lidas e sempre exibindo não lidas) e `GET /notificacoes/contador` (não lidas).
- [ ] 3.2 `POST /notificacoes/{id}/ler` e `POST /notificacoes/marcar-todas-lidas`, escopando
  por `usuario_id = current_user`. Montar o router em `main.py`.
- [ ] 3.3 Schemas Pydantic de notificação em `schemas/`.
- [ ] 3.4 Teste pytest: contador não zera ao listar; marcar uma decrementa; marcar todas
  zera; **acesso negado** ao ler/marcar notificação de outro usuário (registro no padrão de
  autorização).

## 4. Parâmetro configurável de antecedência (US 8.5)

- [ ] 4.1 Expor o parâmetro `dias_antecedencia_alerta_prazo` no fluxo de configuração
  (`routers/sistema_config.py` + schema), edição protegida por `require_perfil(ADMINISTRADOR)`.
- [ ] 4.2 Teste pytest: Admin altera o valor e ele persiste; **acesso negado** para
  Servidor/Gestor; valor padrão 2 quando nunca alterado.

## 5. Rotinas diárias no job de manutenção (US 5.2 Cen.2, US 5.4, US 5.1 Cen.4/4b)

- [ ] 5.1 `services/prazo.py::verificar_prazos(session, agora)`: seleciona processos ativos
  com `prazo_em <= hoje + dias_antecedencia`; para cada (processo, servidor da unidade atual)
  sem `alerta_prazo` para o `prazo_referencia` vigente, gera notificação interna e enfileira
  e-mail "Prazo próximo" (dedup por `event_id`).
- [ ] 5.2 `services/notificacao.py::expurgar_notificacoes_lidas(session, agora)`: DELETE de
  `lida_em IS NOT NULL AND lida_em < agora - 30d`; preserva não lidas por construção do WHERE.
- [ ] 5.3 Acrescentar as duas chamadas em `jobs/entrypoint.py::run()` após arquivamento e
  purga de documentos, com logging por passo.
- [ ] 5.4 Teste pytest de idempotência: reexecutar `verificar_prazos` no mesmo estado não
  duplica alerta/e-mail; retomada após "dias parados" cobre a janela; expurgo remove só
  lidas +30d e nunca remove não lidas. (Obrigatório — rotina automática + histórico.)

## 6. Contrato de tipos e frontend (sino)

- [ ] 6.1 `pnpm gen:types` para regenerar `packages/api-types` (openapi.json + schema.ts) e
  conferir `pnpm gen:types:check`.
- [ ] 6.2 Cliente tipado em `apps/web/lib/api.ts` para listar/contar/marcar notificações.
- [ ] 6.3 Componente de sino no shell autenticado (`components/`): contador + painel com
  número/assunto/origem, indicador de não lida, ação "marcar como lida" e "marcar todas";
  revalidar ao focar a aba e ao abrir o painel.
- [ ] 6.4 Teste Vitest + RTL do componente de sino (contador, estado lido/não-lido, marcar
  todas).

## 7. E2E (despacho é alterado — obrigatório)

- [ ] 7.1 Teste E2E Playwright: servidor da unidade A despacha um processo para a unidade B;
  um servidor da unidade B vê o contador do sino incrementar e a notificação com número,
  assunto e unidade de origem; ao clicar, o contador decrementa e persiste após reload.

## 8. Fechamento

- [ ] 8.1 Rodar `uv run ruff check .`, `uv run pytest`, `pnpm --filter @setes/web typecheck`,
  `pnpm --filter @setes/web test` e `pnpm gen:types:check`; corrigir pendências.
- [ ] 8.2 `openspec validate --changes notificacoes-e-alertas` e revisar o diff antes de abrir PR.
