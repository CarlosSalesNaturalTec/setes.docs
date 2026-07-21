# quadro-kanban

## MODIFIED Requirements

### Requirement: Quadro Kanban da unidade (Servidor)
O sistema SHALL exibir ao Servidor um quadro Kanban **de visualização** (não manipulável por drag-and-drop) com as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo apenas os processos atualmente na sua unidade. Cada card SHALL exibir número, **tipo de processo**, assunto, **unidade atual por extenso** (nome completo, não sigla), **data de criação** ("Criado em dd/mm/aaaa hh:mm"), prazo e dias restantes, ordenados por prazo. Cada card SHALL expor o atributo `sigiloso`, e os processos sigilosos SHALL ser exibidos normalmente no Kanban da unidade com um indicador visual de "Sigiloso" (ícone de cadeado 🔒). Ver PRD US 2.3, US 2.6 (Cen.3) e US 1.4.

#### Scenario: Exibição do Kanban por colunas de status
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" com os cards dos processos da COFIN, cada card com número, tipo de processo, assunto, unidade atual por extenso, data de criação, prazo e dias restantes; os cards NÃO são arrastáveis — as transições ocorrem apenas por ações explícitas (PRD US 2.3 Cen.1)

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
- **ENTÃO** o card do processo sigiloso aparece normalmente na sua coluna de status, com o indicador visual de "Sigiloso" (ícone de cadeado 🔒); cards de processos não sigilosos não exibem esse indicador (PRD US 2.6 Cen.3)

### Requirement: Quadro Kanban consolidado (Gestor)
O sistema SHALL exibir ao Gestor um quadro Kanban consolidado com os processos de **todas as unidades que ele gerencia**, com número, tipo de processo, assunto, **nome da unidade atual por extenso**, **data de criação**, prazo e dias restantes em cada card, e a possibilidade de filtrar por unidade, sem exibir processos de unidades que ele não gerencia. Ver PRD US 2.8 e US 8.6b.

#### Scenario: Kanban multi-unidade
- **DADO** que estou autenticado como Gestor das unidades COFIN, AJUR e DIRAD
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo um Kanban consolidado com colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" contendo os cards das três unidades, cada card exibindo número, tipo de processo, assunto, unidade atual por extenso, data de criação, prazo e dias restantes (PRD US 2.8 Cen.1)

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

## ADDED Requirements

### Requirement: Alternância entre visualização Kanban e Lista
O sistema SHALL oferecer na tela de Processos um controle de alternância entre dois modos de visualização dos mesmos processos: **Kanban** (colunas por status) e **Lista** (linhas empilhadas). O modo Lista SHALL exibir cada processo como uma linha contendo número, tipo de processo, assunto, unidade atual por extenso, data de criação e o indicador de sigilo 🔒 quando aplicável, com a *pill* de status alinhada à direita. Ambos os modos SHALL respeitar exatamente o mesmo escopo de visibilidade por unidade/perfil do Kanban — a Lista NÃO SHALL ampliar o conjunto de processos visíveis. O modo padrão ao abrir a tela SHALL ser o Kanban.

#### Scenario: Alternar de Kanban para Lista
- **DADO** que estou na tela de Processos exibindo o Kanban
- **QUANDO** aciono o controle de visualização "Lista"
- **ENTÃO** os mesmos processos passam a ser exibidos como linhas empilhadas, cada linha com número, tipo, assunto, unidade por extenso, data de criação, indicador 🔒 quando sigiloso, e a *pill* de status à direita

#### Scenario: Alternar de Lista para Kanban
- **DADO** que estou na tela de Processos exibindo a Lista
- **QUANDO** aciono o controle de visualização "Kanban"
- **ENTÃO** os mesmos processos voltam a ser exibidos em colunas por status

#### Scenario: Lista respeita o escopo de unidade — acesso negado
- **DADO** que estou autenticado como Gestor das unidades COFIN e AJUR
- **QUANDO** alterno para o modo Lista
- **ENTÃO** a Lista exibe apenas processos de COFIN e AJUR, jamais processos da DIRAD (unidade que não gerencio), mantendo o mesmo escopo e a mesma rejeição de acesso do Kanban consolidado

### Requirement: Cores por coluna de status no Kanban
O sistema SHALL apresentar cada coluna do Kanban com uma cor associada ao seu status, de modo consistente e distinguível: "Aberto" em azul, "Em Tramitação" em âmbar, "Concluído" em verde e "Arquivado" em cinza. A cor SHALL ser um atributo de identidade visual da coluna (cabeçalho), sem alterar a máquina de estados nem a ordenação dos cards.

#### Scenario: Colunas exibidas com cor por status
- **DADO** que estou na tela de Processos no modo Kanban
- **QUANDO** o quadro é renderizado
- **ENTÃO** o cabeçalho da coluna "Aberto" é azul, "Em Tramitação" âmbar, "Concluído" verde e "Arquivado" cinza, cada um com o respectivo título e a contagem de cards da coluna

### Requirement: Contador de processos no cabeçalho
O sistema SHALL exibir no cabeçalho da tela de Processos um contador com o total de processos visíveis no escopo atual, no formato "{n} processo(s)", refletindo o número real de processos retornados.

#### Scenario: Contador reflete o total visível
- **DADO** que meu escopo possui 5 processos visíveis
- **QUANDO** acesso a tela de Processos
- **ENTÃO** o cabeçalho exibe "5 processo(s)"

#### Scenario: Contador com escopo vazio
- **DADO** que meu escopo não possui processos visíveis
- **QUANDO** acesso a tela de Processos
- **ENTÃO** o cabeçalho exibe "0 processo(s)" e as colunas/lista aparecem vazias com a mensagem correspondente
