# workflow-tramitacao

## MODIFIED Requirements

### Requirement: Histórico de tramitação imutável
O sistema SHALL registrar cada movimentação do processo (criação, despacho, devolução, conclusão, arquivamento automático, marcação de sigilo, remoção de sigilo) como um **evento imutável** (INSERT, nunca UPDATE ou DELETE), guardando unidade de origem, unidade de destino, responsável, data/hora e status resultante, e SHALL exibi-los como uma linha do tempo. Os eventos `marcar_sigilo` e `remover_sigilo` registram o responsável humano que agiu, têm unidade de origem/destino nulas (o sigilo não move o processo) e `status_resultante` igual ao status atual do processo (o sigilo não altera o status). Ver PRD US 2.4, US 2.6 e RF 25 (histórico imutável — invariante do projeto).

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
