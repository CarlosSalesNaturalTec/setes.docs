# rotinas-agendadas

## Purpose

Infraestrutura de Cloud Scheduler + Cloud Run Jobs (diário e trimestral) e o contrato de idempotência/retomada exigido pela US 2.5 (Cenário 4) e US 10.3.

## Requirements

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

### Requirement: Rotina diária de verificação de prazos
O sistema SHALL executar, dentro do job diário de manutenção, uma rotina de verificação de
prazos que seleciona processos ativos (`status` em `Aberto`/`Em Tramitação`) cujo `prazo_em`
está a vencer dentro da janela de antecedência configurada e, para cada um, gera a
notificação interna `alerta_prazo` (capability `notificacoes-internas`) e enfileira o e-mail
de prazo (capability `alertas-email-processo`) aos servidores da unidade atual. A seleção
SHALL ser função do estado atual do banco, honrando o contrato de idempotência já definido
nesta capability. Ver PRD US 5.2 Cen.2 e US 5.4.

#### Scenario: Seleção por estado atual dentro da janela configurada
- **QUANDO** a rotina diária é executada
- **ENTÃO** ela seleciona os processos ativos com `prazo_em <= hoje + dias_antecedencia` (e
  ainda não vencidos/tratados), gerando alerta interno e enfileirando e-mail para os
  servidores da unidade atual de cada um

#### Scenario: Idempotência — reexecução no mesmo dia não duplica alerta
- **DADO** que a rotina já gerou o alerta de prazo de um processo para o `prazo_em` vigente
- **QUANDO** a rotina é executada novamente sobre o mesmo estado
- **ENTÃO** nenhum alerta interno ou e-mail duplicado é gerado para esse processo, pois a
  existência do alerta para o `prazo_em` vigente serve como guard

#### Scenario: Retomada após indisponibilidade cobre os prazos do período
- **DADO** que a rotina não pôde executar por um ou mais dias
- **QUANDO** ela é executada ao retornar à operação normal
- **ENTÃO** todos os processos cujo `prazo_em` entrou na janela durante a indisponibilidade
  recebem o alerta nesta execução, sem alertas duplicados para os já tratados

### Requirement: Rotina diária de expurgo de notificações lidas
O sistema SHALL executar, dentro do job diário de manutenção, uma rotina que remove
fisicamente as notificações **lidas** (`lida_em` preenchido) há mais de 30 dias, preservando
integralmente as notificações **não lidas**, qualquer que seja a sua idade. Ver PRD US 5.1
Cen.4/Cen.4b.

#### Scenario: Expurga notificações lidas há mais de 30 dias (US 5.1 Cen.4)
- **QUANDO** a rotina diária é executada
- **ENTÃO** toda notificação com `lida_em` anterior a 30 dias atrás é removida

#### Scenario: Notificações não lidas nunca são expurgadas (US 5.1 Cen.4b)
- **DADO** que existe uma notificação não lida gerada há mais de 30 dias
- **QUANDO** a rotina diária de expurgo é executada
- **ENTÃO** essa notificação é preservada; apenas notificações lidas há mais de 30 dias são
  removidas

### Requirement: Parâmetro configurável de antecedência de alerta de prazo
O sistema SHALL manter o parâmetro operacional "Dias de antecedência para alerta de prazo"
em `sistema_config` (singleton id=1), com valor padrão 2, editável em runtime **apenas** pelo
Administrador e lido pela rotina de verificação de prazos a cada execução — sem hardcode.
Ver PRD US 8.5 e a invariante "parâmetros operacionais são configuráveis em runtime".

#### Scenario: Administrador altera o parâmetro e a rotina passa a usá-lo
- **DADO** que o Administrador define "Dias de antecedência para alerta de prazo" como 5
- **QUANDO** a rotina diária de verificação de prazos é executada em seguida
- **ENTÃO** a janela de seleção passa a considerar processos com `prazo_em` a vencer em até 5
  dias corridos

#### Scenario: Valor padrão quando nunca configurado
- **DADO** que o parâmetro nunca foi alterado após a inicialização do sistema
- **QUANDO** a rotina de verificação de prazos é executada
- **ENTÃO** ela usa o valor padrão de 2 dias corridos

#### Scenario: Acesso negado — perfil não-Administrador não altera o parâmetro
- **DADO** que um usuário com perfil Servidor ou Gestor está autenticado
- **QUANDO** ele tenta alterar "Dias de antecedência para alerta de prazo"
- **ENTÃO** a operação é rejeitada com acesso negado e o parâmetro permanece inalterado

### Requirement: Execução de lógica de negócio pelo job trimestral de anonimização
O job `job-anonimizacao-lgpd`, cuja infraestrutura (gatilho, janela trimestral, service
account) já é provisionada pelo requisito "Infraestrutura de rotinas agendadas via
Scheduler e Cloud Run Jobs", SHALL executar um entrypoint próprio que aplica a lógica de
negócio da rotina de anonimização automática (capability `anonimizacao-lgpd`), e não mais
o entrypoint placeholder compartilhado com o job diário de manutenção.

#### Scenario: Disparo do job trimestral executa a anonimização real
- **QUANDO** o Cloud Scheduler aciona o job `job-anonimizacao-lgpd` na janela trimestral configurada
- **ENTÃO** o entrypoint dedicado do job seleciona e anonimiza os processos elegíveis conforme a capability `anonimizacao-lgpd`, honrando o contrato de idempotência já estabelecido nesta capability
