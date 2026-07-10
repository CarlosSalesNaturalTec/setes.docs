# fila-notificacoes

## Purpose

Cloud Tasks (fila `emails`, `maxAttempts=1`) e o endpoint interno OIDC-only do serviço `api`, com o cenário de rejeição de chamada não autenticada.

## Requirements

### Requirement: Fila de e-mail assíncrona via Cloud Tasks
O sistema SHALL provisionar uma fila Cloud Tasks (`emails`) que entrega tarefas de envio de e-mail, por chamada HTTP, a um endpoint interno do próprio serviço `api`, dispensando um worker dedicado. A fila SHALL usar `maxAttempts=1`, de modo que uma falha de envio não gere novas tentativas automáticas para o mesmo evento (US 5.2, Cenário 3).

#### Scenario: Enfileiramento e entrega ao endpoint interno
- **WHEN** o serviço `api` enfileira uma tarefa de e-mail
- **THEN** o Cloud Tasks entrega a tarefa via HTTP ao endpoint interno do serviço `api`, respeitando o limite de despacho por segundo configurado na fila

#### Scenario: Sem novas tentativas após falha de envio (US 5.2, Cenário 3)
- **WHEN** o endpoint interno tenta enviar o e-mail ao provedor SaaS e a entrega falha
- **THEN** a falha é registrada em log do sistema e a tarefa é confirmada (ACK), sem redespacho automático, pois a fila usa `maxAttempts=1`

### Requirement: Endpoint interno protegido por OIDC
O sistema SHALL expor o endpoint de processamento de tarefas apenas para chamadas autenticadas por token OIDC emitido pela `sa-tasks-invoker`, negando qualquer chamada não autenticada.

#### Scenario: Chamada autenticada pelo Cloud Tasks é aceita
- **WHEN** o Cloud Tasks invoca o endpoint interno com um token OIDC da `sa-tasks-invoker`
- **THEN** a requisição é aceita e a tarefa é processada

#### Scenario: Acesso negado — chamada sem token OIDC
- **WHEN** uma requisição é feita ao endpoint interno sem token OIDC válido da `sa-tasks-invoker`
- **THEN** a requisição é rejeitada com erro de autorização
