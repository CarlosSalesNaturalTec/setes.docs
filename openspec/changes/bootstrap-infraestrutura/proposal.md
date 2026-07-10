## Why

O SETES.DOCS ainda não possui nenhuma infraestrutura provisionada. Antes de abrir qualquer change de negócio (identidade, processos, tramitação, documentos), é preciso estabelecer a topologia base do Google Cloud — a plataforma de execução, o banco, o armazenamento, os segredos, as rotinas agendadas e o pipeline de entrega. Este é o "change zero": todos os demais changes dependem dele. A escolha de região e das travas de residência de dados também precisa ser feita agora, porque o cliente é órgão da administração pública brasileira (Bahia) e a conformidade LGPD exige que os dados residam no Brasil desde o primeiro recurso criado.

## What Changes

- Provisionar **um único projeto GCP de produção** na região **`southamerica-east1`** (Osasco/SP) — sem ambiente de staging separado no MVP.
- **Cloud Run × 2**: serviço `web` (Next.js/App Router) e serviço `api` (FastAPI). API com `min-instances=1`.
- **Cloud SQL for PostgreSQL** com **IP privado** (sem IP público), acessado pela API via **Direct VPC egress**. Instância vazia — nenhuma tabela de negócio é criada aqui (schema vem em changes futuros via Alembic).
- **Cloud Storage**: um bucket único para documentos anexados, com estrutura de prefixo por processo, versionamento e soft-delete nativo como rede de segurança.
- **Secret Manager**: 3 segredos novos — `db-password`, `jwt-signing-key`, `sendgrid-api-key` — com replicação fixada em `southamerica-east1`.
- **Cloud Scheduler + Cloud Run Jobs**: provisiona a infraestrutura de duas rotinas (job diário de manutenção e job trimestral de anonimização). Apenas a infraestrutura e o contrato de idempotência — a lógica de negócio (arquivamento US 2.5, anonimização US 10.3) é implementada em changes futuros.
- **Cloud Tasks**: fila `emails` para envio assíncrono via provedor SaaS (SendGrid/Mailgun), invocando um endpoint interno OIDC-only do serviço `api`. Pub/Sub descartado.
- **CI/CD**: GitHub Actions autenticando via **Workload Identity Federation** (sem chaves de service account) → Artifact Registry → deploy no Cloud Run.
- **Estrutura de monorepo**: `apps/web`, `apps/api`, `packages/api-types` (tipos TS gerados do OpenAPI) e `infra/` (Terraform).
- **IAM**: 6 service accounts dedicadas, princípio de menor privilégio, roles concedidos no nível do recurso.
- **Org policies** de governança: `gcp.resourceLocations` (trava a região) e `iam.disableServiceAccountKeyCreation` (força WIF).
- **Fora de escopo (não muda):** assinatura digital ICP-Brasil (Épico 4 — condicionado a Discovery Técnico, movido para Fase 2); ambiente de staging; qualquer schema/tabela de negócio.

## Capabilities

### New Capabilities
- `plataforma-gcp`: projeto GCP único em `southamerica-east1`, serviços Cloud Run (web/api), org policies de residência de dados e não-criação de chaves de SA, e o pipeline de entrega (GitHub Actions + WIF + Artifact Registry).
- `conectividade-e-seguranca`: Cloud SQL com IP privado (Direct VPC egress), bucket de documentos, Secret Manager e o modelo de IAM com service accounts de menor privilégio — incluindo os cenários de acesso negado.
- `rotinas-agendadas`: infraestrutura de Cloud Scheduler + Cloud Run Jobs (diário e trimestral) e o contrato de idempotência/retomada exigido pela US 2.5 (Cenário 4) e US 10.3.
- `fila-notificacoes`: Cloud Tasks (fila `emails`, `maxAttempts=1`) e o endpoint interno OIDC-only do serviço `api`, com o cenário de rejeição de chamada não autenticada.

### Modified Capabilities
- (nenhuma — não existem specs em `openspec/specs/` ainda; este é o primeiro change)

## Impact

- **Código:** cria a estrutura de monorepo (`apps/web`, `apps/api`, `packages/api-types`, `infra/`), Dockerfiles por serviço, workflows do GitHub Actions e módulos Terraform. Nenhuma feature de negócio é implementada.
- **Dependência de change anterior:** nenhuma. Este é o change base; todos os changes de negócio subsequentes o requerem.
- **Tabelas PostgreSQL:** nenhuma tabela nova. Apenas provisiona a instância Cloud SQL vazia e o usuário/role de aplicação. Migrations Alembic de negócio virão em changes seguintes.
- **Secret Manager:** 3 segredos novos (`db-password`, `jwt-signing-key`, `sendgrid-api-key`).
- **Cloud Storage:** 1 bucket novo (documentos anexados).
- **LGPD:** este change não coleta nem trata dados pessoais diretamente, mas **estabelece as garantias de base**: residência de dados em território nacional (`southamerica-east1` + org policy de location), replicação de segredos fixada no Brasil, e a infraestrutura de anonimização automática que dará suporte à US 10.3. O bucket e o banco que armazenarão dados pessoais nascem já dentro da fronteira de dados brasileira.
- **Sistemas externos:** provedor de e-mail SaaS (SendGrid ou Mailgun) — a definição do provedor específico é registrada no design.
