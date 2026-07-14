# gestao-usuarios

## Purpose

Cadastro de usuários por Administrador (qualquer unidade/perfil) e por Gestor (escopo restrito), vínculo de Servidor a exatamente uma unidade e definição das unidades geridas por um Gestor.

## Requirements

### Requirement: Cadastro de usuário por Administrador
O sistema SHALL permitir que um Administrador cadastre novos usuários em qualquer unidade, com qualquer perfil (Servidor, Gestor ou Administrador), disparando o envio de link de primeiro acesso. Ver PRD US 1.1.

#### Scenario: Cadastro de servidor com sucesso
- **DADO** que estou autenticado como Administrador
- **QUANDO** preencho nome, e-mail, unidade e perfil e confirmo o cadastro
- **ENTÃO** o novo usuário é criado com status "Ativo — pendente de primeiro acesso" e um e-mail com link de primeiro acesso (validade 48h) é enviado (PRD US 1.1 Cen.1, Cen.1a)

#### Scenario: E-mail duplicado
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com um e-mail já em uso
- **ENTÃO** o sistema rejeita o cadastro exibindo "E-mail já cadastrado no sistema" (PRD US 1.1 Cen.2)

#### Scenario: E-mail com formato inválido
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com e-mail em formato inválido
- **ENTÃO** o sistema rejeita o cadastro exibindo "Formato de e-mail inválido" (PRD US 1.1 Cen.3)

#### Scenario: Nome vazio ou apenas espaços
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com o campo nome vazio ou só espaços
- **ENTÃO** o sistema rejeita o cadastro exibindo "Nome é obrigatório" (PRD US 1.1 Cen.4)

#### Scenario: Unidade inexistente ou inativa
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário vinculado a uma unidade que não existe ou está desativada
- **ENTÃO** o sistema rejeita o cadastro exibindo "Unidade inválida ou inativa" (PRD US 1.1 Cen.5)

### Requirement: Cadastro de usuário por Gestor com escopo restrito
O sistema SHALL permitir que um Gestor cadastre usuários com perfil Servidor apenas nas unidades que gerencia, e SHALL negar o cadastro em unidades não geridas ou com perfil privilegiado. Ver PRD US 1.2.

#### Scenario: Cadastro na unidade gerenciada
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** cadastro um novo usuário vinculado à COFIN com perfil de Servidor
- **ENTÃO** o cadastro é realizado com sucesso (PRD US 1.2 Cen.1)

#### Scenario: Tentativa de cadastro em unidade não gerenciada — acesso negado
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** tento cadastrar um usuário vinculado a uma unidade que não gerencio
- **ENTÃO** o sistema rejeita a operação exibindo "Você não tem permissão para cadastrar usuários nesta unidade" (PRD US 1.2 Cen.2)

#### Scenario: Tentativa de cadastro com perfil privilegiado — acesso negado
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** tento cadastrar um usuário com perfil de Gestor ou Administrador
- **ENTÃO** o sistema rejeita a operação exibindo que apenas o Administrador pode atribuir esses perfis (PRD US 1.2 Cen.3)

### Requirement: Vínculo de Servidor a exatamente uma unidade
O sistema SHALL manter, para cada usuário com perfil Servidor, o vínculo com exatamente uma unidade por vez, substituindo o vínculo anterior em caso de transferência. Ver PRD US 8.6.

#### Scenario: Transferência de servidor entre unidades
- **DADO** que o servidor João está vinculado à unidade COFIN
- **QUANDO** o Administrador altera a unidade de João para AJUR
- **ENTÃO** o vínculo com COFIN é removido, o vínculo com AJUR é estabelecido, e João passa a enxergar apenas dados da unidade AJUR, mantendo seu histórico de atuação na COFIN (PRD US 8.6 Cen.1)

#### Scenario: Tentativa de vínculo duplo como Servidor
- **DADO** que o servidor João já está vinculado à unidade COFIN
- **QUANDO** o Administrador tenta também vinculá-lo à unidade AJUR mantendo o perfil de Servidor
- **ENTÃO** o sistema rejeita a operação exibindo que Servidores só podem estar vinculados a uma unidade por vez (PRD US 8.6 Cen.2)

### Requirement: Unidades geridas por Gestor
O sistema SHALL permitir que um Administrador defina uma ou mais unidades geridas por um usuário com perfil Gestor. Ver PRD US 8.6b.

#### Scenario: Vinculação de Gestor a múltiplas unidades
- **DADO** que o usuário Maria possui perfil de Gestor
- **QUANDO** o Administrador seleciona as unidades COFIN, AJUR e DIRAD como unidades geridas por Maria
- **ENTÃO** Maria passa a ter visibilidade consolidada e permissão de cadastro de usuários nas três unidades (PRD US 8.6b Cen.1)

#### Scenario: Gestor com apenas uma unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** cadastro ou edito um Gestor selecionando apenas uma unidade gerenciada
- **ENTÃO** o sistema aceita a configuração normalmente (PRD US 8.6b Cen.2)
