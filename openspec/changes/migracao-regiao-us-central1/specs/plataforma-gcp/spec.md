## MODIFIED Requirements

### Requirement: Projeto GCP único em região única
O sistema SHALL ser provisionado em um único projeto GCP, com **todos** os recursos regionais criados na mesma região, definida pela variável `region` do Terraform e fixada em **`us-central1`**. A escolha da região é uma decisão de **custo** do cliente, e não um requisito de residência de dados — o controlador é instituição **privada** e autorizou expressamente o tratamento fora do território nacional.

O sistema NÃO SHALL afirmar, em código, comentário, documentação ou spec, residência de dados em território brasileiro. A **transferência internacional de dados** decorrente dessa escolha SHALL possuir base legal documentada pelo controlador (Lei 13.709/2018, Art. 33), e o tratamento no exterior SHALL ser informado na política de privacidade e no aviso de tratamento. Todas as demais garantias de proteção de dados — controle de acesso, ausência de leitura pública, anonimização, retenção e purga — permanecem integralmente aplicáveis.

#### Scenario: Recurso regional criado na região configurada
- **QUANDO** qualquer recurso regional (Cloud Run, Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Run Job, Artifact Registry) é provisionado
- **ENTÃO** o recurso é criado em `us-central1`, referenciando `var.region` — nenhuma região literal diferente aparece nos módulos

#### Scenario: Segredos com replicação fixada na região única
- **QUANDO** um segredo é criado no Secret Manager
- **ENTÃO** ele usa replicação gerenciada pelo usuário fixada em `us-central1`, e não replicação automática global — a fixação permanece por controle de localização, ainda que a região não seja mais nacional

#### Scenario: Repositório não afirma residência nacional
- **QUANDO** o código de infraestrutura, seus comentários e as specs são inspecionados
- **ENTÃO** não há nenhuma afirmação de que os dados residem em território brasileiro nem de que a residência nacional é requisito de conformidade

#### Scenario: Transferência internacional documentada antes do provisionamento
- **DADO** que o tratamento passa a ocorrer fora do território nacional
- **QUANDO** a mudança de região é executada
- **ENTÃO** a base legal da transferência internacional, a identificação de quem autorizou a decisão pelo cliente e a autorização de descarte dos dados existentes já estão registradas em documentação versionada

#### Scenario: Garantias de proteção preservadas após a mudança de região
- **DADO** que o ambiente foi reconstruído na região nova
- **QUANDO** verifico os controles de proteção de dados
- **ENTÃO** o bucket mantém `public_access_prevention`, o acesso ao conteúdo continua mediado pela aplicação, e as rotinas de anonimização, retenção e purga permanecem operantes e inalteradas
