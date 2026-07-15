# workflow-tramitacao

## Purpose

Máquina de estados do processo (Aberto → Em Tramitação → Concluído → Arquivado) e as ações que a movem — despacho e devolução — com histórico imutável de eventos (US 2.2, 2.2b, 2.4).

## Requirements

### Requirement: Máquina de estados do processo
O sistema SHALL modelar o status do processo como uma máquina de estados explícita — `Aberto → Em Tramitação → Concluído → Arquivado` — cujas transições ocorrem **exclusivamente por ação explícita** (Despachar, Concluir) ou pela rotina automática de arquivamento, nunca por campo de texto livre nem por manipulação direta (drag-and-drop) no Kanban. Ver PRD RF 10 e US 2.3. **Escopo deste change**: o estado `Arquivado` existe na máquina, mas a transição `Concluído → Arquivado` (rotina automática) é entregue em change posterior; aqui nenhum processo alcança `Arquivado`.

#### Scenario: Transições válidas por ação explícita
- **DADO** um processo com status "Aberto"
- **QUANDO** o Servidor aciona "Despachar" para a próxima unidade do roteiro
- **ENTÃO** o status transita para "Em Tramitação"; despachos subsequentes o mantêm em "Em Tramitação" até a última unidade, quando a ação de conclusão o transita para "Concluído"

#### Scenario: Transição de status inexistente por caminho não explícito — rejeitada
- **DADO** um processo em qualquer status
- **QUANDO** há tentativa de alterar o status por um meio que não seja uma ação explícita prevista (Despachar/Concluir) ou a rotina automática de arquivamento
- **ENTÃO** o sistema rejeita a alteração, pois o status é uma máquina de estados e não um campo editável livremente

### Requirement: Despacho para a próxima unidade do roteiro
O sistema SHALL permitir que o Servidor da unidade atual despache o processo para a próxima unidade do roteiro-snapshot, alterando o status para "Em Tramitação" e registrando o evento no histórico imutável; na última unidade do roteiro, a ação SHALL solicitar confirmação de conclusão e, se confirmada, alterar o status para "Concluído". Ver PRD US 2.2.

#### Scenario: Despacho para a próxima unidade do roteiro
- **DADO** que um processo do tipo "Licitação" está na unidade COFIN com status "Aberto" e seu roteiro define COFIN → AJUR → DIRAD
- **QUANDO** eu, Servidor da COFIN, aciono "Despachar"
- **ENTÃO** o sistema move o processo para a unidade AJUR, altera o status para "Em Tramitação" e registra data/hora e responsável no histórico (PRD US 2.2 Cen.1)

#### Scenario: Processo na última unidade do roteiro
- **DADO** que um processo está na última unidade prevista no roteiro
- **QUANDO** o Servidor aciona "Despachar"
- **ENTÃO** o sistema exibe "Este é o destino final do roteiro. Deseja concluir o processo?" e, ao confirmar, altera o status para "Concluído" (PRD US 2.2 Cen.2)

#### Scenario: Cancelamento da conclusão na última unidade
- **DADO** que um processo está na última unidade do roteiro
- **QUANDO** o Servidor aciona "Despachar" e, na confirmação, clica em "Cancelar"
- **ENTÃO** o processo permanece na unidade atual com o mesmo status, sem alteração no histórico (PRD US 2.2 Cen.3)

#### Scenario: Roteiro com unidade única
- **DADO** um processo de tipo cujo roteiro tem apenas uma unidade, criado nessa mesma unidade (status "Aberto")
- **QUANDO** o Servidor aciona "Despachar"
- **ENTÃO** o sistema exibe "Esta é a unidade de origem e destino final do roteiro. Deseja concluir o processo?" e, ao confirmar, altera o status para "Concluído" (PRD US 2.2 Cen.4)

#### Scenario: Servidor de outra unidade tenta despachar — acesso negado
- **DADO** que um processo está na unidade AJUR e estou autenticado como Servidor da unidade COFIN
- **QUANDO** tento despachar esse processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para esta unidade" e registra a tentativa em log de segurança (PRD US 1.4 Cen.2)

### Requirement: Devolução para a unidade anterior
O sistema SHALL permitir que o Servidor da unidade atual devolva o processo para a unidade imediatamente anterior do roteiro, mediante motivo predefinido obrigatório e justificativa opcional, registrando a devolução no histórico imutável; a devolução SHALL ser bloqueada quando o processo estiver na primeira unidade do roteiro. Ver PRD US 2.2b.

#### Scenario: Devolução para a unidade anterior
- **DADO** que um processo está na minha unidade e veio da unidade COFIN
- **QUANDO** aciono "Devolver", seleciono um motivo predefinido ("Documentação insuficiente", "Correção de dados" ou "Diligência complementar") e, opcionalmente, adiciono justificativa
- **ENTÃO** o processo retorna para a unidade COFIN com status "Em Tramitação" e a devolução é registrada no histórico com data/hora, responsável, motivo e justificativa (PRD US 2.2b Cen.1)

#### Scenario: Tentativa de devolução na primeira unidade do roteiro
- **DADO** que um processo está na primeira unidade do roteiro
- **QUANDO** o Servidor tenta acionar "Devolver"
- **ENTÃO** o sistema exibe "Não é possível devolver um processo que está na unidade de origem do roteiro" e a ação não é concluída (PRD US 2.2b Cen.2)

#### Scenario: Devolução sem seleção de motivo
- **DADO** que estou devolvendo um processo
- **QUANDO** tento confirmar a devolução sem selecionar um motivo
- **ENTÃO** o sistema exibe "Selecione um motivo para a devolução" e não conclui a ação (PRD US 2.2b Cen.3)

### Requirement: Histórico de tramitação imutável
O sistema SHALL registrar cada movimentação do processo (criação, despacho, devolução, conclusão) como um **evento imutável** (INSERT, nunca UPDATE ou DELETE), guardando unidade de origem, unidade de destino, responsável, data/hora e status resultante, e SHALL exibi-los como uma linha do tempo. Ver PRD US 2.4 e RF 25 (histórico imutável — invariante do projeto).

#### Scenario: Visualização do histórico
- **DADO** que um processo já passou por três unidades (COFIN → AJUR → DIRAD)
- **QUANDO** acesso a tela de detalhes do processo e clico em "Histórico"
- **ENTÃO** visualizo uma linha do tempo com cada movimentação, contendo unidade de origem, unidade de destino, responsável, data/hora e status naquele momento (PRD US 2.4 Cen.1)

#### Scenario: Histórico de processo recém-criado sem movimentações
- **DADO** que um processo foi criado mas ainda não foi despachado
- **QUANDO** acesso os detalhes do processo e clico em "Histórico"
- **ENTÃO** visualizo "Nenhuma movimentação registrada" e a data de criação como informação complementar (PRD US 2.4 Cen.2)

#### Scenario: Evento de tramitação é imutável
- **DADO** um evento de tramitação já registrado no histórico
- **QUANDO** qualquer fluxo do sistema processa uma nova movimentação do mesmo processo
- **ENTÃO** um novo evento é inserido, e o evento anterior permanece inalterado — nenhum evento de histórico é atualizado ou removido (RF 25; invariante de histórico imutável)
