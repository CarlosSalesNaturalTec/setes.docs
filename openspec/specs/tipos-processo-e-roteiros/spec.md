# tipos-processo-e-roteiros

## Purpose

Cadastro de tipos de processo e definição do roteiro de tramitação (sequência ordenada de unidades administrativas), com versionamento por processo, validações e restrição de gestão ao perfil Administrador.

## Requirements

### Requirement: Definição de roteiro de tramitação
O sistema SHALL permitir que um Administrador crie um tipo de processo e defina seu roteiro de tramitação como uma sequência ordenada de unidades administrativas, obrigatória para todo processo criado com esse tipo. Ver PRD US 8.2.

#### Scenario: Definição de roteiro
- **DADO** que estou autenticado como Administrador
- **QUANDO** crio ou edito um tipo de processo e defino a sequência de unidades do roteiro
- **ENTÃO** todos os processos criados com esse tipo seguirão esse roteiro obrigatório, e as unidades de destino aparecerão como opções durante o despacho (PRD US 8.2 Cen.1)

### Requirement: Versionamento de roteiro
O sistema SHALL preservar, para cada processo já criado, o roteiro vigente no momento de sua criação, de modo que alterações posteriores no roteiro de um tipo de processo se apliquem apenas a processos criados a partir da alteração. Ver PRD US 8.2.

#### Scenario: Alteração de roteiro em uso
- **DADO** que existem processos em andamento do tipo "Licitação"
- **QUANDO** o Administrador altera o roteiro do tipo "Licitação"
- **ENTÃO** o novo roteiro se aplica apenas a processos criados após a alteração; processos em andamento mantêm o roteiro vigente no momento de sua criação (PRD US 8.2 Cen.2)

### Requirement: Validação de tipo de processo e roteiro
O sistema SHALL rejeitar a criação de um tipo de processo sem nenhuma unidade no roteiro, e SHALL rejeitar nomes de tipo de processo duplicados. Ver PRD US 8.2.

#### Scenario: Roteiro vazio rejeitado
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento criar um tipo de processo sem adicionar nenhuma unidade ao roteiro
- **ENTÃO** o sistema rejeita a operação exibindo "O roteiro deve conter ao menos uma unidade" (PRD US 8.2 Cen.3)

#### Scenario: Nome de tipo de processo duplicado
- **DADO** que já existe um tipo de processo chamado "Licitação"
- **QUANDO** tento criar outro tipo de processo com o mesmo nome
- **ENTÃO** o sistema rejeita a operação exibindo "Já existe um tipo de processo com este nome" (PRD US 8.2 Cen.4)

### Requirement: Gestão de tipos de processo restrita ao Administrador
O sistema SHALL restringir o cadastro, edição e definição de roteiro de tipos de processo ao perfil Administrador.

#### Scenario: Gestor tenta gerenciar tipo de processo — acesso negado
- **DADO** que estou autenticado como Gestor
- **QUANDO** tento criar, editar ou definir o roteiro de um tipo de processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar tipos de processo" e registra a tentativa em log de segurança

#### Scenario: Servidor tenta gerenciar tipo de processo — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento criar, editar ou definir o roteiro de um tipo de processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar tipos de processo" e registra a tentativa em log de segurança
