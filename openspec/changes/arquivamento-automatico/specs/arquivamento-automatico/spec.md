# arquivamento-automatico

## ADDED Requirements

### Requirement: Arquivamento automático de processos concluídos
O sistema SHALL executar uma rotina diária que seleciona os processos com status "Concluído" cujo prazo de arquivamento (congelado na conclusão) já expirou e os transiciona para "Arquivado", registrando um evento imutável de arquivamento no histórico de cada processo. A seleção é **função do estado atual** (`status = 'concluido' AND arquivar_em <= now()`), nunca do intervalo desde a última execução. Ver PRD US 2.5.

#### Scenario: Arquivamento automático por tempo
- **DADO** que um processo foi concluído há 30 dias e o prazo de arquivamento vigente na conclusão era de 30 dias
- **QUANDO** a rotina diária de arquivamento é executada
- **ENTÃO** o processo é movido do status "Concluído" para "Arquivado" e o evento é registrado no histórico do processo (PRD US 2.5 Cen.1)

#### Scenario: Arquivamento em lote com evento individual por processo
- **DADO** que múltiplos processos concluídos já ultrapassaram seu prazo de arquivamento
- **QUANDO** a rotina diária é executada
- **ENTÃO** todos são movidos para "Arquivado" em uma execução, e cada movimentação é registrada individualmente no histórico do respectivo processo (PRD US 2.5 Cen.3)

#### Scenario: Execução repetida não duplica efeito
- **DADO** que a rotina de arquivamento já processou um conjunto de processos vencidos
- **QUANDO** a rotina é executada novamente sobre o mesmo estado do banco
- **ENTÃO** nenhum processo já "Arquivado" é reprocessado nem gera evento de histórico duplicado, pois a transição de estado é o guard contra reprocessamento (spec `rotinas-agendadas`)

#### Scenario: Retomada após execução perdida por indisponibilidade
- **DADO** que a rotina não pôde ser executada por um ou mais dias por indisponibilidade do sistema
- **QUANDO** o sistema retorna à operação normal e a rotina é executada
- **ENTÃO** todos os processos cujo prazo de arquivamento expirou durante o período de indisponibilidade são arquivados nesta execução, sem perda de eventos de arquivamento (PRD US 2.5 Cen.4)

### Requirement: Congelamento do prazo de arquivamento na conclusão
O sistema SHALL, no momento em que um processo é concluído, congelar o instante a partir do qual ele poderá ser arquivado (`arquivar_em = concluido_em + prazo de arquivamento vigente`), gravando-o no próprio processo. Alterações posteriores do prazo de arquivamento global NÃO SHALL afetar processos já concluídos — a não-retroatividade é garantida pelo congelamento. Ver PRD US 2.5 Cen.2.

#### Scenario: Alteração do prazo não afeta processos já concluídos
- **DADO** que existem 10 processos concluídos há 25 dias com prazo de arquivamento de 30 dias congelado na conclusão, e o Administrador altera o prazo global de 30 para 15 dias
- **QUANDO** a rotina diária de arquivamento é executada
- **ENTÃO** nenhum dos 10 processos é arquivado nesta execução, pois todos mantêm o prazo de 30 dias vigente no momento de suas conclusões; o novo prazo de 15 dias aplica-se apenas a processos concluídos a partir da alteração (PRD US 2.5 Cen.2)

#### Scenario: Prazo congelado como instante absoluto na conclusão
- **DADO** que um processo é concluído em uma data específica com prazo de arquivamento vigente de N dias
- **QUANDO** a conclusão é registrada
- **ENTÃO** o sistema grava no processo o instante `arquivar_em = data de conclusão + N dias`, e a rotina de arquivamento passa a comparar esse instante congelado com o momento atual

### Requirement: Prazo de arquivamento configurável
O sistema SHALL manter o prazo de arquivamento de processos concluídos (padrão: 30 dias) como parâmetro operacional configurável em runtime pelo Administrador, validado como número inteiro positivo, aplicando-se apenas a conclusões futuras. **Nota de escopo**: este é o único parâmetro operacional entregue aqui (fatia mínima da US 8.5); os demais parâmetros e a tela de "Configurações do Sistema" completa ficam para change futuro. Ver PRD US 8.5.

#### Scenario: Configuração do prazo de arquivamento
- **DADO** que estou autenticado como Administrador
- **QUANDO** altero o prazo de arquivamento de 30 para 60 dias
- **ENTÃO** o novo prazo é salvo e passa a valer apenas para processos concluídos a partir desta data; processos já concluídos mantêm o prazo vigente no momento da conclusão (PRD US 8.5 Cen.1)

#### Scenario: Valor inválido rejeitado
- **DADO** que estou autenticado como Administrador na configuração do prazo de arquivamento
- **QUANDO** informo um valor negativo, zero ou não inteiro
- **ENTÃO** o sistema exibe "O valor deve ser um número inteiro positivo" e não salva a configuração (PRD US 8.5 Cen.3)

#### Scenario: Acesso negado — não Administrador tenta configurar
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento alterar o prazo de arquivamento
- **ENTÃO** o sistema rejeita a operação por falta de permissão e registra a tentativa em log de segurança
