## ADDED Requirements

### Requirement: Tipos de processo cadastrados apresentados em tabela

A tela de administração de tipos de processo SHALL apresentar os tipos já cadastrados
em **tabela**, com uma linha por tipo e colunas para o **nome**, o **prazo de
anonimização LGPD (em anos)** e a **ação de salvar** o prazo daquela linha. O
formulário de cadastro de novo tipo SHALL permanecer na mesma tela, acima da tabela.

A edição do prazo SHALL permanecer **inline, por linha e individual**: o valor de
cada linha é salvo isoladamente, e a mensagem de erro de uma linha SHALL ser exibida
junto dela, sem afetar as demais.

A reorganização é **exclusivamente de apresentação**. A tabela NÃO SHALL oferecer
ações que não existem hoje — edição de nome, desativação ou exclusão de tipo de
processo — nem sugerir sua disponibilidade. As regras de validação do prazo e a
restrição de acesso ao perfil Administrador permanecem inalteradas.

#### Scenario: Tipos cadastrados exibidos em tabela

- **DADO** que estou autenticado como Administrador e existem tipos de processo
  cadastrados
- **QUANDO** acesso a tela de tipos de processo
- **ENTÃO** vejo uma tabela com uma linha por tipo, exibindo o nome e o prazo de
  anonimização LGPD vigente de cada um
- **E** o formulário de cadastro de novo tipo permanece disponível na mesma tela

#### Scenario: Prazo salvo individualmente por linha

- **DADO** que a tabela exibe vários tipos de processo
- **QUANDO** altero o prazo de anonimização de um tipo e aciono a ação de salvar
  daquela linha
- **ENTÃO** apenas o prazo daquele tipo é persistido, e os prazos dos demais tipos
  permanecem inalterados

#### Scenario: Erro de uma linha não afeta as demais

- **DADO** que altero o prazo de um tipo para um valor inválido
- **QUANDO** aciono a ação de salvar daquela linha
- **ENTÃO** a mensagem de erro é exibida junto daquela linha, o prazo permanece
  inalterado
- **E** as demais linhas continuam exibindo seus valores e permanecem editáveis

#### Scenario: Tabela não oferece ações inexistentes

- **DADO** que estou na tela de tipos de processo
- **QUANDO** examino as ações disponíveis em cada linha
- **ENTÃO** a única ação é salvar o prazo de anonimização — não há edição de nome,
  desativação nem exclusão de tipo de processo

#### Scenario: Nenhum tipo cadastrado

- **DADO** que ainda não existe nenhum tipo de processo cadastrado
- **QUANDO** acesso a tela
- **ENTÃO** vejo uma indicação de que não há tipos cadastrados, em vez de uma tabela
  com corpo vazio sem explicação
- **E** o formulário de cadastro permanece disponível

#### Scenario: Acesso por não-Administrador continua negado

- **DADO** que estou autenticado como Servidor ou como Gestor
- **QUANDO** acesso a rota de administração de tipos de processo
- **ENTÃO** o acesso é negado exatamente como antes da reorganização, sem que a
  tabela ou o formulário sejam renderizados
