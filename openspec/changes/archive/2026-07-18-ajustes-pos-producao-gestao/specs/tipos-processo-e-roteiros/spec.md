## MODIFIED Requirements

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
