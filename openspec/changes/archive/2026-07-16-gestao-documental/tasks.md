## 1. Schema e modelo (migration antes de endpoint)

- [x] 1.1 Migration `0006_gestao_documental` (encadeada em `0005`): `CREATE TABLE documento` com todas as colunas (`id`, `processo_id` FK, `nome_original`, `nome_exibicao`, `objeto_chave UNIQUE`, `tipo_conteudo`, `tamanho_bytes CHECK (>0)`, `hash_sha256`, `anexado_por_id` FK, `anexado_em`, `removido_em NULL`, `removido_por_id NULL` FK, `purgar_em NULL`). Critério: `uv run alembic upgrade head` cria a tabela; `downgrade` a remove.
- [x] 1.2 Na mesma migration, índices parciais `ix_documento_processo_visivel` (WHERE `removido_em IS NULL`) e `ix_documento_purga` (WHERE `removido_em IS NOT NULL`). Critério: índices presentes no schema pós-upgrade.
- [x] 1.3 Na migration, `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'remover_documento'` em bloco/transação própria. Critério: enum aceita o novo valor; documentar no `downgrade` que o valor não é removido (limitação Postgres).
- [x] 1.4 Modelo SQLAlchemy `Documento` em `db/models.py` (Mapped[...] espelhando a tabela) e valor `REMOVER_DOCUMENTO = "remover_documento"` em `TipoEventoTramitacao`. Critério: `uv run pytest` importa sem erro; modelo casa com a migration.

## 2. Adaptador de armazenamento (storage)

- [x] 2.1 Adicionar dependência `google-cloud-storage` ao `apps/api/pyproject.toml` e `uv sync`. Critério: import disponível; lockfile atualizado.
- [x] 2.2 `config.py`: envs `DOCUMENTOS_BUCKET` e flag de storage local (dev/E2E). Critério: `Settings` expõe os campos com defaults seguros para dev.
- [x] 2.3 `services/storage.py`: interface (`salvar`, `abrir`, `remover`, opcional `url_assinada`) com backend **local (filesystem)** para pytest/dev. Critério: teste unitário salva/abre/remove num diretório temporário.
- [x] 2.4 `services/storage.py`: backend **GCS** (ADC via SA do Cloud Run, sem chave JSON), selecionado por config. Critério: seleção de backend coberta por teste; GCS não é exercido em pytest (só local).

## 3. Serviço de documentos

- [x] 3.1 `services/documento.py` — `anexar(...)`: validação de MIME (extensão + sniffing do content-type real) e tamanho (1 byte..20 MB), rejeitando formato/tamanho/vazio com as mensagens do PRD (US 3.1 Cen.2/2b). Critério: teste cobre cada rejeição; nada é gravado em falha.
- [x] 3.2 `services/documento.py` — cálculo de `hash_sha256` do conteúdo e resolução de `nome_exibicao` com sufixo `(n)` por processo (desduplicação, US 3.1 Cen.5). Critério: teste anexa dois `parecer.pdf` e obtém `parecer.pdf` + `parecer (1).pdf`, ambos persistidos.
- [x] 3.3 `services/documento.py` — `anexar` grava objeto no storage (chave `{processo_id}/{uuid}`) e insere linha `documento`. Critério: teste de integração verifica objeto no backend local + linha no banco.
- [x] 3.4 `services/documento.py` — `listar(processo)` retorna só visíveis (`removido_em IS NULL`). Critério: teste com um removido e um visível retorna apenas o visível.
- [x] 3.5 `services/documento.py` — helper de custódia `pode_remover(processo)` conforme **D1** (permite em `Aberto`; permite em `Em Tramitação` só se entrou por devolução e não houve despacho desde então; bloqueia após despacho/conclusão/arquivamento). Critério: teste unitário cobre os quatro cenários do PRD (Cen.3/4/4b/4c).
- [x] 3.6 `services/documento.py` — `remover(processo, documento, usuario)`: aplica soft-delete (`removido_em`, `removido_por_id`, `purgar_em = removido_em + 30d`), insere evento imutável `remover_documento` em `tramitacao`, respeitando `pode_remover`. Critério: teste verifica soft-delete + evento no histórico + bloqueio quando `pode_remover` é falso.

## 4. Endpoints (routers/documentos.py)

- [x] 4.1 `POST /processos/{id}/documentos` (multipart): reusa `_exigir_acesso_ao_processo`, chama `anexar`, retorna `DocumentoResponse` 201. Critério: teste de API anexa com sucesso e retorna metadados.
- [x] 4.2 `GET /processos/{id}/documentos`: lista visíveis autorizados por unidade. Critério: teste de API lista só visíveis.
- [x] 4.3 `GET /processos/{id}/documentos/{doc}/conteudo`: streaming autenticado (`inline` para PDF/imagem, `attachment` para DOC/DOCX, com aviso), reusa `_exigir_acesso_ao_processo`. Critério: teste verifica `Content-Disposition` correto por tipo (US 3.2 Cen.1/3).
- [x] 4.4 `GET /processos/{id}/documentos/{doc}/download`: streaming `attachment` mantendo nome original (US 3.2 Cen.2). Critério: teste verifica nome/formato no header.
- [x] 4.5 `DELETE /processos/{id}/documentos/{doc}`: chama `remover`; mapeia bloqueio de custódia para 409/422 com a mensagem do PRD. Critério: teste cobre remoção OK e bloqueio pós-despacho.
- [x] 4.6 Montar `documentos.router` em `main.py` e schemas `DocumentoResponse` em `schemas/`. Critério: `/openapi.json` expõe as rotas.

## 5. Testes obrigatórios de backend (histórico imutável + dado pessoal)

- [x] 5.1 Teste de **acesso negado**: Servidor de outra unidade tenta anexar/baixar/remover → 403 e linha em `log_seguranca` (invariante de visibilidade). Critério: assert no status e no log.
- [x] 5.2 Teste do **evento imutável** `remover_documento`: presença no histórico com responsável, unidades nulas, `status_resultante` = status atual, e ausência de UPDATE/DELETE de eventos. Critério: assert sobre `tramitacao`.
- [x] 5.3 Teste de **MIME falsificado** (extensão `.pdf`, conteúdo `.exe`): upload rejeitado. Critério: 4xx e nada persistido.

## 6. Purga física (passo do job diário)

- [x] 6.1 `services/documento.py` — `purgar_documentos_vencidos(session, agora)`: seleciona `removido_em IS NOT NULL AND purgar_em <= agora`, remove objeto do storage **antes** de deletar a linha, commit por documento (D7). Critério: teste com um vencido e um dentro do prazo purga só o vencido.
- [x] 6.2 Teste de **idempotência/retomada** da purga: segunda execução imediata é no-op; objeto ausente no `remover` não quebra. Critério: reexecução não altera contagem nem lança.
- [x] 6.3 Acrescentar o passo `purgar_documentos_vencidos` ao `app/jobs/entrypoint.py` após `arquivar_vencidos`, com log próprio. Critério: `uv run python -m app.jobs.entrypoint` roda os dois passos; log distingue cada um.

## 7. Frontend (tela de detalhe do processo)

- [x] 7.1 `pnpm gen:types` após estabilizar o OpenAPI; commitar snapshot `packages/api-types`. Critério: `pnpm gen:types:check` passa.
- [x] 7.2 Seção "Documentos" em `app/processos/[id]`: lista de anexos (nome, tipo, tamanho, data) + estado vazio. Critério: renderiza lista e vazio.
- [x] 7.3 Componente de upload (multipart via `lib/api.ts`) com feedback de erro de formato/tamanho/vazio. Critério: erros do backend exibidos ao usuário.
- [x] 7.4 Visualização inline (PDF/imagem) e ações de download; DOC/DOCX dispara download com o aviso do PRD (US 3.2 Cen.3). Critério: comportamento por tipo correto.
- [x] 7.5 Ação "Remover" com modal de confirmação; oculta/desabilita quando o processo já foi despachado (reflete `pode_remover`). Critério: confirmação exigida; ação indisponível pós-despacho.
- [x] 7.6 Teste de componente (Vitest/RTL) da seção de documentos: lista, upload, erro, e confirmação de remoção. Critério: `pnpm --filter @setes/web test` passa.

## 8. E2E (Playwright) — fluxo crítico de anexo

- [x] 8.1 E2E do fluxo **anexar → visualizar inline → baixar → remover** num processo `Aberto` da unidade do servidor, e assert de que a remoção **após despacho** é bloqueada. Critério: `cd apps/web && pnpm test:e2e` passa (upload de anexo é ação frequente e crítica do MVP; incluído por prudência).

## 9. Validação final

- [x] 9.1 Rodar `uv run ruff check .`, `uv run pytest`, `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`, `pnpm gen:types:check` e o E2E. Critério: tudo verde.
- [x] 9.2 `openspec verify --change gestao-documental` (ou `/opsx:verify`): implementação coerente com specs/design. Critério: sem divergências pendentes.
