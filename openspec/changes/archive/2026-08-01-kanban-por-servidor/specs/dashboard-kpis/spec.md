## ADDED Requirements

### Requirement: Cards de contagem de processos por status
O sistema SHALL exibir, no topo do dashboard, cinco cards de contagem sobre o escopo de unidades geridas: **Total** (soma de Abertos, Em Tramitação, Concluídos e Arquivados), **Abertos**, **Em Tramitação**, **Concluídos** e **Arquivados**. O Total SHALL ser derivado da soma das quatro parcelas exibidas, de modo que nunca discorde delas. As contagens SHALL respeitar o escopo de unidades geridas do Gestor e o filtro de unidade quando aplicado, e SHALL ser negadas a perfis sem permissão de dashboard.

#### Scenario: Cards refletem a distribuição por status
- **DADO** que as unidades que gerencio possuem 12 processos abertos, 30 em tramitação, 8 concluídos e 5 arquivados
- **QUANDO** acesso o dashboard
- **ENTÃO** vejo os cards com os valores 12, 30, 8 e 5, e o card "Total" exibindo 55

#### Scenario: Total é sempre a soma das parcelas
- **DADO** que o dashboard está carregado
- **QUANDO** comparo o valor do card "Total" com a soma dos demais cards
- **ENTÃO** os valores coincidem exatamente, sem divergência entre as contagens

#### Scenario: Contagens respeitam o filtro por unidade
- **DADO** que sou Gestor de três unidades e o dashboard exibe as contagens consolidadas
- **QUANDO** filtro por uma unidade específica
- **ENTÃO** os cinco cards passam a refletir apenas os processos dessa unidade

#### Scenario: Escopo vazio zera os cards
- **DADO** que sou Gestor de unidades sem nenhum processo
- **QUANDO** acesso o dashboard
- **ENTÃO** os cinco cards exibem zero, sem erro e sem estado quebrado

#### Scenario: Contagens de unidade não gerida — acesso negado
- **DADO** que sou Gestor das unidades COFIN e AJUR
- **QUANDO** tento obter as contagens filtrando pela unidade DIRAD, que não gerencio
- **ENTÃO** o sistema rejeita a requisição com acesso negado e registra a tentativa em log de segurança

#### Scenario: Servidor não acessa os cards de contagem — acesso negado
- **DADO** que estou autenticado com perfil Servidor
- **QUANDO** tento acessar o endpoint de contagens do dashboard
- **ENTÃO** o sistema rejeita a requisição com "Acesso negado — você não tem permissão para esta operação" e registra a tentativa em log de segurança
