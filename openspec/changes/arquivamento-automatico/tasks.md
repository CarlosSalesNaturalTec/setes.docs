> **Nota sobre testes:** este change **não** exige E2E Playwright — a rotina de arquivamento não tem fluxo de usuário (é um Cloud Run Job disparado por cron). É exercitada por invocação direta do serviço/entrypoint contra Postgres real. As tarefas que tocam histórico de tramitação e transição de estado exigem teste automatizado (regra `tasks` do `config.yaml`), aqui contra banco real.

## 1. Schema — migration Alembic `0004_arquivamento_automatico`

- [x] 1.1 Adicionar `arquivamento_automatico` ao enum `TipoEventoTramitacao` em `models.py` e o campo `arquivar_em` (timestamptz nullable) em `Processo`; `prazo_arquivamento_dias` (int) em `SistemaConfig`; tornar `Tramitacao.responsavel_id` nullable — aceite: `import app.db.models` sem erro
- [x] 1.2 Criar migration `0004_arquivamento_automatico` (`down_revision="0003_processos_workflow"`, revision ≤ 32 chars) com `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'arquivamento_automatico'` — aceite: `alembic upgrade head` roda limpo a partir de `0003` (valor adicionado, não usado na mesma migration)
- [x] 1.3 Na mesma migration: `ADD COLUMN processo.arquivar_em timestamptz NULL` e índice `ix_processo_status_arquivar_em (status, arquivar_em)` — aceite: `\d processo` mostra a coluna e `\di` o índice
- [x] 1.4 `ADD COLUMN sistema_config.prazo_arquivamento_dias int NOT NULL DEFAULT 30` — aceite: `SELECT prazo_arquivamento_dias FROM sistema_config WHERE id=1` retorna 30 logo após a migration (linha singleton já semeada fica válida pelo default)
- [x] 1.5 `ALTER COLUMN tramitacao.responsavel_id DROP NOT NULL` + `ADD CONSTRAINT ck_tramitacao_responsavel CHECK (responsavel_id IS NOT NULL OR tipo_evento = 'arquivamento_automatico')` — aceite: INSERT de evento humano sem responsável é rejeitado pelo CHECK; INSERT de `arquivamento_automatico` com `responsavel_id=NULL` é aceito
- [x] 1.6 Escrever `downgrade()` (drop CHECK → restaura NOT NULL → drop coluna sistema_config → drop índice+coluna processo; documentar que o valor de enum permanece órfão, inócuo) e testar ciclo `alembic downgrade -1` + `upgrade head` em banco sem linhas de arquivamento — aceite: ciclo up/down/up roda sem erro

## 2. Congelamento do prazo na conclusão (US 2.5 Cen.2)

- [x] 2.1 Na ação de conclusão de `services/processo.py` (ramo da última etapa do `despachar`), ler `prazo_arquivamento_dias` de `sistema_config` e gravar `processo.arquivar_em = concluido_em + prazo_dias` (dias corridos) — aceite: um processo concluído passa a ter `arquivar_em` preenchido; processo não concluído mantém `arquivar_em = NULL`
- [x] 2.2 Teste automatizado do congelamento não-retroativo: concluir processo com prazo 30; alterar o prazo global para 15; verificar que `arquivar_em` do processo já concluído **não muda** e reflete os 30 dias originais (US 2.5 Cen.2) — **obrigatório (toca histórico/transição e a regra de não-retroatividade)**

## 3. Prazo de arquivamento configurável (fatia mínima US 8.5)

- [x] 3.1 Schema Pydantic e router `sistema_config`: `GET /sistema-config` (retorna `prazo_arquivamento_dias`) e `PUT /sistema-config` (atualiza), ambos `require_perfil(ADMINISTRADOR)`; montar em `main.py` — aceite: GET retorna 30 por padrão; Servidor/Gestor recebem 403 e a tentativa é gravada em `log_seguranca`
- [x] 3.2 Validação de inteiro positivo no PUT: valor negativo, zero ou não inteiro → 422 "O valor deve ser um número inteiro positivo" (US 8.5 Cen.3) — aceite: `PUT` com 0/-5 rejeitado; com 60 aceito e persistido
- [x] 3.3 Teste automatizado do endpoint: leitura padrão, escrita válida, valor inválido, e acesso negado a não-Administrador com log — **obrigatório (regra de visibilidade por perfil)**

## 4. Serviço de arquivamento (US 2.5)

- [x] 4.1 Implementar `app/services/arquivamento.py` — `arquivar_vencidos(db, *, agora) -> int`: seleciona `status='concluido' AND arquivar_em <= agora`; para cada processo, `validar_transicao(concluido→arquivado)`, seta `status=arquivado`, insere `Tramitacao(tipo_evento=arquivamento_automatico, responsavel_id=NULL, unidades NULL, status_resultante=arquivado)`, commit por processo — aceite: retorna a contagem de processos efetivamente arquivados
- [x] 4.2 Adicionar a transição `concluido → arquivado` a `_TRANSICOES` em `services/processo_estado.py` — aceite: `validar_transicao(CONCLUIDO, ARQUIVADO)` não levanta; nenhuma outra transição nova é introduzida
- [x] 4.3 Teste automatizado de idempotência/retomada contra Postgres real: (a) vencidos são arquivados e geram 1 evento cada; (b) reexecução sobre o mesmo estado arquiva 0 e não duplica evento (Cen.3); (c) vários vencidos durante "indisponibilidade" são capturados numa execução (Cen.4); (d) processo não vencido não é tocado — **obrigatório (toca histórico de tramitação e transição de estado)**
- [x] 4.4 Teste automatizado: o evento de arquivamento é imutável e não altera dados de interessados (só status + evento) — **obrigatório (histórico imutável)**

## 5. Entrypoint real do job diário

- [x] 5.1 Substituir o placeholder de `app/jobs/entrypoint.py`: abrir sessão via `get_session_factory()`, capturar `agora = datetime.now(timezone.utc)`, chamar `arquivar_vencidos(db, agora=agora)`, logar o total e retornar 0; fechar a sessão no `finally` — aceite: `uv run python -m app.jobs.entrypoint` contra banco local arquiva os vencidos e loga a contagem
- [x] 5.2 Preservar `app/jobs/manutencao_diaria.py` e `tests/test_idempotencia.py` como guard de lógica pura (contrato in-memory) — aceite: `test_idempotencia.py` continua verde, sem alteração

## 6. Contrato de tipos e verificação final

- [x] 6.1 Regenerar o contrato front↔back: `pnpm gen:types` e commitar `packages/api-types` (mudança do endpoint `sistema-config`) — aceite: `pnpm gen:types:check` passa
- [x] 6.2 Rodar as suítes locais: `uv run ruff check .` e `uv run pytest` (API, Postgres real) — aceite: todas verdes
- [x] 6.3 Validar o passo de arquivamento fim a fim contra a stack local: criar → despachar até concluir com prazo curto → invocar `entrypoint` com `agora` além de `arquivar_em` → confirmar status `arquivado` no Kanban e evento no histórico — aceite: processo migra para a coluna "Arquivado" e o evento aparece na linha do tempo
