## ADDED Requirements

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
