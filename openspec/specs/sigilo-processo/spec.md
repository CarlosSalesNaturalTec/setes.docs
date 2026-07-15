# sigilo-processo

## Purpose

Marcação e remoção de sigilo em processos, restringindo apenas a visibilidade pública (Épico 7) sem afetar a visibilidade interna nem o status do processo (US 2.6).

## Requirements

### Requirement: Marcar processo como sigiloso
O sistema SHALL permitir que um Servidor ou Gestor **da unidade atual do processo**, ou um Administrador **em processo de qualquer unidade**, marque um processo como sigiloso, atribuindo `sigiloso = true`, registrando a ação como evento imutável no histórico de tramitação e passando o processo a **não** ser exibível na consulta pública (a ocultação efetiva é implementada no Épico 7). Ver PRD US 2.6 (Cen.1, Cen.1b).

#### Scenario: Marcação de processo como sigiloso pela unidade atual
- **DADO** que estou autenticado como Servidor ou Gestor da unidade atual do processo
- **QUANDO** acesso o processo e aciono "Marcar como Sigiloso"
- **ENTÃO** o processo passa a `sigiloso = true`, a ação é registrada no histórico de tramitação (evento `marcar_sigilo`, com responsável e data/hora) e o processo deixa de ser elegível à consulta pública (PRD US 2.6 Cen.1)

#### Scenario: Marcação por Administrador em processo de qualquer unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** acesso um processo de qualquer unidade e aciono "Marcar como Sigiloso"
- **ENTÃO** a operação é concluída com sucesso, independentemente da unidade em que o processo se encontra, e a ação é registrada no histórico de tramitação (PRD US 2.6 Cen.1b)

#### Scenario: Marcação idempotente de processo já sigiloso
- **DADO** que um processo já está marcado como sigiloso
- **QUANDO** um usuário autorizado aciona novamente "Marcar como Sigiloso"
- **ENTÃO** o processo permanece `sigiloso = true` e **nenhum evento duplicado** é inserido no histórico (a operação é um no-op idempotente)

### Requirement: Remover sigilo de processo
O sistema SHALL permitir que um Servidor ou Gestor da unidade atual do processo, ou um Administrador em processo de qualquer unidade, remova o sigilo de um processo, atribuindo `sigiloso = false`, registrando a ação como evento imutável no histórico de tramitação e devolvendo o processo à elegibilidade da consulta pública (Épico 7). Ver PRD US 2.6 (Cen.2, Cen.1b).

#### Scenario: Desmarcação de sigilo
- **DADO** que um processo está marcado como sigiloso
- **QUANDO** um usuário com permissão (Servidor ou Gestor da unidade atual, ou Administrador) aciona "Remover Sigilo"
- **ENTÃO** o processo passa a `sigiloso = false`, a ação é registrada no histórico de tramitação (evento `remover_sigilo`, com responsável e data/hora) e o processo volta a ser elegível à consulta pública (PRD US 2.6 Cen.2)

#### Scenario: Remoção idempotente de processo não sigiloso
- **DADO** que um processo não está marcado como sigiloso
- **QUANDO** um usuário autorizado aciona "Remover Sigilo"
- **ENTÃO** o processo permanece `sigiloso = false` e nenhum evento duplicado é inserido no histórico (no-op idempotente)

### Requirement: Acesso negado à marcação de sigilo fora do escopo de unidade
O sistema SHALL negar a marcação ou remoção de sigilo por usuário sem acesso à unidade atual do processo (Servidor de outra unidade, Gestor de unidade não gerida), retornando "acesso negado" e registrando a tentativa em `log_seguranca` (linha imutável). Ver PRD US 2.6 e o invariante de visibilidade por unidade (US 1.4 Cen.2).

#### Scenario: Servidor de outra unidade tenta marcar sigilo
- **DADO** que estou autenticado como Servidor da unidade COFIN e o processo está atualmente em outra unidade
- **QUANDO** tento acionar "Marcar como Sigiloso" ou "Remover Sigilo" sobre esse processo
- **ENTÃO** o sistema exibe "Acesso negado — você não tem permissão para visualizar este processo", a operação não é concluída e a tentativa é registrada em `log_seguranca`

### Requirement: Visibilidade interna do processo sigiloso
O sistema SHALL manter o processo sigiloso visível normalmente para os usuários com acesso à sua unidade (Kanban e detalhe), exibindo um indicador visual de "Sigiloso" (ícone de cadeado ou tarja). O sigilo restringe apenas a visibilidade **pública** (Épico 7), nunca a visibilidade interna autorizada. Ver PRD US 2.6 (Cen.3).

#### Scenario: Processo sigiloso visível internamente com indicador
- **DADO** que um processo está marcado como sigiloso
- **QUANDO** um Servidor da unidade atual do processo acessa o sistema
- **ENTÃO** o processo aparece normalmente no Kanban da unidade e na tela de detalhe, com um indicador visual de "Sigiloso" (cadeado ou tarja) (PRD US 2.6 Cen.3)

### Requirement: Sigilo é ortogonal ao status do processo
O sistema SHALL tratar o sigilo como atributo booleano independente da máquina de estados do processo. Marcar ou remover sigilo NÃO altera o status (`Aberto/Em Tramitação/Concluído/Arquivado`) nem constitui uma transição de estado; um processo pode ser sigiloso em qualquer status.

#### Scenario: Marcar sigilo não altera o status
- **DADO** um processo em qualquer status (por exemplo "Em Tramitação")
- **QUANDO** um usuário autorizado marca ou remove o sigilo
- **ENTÃO** o status do processo permanece inalterado; apenas o atributo `sigiloso` muda e um evento de sigilo é registrado no histórico
