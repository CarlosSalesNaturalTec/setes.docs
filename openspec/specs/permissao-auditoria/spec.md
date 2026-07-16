# permissao-auditoria

## Purpose

Concessão e revogação, pelo Administrador, da permissão de auditoria — um atributo
ortogonal ao perfil do usuário que habilita o consumo de recursos de auditoria (Épico 9).

## Requirements

### Requirement: Concessão de permissão de auditoria por Administrador
O sistema SHALL permitir que um Administrador conceda a permissão de auditoria a qualquer
usuário existente, marcando `usuario.pode_auditar = true`. A permissão é **ortogonal ao
perfil** — o `perfil` do usuário (Servidor, Gestor ou Administrador) NÃO é alterado pela
concessão. A concessão SHALL ser registrada como evento imutável em `log_seguranca`
(`tipo_evento = permissao_auditoria_concedida`, com o Administrador responsável no
contexto). O consumo da permissão (visualizar processos sigilosos, gerar relatórios
consolidados) NÃO faz parte deste requisito — é do Épico 9. Ver PRD US 8.3 (Cen.1).

#### Scenario: Concessão de permissão de auditoria
- **DADO** que estou autenticado como Administrador
- **QUANDO** aciono "Conceder Permissão de Auditoria" sobre um usuário existente
- **ENTÃO** o usuário passa a ter a permissão de auditoria ativa (`pode_auditar = true`),
  seu perfil permanece inalterado, e a concessão é registrada em `log_seguranca` (PRD US 8.3 Cen.1)

#### Scenario: Concessão idempotente
- **DADO** que um usuário já possui permissão de auditoria ativa
- **QUANDO** o Administrador aciona novamente "Conceder Permissão de Auditoria" sobre ele
- **ENTÃO** o sistema mantém a permissão ativa e não registra um novo evento de concessão
  (só há registro em transição real de estado)

### Requirement: Revogação de permissão de auditoria por Administrador
O sistema SHALL permitir que um Administrador revogue a permissão de auditoria de um
usuário que a possua, marcando `usuario.pode_auditar = false`. A revogação SHALL retornar
o usuário ao estado anterior sem "lembrar" ou alterar seu perfil, e SHALL ser registrada
como evento imutável em `log_seguranca` (`tipo_evento = permissao_auditoria_revogada`,
com o Administrador responsável no contexto). Após a revogação, o usuário perde qualquer
acesso derivado da permissão de auditoria (o acesso em si é aplicado pelo Épico 9). Ver
PRD US 8.3 (Cen.2).

#### Scenario: Revogação de permissão de auditoria
- **DADO** que um usuário possui permissão de auditoria ativa
- **QUANDO** o Administrador aciona "Revogar Permissão de Auditoria" sobre esse usuário
- **ENTÃO** a permissão é removida (`pode_auditar = false`), o perfil permanece inalterado,
  e a revogação é registrada em `log_seguranca` (PRD US 8.3 Cen.2)

#### Scenario: Revogação idempotente
- **DADO** que um usuário não possui permissão de auditoria
- **QUANDO** o Administrador aciona "Revogar Permissão de Auditoria" sobre ele
- **ENTÃO** o sistema mantém a permissão inativa e não registra um novo evento de revogação

### Requirement: Acesso negado à gestão de permissão de auditoria por não-Administrador
O sistema SHALL restringir a concessão e a revogação da permissão de auditoria
exclusivamente ao perfil Administrador, negando a operação a Servidor, Gestor ou a
qualquer usuário com permissão de auditoria (o auditor não se autoconcede nem concede a
outros). Toda tentativa negada SHALL ser registrada em `log_seguranca`
(`tipo_evento = acesso_negado`). Ver PRD US 8.3 e o perfil Administrador (guardião da
configuração; concessão de auditoria é ato administrativo).

#### Scenario: Servidor ou Gestor tenta conceder permissão de auditoria — acesso negado
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento conceder ou revogar a permissão de auditoria de qualquer usuário
- **ENTÃO** o sistema retorna "acesso negado", nenhuma permissão é alterada, e a tentativa
  é registrada em `log_seguranca` (`acesso_negado`)

#### Scenario: Usuário com permissão de auditoria tenta conceder a outro — acesso negado
- **DADO** que estou autenticado como usuário com permissão de auditoria ativa mas sem
  perfil Administrador
- **QUANDO** tento conceder a permissão de auditoria a outro usuário
- **ENTÃO** o sistema retorna "acesso negado" e nenhuma permissão é alterada
