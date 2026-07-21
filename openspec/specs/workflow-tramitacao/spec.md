# workflow-tramitacao

## Purpose

Máquina de estados do processo (Aberto → Em Tramitação → Concluído → Arquivado) e as ações que a movem — despacho e devolução — com histórico imutável de eventos (US 2.2, 2.2b, 2.4).

## Requirements

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
O sistema SHALL registrar cada movimentação do processo (criação, despacho, devolução, conclusão, arquivamento automático, marcação de sigilo, remoção de sigilo, remoção de documento, restauração de documento) como um **evento imutável** (INSERT, nunca UPDATE ou DELETE), guardando unidade de origem, unidade de destino, responsável, data/hora e status resultante, e SHALL exibi-los como uma linha do tempo. Os eventos `marcar_sigilo` e `remover_sigilo` registram o responsável humano que agiu, têm unidade de origem/destino nulas (o sigilo não move o processo) e `status_resultante` igual ao status atual do processo (o sigilo não altera o status). Os eventos `remover_documento` e `restaurar_documento` registram o responsável humano que agiu sobre o anexo (o Administrador, no caso da restauração), têm unidade de origem/destino nulas (não movem o processo) e `status_resultante` igual ao status atual do processo (não alteram o status). Ver PRD US 2.4, US 2.6, US 3.1, US 8.7 e RF 25 (histórico imutável — invariante do projeto).

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

#### Scenario: Marcação e remoção de sigilo geram eventos imutáveis
- **DADO** um processo cujo sigilo é marcado e depois removido por usuários autorizados
- **QUANDO** acesso o histórico do processo
- **ENTÃO** visualizo um evento `marcar_sigilo` e um evento `remover_sigilo`, cada um com responsável e data/hora, sem unidade de origem/destino e com o status do processo naquele momento; ambos são imutáveis e não alteram o status do processo (PRD US 2.6 Cen.1/2)

#### Scenario: Remoção de documento gera evento imutável
- **DADO** que um documento é removido (soft-delete) de um processo por um usuário autorizado
- **QUANDO** acesso o histórico do processo
- **ENTÃO** visualizo um evento `remover_documento` com responsável e data/hora, sem unidade de origem/destino e com o status atual do processo; o evento é imutável e não altera o status do processo (PRD US 3.1 Cen.3)

#### Scenario: Restauração de documento gera evento imutável
- **DADO** que um documento removido é restaurado por um Administrador dentro do período de retenção
- **QUANDO** acesso o histórico do processo
- **ENTÃO** visualizo um evento `restaurar_documento` com o Administrador responsável e data/hora, sem unidade de origem/destino e com o status atual do processo; o evento é imutável e não altera o status do processo (PRD US 8.7 Cen.1)

### Requirement: Feedback ao Servidor após despacho ou devolução bem-sucedidos

Após um despacho (US 2.2) ou devolução (US 2.2b) concluído com sucesso, o cliente SHALL comunicar o resultado ao Servidor a partir da **resposta da própria ação** (a `ProcessoResponse` retornada), sem re-buscar o processo com uma leitura subsequente. O cliente SHALL inferir se o processo saiu do escopo da unidade comparando o `unidade_atual_id` que estava em tela (antes da ação) com o `unidade_atual_id` retornado pela resposta:

- Se o `unidade_atual_id` **mudou**, o processo saiu do escopo do Servidor de
  origem — o cliente SHALL exibir uma confirmação de **sucesso** nomeando a
  unidade de destino e navegar para o Kanban (`/processos`), e NÃO SHALL disparar
  uma releitura do detalhe do processo (que retornaria 403 por o processo já não
  pertencer ao escopo da unidade).
- Se o `unidade_atual_id` **não mudou** (ex.: conclusão na própria unidade, com
  status resultante "Concluído", ou roteiro de unidade única), o cliente SHALL
  permanecer na tela de detalhes, atualizando o processo exibido com a resposta e
  recarregando o histórico.

Em nenhuma hipótese uma ação de despacho ou devolução concluída com sucesso SHALL
ser apresentada ao Servidor como erro de acesso ("Acesso negado — você não tem
permissão para visualizar este processo"). Esta é uma correção de feedback no
cliente; a autorização por unidade do backend (negar leitura de processo fora do
escopo, PRD US 1.4 Cen.2) permanece inalterada.

#### Scenario: Despacho para a próxima unidade — sucesso, sem falso erro de acesso
- **DADO** que sou Servidor da unidade COFIN e o processo 2026/000007 está na COFIN, com o roteiro COFIN → AJUR → DIRAD
- **QUANDO** aciono "Despachar" e a ação é concluída (o processo passa a `unidade_atual_id` = AJUR, status "Em Tramitação")
- **ENTÃO** o cliente exibe uma confirmação de sucesso informando que o processo foi despachado para a unidade AJUR e me leva ao Kanban, sem exibir "Acesso negado — você não tem permissão para visualizar este processo" e sem re-buscar o detalhe do processo

#### Scenario: Devolução para a unidade anterior — sucesso, sem falso erro de acesso
- **DADO** que sou Servidor da unidade AJUR, o processo está na AJUR e veio da COFIN
- **QUANDO** aciono "Devolver", seleciono um motivo e confirmo, e a ação é concluída (o processo volta para `unidade_atual_id` = COFIN, status "Em Tramitação")
- **ENTÃO** o cliente exibe uma confirmação de sucesso informando que o processo foi devolvido para a unidade COFIN e me leva ao Kanban, sem exibir mensagem de acesso negado e sem re-buscar o detalhe do processo

#### Scenario: Conclusão na própria unidade — permanece na tela de detalhes
- **DADO** que sou Servidor da unidade atual e o processo está na última unidade do roteiro
- **QUANDO** aciono "Despachar", confirmo a conclusão e a ação é concluída (o processo permanece com o mesmo `unidade_atual_id` e passa a status "Concluído")
- **ENTÃO** o cliente permanece na tela de detalhes do processo, atualiza o status exibido para "Concluído" e recarrega o histórico, sem navegar para o Kanban e sem erro de acesso

#### Scenario: Cancelamento da conclusão — nenhuma navegação nem mensagem de sucesso
- **DADO** que o processo está na última unidade do roteiro e o backend respondeu pedindo confirmação de conclusão
- **QUANDO** clico em "Cancelar" no modal de confirmação
- **ENTÃO** o processo permanece na tela de detalhes com o mesmo status, sem navegação para o Kanban, sem confirmação de sucesso e sem alteração no histórico (PRD US 2.2 Cen.3)

#### Scenario: Falha real do despacho — erro exibido, sem navegação
- **DADO** que sou Servidor da unidade atual e aciono "Despachar"
- **QUANDO** o backend rejeita a ação com um erro real (ex.: 403 de autorização por unidade, ou outra falha da própria chamada de despacho)
- **ENTÃO** o cliente exibe a mensagem de erro correspondente e permanece na tela de detalhes, sem navegar para o Kanban e sem confirmação de sucesso
