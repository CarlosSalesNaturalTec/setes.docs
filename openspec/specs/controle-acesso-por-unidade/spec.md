# controle-acesso-por-unidade

## Purpose

Primitiva de autorização reutilizável que restringe operações por perfil (Servidor, Gestor, Administrador) e por escopo de unidade, negando acesso e registrando tentativas em log de segurança quando o escopo não é atendido. Também cobre a tela "Meu Perfil".

## Requirements

### Requirement: Autorização por perfil e unidade
O sistema SHALL prover uma primitiva de autorização reutilizável que restringe cada operação por perfil (Servidor, Gestor, Administrador) e por escopo de unidade (unidade própria do Servidor; unidades geridas do Gestor; qualquer unidade para o Administrador), negando o acesso e registrando a tentativa em log de segurança quando o escopo não é atendido. Esta primitiva é a base que os endpoints de `gestao-usuarios`, `unidades-administrativas` e `tipos-processo-e-roteiros` deste change consomem, e que os endpoints de processo (Épico 2, PRD US 1.4) consumirão para o filtro de Kanban.

#### Scenario: Servidor tenta operar sobre unidade que não é a sua — acesso negado
- **DADO** que estou autenticado como Servidor vinculado à unidade COFIN
- **QUANDO** tento executar uma operação restrita à unidade AJUR (unidade da qual não faço parte)
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para esta unidade" e registra a tentativa em log de segurança (adaptação de PRD US 1.4 Cen.2 às operações deste change)

#### Scenario: Gestor opera sobre unidade que gerencia
- **DADO** que estou autenticado como Gestor da unidade COFIN (PRD US 8.6b)
- **QUANDO** executo uma operação restrita à unidade COFIN
- **ENTÃO** o sistema permite a operação

#### Scenario: Gestor tenta operar sobre unidade que não gerencia — acesso negado
- **DADO** que estou autenticado como Gestor das unidades COFIN e AJUR
- **QUANDO** tento executar uma operação restrita à unidade DIRAD (que não gerencio)
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para esta unidade" e registra a tentativa em log de segurança

#### Scenario: Administrador opera sobre qualquer unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** executo uma operação restrita a qualquer unidade do sistema
- **ENTÃO** o sistema permite a operação, independentemente da unidade

### Requirement: Tela "Meu Perfil"
O sistema SHALL permitir que todo usuário autenticado visualize seus próprios dados cadastrais e o estado (vazio ou populado) de seu histórico de atuação em processos e de documentos assinados digitalmente. Ver PRD US 1.5. **Escopo deste change**: como as entidades `processo` e `documento` ainda não existem (dependem do Épico 2/3), apenas o estado vazio é observável nesta implementação; a listagem populada (PRD US 1.5 Cen.1) é entregue quando essas entidades existirem.

#### Scenario: Perfil de usuário recém-cadastrado sem histórico
- **DADO** que sou um usuário recém-cadastrado que nunca atuou em nenhum processo
- **QUANDO** acesso a tela "Meu Perfil"
- **ENTÃO** visualizo meus dados cadastrais, e as seções de histórico exibem "Nenhum processo registrado" e "Nenhum documento assinado" (PRD US 1.5 Cen.2)

#### Scenario: Usuário tenta visualizar o perfil de outro usuário — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento acessar a tela "Meu Perfil" de outro usuário via manipulação direta de URL/ID
- **ENTÃO** o sistema rejeita o acesso exibindo "Acesso negado" e registra a tentativa em log de segurança
