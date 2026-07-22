## MODIFIED Requirements

### Requirement: Autorização por perfil e unidade
O sistema SHALL prover uma primitiva de autorização reutilizável que restringe cada operação por perfil (Servidor, Gestor, Administrador) e por escopo de unidade (unidade própria do Servidor; unidades geridas do Gestor; qualquer unidade para o Administrador), negando o acesso e registrando a tentativa em log de segurança quando o escopo não é atendido. Os endpoints de processo (Épico 2) **consomem efetivamente** esta primitiva para o filtro de Kanban, a busca interna e o acesso a detalhes/ações de processo, aplicando a US 1.4 na prática.

Para **leitura** de processo (detalhe, histórico, documentos), o escopo SHALL compreender a **unidade atual OU a unidade de origem** do processo — exceto quando o processo estiver sigiloso e fora da unidade atual do usuário, caso em que a leitura por origem é negada com "Acesso restrito — solicite autorização ao Administrador". Para **escrita** (despacho, devolução, sigilo, anexar/remover documentos), o escopo SHALL permanecer **estrito à unidade atual**: a visibilidade por origem não concede nenhuma ação. Ver PRD US 1.4 (revisada por este change).

#### Scenario: Servidor tenta operar sobre unidade que não é a sua — acesso negado
- **DADO** que estou autenticado como Servidor vinculado à unidade COFIN
- **QUANDO** tento executar uma operação restrita à unidade AJUR (unidade da qual não faço parte)
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para esta unidade" e registra a tentativa em log de segurança (adaptação de PRD US 1.4 Cen.2)

#### Scenario: Servidor tenta acessar por URL direta um processo de outra unidade — acesso negado
- **DADO** que estou autenticado como Servidor da unidade COFIN e conheço o ID de um processo que **não está na COFIN nem tem a COFIN como unidade de origem**
- **QUANDO** tento acessar diretamente a URL desse processo de outra unidade
- **ENTÃO** o sistema exibe "Acesso negado — você não tem permissão para visualizar este processo" e registra a tentativa de acesso indevido em log de segurança (PRD US 1.4 Cen.2)

#### Scenario: Leitura de processo despachado pela unidade de origem
- **DADO** que estou autenticado como Servidor da COFIN e um processo não sigiloso com unidade de origem COFIN está atualmente na AJUR
- **QUANDO** acesso o detalhe, o histórico ou os documentos desse processo
- **ENTÃO** o sistema permite a **leitura** (modo somente leitura), sem registrar acesso negado

#### Scenario: Escrita por unidade de origem — acesso negado
- **DADO** que estou autenticado como Servidor da COFIN e um processo com origem COFIN está atualmente na AJUR
- **QUANDO** tento despachar, devolver, alternar sigilo ou anexar/remover documento desse processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — você não tem permissão para visualizar este processo" e registra a tentativa em log de segurança — a visibilidade por origem não concede escrita

#### Scenario: Leitura por origem de processo sigiloso — acesso negado
- **DADO** que estou autenticado como Servidor da COFIN e um processo com origem COFIN, atualmente na AJUR, foi marcado como sigiloso
- **QUANDO** tento acessar o detalhe desse processo
- **ENTÃO** o sistema rejeita exibindo "Acesso restrito — solicite autorização ao Administrador" e registra a tentativa em log de segurança (o sigilo prevalece sobre o acompanhamento por origem)

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
