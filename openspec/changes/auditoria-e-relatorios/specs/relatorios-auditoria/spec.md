## ADDED Requirements

### Requirement: Relatório consolidado de tramitação em tela
O sistema SHALL disponibilizar a usuário com permissão de auditoria (`usuario.pode_auditar = true`) um relatório consolidado de tramitação, filtrável por **período**, **unidade** e **tipo de processo**, exibido **na própria interface**, contendo: total de processos no período, tempo médio de tramitação e a lista de processos com status atual e unidade atual. A exportação em arquivo (PDF/CSV) **NÃO** faz parte deste escopo — o PRD a define como versão futura. As agregações de total e tempo médio de tramitação reaproveitam a lógica já consolidada no serviço de dashboard, aplicada a escopo global (todas as unidades), não às unidades geridas por um Gestor. Ver PRD US 9.2 (Cen.1).

#### Scenario: Geração de relatório com filtros
- **DADO** que estou autenticado com `pode_auditar = true`
- **QUANDO** solicito um relatório filtrando por período, unidade ou tipo de processo
- **ENTÃO** o sistema exibe em tela um relatório consolidado contendo o total de processos no período, o tempo médio de tramitação e a lista de processos com status atual e unidade atual, sem oferecer exportação de arquivo (PRD US 9.2 Cen.1)

#### Scenario: Status do processo apresentado como estado da máquina de estados
- **DADO** um relatório consolidado gerado com resultados
- **QUANDO** a lista de processos é exibida
- **ENTÃO** o status de cada processo é um dos estados explícitos da máquina de estados (`Aberto`, `Em Tramitação`, `Concluído`, `Arquivado`), nunca texto livre

### Requirement: Relatório sem dados para os filtros informados
O sistema SHALL exibir a mensagem `"Nenhum dado encontrado para os filtros informados"` quando um relatório for solicitado com filtros que não retornam nenhum processo, em vez de uma lista vazia sem contexto. Ver PRD US 9.2 (Cen.2).

#### Scenario: Filtros sem resultados
- **DADO** que estou autenticado com permissão de auditoria
- **QUANDO** solicito um relatório com filtros de período, unidade ou tipo que não retornam nenhum processo
- **ENTÃO** o sistema exibe `"Nenhum dado encontrado para os filtros informados"` (PRD US 9.2 Cen.2)

### Requirement: Acesso ao relatório restrito a usuário com permissão de auditoria
O sistema SHALL restringir a geração do relatório consolidado a usuários com `pode_auditar = true`. Usuário autenticado sem permissão de auditoria que tente acessar a rota de relatório recebe acesso negado, registrado como linha imutável em `log_seguranca` (`tipo_evento = acesso_negado`).

#### Scenario: Usuário sem permissão de auditoria tenta gerar relatório
- **DADO** que estou autenticado sem permissão de auditoria (`pode_auditar = false`)
- **QUANDO** tento acessar a rota de relatório consolidado de auditoria
- **ENTÃO** o sistema nega o acesso, o relatório não é gerado e a tentativa é registrada em `log_seguranca` (`tipo_evento = acesso_negado`)
