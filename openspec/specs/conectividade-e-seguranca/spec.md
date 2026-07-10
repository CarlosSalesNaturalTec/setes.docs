# conectividade-e-seguranca

## Purpose

Cloud SQL com IP privado (Direct VPC egress), bucket de documentos, Secret Manager e o modelo de IAM com service accounts de menor privilégio — incluindo os cenários de acesso negado.

## Requirements

### Requirement: Banco de dados acessível apenas por rede privada
O sistema SHALL provisionar o Cloud SQL for PostgreSQL sem IP público, acessível somente por IP privado a partir do serviço `api` e dos Cloud Run Jobs via Direct VPC egress.

#### Scenario: API conecta ao banco por IP privado
- **WHEN** o serviço `api` estabelece conexão com o Cloud SQL
- **THEN** a conexão ocorre pelo IP privado da instância, sem trafegar pela internet pública

#### Scenario: Acesso negado — conexão pela internet pública
- **WHEN** uma tentativa de conexão ao banco é feita a partir de um endereço da internet pública
- **THEN** a conexão é recusada, pois a instância não possui IP público habilitado

#### Scenario: Teto de conexões respeitado
- **WHEN** o serviço `api` escala horizontalmente até `max-instances`
- **THEN** o total de conexões abertas (instâncias × tamanho do pool) permanece abaixo do `max_connections` configurado na instância Cloud SQL

### Requirement: Armazenamento de documentos com acesso restrito
O sistema SHALL provisionar um bucket único no Cloud Storage para documentos anexados, com acesso uniforme no nível do bucket e sem exposição pública.

#### Scenario: Documento gravado sob prefixo do processo
- **WHEN** um documento é armazenado
- **THEN** ele é gravado sob o prefixo `processos/{processo_id}/`, mantendo o processo como chave estável mesmo que o processo tramite entre unidades

#### Scenario: Acesso negado — leitura pública do bucket
- **WHEN** um usuário anônimo tenta acessar um objeto do bucket diretamente
- **THEN** o acesso é negado, pois o bucket não concede permissão a `allUsers`/`allAuthenticatedUsers`

#### Scenario: Rede de segurança para exclusão acidental
- **WHEN** um objeto é excluído do bucket
- **THEN** o versionamento e o soft-delete nativo do Cloud Storage retêm uma cópia recuperável por um período configurado, como defesa contra exclusão acidental de infraestrutura

### Requirement: Segredos acessíveis apenas por service accounts autorizadas
O sistema SHALL armazenar `db-password`, `jwt-signing-key` e `sendgrid-api-key` no Secret Manager, concedendo acesso de leitura no nível de cada segredo apenas às service accounts que dele necessitam.

#### Scenario: Serviço acessa somente os segredos autorizados
- **WHEN** o serviço `api` é iniciado
- **THEN** ele acessa apenas os segredos aos quais sua service account recebeu `secretAccessor`, injetados como variáveis de ambiente

#### Scenario: Acesso negado — segredo sem binding
- **WHEN** uma service account sem binding `secretAccessor` em um segredo tenta lê-lo
- **THEN** o acesso é negado pelo Secret Manager

### Requirement: Service accounts de menor privilégio por identidade
O sistema SHALL provisionar uma service account dedicada por identidade de execução (`sa-web`, `sa-api`, `sa-jobs`, `sa-scheduler`, `sa-tasks-invoker`, `sa-deploy`), sem uso de papéis primitivos (Owner/Editor) e com permissões concedidas no nível do recurso.

#### Scenario: Nenhuma service account com papel primitivo
- **WHEN** os bindings de IAM do projeto são auditados
- **THEN** nenhuma das service accounts de execução possui os papéis `roles/owner` ou `roles/editor`

#### Scenario: Acesso negado — job tenta ação fora do seu escopo
- **WHEN** a `sa-jobs` tenta uma operação para a qual não recebeu permissão (ex.: invocar um serviço Cloud Run público)
- **THEN** a operação é negada por falta de binding correspondente
