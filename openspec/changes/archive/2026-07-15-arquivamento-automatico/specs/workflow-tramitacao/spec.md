# workflow-tramitacao

## MODIFIED Requirements

### Requirement: Máquina de estados do processo
O sistema SHALL modelar o status do processo como uma máquina de estados explícita — `Aberto → Em Tramitação → Concluído → Arquivado` — cujas transições ocorrem **exclusivamente por ação explícita** (Despachar, Concluir) ou pela rotina automática de arquivamento, nunca por campo de texto livre nem por manipulação direta (drag-and-drop) no Kanban. A transição `Concluído → Arquivado` é realizada **apenas** pela rotina automática de arquivamento (capability `arquivamento-automatico`), nunca por ação de usuário. Ver PRD RF 10, US 2.3 e US 2.5.

#### Scenario: Transições válidas por ação explícita
- **DADO** um processo com status "Aberto"
- **QUANDO** o Servidor aciona "Despachar" para a próxima unidade do roteiro
- **ENTÃO** o status transita para "Em Tramitação"; despachos subsequentes o mantêm em "Em Tramitação" até a última unidade, quando a ação de conclusão o transita para "Concluído"

#### Scenario: Transição Concluído → Arquivado apenas pela rotina automática
- **DADO** um processo com status "Concluído" cujo prazo de arquivamento já expirou
- **QUANDO** a rotina automática de arquivamento é executada
- **ENTÃO** o status transita para "Arquivado" e um evento imutável de arquivamento é registrado no histórico; essa transição não é acionável por nenhuma ação de usuário

#### Scenario: Transição de status inexistente por caminho não explícito — rejeitada
- **DADO** um processo em qualquer status
- **QUANDO** há tentativa de alterar o status por um meio que não seja uma ação explícita prevista (Despachar/Concluir) ou a rotina automática de arquivamento
- **ENTÃO** o sistema rejeita a alteração, pois o status é uma máquina de estados e não um campo editável livremente
