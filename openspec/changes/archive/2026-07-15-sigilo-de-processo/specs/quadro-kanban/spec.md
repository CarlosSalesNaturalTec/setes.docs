# quadro-kanban

## MODIFIED Requirements

### Requirement: Quadro Kanban da unidade (Servidor)
O sistema SHALL exibir ao Servidor um quadro Kanban **de visualização** (não manipulável por drag-and-drop) com as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo apenas os processos atualmente na sua unidade, com número, assunto, prazo e dias restantes em cada card, ordenados por prazo. Cada card SHALL expor o atributo `sigiloso`, e os processos sigilosos SHALL ser exibidos normalmente no Kanban da unidade com um indicador visual de "Sigiloso" (ícone de cadeado ou tarja). Ver PRD US 2.3, US 2.6 (Cen.3) e US 1.4.

#### Scenario: Exibição do Kanban por colunas de status
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" com os cards dos processos da COFIN, cada card com número, assunto, prazo e dias restantes; os cards NÃO são arrastáveis — as transições ocorrem apenas por ações explícitas (PRD US 2.3 Cen.1)

#### Scenario: Ordenação dos cards por prazo com destaque de vencidos
- **DADO** que minha unidade possui múltiplos processos em uma mesma coluna
- **QUANDO** visualizo o Kanban
- **ENTÃO** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos vencidos aparecem no topo com destaque visual: dias vencidos em vermelho com ícone de prazo, texto em negrito e barra vermelha de 4px na borda esquerda do card (PRD US 2.3 Cen.4)

#### Scenario: Novo processo despachado aparece após atualização
- **DADO** que um processo foi despachado para minha unidade por outra unidade
- **QUANDO** eu aciono o botão "Atualizar" do Kanban ou navego para outra tela e retorno
- **ENTÃO** o novo processo aparece na coluna "Aberto" da minha unidade (PRD US 2.3 Cen.2). **Nota de escopo**: o incremento do indicador de notificações citado no PRD US 2.3 Cen.2 depende de notificações internas (Épico 5) e não faz parte deste change.

#### Scenario: Kanban vazio
- **DADO** que estou autenticado como Servidor de uma unidade sem processos
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas vazias com a mensagem "Nenhum processo encontrado nesta unidade" (PRD US 2.3 Cen.3)

#### Scenario: Card de processo sigiloso com indicador
- **DADO** que a minha unidade possui um processo marcado como sigiloso
- **QUANDO** visualizo o Kanban da unidade
- **ENTÃO** o card do processo sigiloso aparece normalmente na sua coluna de status, com um indicador visual de "Sigiloso" (ícone de cadeado ou tarja); cards de processos não sigilosos não exibem esse indicador (PRD US 2.6 Cen.3)
