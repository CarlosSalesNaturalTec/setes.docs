## ADDED Requirements

### Requirement: Execução de lógica de negócio pelo job trimestral de anonimização
O job `job-anonimizacao-lgpd`, cuja infraestrutura (gatilho, janela trimestral, service
account) já é provisionada pelo requisito "Infraestrutura de rotinas agendadas via
Scheduler e Cloud Run Jobs", SHALL executar um entrypoint próprio que aplica a lógica de
negócio da rotina de anonimização automática (capability `anonimizacao-lgpd`), e não mais
o entrypoint placeholder compartilhado com o job diário de manutenção.

#### Scenario: Disparo do job trimestral executa a anonimização real
- **QUANDO** o Cloud Scheduler aciona o job `job-anonimizacao-lgpd` na janela trimestral configurada
- **ENTÃO** o entrypoint dedicado do job seleciona e anonimiza os processos elegíveis conforme a capability `anonimizacao-lgpd`, honrando o contrato de idempotência já estabelecido nesta capability
