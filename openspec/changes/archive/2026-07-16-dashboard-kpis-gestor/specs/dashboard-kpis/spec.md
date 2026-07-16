# Spec Delta — dashboard-kpis (Épico 6, US 6.1)

Capability dona do dashboard de indicadores operacionais do Gestor: cálculo e
exposição dos KPIs, escopo de visibilidade por unidade gerida (com acesso
negado), drill-down dos KPIs clicáveis, estado vazio, e o parâmetro operacional
`dias_para_processo_parado`. Referencia PRD US 6.1 e US 8.5.

## ADDED Requirements

### Requirement: Dashboard de KPIs operacionais do Gestor
O sistema SHALL disponibilizar ao perfil **Gestor** um dashboard com os
indicadores operacionais das unidades que ele gerencia (via `unidade_gestor`),
calculados sobre os processos dessas unidades. Os indicadores SHALL ser:
(a) **total de processos ativos** — processos com status `Aberto` ou
`Em Tramitação`; (b) **tempo médio de tramitação** — média, em dias corridos,
do intervalo `criado_em → concluido_em`, considerando **apenas** processos
concluídos nos últimos 12 meses; (c) **quantidade de processos parados** —
processos ativos cuja última movimentação (evento mais recente em `tramitacao`)
ocorreu há **mais** que o parâmetro `dias_para_processo_parado` (dias corridos);
(d) **produtividade por unidade** — quantidade de processos concluídos no mês
corrente, agrupada por unidade; (e) **lista de processos com prazo vencido ou
próximo do vencimento** — processos ativos cujo `prazo_em` já venceu ou vence
dentro da janela de antecedência configurada (`dias_antecedencia_alerta_prazo`).
O cálculo SHALL considerar exclusivamente os processos das unidades geridas pelo
Gestor autenticado. Ver PRD US 6.1 Cen.1.

#### Scenario: Exibição do dashboard com indicadores
- **DADO** que estou autenticado como Gestor de ao menos uma unidade que possui processos
- **QUANDO** acesso o Dashboard
- **ENTÃO** o sistema retorna o total de processos ativos, o tempo médio de tramitação (dias corridos, criação→conclusão, apenas concluídos nos últimos 12 meses), a quantidade de processos parados (sem movimentação há mais que `dias_para_processo_parado`), a produtividade por unidade (concluídos no mês corrente) e a lista de processos com prazo vencido ou próximo do vencimento — todos restritos às unidades que gerencio (PRD US 6.1 Cen.1)

#### Scenario: Cada KPI computado apenas sobre unidades geridas
- **DADO** que sou Gestor da unidade COFIN e que existem processos na unidade AJUR (que não gerencio)
- **QUANDO** acesso o Dashboard
- **ENTÃO** nenhum processo da AJUR é incluído em qualquer KPI ou lista — todos os números refletem exclusivamente a COFIN

### Requirement: Estado vazio do dashboard
O sistema SHALL, quando as unidades geridas pelo Gestor não possuírem processos
que satisfaçam um indicador, retornar os KPIs correspondentes com **valor zero**
e sinalizar ausência de dados, para que a interface exiba a mensagem "Nenhum
dado disponível para o período" em cada seção sem dados. Ver PRD US 6.1 Cen.2.

#### Scenario: Dashboard sem dados (gestor recém-cadastrado)
- **DADO** que estou autenticado como Gestor de unidades que ainda não possuem processos
- **QUANDO** acesso o Dashboard
- **ENTÃO** os cards de KPI apresentam valor zero e cada seção sem dados é sinalizada para exibir "Nenhum dado disponível para o período" (PRD US 6.1 Cen.2)

### Requirement: Filtro por unidade gerida
O sistema SHALL permitir ao Gestor filtrar o dashboard por **uma** unidade
específica dentre as que gerencia, recalculando todos os KPIs e listas para
considerar apenas os processos daquela unidade. Sem filtro, o dashboard SHALL
consolidar todas as unidades geridas. Ver PRD US 6.1 Cen.3.

#### Scenario: Filtro por unidade gerenciada
- **DADO** que estou autenticado como Gestor de três unidades (COFIN, AJUR, DIRAD)
- **QUANDO** seleciono apenas a unidade COFIN no filtro do Dashboard
- **ENTÃO** todos os KPIs e listas são recalculados considerando apenas os processos da COFIN (PRD US 6.1 Cen.3)

### Requirement: Drill-down de "Processos Ativos" e "Processos Parados"
O sistema SHALL expor, para os KPIs **Total de Processos Ativos** e
**Processos Parados**, uma listagem detalhada dos processos que compõem cada
número, respeitando o mesmo escopo (unidades geridas e filtro de unidade
aplicado). A lista de **ativos** SHALL apresentar, por processo, número,
assunto, unidade atual e dias restantes até o prazo. A lista de **parados**
SHALL apresentar, por processo, número, assunto, unidade atual e dias parados
(dias corridos desde a última movimentação). Os KPIs **Tempo Médio de
Tramitação** e **Produtividade por Unidade** SHALL ser apenas informativos, sem
drill-down. Ver PRD US 6.1 Cen.4, Cen.5 e Cen.6.

#### Scenario: Drill-down a partir do KPI "Processos Parados"
- **DADO** que o KPI "Processos Parados" exibe o valor 7
- **QUANDO** aciono o drill-down desse KPI
- **ENTÃO** o sistema retorna a listagem dos 7 processos sem movimentação há mais que `dias_para_processo_parado`, com número, assunto, unidade atual e dias parados de cada um (PRD US 6.1 Cen.4)

#### Scenario: Drill-down a partir do KPI "Processos Ativos"
- **DADO** que o KPI "Total de Processos Ativos" exibe o valor 42
- **QUANDO** aciono o drill-down desse KPI
- **ENTÃO** o sistema retorna a listagem dos 42 processos ativos (Aberto + Em Tramitação), com número, assunto, unidade atual e dias restantes de cada um (PRD US 6.1 Cen.5)

#### Scenario: KPIs sem drill-down
- **DADO** que estou visualizando o dashboard
- **QUANDO** interajo com os cards "Tempo Médio de Tramitação" ou "Produtividade por Unidade"
- **ENTÃO** nenhuma ação de drill-down é disparada — apenas "Processos Ativos" e "Processos Parados" possuem listagem detalhada (PRD US 6.1 Cen.6)

### Requirement: Visibilidade restrita ao perfil Gestor e às unidades geridas
O sistema SHALL restringir o acesso ao dashboard e a seus drill-downs ao perfil
**Gestor**. Qualquer requisição de usuário sem perfil de Gestor, ou de Gestor
que filtre/consulte uma unidade que **não** gerencia, SHALL ser rejeitada por
falta de permissão e registrada como linha imutável em `log_seguranca`
(`tipo_evento = acesso_negado`). O caminho de rejeição é parte obrigatória do
requisito, não só o caminho feliz.

#### Scenario: Acesso negado — usuário não é Gestor
- **DADO** que estou autenticado com perfil que não é Gestor (ex.: Servidor)
- **QUANDO** requisito o dashboard ou um de seus drill-downs
- **ENTÃO** o sistema rejeita a operação por falta de permissão e grava uma linha imutável em `log_seguranca` com `tipo_evento = acesso_negado`

#### Scenario: Acesso negado — Gestor consulta unidade que não gerencia
- **DADO** que sou Gestor das unidades COFIN e AJUR
- **QUANDO** requisito o dashboard filtrando pela unidade DIRAD, que não gerencio
- **ENTÃO** o sistema rejeita a operação por falta de permissão e grava uma linha imutável em `log_seguranca` com `tipo_evento = acesso_negado`

### Requirement: Parâmetro "dias para processo parado" configurável
O sistema SHALL manter o limiar de "processo parado" (padrão: **7 dias
corridos**) como parâmetro operacional `dias_para_processo_parado` em
`sistema_config` (singleton id=1), configurável em runtime **apenas** pelo
Administrador, validado como número inteiro positivo. O valor vigente SHALL ser
lido em runtime pelo cálculo do KPP "Processos Parados" — nunca hardcoded. Esta
é mais uma fatia da US 8.5 (precedente: prazo de arquivamento); a tela de
"Configurações do Sistema" completa segue em change futuro. Ver PRD US 8.5
(linha 703) e US 6.1.

#### Scenario: Administrador configura o limiar de processo parado
- **DADO** que estou autenticado como Administrador
- **QUANDO** defino `dias_para_processo_parado` como um número inteiro positivo e salvo
- **ENTÃO** o sistema persiste o valor em `sistema_config` e o KPI "Processos Parados" passa a usá-lo no próximo cálculo

#### Scenario: Valor inválido é rejeitado
- **DADO** que estou autenticado como Administrador na configuração do limiar de processo parado
- **QUANDO** informo um valor não inteiro ou menor ou igual a zero e tento salvar
- **ENTÃO** o sistema exibe "O valor deve ser um número inteiro positivo" e não salva a configuração

#### Scenario: Acesso negado — não Administrador tenta configurar
- **DADO** que estou autenticado com perfil diferente de Administrador
- **QUANDO** tento alterar `dias_para_processo_parado`
- **ENTÃO** o sistema rejeita a operação por falta de permissão e registra a tentativa em `log_seguranca` com `tipo_evento = acesso_negado`
