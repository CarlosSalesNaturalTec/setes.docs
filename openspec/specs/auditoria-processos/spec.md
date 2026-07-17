# auditoria-processos Specification

## Purpose
TBD - created by archiving change auditoria-e-relatorios. Update Purpose after archive.
## Requirements
### Requirement: Leitura irrestrita de processo por Auditor
O sistema SHALL permitir que um usuário autenticado com permissão de auditoria (`usuario.pode_auditar = true`) visualize **qualquer** processo do sistema — de qualquer unidade, inclusive **sigilosos** — de forma completa: detalhe do processo, histórico de tramitação e documentos anexados (com respectivas assinaturas digitais, quando existirem). Este acesso é um caminho de autorização **paralelo** à visibilidade por unidade (`require_acesso_unidade`): a permissão de auditoria é **ortogonal ao perfil** (Servidor/Gestor/Administrador) e independe de o processo estar na unidade do usuário. Ver PRD US 9.1 (Cen.1).

#### Scenario: Auditor autorizado acessa processo de qualquer unidade
- **DADO** que estou autenticado como usuário com `pode_auditar = true`
- **QUANDO** acesso um processo de qualquer unidade, inclusive restrito ou sigiloso
- **ENTÃO** visualizo o processo completo — detalhe, histórico de tramitação e todos os documentos anexados (com respectivas assinaturas digitais quando houver) — independentemente de o processo estar ou não na minha unidade (PRD US 9.1 Cen.1)

#### Scenario: Permissão de auditoria não altera a visibilidade padrão por unidade
- **DADO** que sou Servidor com `pode_auditar = false`
- **QUANDO** acesso o Kanban e a leitura de processos da minha unidade
- **ENTÃO** continuo restrito exclusivamente aos processos da minha unidade (US 1.4), sem qualquer acesso ampliado — a leitura irrestrita depende **estritamente** da flag `pode_auditar`

### Requirement: Permissão de auditoria é somente leitura
O sistema SHALL restringir a permissão de auditoria (`usuario.pode_auditar`) a **operações de leitura** (detalhe, histórico, listagem/visualização/download de documentos, relatório). A permissão NÃO concede nenhuma operação de **escrita** sobre o processo — marcar/remover sigilo, anexar/remover documento, despachar ou devolver. Um usuário cujo único vínculo com o processo é a permissão de auditoria (sem acesso à unidade atual) que tente qualquer operação de escrita SHALL receber acesso negado (`403`, mensagem genérica de acesso negado por unidade), registrado em `log_seguranca` (`tipo_evento = acesso_negado`), preservando a natureza de fiscalização não-interventiva do Auditor.

#### Scenario: Auditor tenta marcar sigilo em processo de outra unidade
- **DADO** que sou usuário com `pode_auditar = true`, sem acesso à unidade atual de um processo
- **QUANDO** tento marcar ou remover o sigilo desse processo
- **ENTÃO** o sistema nega a operação com `403` e a mensagem genérica de acesso negado por unidade, a marcação não é alterada e a tentativa é registrada em `log_seguranca` (`tipo_evento = acesso_negado`) — a permissão de auditoria não destrava escrita

#### Scenario: Auditor tenta anexar ou remover documento em processo de outra unidade
- **DADO** que sou usuário com `pode_auditar = true`, sem acesso à unidade atual de um processo, e consigo **ler** seus documentos (US 9.1)
- **QUANDO** tento anexar um novo documento ou remover um documento existente
- **ENTÃO** o sistema nega a operação com `403` e a mensagem genérica de acesso negado por unidade, o acervo de documentos permanece inalterado, e nenhum evento `acesso_auditoria` é registrado para a tentativa de escrita

### Requirement: Acesso negado a processo sigiloso sem permissão de auditoria
O sistema SHALL negar a leitura de um processo **sigiloso** fora do escopo de unidade a um usuário autenticado **sem** permissão de auditoria (`pode_auditar = false`), retornando a mensagem específica `"Acesso restrito — solicite autorização ao Administrador"` (distinta da rejeição genérica de unidade) e registrando a tentativa como linha imutável em `log_seguranca` (`tipo_evento = acesso_negado`). Ver PRD US 9.1 (Cen.2) e o invariante de visibilidade por unidade com caminho de "acesso negado" explícito.

#### Scenario: Usuário sem permissão tenta acessar processo sigiloso
- **DADO** que estou autenticado sem permissão de auditoria (`pode_auditar = false`) e o processo é sigiloso e está fora do meu escopo de unidade
- **QUANDO** tento acessar o processo, seu histórico ou seus documentos
- **ENTÃO** o sistema retorna a mensagem `"Acesso restrito — solicite autorização ao Administrador"`, a leitura não é concluída e a tentativa é registrada em `log_seguranca` (`tipo_evento = acesso_negado`) (PRD US 9.1 Cen.2)

#### Scenario: Rejeição de sigiloso distingue-se da rejeição de unidade
- **DADO** que um processo **não** sigiloso está fora do meu escopo de unidade e não tenho permissão de auditoria
- **QUANDO** tento acessá-lo
- **ENTÃO** recebo a mensagem genérica de acesso negado por unidade já existente (não a mensagem de auditoria), preservando a distinção entre "fora da minha unidade" e "sigiloso sem autorização de auditoria"

### Requirement: Registro imutável do acesso de auditoria bem-sucedido
O sistema SHALL registrar como evento imutável em `log_seguranca` (`tipo_evento = acesso_auditoria`) **todo** acesso de leitura bem-sucedido concedido por meio da permissão de auditoria — isto é, quando um usuário com `pode_auditar = true` lê um processo ao qual, sem a permissão, não teria acesso pela regra de unidade. O registro guarda o usuário auditor, o processo acessado e a data/hora, formando trilha rastreável de quem auditou o quê. O registro é um INSERT de evento, nunca UPDATE.

#### Scenario: Acesso de auditoria a processo fora da unidade é registrado
- **DADO** que sou Auditor com `pode_auditar = true` acessando um processo de outra unidade
- **QUANDO** a leitura do processo (detalhe, histórico ou documentos) é concedida pela permissão de auditoria
- **ENTÃO** o sistema insere uma linha em `log_seguranca` com `tipo_evento = acesso_auditoria`, o identificador do usuário auditor, o identificador do processo e a data/hora do acesso

#### Scenario: Leitura na própria unidade não gera evento de auditoria redundante
- **DADO** que sou Auditor com `pode_auditar = true` e também Servidor da unidade atual do processo
- **QUANDO** acesso um processo da minha própria unidade, ao qual já teria acesso pela regra de unidade
- **ENTÃO** o acesso é concedido pela visibilidade de unidade normal e **não** gera evento `acesso_auditoria` (o rastro de auditoria cobre apenas o acesso que só a permissão de auditoria viabiliza)

