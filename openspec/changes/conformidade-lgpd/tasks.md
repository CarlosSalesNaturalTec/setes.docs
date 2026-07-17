## 1. Migrations (schema antes de endpoint)

- [ ] 1.1 Criar migration Alembic: tabela `solicitacao_lgpd_contador_ano` (`ano` PK, `ultimo_sequencial`)
- [ ] 1.2 Criar migration Alembic: enums `tipo_solicitacao_lgpd` e `status_solicitacao_lgpd`
- [ ] 1.3 Criar migration Alembic: tabela `solicitacao_lgpd` (protocolo único, FK `processo_id`, dados do solicitante, tipo, status, chave do documento, justificativa de rejeição, `criado_em`, `atendido_em`, `atendido_por_id`)
- [ ] 1.4 Criar migration Alembic: `ALTER TABLE tipo_processo ADD COLUMN prazo_anonimizacao_anos INTEGER NOT NULL DEFAULT 5`
- [ ] 1.5 Criar migration Alembic: `ALTER TABLE processo_interessado ADD COLUMN anonimizado_em TIMESTAMPTZ NULL`
- [ ] 1.6 Criar migration Alembic: `ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'interessado_anonimizado'`
- [ ] 1.7 Rodar `uv run alembic upgrade head` localmente contra Postgres de dev e confirmar sucesso sem erros
- [ ] 1.8 Adicionar os novos modelos SQLAlchemy (`SolicitacaoLgpd`, `SolicitacaoLgpdContadorAno`) e as colunas/enums em `app/db/models.py`

## 2. Infraestrutura (Terraform)

- [ ] 2.1 Adicionar `google_storage_bucket.lgpd_solicitacoes` em `infra/storage.tf` (uniform bucket-level access, mesmo padrão do bucket de documentos)
- [ ] 2.2 Adicionar binding `storage.objectUser` de `sa-api` no novo bucket em `infra/iam.tf` (sem acesso de `sa-jobs`)
- [ ] 2.3 Adicionar output `lgpd_solicitacoes_bucket` em `infra/outputs.tf`
- [ ] 2.4 Adicionar variável `LGPD_SOLICITACOES_BUCKET` em `app/config.py` (mesmo padrão de `documentos_bucket`)
- [ ] 2.5 Atualizar `infra/jobs_scheduler.tf`: trocar `command` de `job-anonimizacao-lgpd` para `["python", "-m", "app.jobs.entrypoint_lgpd"]` (schedule/service account/VPC inalterados)
- [ ] 2.6 Rodar `terraform plan` em `infra/` e revisar o diff antes de aplicar (aplicação fica fora deste change, a cargo do pipeline de deploy)

## 3. Serviço de anonimização (compartilhado)

- [ ] 3.1 Implementar `services/lgpd.py::anonimizar_interessados(db, processo, *, agora, origem, solicitacao_lgpd_id=None) -> int` — anonimiza interessados com `anonimizado_em IS NULL`, registra 1 evento `interessado_anonimizado` em `log_seguranca` por processo
- [ ] 3.2 Implementar gerador de identificador anonimizado irreversível (hash truncado não correlacionável ao CPF/CNPJ original)
- [ ] 3.3 Teste automatizado: `anonimizar_interessados` substitui nome e documento, marca `anonimizado_em`, preserva `processo.numero`/datas/unidades/status/histórico de tramitação
- [ ] 3.4 Teste automatizado: chamar `anonimizar_interessados` duas vezes sobre o mesmo processo não gera segundo evento em `log_seguranca` nem sobrescreve `anonimizado_em` já preenchido (idempotência)
- [ ] 3.5 Teste automatizado: identificador anonimizado gerado não permite recuperar o CPF/CNPJ original

## 4. Canal público de solicitação (US 10.1)

- [ ] 4.1 Implementar `services/numero_processo.py`-equivalente para protocolo: `services/protocolo_lgpd.py::gerar_protocolo(db) -> str` (formato `LGPD/AAAA/NNNNNN`, upsert atômico em `solicitacao_lgpd_contador_ano`)
- [ ] 4.2 Implementar schema Pydantic `SolicitacaoLgpdCreate` (nome, CPF, e-mail, número do processo, tipo de solicitação) e validação de CPF (reaproveitar validador já usado em `processo_interessado`)
- [ ] 4.3 Implementar `POST /publico/lgpd/solicitacoes` em `routers/lgpd.py`: valida processo existente, valida documento de identificação (PDF/JPG/PNG, não vazio, ≤20MB), grava no bucket dedicado, gera protocolo, insere `solicitacao_lgpd`, enfileira e-mail de confirmação com protocolo
- [ ] 4.4 Aplicar rate limiting `RATE_LIMIT_CONSULTA_PUBLICA` (`slowapi`) ao endpoint público de solicitação
- [ ] 4.5 Teste automatizado: solicitação com dados válidos gera protocolo único e registra a solicitação (dado pessoal — teste obrigatório)
- [ ] 4.6 Teste automatizado: campos obrigatórios ausentes retornam erro de validação
- [ ] 4.7 Teste automatizado: documento de identificação com formato inválido ou vazio é rejeitado
- [ ] 4.8 Teste automatizado: número de processo inexistente retorna "Nenhum processo encontrado com o número informado"
- [ ] 4.9 Implementar página pública `apps/web/app/lgpd/solicitacao/page.tsx` com o formulário e a tela de confirmação de protocolo
- [ ] 4.10 Regenerar contrato (`pnpm gen:types`) e ajustar `apps/web/lib/api.ts`

## 5. Fila administrativa e atendimento/rejeição (US 10.2)

- [ ] 5.1 Implementar `GET /lgpd/solicitacoes` (Admin-only) com filtros por status, listando protocolo/data/solicitante/processo/tipo/status
- [ ] 5.2 Implementar `POST /lgpd/solicitacoes/{id}/atender` (Admin-only): valida transição de estado (só a partir de pendente/em_analise), chama `anonimizar_interessados(origem="manual", solicitacao_lgpd_id=id)`, marca `atendida`/`atendido_em`/`atendido_por_id`, enfileira e-mail de conclusão
- [ ] 5.3 Implementar `POST /lgpd/solicitacoes/{id}/rejeitar` (Admin-only): exige `justificativa` não vazia, marca `rejeitada`, enfileira e-mail com a justificativa
- [ ] 5.4 Teste automatizado: acesso negado (Servidor/Gestor/Auditor) às rotas de fila/atendimento/rejeição, registrado em `log_seguranca`
- [ ] 5.5 Teste automatizado: atendimento de solicitação anonimiza os interessados do processo indicado e muda status para "Atendida" (dado pessoal — teste obrigatório)
- [ ] 5.6 Teste automatizado: rejeição sem justificativa é rejeitada; rejeição com justificativa muda status e preserva o texto
- [ ] 5.7 Teste automatizado: tentativa de atender/rejeitar solicitação já em estado terminal (atendida/rejeitada) é rejeitada
- [ ] 5.8 Implementar página `apps/web/app/admin/lgpd/page.tsx` com a fila, ações "Atender"/"Rejeitar" e modal de justificativa
- [ ] 5.9 Regenerar contrato (`pnpm gen:types`) e ajustar `apps/web/lib/api.ts`

## 6. Prazo de anonimização por tipo de processo (US 10.3 Cen.2)

- [ ] 6.1 Adicionar `prazo_anonimizacao_anos` ao schema `TipoProcessoUpdate`/`TipoProcessoResponse` e à rota de edição em `routers/tipos_processo.py`, com validação de inteiro positivo (Admin-only)
- [ ] 6.2 Teste automatizado: configurar prazo válido persiste o valor; valor zero/negativo é rejeitado
- [ ] 6.3 Teste automatizado: acesso negado (Servidor/Gestor) ao configurar o parâmetro
- [ ] 6.4 Adicionar o campo "Prazo de anonimização LGPD (anos)" em `apps/web/app/admin/tipos-processo/page.tsx`
- [ ] 6.5 Regenerar contrato (`pnpm gen:types`) e ajustar `apps/web/lib/api.ts`

## 7. Rotina trimestral automática (US 10.3)

- [ ] 7.1 Implementar `services/anonimizacao_lgpd.py::processar_anonimizacao_automatica(db, *, agora) -> int` com a query de seleção (processo `Arquivado` + `arquivado_em + prazo_anonimizacao_anos <= agora` + interessado ainda não anonimizado), chamando `anonimizar_interessados(origem="automatico")` por processo selecionado
- [ ] 7.2 Implementar `app/jobs/entrypoint_lgpd.py` (mesmo padrão de `app/jobs/entrypoint.py`: abre sessão, executa, loga total, fecha sessão)
- [ ] 7.3 Teste automatizado: processo arquivado há mais tempo que o prazo do seu tipo é anonimizado; processo dentro do prazo não é tocado (dado pessoal — teste obrigatório)
- [ ] 7.4 Teste automatizado: execução repetida sobre o mesmo estado não reprocessa processo já anonimizado (idempotência, mesmo padrão de `tests/test_idempotencia.py`)
- [ ] 7.5 Teste automatizado: retomada simulando processos vencidos durante indisponibilidade são todos anonimizados na execução seguinte, sem duplicar evento
- [ ] 7.6 Rodar `uv run python -m app.jobs.entrypoint_lgpd` localmente contra Postgres de dev e confirmar execução sem erros

## 8. Fechamento

- [ ] 8.1 Rodar `uv run ruff check .` e `uv run pytest` (suíte completa) em `apps/api`
- [ ] 8.2 Rodar `pnpm --filter @setes/web typecheck` e `pnpm --filter @setes/web test`
- [ ] 8.3 Rodar `pnpm gen:types:check` e confirmar ausência de drift
- [ ] 8.4 Atualizar `docs/PRD.md` ou changelog interno se aplicável (checar convenção do repo antes de tocar o PRD, que é fonte de verdade e normalmente não é editado por change)
