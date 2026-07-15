# controle-acesso-por-unidade

## MODIFIED Requirements

### Requirement: Autorização por perfil e unidade
O sistema SHALL prover uma primitiva de autorização reutilizável que restringe cada operação por perfil (Servidor, Gestor, Administrador) e por escopo de unidade (unidade própria do Servidor; unidades geridas do Gestor; qualquer unidade para o Administrador), negando o acesso e registrando a tentativa em log de segurança quando o escopo não é atendido. Os endpoints de processo (Épico 2) **consomem efetivamente** esta primitiva para o filtro de Kanban, a busca interna e o acesso a detalhes/ações de processo, aplicando a US 1.4 na prática. Ver PRD US 1.4.

#### Scenario: Servidor tenta operar sobre unidade que não é a sua — acesso negado
- **DADO** que estou autenticado como Servidor vinculado à unidade COFIN
- **QUANDO** tento executar uma operação restrita à unidade AJUR (unidade da qual não faço parte)
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para esta unidade" e registra a tentativa em log de segurança (adaptação de PRD US 1.4 Cen.2)

#### Scenario: Servidor tenta acessar por URL direta um processo de outra unidade — acesso negado
- **DADO** que estou autenticado como Servidor da unidade COFIN e conheço o ID de um processo que nunca passou pela COFIN
- **QUANDO** tento acessar diretamente a URL desse processo de outra unidade
- **ENTÃO** o sistema exibe "Acesso negado — você não tem permissão para visualizar este processo" e registra a tentativa de acesso indevido em log de segurança (PRD US 1.4 Cen.2)

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
O sistema SHALL permitir que todo usuário autenticado visualize seus próprios dados cadastrais e seu histórico de atuação em processos. Agora que a entidade `processo` existe, a seção de histórico de atuação SHALL listar os processos em que o usuário atuou (número, assunto, data da ação e tipo de ação). A seção de documentos assinados permanece vazia até o Épico 3/4 (gestão documental e assinatura). Ver PRD US 1.5.

#### Scenario: Visualização do perfil com histórico de atuação
- **DADO** que estou autenticado e atuei em processos (criação, despacho ou devolução)
- **QUANDO** acesso a tela "Meu Perfil"
- **ENTÃO** visualizo meus dados cadastrais e a lista de processos em que atuei, com número, assunto, data da ação e tipo de ação realizada (PRD US 1.5 Cen.1)

#### Scenario: Perfil de usuário recém-cadastrado sem histórico
- **DADO** que sou um usuário recém-cadastrado que nunca atuou em nenhum processo
- **QUANDO** acesso a tela "Meu Perfil"
- **ENTÃO** visualizo meus dados cadastrais, e as seções de histórico exibem "Nenhum processo registrado" e "Nenhum documento assinado" (PRD US 1.5 Cen.2)

#### Scenario: Servidor transferido mantém histórico de atuação na unidade anterior
- **DADO** que eu era Servidor da unidade COFIN, atuei em processos lá, e fui transferido para a unidade AJUR
- **QUANDO** acesso "Meu Perfil"
- **ENTÃO** visualizo os processos em que atuei quando estava na COFIN (histórico permanece), mas não tenho acesso ao Kanban nem aos detalhes atuais dos processos que estão na COFIN, exceto se também tramitaram pela AJUR (PRD US 1.4 Cen.3)

#### Scenario: Usuário tenta visualizar o perfil de outro usuário — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento acessar a tela "Meu Perfil" de outro usuário via manipulação direta de URL/ID
- **ENTÃO** o sistema rejeita o acesso exibindo "Acesso negado" e registra a tentativa em log de segurança
