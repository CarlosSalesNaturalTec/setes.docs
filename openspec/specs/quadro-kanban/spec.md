# quadro-kanban

## Purpose

Visualização Kanban por unidade (Servidor) e consolidada por unidades geridas (Gestor), com ordenação por prazo e filtro (US 2.3, 2.8).

## Requirements

### Requirement: Quadro Kanban da unidade (Servidor)
O sistema SHALL exibir ao Servidor um quadro Kanban **de visualização** (não manipulável por drag-and-drop) com as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo apenas os processos atualmente na sua unidade, com número, assunto, prazo e dias restantes em cada card, ordenados por prazo. Ver PRD US 2.3 e US 1.4.

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

### Requirement: Quadro Kanban consolidado (Gestor)
O sistema SHALL exibir ao Gestor um quadro Kanban consolidado com os processos de **todas as unidades que ele gerencia**, com o nome da unidade atual em cada card e a possibilidade de filtrar por unidade, sem exibir processos de unidades que ele não gerencia. Ver PRD US 2.8 e US 8.6b.

#### Scenario: Kanban multi-unidade
- **DADO** que estou autenticado como Gestor das unidades COFIN, AJUR e DIRAD
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo um Kanban consolidado com colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" contendo os cards das três unidades, cada card exibindo número, assunto, unidade atual, prazo e dias restantes (PRD US 2.8 Cen.1)

#### Scenario: Filtro por unidade no Kanban do Gestor
- **DADO** que estou visualizando o Kanban consolidado com processos de três unidades
- **QUANDO** seleciono uma unidade específica no filtro
- **ENTÃO** o Kanban passa a exibir apenas os processos da unidade selecionada (PRD US 2.8 Cen.2)

#### Scenario: Kanban consolidado vazio
- **DADO** que estou autenticado como Gestor de unidades sem processos
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas vazias com a mensagem "Nenhum processo encontrado nas unidades gerenciadas" (PRD US 2.8 Cen.3)

#### Scenario: Gestor não visualiza processos de unidade que não gerencia — acesso negado
- **DADO** que estou autenticado como Gestor das unidades COFIN e AJUR
- **QUANDO** o Kanban consolidado é montado ou tento filtrar/acessar processos da unidade DIRAD (que não gerencio)
- **ENTÃO** o sistema não inclui nem retorna processos da DIRAD; uma tentativa de acesso direto é rejeitada com "Acesso negado — você não tem permissão para esta unidade" e registrada em log de segurança (PRD US 1.4 Cen.2 adaptado ao Gestor)
