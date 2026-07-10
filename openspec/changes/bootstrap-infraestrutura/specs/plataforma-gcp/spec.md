## ADDED Requirements

### Requirement: Projeto GCP único em território nacional
O sistema SHALL ser provisionado em um único projeto GCP de produção, com todos os recursos regionais criados na região `southamerica-east1` (Osasco/SP), para garantir residência de dados em território brasileiro conforme a LGPD.

#### Scenario: Recurso regional criado na região correta
- **WHEN** qualquer recurso regional (Cloud Run, Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Run Job) é provisionado
- **THEN** o recurso é criado na região `southamerica-east1`

#### Scenario: Residência de região garantida por convenção de módulo (MVP)
- **WHEN** um recurso é provisionado pelo Terraform deste repositório
- **THEN** o módulo referencia `var.region` (`southamerica-east1`) para todo recurso regional — não há bloqueio automático via org policy `gcp.resourceLocations` no MVP, pois o projeto `setes-docs` não pertence a uma Organização GCP (exigência de `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta); a garantia é de revisão de PR, não de enforcement da plataforma. Revisitar se o projeto migrar para dentro de uma Organização.

#### Scenario: Segredos com replicação fixada no Brasil
- **WHEN** um segredo é criado no Secret Manager
- **THEN** ele usa replicação gerenciada pelo usuário fixada em `southamerica-east1`, e não replicação automática global

### Requirement: Serviços de aplicação no Cloud Run
O sistema SHALL executar o frontend (Next.js) e o backend (FastAPI) como dois serviços Cloud Run independentes, cada um com sua própria service account e imagem de contêiner.

#### Scenario: Serviço responde a health check
- **WHEN** uma requisição de health check é feita ao serviço `api` ou `web` após o deploy
- **THEN** o serviço responde com status HTTP 200

#### Scenario: API roda com custo zero em ocioso no MVP
- **WHEN** o serviço `api` está provisionado
- **THEN** ele mantém `min-instances=0`, aceitando cold start na primeira requisição após período ocioso em troca de custo zero sem tráfego

### Requirement: Governança de identidade sem chaves de longa duração
O sistema SHALL impedir a criação de chaves de service account de longa duração, forçando autenticação federada (Workload Identity Federation) no pipeline de CI/CD.

#### Scenario: Deploy autenticado via Workload Identity Federation
- **WHEN** o pipeline do GitHub Actions realiza deploy no Cloud Run
- **THEN** ele autentica via Workload Identity Federation, sem usar arquivo de chave JSON de service account

#### Scenario: Ausência de chaves de SA garantida por não uso, não por policy (MVP)
- **WHEN** o pipeline de deploy e todo o Terraform deste repositório são executados
- **THEN** nenhum arquivo de chave JSON de service account é gerado ou referenciado — mas a criação manual de uma chave não é bloqueada automaticamente no MVP, pois a org policy `iam.disableServiceAccountKeyCreation` exige `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta GCP, e `setes-docs` não pertence a uma Organização. Revisitar se o projeto migrar para dentro de uma Organização.
