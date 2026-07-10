## ADDED Requirements

### Requirement: Projeto GCP único em território nacional
O sistema SHALL ser provisionado em um único projeto GCP de produção, com todos os recursos regionais criados na região `southamerica-east1` (Osasco/SP), para garantir residência de dados em território brasileiro conforme a LGPD.

#### Scenario: Recurso regional criado na região correta
- **WHEN** qualquer recurso regional (Cloud Run, Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Run Job) é provisionado
- **THEN** o recurso é criado na região `southamerica-east1`

#### Scenario: Acesso negado — criação de recurso fora da região
- **WHEN** um recurso é solicitado em uma região diferente de `southamerica-east1`
- **THEN** a org policy `gcp.resourceLocations` bloqueia a criação e a operação falha

#### Scenario: Segredos com replicação fixada no Brasil
- **WHEN** um segredo é criado no Secret Manager
- **THEN** ele usa replicação gerenciada pelo usuário fixada em `southamerica-east1`, e não replicação automática global

### Requirement: Serviços de aplicação no Cloud Run
O sistema SHALL executar o frontend (Next.js) e o backend (FastAPI) como dois serviços Cloud Run independentes, cada um com sua própria service account e imagem de contêiner.

#### Scenario: Serviço responde a health check
- **WHEN** uma requisição de health check é feita ao serviço `api` ou `web` após o deploy
- **THEN** o serviço responde com status HTTP 200

#### Scenario: API mantém instância aquecida
- **WHEN** o serviço `api` está provisionado
- **THEN** ele mantém `min-instances=1`, evitando cold start na primeira requisição do horário de operação

### Requirement: Governança de identidade sem chaves de longa duração
O sistema SHALL impedir a criação de chaves de service account de longa duração, forçando autenticação federada (Workload Identity Federation) no pipeline de CI/CD.

#### Scenario: Deploy autenticado via Workload Identity Federation
- **WHEN** o pipeline do GitHub Actions realiza deploy no Cloud Run
- **THEN** ele autentica via Workload Identity Federation, sem usar arquivo de chave JSON de service account

#### Scenario: Acesso negado — criação de chave de service account
- **WHEN** uma chave JSON de service account é solicitada em qualquer service account do projeto
- **THEN** a org policy `iam.disableServiceAccountKeyCreation` bloqueia a operação
