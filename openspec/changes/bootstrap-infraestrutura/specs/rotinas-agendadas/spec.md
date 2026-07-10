## ADDED Requirements

### Requirement: Infraestrutura de rotinas agendadas via Scheduler e Cloud Run Jobs
O sistema SHALL provisionar a infraestrutura de rotinas automáticas usando Cloud Scheduler como gatilho e Cloud Run Jobs como executor, com uma `sa-scheduler` que apenas dispara os jobs e uma `sa-jobs` sem ingress público que os executa.

#### Scenario: Scheduler dispara o job na janela configurada
- **WHEN** o horário cron configurado é atingido
- **THEN** o Cloud Scheduler, usando a `sa-scheduler`, aciona a execução do Cloud Run Job correspondente

#### Scenario: Acesso negado — disparo de job por identidade não autorizada
- **WHEN** uma identidade sem permissão de execução tenta disparar um Cloud Run Job
- **THEN** a execução é negada, pois apenas a `sa-scheduler` possui o binding de execução no job

#### Scenario: Duas rotinas provisionadas
- **WHEN** a infraestrutura é aplicada
- **THEN** existem dois jobs agendados: um job diário de manutenção e um job trimestral de anonimização, cada um com gatilho, janela de execução e service account documentados

### Requirement: Contrato de idempotência e retomada das rotinas
O sistema SHALL garantir que toda rotina agendada seja idempotente por design — operando sobre o estado atual do banco, e não sobre o intervalo desde a última execução — de modo que execuções repetidas ou a retomada após indisponibilidade produzam o mesmo resultado, sem efeitos duplicados. Referência: US 2.5 (Cenário 4) e US 10.3.

#### Scenario: Retomada após execução perdida (US 2.5, Cenário 4)
- **WHEN** a rotina não pôde ser executada por um ou mais dias devido a indisponibilidade e depois é executada ao retornar à operação normal
- **THEN** todos os itens cujo critério de tempo expirou durante o período de indisponibilidade são processados nesta execução, sem perda de eventos

#### Scenario: Execução repetida não duplica efeito
- **WHEN** a rotina de arquivamento é executada mais de uma vez sobre o mesmo estado
- **THEN** um item já processado (ex.: processo já em estado "Arquivado") não é reprocessado nem gera evento duplicado no histórico de tramitação

#### Scenario: Guard de transição de estado
- **WHEN** o job seleciona os itens a processar
- **THEN** a seleção é uma função do estado atual (ex.: `status = 'Concluído' AND prazo_vigente <= now()`), e a transição de estado serve como guard contra reprocessamento
