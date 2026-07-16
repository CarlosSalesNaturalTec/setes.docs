# gestao-usuarios

## ADDED Requirements

### Requirement: Desativação de usuário com guarda de processos pendentes
O sistema SHALL permitir que um Administrador desative um usuário, transicionando seu
`status` para `inativo`, desde que o usuário NÃO possua processos em andamento sob sua
responsabilidade. Considera-se "processo em andamento sob responsabilidade do usuário U"
todo processo cujo `status` é `aberto` ou `em_tramitacao` e cujo **último responsável de
tramitação** é U, ou que U criou e ainda não teve nenhuma tramitação (definição do
`design.md`, D2). Se houver ao menos um processo nessa condição, a desativação SHALL ser
bloqueada com a mensagem "Este usuário possui X processo(s) em andamento. Reatribua os
processos antes de desativar.", onde X é a contagem. Toda desativação efetivada SHALL ser
registrada como evento imutável em `log_seguranca` (`tipo_evento = usuario_desativado`,
com o Administrador responsável no contexto). O login de usuário `inativo` já é rejeitado,
de modo que a desativação encerra o acesso ao sistema. Ver PRD US 8.4.

#### Scenario: Desativação de usuário sem processos pendentes
- **DADO** que estou autenticado como Administrador e o usuário-alvo está ativo e não
  possui processos em andamento sob sua responsabilidade
- **QUANDO** aciono "Desativar Usuário" sobre ele
- **ENTÃO** o usuário é marcado como `inativo`, não consegue mais fazer login, e a
  desativação é registrada em `log_seguranca` (PRD US 8.4 Cen.1)

#### Scenario: Desativação bloqueada por processos em andamento
- **DADO** que estou autenticado como Administrador e o usuário-alvo é o último
  responsável por 3 processos em andamento
- **QUANDO** tento desativá-lo
- **ENTÃO** o sistema exibe "Este usuário possui 3 processo(s) em andamento. Reatribua os
  processos antes de desativar." e a desativação NÃO é concluída (PRD US 8.4 Cen.2)

#### Scenario: Processo concluído ou arquivado não bloqueia a desativação
- **DADO** que o usuário-alvo foi o último responsável apenas por processos com status
  `concluido` ou `arquivado` (nenhum em andamento)
- **QUANDO** o Administrador aciona "Desativar Usuário"
- **ENTÃO** a desativação é concluída (processos fora de andamento não contam para a guarda)

#### Scenario: Desativação idempotente de usuário já inativo
- **DADO** que o usuário-alvo já está com status `inativo`
- **QUANDO** o Administrador aciona "Desativar Usuário" novamente
- **ENTÃO** o sistema informa "Usuário já está inativo" e não registra um novo evento de desativação

#### Scenario: Não-Administrador tenta desativar usuário — acesso negado
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento desativar qualquer usuário
- **ENTÃO** o sistema retorna "acesso negado", nenhum status é alterado, e a tentativa é
  registrada em `log_seguranca` (`acesso_negado`)
