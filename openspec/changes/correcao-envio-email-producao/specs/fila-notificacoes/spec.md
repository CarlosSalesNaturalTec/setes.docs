## MODIFIED Requirements

### Requirement: Endpoint interno protegido por OIDC
O sistema SHALL expor o endpoint de processamento de tarefas apenas para chamadas autenticadas por token OIDC emitido pela `sa-tasks-invoker`, negando qualquer chamada não autenticada. O token entregue pelo Cloud Tasks SHALL ser assinado com `audience` igual ao audience esperado pelo endpoint interno (a URL base do serviço `api`, sem o path do endpoint), de modo que a chamada legítima do Cloud Tasks seja aceita.

#### Scenario: Chamada autenticada pelo Cloud Tasks é aceita
- **WHEN** o Cloud Tasks invoca o endpoint interno com um token OIDC da `sa-tasks-invoker`
- **THEN** a requisição é aceita e a tarefa é processada

#### Scenario: Token com audience igual ao esperado pelo endpoint
- **DADO** que o serviço `api` enfileira uma tarefa de e-mail definindo o `audience` do token OIDC como a URL base do serviço (a mesma string validada pelo endpoint interno)
- **QUANDO** o Cloud Tasks entrega a tarefa e o endpoint interno valida o token
- **ENTÃO** o `aud` do token corresponde ao audience esperado, a validação OIDC passa e a tarefa é processada

#### Scenario: Acesso negado — token com audience divergente
- **DADO** que uma requisição ao endpoint interno apresenta um token OIDC cujo `aud` não corresponde ao audience esperado (a URL base do serviço `api`)
- **QUANDO** o endpoint interno valida o token
- **ENTÃO** a requisição é rejeitada com erro de autorização (401), a tarefa não é processada e, como a fila usa `maxAttempts=1`, não há redespacho

#### Scenario: Acesso negado — chamada sem token OIDC
- **WHEN** uma requisição é feita ao endpoint interno sem token OIDC válido da `sa-tasks-invoker`
- **THEN** a requisição é rejeitada com erro de autorização
