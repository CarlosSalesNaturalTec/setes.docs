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
O sistema SHALL rejeitar a criação de um tipo de processo sem nenhuma unidade no
roteiro, SHALL rejeitar nomes de tipo de processo duplicados, e SHALL rejeitar a
inclusão de **unidades inativas** no roteiro — tanto na criação do tipo quanto no
versionamento do roteiro. A tela de montagem do roteiro SHALL oferecer apenas
unidades ativas como opção; a barreira efetiva, porém, é validada no backend.
Espelha o tratamento já adotado no cadastro de usuário ("Unidade inexistente ou
inativa"). Ver PRD US 8.2.

#### Scenario: Roteiro vazio rejeitado
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento criar um tipo de processo sem adicionar nenhuma unidade ao roteiro
- **ENTÃO** o sistema rejeita a operação exibindo "O roteiro deve conter ao menos uma unidade" (PRD US 8.2 Cen.3)

#### Scenario: Nome de tipo de processo duplicado
- **DADO** que já existe um tipo de processo chamado "Licitação"
- **QUANDO** tento criar outro tipo de processo com o mesmo nome
- **ENTÃO** o sistema rejeita a operação exibindo "Já existe um tipo de processo com este nome" (PRD US 8.2 Cen.4)

#### Scenario: Unidade inativa no roteiro rejeitada na criação
- **DADO** que estou autenticado como Administrador e a unidade COFIN está inativa
- **QUANDO** tento criar um tipo de processo incluindo a unidade COFIN no roteiro
- **ENTÃO** o sistema rejeita a operação exibindo "Unidade inválida no roteiro" e nenhum tipo de processo é criado

#### Scenario: Unidade inativa no roteiro rejeitada no versionamento
- **DADO** que estou autenticado como Administrador editando o roteiro de um tipo existente
- **QUANDO** tento salvar uma nova versão do roteiro incluindo uma unidade inativa
- **ENTÃO** o sistema rejeita a operação exibindo "Unidade inválida no roteiro" e o roteiro vigente é mantido

#### Scenario: Seletor de roteiro lista apenas unidades ativas
- **DADO** que estou autenticado como Administrador montando um roteiro
- **QUANDO** abro o seletor de "Adicionar unidade ao roteiro"
- **ENTÃO** apenas unidades ativas aparecem como opção

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

### Requirement: Prazo de anonimização LGPD configurável por tipo de processo
O sistema SHALL permitir que o Administrador configure, para cada tipo de processo, o
prazo legal de anonimização LGPD (em anos), usado pela rotina automática trimestral
(capability `anonimizacao-lgpd`) para determinar quando processos arquivados desse tipo
se tornam elegíveis para anonimização. O valor SHALL ser um número inteiro positivo, com
padrão de 5 anos quando não configurado, e a alteração SHALL se aplicar apenas a partir
da data da mudança, sem efeito retroativo sobre a contagem de processos já arquivados.
Ver PRD US 10.3 Cen.2.

#### Scenario: Configuração do prazo de anonimização de um tipo de processo
- **DADO** que estou autenticado como Administrador
- **QUANDO** acesso as configurações de um tipo de processo e defino o prazo de anonimização LGPD em 5 anos
- **ENTÃO** o sistema registra a configuração e exibe "Prazo de anonimização configurado: 5 anos. A partir desta data, processos deste tipo serão anonimizados após 5 anos de arquivamento." (PRD US 10.3 Cen.2)

#### Scenario: Valor padrão quando nunca configurado
- **DADO** que um tipo de processo nunca teve o prazo de anonimização LGPD alterado
- **QUANDO** a rotina trimestral de anonimização avalia processos arquivados desse tipo
- **ENTÃO** ela usa o valor padrão de 5 anos

#### Scenario: Valor inválido rejeitado
- **DADO** que estou autenticado como Administrador configurando o prazo de anonimização LGPD de um tipo de processo
- **QUANDO** informo um valor zero ou negativo
- **ENTÃO** o sistema rejeita a configuração exibindo que o valor deve ser um número inteiro positivo

#### Scenario: Acesso negado — perfil não-Administrador
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento configurar o prazo de anonimização LGPD de um tipo de processo
- **ENTÃO** a operação é rejeitada com acesso negado e o parâmetro permanece inalterado
