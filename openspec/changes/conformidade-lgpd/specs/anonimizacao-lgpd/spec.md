## ADDED Requirements

### Requirement: Anonimização automática de processos arquivados após prazo legal
O sistema SHALL executar, trimestralmente, uma rotina que seleciona processos com status
`Arquivado` cujo prazo legal de anonimização — configurável por tipo de processo
(capability `tipos-processo-e-roteiros`) — já expirou desde a data de arquivamento, e
anonimiza os dados pessoais de todos os interessados vinculados ainda não anonimizados
(nome completo, CPF, CNPJ substituídos por identificadores anonimizados, sem
possibilidade técnica de recuperação do dado original), preservando número do processo,
datas, unidades, status e histórico de tramitação íntegros. O evento SHALL ser registrado
em log de conformidade. Ver PRD US 10.3.

#### Scenario: Anonimização automática após prazo legal
- **DADO** que um processo está arquivado há 5 anos e o prazo de anonimização configurado para seu tipo de processo é de 5 anos
- **QUANDO** a rotina trimestral de anonimização é executada
- **ENTÃO** todos os dados pessoais dos interessados desse processo (nome completo, CPF, CNPJ) são substituídos por identificadores anonimizados irreversíveis, mantendo-se o número do processo, datas, unidades, status e histórico de tramitação íntegros, e o evento é registrado em log de conformidade (PRD US 10.3 Cen.1)

#### Scenario: Processo arquivado dentro do prazo não é anonimizado
- **DADO** que um processo está arquivado há menos tempo do que o prazo de anonimização configurado para seu tipo de processo
- **QUANDO** a rotina trimestral de anonimização é executada
- **ENTÃO** o processo não é selecionado e seus interessados permanecem com os dados pessoais originais

#### Scenario: Idempotência — processo já anonimizado não é reprocessado
- **DADO** que todos os interessados de um processo arquivado já foram anonimizados em uma execução anterior da rotina
- **QUANDO** a rotina trimestral é executada novamente
- **ENTÃO** o processo não é reselecionado e nenhum evento duplicado de anonimização é registrado, pois a seleção é função do estado atual dos interessados (guard de transição)

#### Scenario: Retomada após execução perdida
- **DADO** que a rotina trimestral não pôde ser executada na janela programada por indisponibilidade do sistema
- **QUANDO** o sistema retorna à operação normal e a rotina é executada
- **ENTÃO** todos os processos cujo prazo de anonimização expirou durante o período de indisponibilidade são anonimizados nesta execução, sem perda de eventos

### Requirement: Serviço único de anonimização, compartilhado entre rotina e atendimento manual
O sistema SHALL centralizar a lógica de anonimização de interessado em um único serviço,
consumido tanto pela rotina trimestral automática (US 10.3) quanto pelo atendimento
manual de solicitação LGPD (capability `solicitacao-lgpd`, US 10.2), de modo que o
critério do que constitui "dado anonimizado" seja idêntico nos dois fluxos.

#### Scenario: Efeito idêntico entre anonimização manual e automática
- **DADO** um interessado de processo com nome e CPF cadastrados
- **QUANDO** ele é anonimizado tanto por atendimento manual de uma solicitação quanto pela rotina automática (em processos diferentes)
- **ENTÃO** em ambos os casos o nome é substituído por "Titular Anonimizado" e o documento por um identificador irreversível, com o mesmo formato e a mesma garantia de não reversibilidade
