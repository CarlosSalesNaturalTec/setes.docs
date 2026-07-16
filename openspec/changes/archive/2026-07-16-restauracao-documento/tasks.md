## 1. Schema e modelo (migration antes de endpoint)

- [x] 1.1 Migration `0007_restauracao_documento` (encadeada em `0006`): `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'restaurar_documento'` em bloco/transação própria; `downgrade` no-op documentado (valor de enum não removível no Postgres). Critério: `uv run alembic upgrade head` aplica; enum aceita o novo valor.
- [x] 1.2 Valor `RESTAURAR_DOCUMENTO = "restaurar_documento"` em `TipoEventoTramitacao` (`db/models.py`). Critério: `uv run pytest` importa sem erro; casa com a migration.

## 2. Serviço de restauração

- [x] 2.1 `services/documento.py` — `listar_removidos_em_retencao(db, *, agora)`: seleciona documentos `removido_em IS NOT NULL AND purgar_em > agora`, cross-processo, com join em `processo` (número/assunto) e ordenação por `removido_em`. Critério: teste com um em retenção, um purgável (purgar_em <= agora) e um visível retorna só o em retenção.
- [x] 2.2 `services/documento.py` — expor/reusar `_resolver_nome_exibicao` para a restauração (anti-colisão, D3). Critério: helper reutilizável sem duplicar lógica.
- [x] 2.3 `services/documento.py` — `restaurar(db, *, documento, admin)`: recarrega o documento com o predicado de retenção **dentro da transação** (404 se não restaurável/purgado), re-resolve `nome_exibicao`, limpa `removido_em`/`removido_por_id`/`purgar_em`, insere evento imutável `restaurar_documento` (Admin, unidades nulas, `status_resultante` = status atual). Sem chamada a `Storage` (D4). Critério: teste verifica campos limpos + evento no histórico + 404 em documento purgado/inexistente.

## 3. Endpoints (routers/documentos_removidos.py)

- [x] 3.1 `GET /admin/documentos-removidos`: `require_perfil(ADMINISTRADOR)`, chama `listar_removidos_em_retencao`, retorna lista (nome, processo, data de remoção, responsável). Critério: teste de API lista só os em retenção; 403 para não-Admin.
- [x] 3.2 `POST /admin/documentos-removidos/{documento_id}/restaurar`: `require_perfil(ADMINISTRADOR)`, chama `restaurar`, retorna `DocumentoResponse`; 404 em documento purgado/inexistente. Critério: teste cobre restauração OK, 404 em purgado e 403 para não-Admin.
- [x] 3.3 Montar `documentos_removidos.router` em `main.py` e schemas de resposta (com número/assunto do processo). Critério: `/openapi.json` expõe as rotas.

## 4. Testes obrigatórios de backend (histórico imutável + dado pessoal)

- [x] 4.1 Teste do **evento imutável** `restaurar_documento`: presença no histórico do processo com Admin responsável, unidades nulas, `status_resultante` = status atual; documento volta a `listar()` visível. Critério: assert sobre `tramitacao` e sobre a listagem de anexos.
- [x] 4.2 Teste de **acesso negado**: Servidor/Gestor/Auditor tenta listar ou restaurar → 403. Critério: assert no status para cada perfil não-Admin.
- [x] 4.3 Teste de **re-resolução de nome** na restauração (colisão com anexo visível → sufixo `(n)`, sem sobrescrita). Critério: ambos os documentos visíveis com nomes distintos.
- [x] 4.4 Teste de **restauração em processo despachado/arquivado** (D1 — sem regra de custódia): restauração bem-sucedida independentemente do status; status do processo inalterado. Critério: documento visível de novo, `processo.status` não muda.

## 5. Frontend (área administrativa)

- [x] 5.1 `pnpm gen:types` após estabilizar o OpenAPI; commitar snapshot `packages/api-types`. Critério: `pnpm gen:types:check` passa.
- [x] 5.2 Rota `app/admin/documentos-removidos`: lista (nome, processo, data de remoção, responsável) + estado vazio "Nenhum documento em período de retenção" + rodapé de purga permanente (US 8.7 Cen.2/3). Critério: renderiza lista, vazio e rodapé.
- [x] 5.3 Ação "Restaurar" (com confirmação) que chama o endpoint e atualiza a lista. Critério: item some da lista de removidos após restaurar; erro de purgado exibido.
- [x] 5.4 Link/entrada de navegação para a área, visível apenas ao Administrador. Critério: item de menu Admin-only.
- [x] 5.5 Teste de componente (Vitest/RTL) da área: lista, vazio, rodapé e restauração. Critério: `pnpm --filter @setes/web test` passa.

## 6. Validação final

- [x] 6.1 Rodar `uv run ruff check .`, `uv run pytest`, `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`, `pnpm gen:types:check`. Critério: tudo verde.
- [x] 6.2 `openspec verify --change restauracao-documento` (ou `/opsx:verify`): implementação coerente com specs/design. Critério: sem divergências pendentes.
