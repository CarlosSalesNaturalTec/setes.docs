## ADDED Requirements

### Requirement: Edição do próprio nome pelo usuário autenticado
O sistema SHALL permitir que qualquer usuário autenticado altere o **próprio nome**
na tela "Meu Perfil", com edição livre limitada a 200 caracteres (conforme o
campo `nome` do modelo). O usuário NÃO pode alterar por auto-serviço o próprio
e-mail nem o próprio perfil — esses permanecem sob gestão do Administrador. A
alteração vale imediatamente em todas as telas e no cabeçalho de sessão. Ver
PRD US 1.5.

#### Scenario: Alteração do próprio nome com sucesso
- **DADO** que estou autenticado como Servidor com o nome "Maria Souza"
- **QUANDO** edito o meu nome em "Meu Perfil" para "Maria Souza Lima" e salvo
- **ENTÃO** o sistema persiste o novo nome, retorna o perfil atualizado e o novo nome passa a aparecer em "Meu Perfil" e no cabeçalho de sessão

#### Scenario: Nome vazio ou apenas espaços rejeitado
- **DADO** que estou autenticado
- **QUANDO** tento salvar o meu nome vazio ou contendo apenas espaços
- **ENTÃO** o sistema rejeita a alteração e mantém o nome anterior

#### Scenario: Nome acima do limite rejeitado
- **DADO** que estou autenticado
- **QUANDO** tento salvar um nome com mais de 200 caracteres
- **ENTÃO** o sistema rejeita a alteração com erro de validação e mantém o nome anterior

#### Scenario: Auto-serviço não altera e-mail nem perfil
- **DADO** que estou autenticado como Servidor
- **QUANDO** uso o endpoint de edição do próprio perfil
- **ENTÃO** somente o nome pode ser alterado; e-mail e perfil não são afetados por esta operação
