## 1. Monorepo e fundação do repositório

- [x] 1.1 Criar estrutura de diretórios do monorepo (`apps/web`, `apps/api`, `packages/api-types`, `infra/`, `.github/workflows/`). Critério: árvore criada e commitada; `pnpm-workspace.yaml` inclui `apps/web` e `packages/*`.
- [x] 1.2 Inicializar `apps/api` (FastAPI 3.12 com `uv`/`pyproject.toml`, gerenciado fora do workspace pnpm) com app mínimo e rota `/health`. Critério: `uv run` sobe o app e `/health` responde 200 localmente.
- [x] 1.3 Inicializar `apps/web` (Next.js App Router + Tailwind + TypeScript) com página raiz e rota de health. Critério: `pnpm dev` sobe o app localmente.
- [x] 1.4 Criar Dockerfile de `apps/api` e Dockerfile de `apps/web`, cada um buildando a partir do seu subdiretório. Critério: `docker build` de cada imagem conclui e o contêiner responde ao health check. — Ambas as imagens buildam (exit 0); contêiner api responde `/health` 200 e web responde `/api/health` 200 e `/` 200.
- [x] 1.5 Configurar geração de tipos OpenAPI→TS: script `pnpm gen:types` que emite `openapi.json` do FastAPI e roda `openapi-typescript` para `packages/api-types`. Critério: `pnpm gen:types` gera o pacote e o `web` importa um tipo dele.

## 2. Terraform — projeto, região e governança

- [x] 2.1 Configurar backend do Terraform em bucket GCS versionado (state remoto) e o provider google apontando para o projeto único. Critério: `terraform init` conecta ao backend remoto. — Feito: `terraform init -backend-config=backend.hcl` contra `gs://setes-docs-tfstate` (projeto `setes-docs`).
- [x] 2.2 Definir variáveis base do projeto (project_id, region=`southamerica-east1`) e habilitar as APIs necessárias (run, sqladmin, storage, secretmanager, cloudscheduler, cloudtasks, artifactregistry, cloudbuild, iam, compute). Critério: `terraform apply` habilita todas as APIs sem erro. — Feito: todas as APIs habilitadas via `terraform apply`.
- [x] 2.3 ~~Aplicar org policy `constraints/gcp.resourceLocations = in:southamerica-east1-locations`~~. **Bloqueado, fora do escopo do MVP**: exige `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta; `setes-docs` não tem Organização GCP por trás (conta pessoal). Confirmado via `terraform apply` e `gcloud org-policies set-policy` (403 `orgpolicy.policies.create`). Recurso comentado em `org_policies.tf` com a explicação; revisitar se o projeto migrar para dentro de uma Organização. (spec: plataforma-gcp — atualizado para refletir a limitação)
- [x] 2.4 ~~Aplicar org policy `constraints/iam.disableServiceAccountKeyCreation`~~. **Mesmo bloqueio de 2.3** — sem Organização GCP não há como conceder `roles/orgpolicy.policyAdmin`. Recurso comentado em `org_policies.tf`. (spec: plataforma-gcp — atualizado para refletir a limitação)

## 3. Terraform — rede e Cloud SQL privado

- [x] 3.1 Provisionar a VPC/subnet e a configuração de Private Service Access para Cloud SQL. Critério: rede pronta para IP privado; `terraform apply` idempotente. — Feito: `setes-vpc`/`setes-subnet` + PSA aplicados.
- [x] 3.2 Provisionar a instância Cloud SQL for PostgreSQL **sem IP público**, apenas IP privado, na região. Critério: instância criada; conexão pública recusada. (spec: conectividade-e-seguranca — acesso público negado) — Feito: `setes-postgres` criada, IP privado `10.132.0.3`, sem IPv4 público. Nota: exigiu adicionar `edition = "ENTERPRISE"` em `cloudsql.tf` — projetos novos no GCP têm `ENTERPRISE_PLUS` como padrão, incompatível com o tier `db-custom-2-4096`.
- [x] 3.3 Criar o database da aplicação e o usuário/role de aplicação (senha vinda do Secret Manager). Critério: usuário criado com privilégios mínimos no database. — Feito: database `setes` + usuário `app` criados.

## 4. Terraform — Storage e Secret Manager

- [x] 4.1 Provisionar o bucket único de documentos com uniform bucket-level access, versionamento e soft-delete nativo habilitados; sem binding público. Critério: bucket criado; acesso anônimo negado. (spec: conectividade-e-seguranca — leitura pública negada / rede de segurança) — Feito: `setes-docs-documentos` criado, `public_access_prevention=enforced`.
- [x] 4.2 Criar os 3 segredos (`db-password`, `jwt-signing-key`, `sendgrid-api-key`) com replicação user-managed fixada em `southamerica-east1`. Critério: segredos criados com replicação regional confirmada. (spec: plataforma-gcp — replicação no Brasil) — Feito: os 3 segredos criados com valores gerados/placeholder; `sendgrid-api-key` precisa da chave real do provedor quando integrado.

## 5. Terraform — IAM (service accounts de menor privilégio)

- [x] 5.1 Criar as 6 service accounts (`sa-web`, `sa-api`, `sa-jobs`, `sa-scheduler`, `sa-tasks-invoker`, `sa-deploy`). Critério: todas criadas; nenhuma com papel primitivo. (spec: conectividade-e-seguranca — sem papel primitivo) — Feito: as 6 SAs criadas.
- [x] 5.2 Conceder bindings da `sa-api`: `cloudsql.client`, `secretAccessor` por segredo (db, jwt, sendgrid), `storage.objectUser` no bucket, `cloudtasks.enqueuer` na fila. Critério: `sa-api` acessa só o autorizado. (spec: conectividade-e-seguranca — segredo sem binding negado) — Feito.
- [x] 5.3 Conceder bindings da `sa-jobs`: `cloudsql.client`, `secretAccessor` (db, sendgrid), `storage.objectAdmin` no bucket; sem ingress. Critério: `sa-jobs` pode deletar objetos; ação fora do escopo negada. (spec: conectividade-e-seguranca — job fora do escopo negado) — Feito.
- [x] 5.4 Conceder bindings de `sa-web` (`run.invoker` em api), `sa-scheduler` (execução dos jobs), `sa-tasks-invoker` (`run.invoker` em api), `sa-deploy` (`artifactregistry.writer`, `run.admin`, `iam.serviceAccountUser`). Critério: cada SA tem só o binding do seu papel. — Feito.

## 6. Terraform — Cloud Run (web e api)

- [x] 6.1 Criar o repositório no Artifact Registry para as imagens. Critério: repositório criado na região. — Feito: `setes-images` criado em `southamerica-east1`.
- [x] 6.2 Provisionar o serviço Cloud Run `api` com `sa-api`, Direct VPC egress para a subnet, secrets injetados como env var (`latest`), `min-instances=0` (MVP), `concurrency=80`. Critério: serviço sobe; `/health` responde 200; conexão ao Cloud SQL por IP privado funciona. (spec: plataforma-gcp — health 200; conectividade — conexão privada) — Feito: imagem real deployada via `deploy.yml`, `startup_probe` em `/health` passou. Conexão privada ao Cloud SQL validada indiretamente pela migration (task 9.1) rodando com sucesso pela mesma rede/Direct VPC egress.
- [x] 6.3 Provisionar o serviço Cloud Run `web` com `sa-web`, `min-instances=0–1`. Critério: serviço sobe e responde 200. (spec: plataforma-gcp — health 200) — Feito: imagem real deployada via `deploy.yml` com sucesso.
- [x] 6.4 Configurar pool de conexões da `api` (`pool_size=5`, `max_overflow=0`) e limitar `max-instances` para respeitar `max_connections` do Cloud SQL. Critério: cálculo documentado (instâncias × pool < max_connections). (spec: conectividade-e-seguranca — teto de conexões)

## 7. Terraform — Cloud Tasks e endpoint interno

- [x] 7.1 Provisionar a fila Cloud Tasks `emails` com `maxAttempts=1` e limite de despacho por segundo. Critério: fila criada com config confirmada. (spec: fila-notificacoes — sem retry após falha) — Feito: fila `emails` criada.
- [x] 7.2 Implementar no `api` o endpoint interno `/internal/tasks/email` protegido por OIDC (aceita somente token da `sa-tasks-invoker`); em falha de envio, loga e retorna 200 (ACK). Critério: chamada sem OIDC é rejeitada; falha de envio não redespacha. (spec: fila-notificacoes — chamada sem OIDC negada; sem retry)
- [x] 7.3 Teste automatizado do endpoint interno: (a) rejeita requisição sem OIDC válido; (b) em falha simulada do provedor, registra log e retorna 200 sem lançar. Critério: testes pytest passam. (obrigatório — endpoint de notificação assíncrona)

## 8. Terraform — Cloud Scheduler + Cloud Run Jobs (infra e contrato)

- [x] 8.1 Provisionar o Cloud Run Job `job-manutencao-diaria` (imagem/entrypoint placeholder) com `sa-jobs`, Direct VPC egress e secrets. Critério: job criado e executável manualmente. (spec: rotinas-agendadas — duas rotinas provisionadas) — Feito: job criado.
- [x] 8.2 Provisionar o Cloud Run Job `job-anonimizacao-lgpd` com `sa-jobs`. Critério: job criado. — Feito.
- [x] 8.3 Provisionar os Cloud Scheduler que disparam os jobs (diário 03:00 America/Bahia; trimestral) usando `sa-scheduler`. Critério: scheduler dispara o job; disparo por identidade não autorizada é negado. (spec: rotinas-agendadas — janela / disparo negado) — Feito: os dois triggers criados. Disparo por identidade não autorizada ainda não testado manualmente (validação operacional, task 11.x).
- [x] 8.4 Documentar e testar o contrato de idempotência com um passo de exemplo idempotente no job diário (seleção por estado atual, guard de transição). Critério: teste automatizado prova que reexecução sobre o mesmo estado não duplica efeito nem evento de histórico. (obrigatório — toca histórico de tramitação; spec: rotinas-agendadas — idempotência/retomada)

## 9. Baseline de banco (Alembic) — schema antes de endpoint

- [x] 9.1 Inicializar Alembic em `apps/api` com conexão via IP privado e migration baseline (vazia ou apenas extensões, ex.: `pgcrypto`). Critério: `alembic upgrade head` roda contra o Cloud SQL sem criar tabela de negócio. — Feito: `alembic upgrade head` executou com sucesso contra `setes-postgres` via IP privado, no job `migrate`. Na primeira tentativa falhou com `sqlalchemy.exc.ArgumentError` — `DATABASE_URL` estava sendo injetado direto do secret `db-password` (só a senha, não uma URL de conexão); corrigido montando a URL a partir de peças (`DB_HOST`/`DB_PORT`/`DB_USER`/`DB_NAME`/`DB_PASSWORD`) em `app/config.py` e `cloudrun.tf`.
- [x] 9.2 Integrar a execução de migrations no fluxo de deploy (passo dedicado, não no processo de request). Critério: migration roda de forma controlada e idempotente no deploy. — Feito: passo dedicado no `deploy.yml` (Cloud Run Job efêmero `migrate`) executou com sucesso, antes do deploy do serviço `api`.

## 10. CI/CD — GitHub Actions + Workload Identity Federation

- [x] 10.1 Configurar o Workload Identity Pool/Provider e permitir a `sa-deploy` ser assumida pelo repositório GitHub. Critério: workflow autentica sem chave JSON. (spec: plataforma-gcp — deploy via WIF) — Feito: pool/provider criados, restritos a `CarlosSalesNaturalTec/processos_gestor`. Variáveis do repositório configuradas no GitHub (Settings → Actions → Variables): `GCP_PROJECT_ID`, `WIF_PROVIDER`, `DEPLOY_SA_EMAIL`, `JOBS_SA_EMAIL`, `CLOUDSQL_PRIVATE_IP`. `google-github-actions/auth@v2` autenticou com sucesso na primeira execução real do `deploy.yml`.
- [x] 10.2 Criar workflow de CI (lint + pytest + Vitest) com path filters por app e drift check do `packages/api-types`. Critério: CI falha se o snapshot de tipos estiver defasado.
- [x] 10.3 Criar workflow de deploy: build → push no Artifact Registry → `gcloud run deploy` de `web` e `api` (só o app alterado). Critério: push na branch alvo publica e faz deploy com sucesso. — Feito: PR #1 mesclada em `main` disparou a primeira execução real (`deploy-web` sucesso de primeira; `deploy-api` falhou na migration por causa do bug de `DATABASE_URL`, corrigido na PR #2 — reexecução completa com sucesso, incluindo migration e deploy dos dois serviços).

## 11. Validação end-to-end

- [ ] 11.1 Validar o fluxo assíncrono de e-mail ponta a ponta em produção: enfileirar tarefa → endpoint interno processa via OIDC → provedor SaaS entrega. Critério: e-mail entregue; falha simulada gera log e não redespacha. — Verificação operacional em produção; requer infra aplicada.
- [ ] 11.2 Auditar IAM e org policies: nenhum papel primitivo, chaves de SA bloqueadas, recursos fora da região bloqueados, segredos replicados só no Brasil. Critério: checklist de segurança/residência aprovado. — Checklist documentado em `infra/README.md`; requer infra aplicada para auditoria.
