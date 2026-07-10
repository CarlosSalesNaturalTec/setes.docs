## 1. Monorepo e fundação do repositório

- [ ] 1.1 Criar estrutura de diretórios do monorepo (`apps/web`, `apps/api`, `packages/api-types`, `infra/`, `.github/workflows/`). Critério: árvore criada e commitada; `pnpm-workspace.yaml` inclui `apps/web` e `packages/*`.
- [ ] 1.2 Inicializar `apps/api` (FastAPI 3.12 com `uv`/`pyproject.toml`, gerenciado fora do workspace pnpm) com app mínimo e rota `/health`. Critério: `uv run` sobe o app e `/health` responde 200 localmente.
- [ ] 1.3 Inicializar `apps/web` (Next.js App Router + Tailwind + TypeScript) com página raiz e rota de health. Critério: `pnpm dev` sobe o app localmente.
- [ ] 1.4 Criar Dockerfile de `apps/api` e Dockerfile de `apps/web`, cada um buildando a partir do seu subdiretório. Critério: `docker build` de cada imagem conclui e o contêiner responde ao health check.
- [ ] 1.5 Configurar geração de tipos OpenAPI→TS: script `pnpm gen:types` que emite `openapi.json` do FastAPI e roda `openapi-typescript` para `packages/api-types`. Critério: `pnpm gen:types` gera o pacote e o `web` importa um tipo dele.

## 2. Terraform — projeto, região e governança

- [ ] 2.1 Configurar backend do Terraform em bucket GCS versionado (state remoto) e o provider google apontando para o projeto único. Critério: `terraform init` conecta ao backend remoto.
- [ ] 2.2 Definir variáveis base do projeto (project_id, region=`southamerica-east1`) e habilitar as APIs necessárias (run, sqladmin, storage, secretmanager, cloudscheduler, cloudtasks, artifactregistry, cloudbuild, iam, compute). Critério: `terraform apply` habilita todas as APIs sem erro.
- [ ] 2.3 Aplicar org policy `constraints/gcp.resourceLocations = in:southamerica-east1-locations`. Critério: tentativa de criar recurso fora da região é bloqueada; validar contra serviços globais legítimos e ajustar allowlist se necessário. (spec: plataforma-gcp — recurso fora da região negado)
- [ ] 2.4 Aplicar org policy `constraints/iam.disableServiceAccountKeyCreation`. Critério: criação de chave JSON de SA é bloqueada. (spec: plataforma-gcp — criação de chave negada)

## 3. Terraform — rede e Cloud SQL privado

- [ ] 3.1 Provisionar a VPC/subnet e a configuração de Private Service Access para Cloud SQL. Critério: rede pronta para IP privado; `terraform apply` idempotente.
- [ ] 3.2 Provisionar a instância Cloud SQL for PostgreSQL **sem IP público**, apenas IP privado, na região. Critério: instância criada; conexão pública recusada. (spec: conectividade-e-seguranca — acesso público negado)
- [ ] 3.3 Criar o database da aplicação e o usuário/role de aplicação (senha vinda do Secret Manager). Critério: usuário criado com privilégios mínimos no database.

## 4. Terraform — Storage e Secret Manager

- [ ] 4.1 Provisionar o bucket único de documentos com uniform bucket-level access, versionamento e soft-delete nativo habilitados; sem binding público. Critério: bucket criado; acesso anônimo negado. (spec: conectividade-e-seguranca — leitura pública negada / rede de segurança)
- [ ] 4.2 Criar os 3 segredos (`db-password`, `jwt-signing-key`, `sendgrid-api-key`) com replicação user-managed fixada em `southamerica-east1`. Critério: segredos criados com replicação regional confirmada. (spec: plataforma-gcp — replicação no Brasil)

## 5. Terraform — IAM (service accounts de menor privilégio)

- [ ] 5.1 Criar as 6 service accounts (`sa-web`, `sa-api`, `sa-jobs`, `sa-scheduler`, `sa-tasks-invoker`, `sa-deploy`). Critério: todas criadas; nenhuma com papel primitivo. (spec: conectividade-e-seguranca — sem papel primitivo)
- [ ] 5.2 Conceder bindings da `sa-api`: `cloudsql.client`, `secretAccessor` por segredo (db, jwt, sendgrid), `storage.objectUser` no bucket, `cloudtasks.enqueuer` na fila. Critério: `sa-api` acessa só o autorizado. (spec: conectividade-e-seguranca — segredo sem binding negado)
- [ ] 5.3 Conceder bindings da `sa-jobs`: `cloudsql.client`, `secretAccessor` (db, sendgrid), `storage.objectAdmin` no bucket; sem ingress. Critério: `sa-jobs` pode deletar objetos; ação fora do escopo negada. (spec: conectividade-e-seguranca — job fora do escopo negado)
- [ ] 5.4 Conceder bindings de `sa-web` (`run.invoker` em api), `sa-scheduler` (execução dos jobs), `sa-tasks-invoker` (`run.invoker` em api), `sa-deploy` (`artifactregistry.writer`, `run.admin`, `iam.serviceAccountUser`). Critério: cada SA tem só o binding do seu papel.

## 6. Terraform — Cloud Run (web e api)

- [ ] 6.1 Criar o repositório no Artifact Registry para as imagens. Critério: repositório criado na região.
- [ ] 6.2 Provisionar o serviço Cloud Run `api` com `sa-api`, Direct VPC egress para a subnet, secrets injetados como env var (`latest`), `min-instances=1`, `concurrency=80`. Critério: serviço sobe; `/health` responde 200; conexão ao Cloud SQL por IP privado funciona. (spec: plataforma-gcp — health 200 / instância aquecida; conectividade — conexão privada)
- [ ] 6.3 Provisionar o serviço Cloud Run `web` com `sa-web`, `min-instances=0–1`. Critério: serviço sobe e responde 200. (spec: plataforma-gcp — health 200)
- [ ] 6.4 Configurar pool de conexões da `api` (`pool_size=5`, `max_overflow=0`) e limitar `max-instances` para respeitar `max_connections` do Cloud SQL. Critério: cálculo documentado (instâncias × pool < max_connections). (spec: conectividade-e-seguranca — teto de conexões)

## 7. Terraform — Cloud Tasks e endpoint interno

- [ ] 7.1 Provisionar a fila Cloud Tasks `emails` com `maxAttempts=1` e limite de despacho por segundo. Critério: fila criada com config confirmada. (spec: fila-notificacoes — sem retry após falha)
- [ ] 7.2 Implementar no `api` o endpoint interno `/internal/tasks/email` protegido por OIDC (aceita somente token da `sa-tasks-invoker`); em falha de envio, loga e retorna 200 (ACK). Critério: chamada sem OIDC é rejeitada; falha de envio não redespacha. (spec: fila-notificacoes — chamada sem OIDC negada; sem retry)
- [ ] 7.3 Teste automatizado do endpoint interno: (a) rejeita requisição sem OIDC válido; (b) em falha simulada do provedor, registra log e retorna 200 sem lançar. Critério: testes pytest passam. (obrigatório — endpoint de notificação assíncrona)

## 8. Terraform — Cloud Scheduler + Cloud Run Jobs (infra e contrato)

- [ ] 8.1 Provisionar o Cloud Run Job `job-manutencao-diaria` (imagem/entrypoint placeholder) com `sa-jobs`, Direct VPC egress e secrets. Critério: job criado e executável manualmente. (spec: rotinas-agendadas — duas rotinas provisionadas)
- [ ] 8.2 Provisionar o Cloud Run Job `job-anonimizacao-lgpd` com `sa-jobs`. Critério: job criado.
- [ ] 8.3 Provisionar os Cloud Scheduler que disparam os jobs (diário 03:00 America/Bahia; trimestral) usando `sa-scheduler`. Critério: scheduler dispara o job; disparo por identidade não autorizada é negado. (spec: rotinas-agendadas — janela / disparo negado)
- [ ] 8.4 Documentar e testar o contrato de idempotência com um passo de exemplo idempotente no job diário (seleção por estado atual, guard de transição). Critério: teste automatizado prova que reexecução sobre o mesmo estado não duplica efeito nem evento de histórico. (obrigatório — toca histórico de tramitação; spec: rotinas-agendadas — idempotência/retomada)

## 9. Baseline de banco (Alembic) — schema antes de endpoint

- [ ] 9.1 Inicializar Alembic em `apps/api` com conexão via IP privado e migration baseline (vazia ou apenas extensões, ex.: `pgcrypto`). Critério: `alembic upgrade head` roda contra o Cloud SQL sem criar tabela de negócio.
- [ ] 9.2 Integrar a execução de migrations no fluxo de deploy (passo dedicado, não no processo de request). Critério: migration roda de forma controlada e idempotente no deploy.

## 10. CI/CD — GitHub Actions + Workload Identity Federation

- [ ] 10.1 Configurar o Workload Identity Pool/Provider e permitir a `sa-deploy` ser assumida pelo repositório GitHub. Critério: workflow autentica sem chave JSON. (spec: plataforma-gcp — deploy via WIF)
- [ ] 10.2 Criar workflow de CI (lint + pytest + Vitest) com path filters por app e drift check do `packages/api-types`. Critério: CI falha se o snapshot de tipos estiver defasado.
- [ ] 10.3 Criar workflow de deploy: build → push no Artifact Registry → `gcloud run deploy` de `web` e `api` (só o app alterado). Critério: push na branch alvo publica e faz deploy com sucesso.

## 11. Validação end-to-end

- [ ] 11.1 Validar o fluxo assíncrono de e-mail ponta a ponta em produção: enfileirar tarefa → endpoint interno processa via OIDC → provedor SaaS entrega. Critério: e-mail entregue; falha simulada gera log e não redespacha.
- [ ] 11.2 Auditar IAM e org policies: nenhum papel primitivo, chaves de SA bloqueadas, recursos fora da região bloqueados, segredos replicados só no Brasil. Critério: checklist de segurança/residência aprovado.
