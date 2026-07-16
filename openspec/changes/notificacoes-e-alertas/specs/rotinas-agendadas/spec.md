## ADDED Requirements

### Requirement: Rotina diária de verificação de prazos
O sistema SHALL executar, dentro do job diário de manutenção, uma rotina de verificação de
prazos que seleciona processos ativos (`status` em `Aberto`/`Em Tramitação`) cujo `prazo_em`
está a vencer dentro da janela de antecedência configurada e, para cada um, gera a
notificação interna `alerta_prazo` (capability `notificacoes-internas`) e enfileira o e-mail
de prazo (capability `alertas-email-processo`) aos servidores da unidade atual. A seleção
SHALL ser função do estado atual do banco, honrando o contrato de idempotência já definido
nesta capability. Ver PRD US 5.2 Cen.2 e US 5.4.

#### Scenario: Seleção por estado atual dentro da janela configurada
- **QUANDO** a rotina diária é executada
- **ENTÃO** ela seleciona os processos ativos com `prazo_em <= hoje + dias_antecedencia` (e
  ainda não vencidos/tratados), gerando alerta interno e enfileirando e-mail para os
  servidores da unidade atual de cada um

#### Scenario: Idempotência — reexecução no mesmo dia não duplica alerta
- **DADO** que a rotina já gerou o alerta de prazo de um processo para o `prazo_em` vigente
- **QUANDO** a rotina é executada novamente sobre o mesmo estado
- **ENTÃO** nenhum alerta interno ou e-mail duplicado é gerado para esse processo, pois a
  existência do alerta para o `prazo_em` vigente serve como guard

#### Scenario: Retomada após indisponibilidade cobre os prazos do período
- **DADO** que a rotina não pôde executar por um ou mais dias
- **QUANDO** ela é executada ao retornar à operação normal
- **ENTÃO** todos os processos cujo `prazo_em` entrou na janela durante a indisponibilidade
  recebem o alerta nesta execução, sem alertas duplicados para os já tratados

### Requirement: Rotina diária de expurgo de notificações lidas
O sistema SHALL executar, dentro do job diário de manutenção, uma rotina que remove
fisicamente as notificações **lidas** (`lida_em` preenchido) há mais de 30 dias, preservando
integralmente as notificações **não lidas**, qualquer que seja a sua idade. Ver PRD US 5.1
Cen.4/Cen.4b.

#### Scenario: Expurga notificações lidas há mais de 30 dias (US 5.1 Cen.4)
- **QUANDO** a rotina diária é executada
- **ENTÃO** toda notificação com `lida_em` anterior a 30 dias atrás é removida

#### Scenario: Notificações não lidas nunca são expurgadas (US 5.1 Cen.4b)
- **DADO** que existe uma notificação não lida gerada há mais de 30 dias
- **QUANDO** a rotina diária de expurgo é executada
- **ENTÃO** essa notificação é preservada; apenas notificações lidas há mais de 30 dias são
  removidas

### Requirement: Parâmetro configurável de antecedência de alerta de prazo
O sistema SHALL manter o parâmetro operacional "Dias de antecedência para alerta de prazo"
em `sistema_config` (singleton id=1), com valor padrão 2, editável em runtime **apenas** pelo
Administrador e lido pela rotina de verificação de prazos a cada execução — sem hardcode.
Ver PRD US 8.5 e a invariante "parâmetros operacionais são configuráveis em runtime".

#### Scenario: Administrador altera o parâmetro e a rotina passa a usá-lo
- **DADO** que o Administrador define "Dias de antecedência para alerta de prazo" como 5
- **QUANDO** a rotina diária de verificação de prazos é executada em seguida
- **ENTÃO** a janela de seleção passa a considerar processos com `prazo_em` a vencer em até 5
  dias corridos

#### Scenario: Valor padrão quando nunca configurado
- **DADO** que o parâmetro nunca foi alterado após a inicialização do sistema
- **QUANDO** a rotina de verificação de prazos é executada
- **ENTÃO** ela usa o valor padrão de 2 dias corridos

#### Scenario: Acesso negado — perfil não-Administrador não altera o parâmetro
- **DADO** que um usuário com perfil Servidor ou Gestor está autenticado
- **QUANDO** ele tenta alterar "Dias de antecedência para alerta de prazo"
- **ENTÃO** a operação é rejeitada com acesso negado e o parâmetro permanece inalterado
