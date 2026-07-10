## ADDED Requirements

### Requirement: Cadastro de unidade administrativa
O sistema SHALL permitir que um Administrador cadastre unidades administrativas com nome, sigla e gestor responsável, disponibilizando-as para vinculação de usuários e composição de roteiros de tramitação. Ver PRD US 8.1.

#### Scenario: Cadastro de unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** cadastro uma nova unidade com nome, sigla e gestor responsável
- **ENTÃO** a unidade é criada como ativa e fica disponível para vinculação de usuários e para composição de roteiros (PRD US 8.1 Cen.1)

### Requirement: Edição de unidade administrativa
O sistema SHALL permitir a edição de nome, sigla e gestor responsável de uma unidade existente, aplicando a alteração imediatamente sem afetar processos já concluídos ou em andamento. Ver PRD US 8.1.

#### Scenario: Edição de unidade existente
- **DADO** que estou autenticado como Administrador e a unidade COFIN já existe
- **QUANDO** altero o nome, sigla ou gestor responsável da unidade COFIN
- **ENTÃO** as alterações são salvas e passam a valer imediatamente em todas as telas e relatórios (PRD US 8.1 Cen.2)

### Requirement: Desativação de unidade administrativa
O sistema SHALL impedir a desativação de uma unidade que possua processos em andamento, e SHALL, ao desativar uma unidade sem pendências, desvincular automaticamente seus usuários e removê-la das opções de novos roteiros, preservando seu histórico. Ver PRD US 8.1. **Nota de escopo**: a contagem de processos em andamento depende da entidade `processo` (Épico 2, ainda inexistente); nesta implementação a contagem é sempre zero, portanto o Cenário de bloqueio abaixo descreve o contrato a ser honrado quando `processo` existir, mas não é observável neste change.

#### Scenario: Desativação bloqueada com processos pendentes
- **DADO** que a unidade COFIN possui processos em andamento
- **QUANDO** o Administrador tenta desativar a unidade COFIN
- **ENTÃO** o sistema rejeita a operação informando a quantidade de processos pendentes e orienta a redistribuí-los ou concluí-los antes (PRD US 8.1 Cen.3)

#### Scenario: Desativação sem processos pendentes
- **DADO** que a unidade COFIN não possui processos em andamento
- **QUANDO** o Administrador desativa a unidade COFIN
- **ENTÃO** a unidade é marcada como inativa, seus usuários vinculados são automaticamente desvinculados (perdendo acesso até serem realocados), a unidade deixa de ser opção em novos roteiros, mas permanece no histórico de processos já tramitados (PRD US 8.1 Cen.4)

### Requirement: Gestão de unidades restrita ao Administrador
O sistema SHALL restringir o cadastro, edição e desativação de unidades administrativas ao perfil Administrador.

#### Scenario: Gestor tenta cadastrar unidade — acesso negado
- **DADO** que estou autenticado como Gestor
- **QUANDO** tento cadastrar, editar ou desativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança

#### Scenario: Servidor tenta cadastrar unidade — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento cadastrar, editar ou desativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança
