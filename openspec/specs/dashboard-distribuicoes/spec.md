# dashboard-distribuicoes

## Purpose

Gráficos de distribuição de processos ativos do Dashboard do Gestor (Épico 6,
US 6.2): agregação de processos **ativos** (Aberto ou Em Tramitação) por
unidade, por tipo de processo e por usuário autor, no escopo das unidades
geridas pelo Gestor — mesma base de cálculo e mesmo filtro `unidade_id` dos
KPIs (`dashboard-kpis`, US 6.1), com cenário de acesso negado explícito e
estado vazio. Escopo complementar aos KPIs, sem substituí-los.

## Requirements

### Requirement: Distribuição de processos ativos por dimensão (US 6.2)

O sistema SHALL expor ao Gestor autenticado a distribuição dos seus processos
**ativos** (status Aberto ou Em Tramitação) em três agregações — por unidade, por
tipo de processo e por usuário autor (`criado_por_id`) — restritas às unidades que
ele gere, sobre a mesma base de cálculo dos KPIs (US 6.1). Cada agregação SHALL
retornar, por grupo, um rótulo (nome da unidade / do tipo / do usuário) e a
quantidade de processos ativos, ordenada da maior para a menor quantidade.
Processos **sigilosos** SHALL ser contados normalmente para o Gestor, sem filtro
adicional. Essas distribuições SHALL conviver com os KPIs no Dashboard, sem
substituí-los.

#### Scenario: Gestor visualiza os três gráficos de distribuição

- **DADO** que estou autenticado como Gestor de unidades que possuem processos ativos
- **QUANDO** acesso o Dashboard
- **ENTÃO** visualizo, abaixo dos KPIs da US 6.1, três gráficos de barras
  horizontais: "Processos por Unidade", "Processos por Tipo" e "Processos por
  Usuário"
- **E** cada barra representa a contagem de processos ativos daquele grupo, no
  escopo das minhas unidades

#### Scenario: Contagem considera apenas processos ativos

- **DADO** um Gestor cujo escopo tem 5 processos ativos (Aberto + Em Tramitação),
  2 concluídos e 1 arquivado
- **QUANDO** as distribuições são calculadas
- **ENTÃO** apenas os 5 processos ativos SHALL ser contabilizados em qualquer das
  três agregações
- **E** os processos concluídos e arquivados NÃO SHALL aparecer em nenhuma barra

#### Scenario: Processos sigilosos entram na contagem do Gestor

- **DADO** um Gestor cujo escopo tem processos ativos, um deles sigiloso
- **QUANDO** as distribuições são calculadas
- **ENTÃO** o processo sigiloso SHALL ser contabilizado nas agregações por
  unidade, por tipo e por usuário, igual a qualquer outro processo ativo do escopo

#### Scenario: Agrupamento por usuário usa o autor do processo

- **DADO** um Gestor cujo escopo tem 5 processos ativos criados por "Ricardo Pita"
  e 2 criados por "Ana Souza"
- **QUANDO** o gráfico "Processos por Usuário" é calculado
- **ENTÃO** a agregação SHALL agrupar por `criado_por_id` (autor do processo),
  exibindo "Ricardo Pita" com 5 e "Ana Souza" com 2

### Requirement: Filtro por unidade gerenciada nas distribuições

As distribuições SHALL aceitar o mesmo parâmetro opcional `unidade_id` dos KPIs
(US 6.1 Cen.3). Sem o parâmetro, o cálculo SHALL considerar todas as unidades
geridas pelo Gestor; com o parâmetro, SHALL restringir a agregação à unidade
informada.

#### Scenario: Filtro restringe as distribuições a uma unidade

- **DADO** um Gestor de três unidades (COFIN, AJUR, DIRAD)
- **QUANDO** solicita as distribuições filtrando apenas a unidade COFIN
- **ENTÃO** as três agregações SHALL ser recalculadas considerando apenas os
  processos ativos da COFIN

### Requirement: Acesso negado a unidade fora do escopo do Gestor

Quando o `unidade_id` informado não pertencer às unidades geridas pelo Gestor
autenticado, o sistema SHALL negar o acesso com HTTP 403, SHALL registrar o
evento em `log_seguranca` como `acesso_negado`, e NÃO SHALL retornar dado algum
de distribuição.

#### Scenario: Gestor solicita distribuição de unidade que não gere

- **DADO** um Gestor que gere apenas a unidade COFIN
- **QUANDO** solicita as distribuições informando o `unidade_id` da unidade DIRAD
  (que ele não gere)
- **ENTÃO** o sistema SHALL responder HTTP 403
- **E** SHALL registrar um evento `acesso_negado` em `log_seguranca`
- **E** nenhum dado de contagem da DIRAD SHALL ser exposto

#### Scenario: Perfil sem gestão não acessa as distribuições

- **DADO** um usuário autenticado com perfil `servidor` (não Gestor)
- **QUANDO** tenta acessar o endpoint de distribuições do dashboard
- **ENTÃO** o acesso SHALL ser negado conforme o RBAC por perfil do dashboard,
  sem retornar dados

### Requirement: Estado vazio das distribuições

Quando não houver processos ativos no escopo (ou na unidade filtrada), cada
gráfico SHALL exibir a mensagem "Nenhum dado disponível para o período" em vez de
um gráfico vazio, coerente com o estado vazio dos KPIs (US 6.1 Cen.2).

#### Scenario: Gestor sem processos ativos

- **DADO** um Gestor de unidades que ainda não possuem processos ativos
- **QUANDO** acessa o Dashboard
- **ENTÃO** cada um dos três gráficos SHALL exibir "Nenhum dado disponível para o
  período" no lugar das barras
