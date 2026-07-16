## ADDED Requirements

### Requirement: Sigilo não restringe a visibilidade de auditoria
O sistema SHALL manter o processo sigiloso plenamente visível a usuários com permissão de auditoria (`usuario.pode_auditar = true`). O sigilo restringe a visibilidade **pública** (Épico 7) e, para usuários **sem** permissão de auditoria, a visibilidade fora do escopo de unidade — mas **nunca** a visibilidade de um auditor autorizado, cujo acesso é justamente a razão de existir da permissão de auditoria. Assim, a ocultação por sigilo é **suspensa** para o auditor autorizado (que enxerga o processo completo, US 9.1 Cen.1), e **aplicada** — com a mensagem específica `"Acesso restrito — solicite autorização ao Administrador"` — a quem tenta acessá-lo sem a permissão (US 9.1 Cen.2). Ver PRD US 9.1 e US 2.6.

#### Scenario: Auditor autorizado enxerga processo sigiloso
- **DADO** que um processo está marcado como sigiloso e estou autenticado com `pode_auditar = true`
- **QUANDO** acesso o processo, seu histórico e seus documentos
- **ENTÃO** o processo é exibido completo, sem qualquer ocultação por sigilo, pois a permissão de auditoria suspende a restrição de sigilo (PRD US 9.1 Cen.1)

#### Scenario: Sigilo permanece aplicado a quem não tem permissão de auditoria
- **DADO** que um processo está marcado como sigiloso e estou autenticado sem permissão de auditoria, fora do escopo de unidade do processo
- **QUANDO** tento acessá-lo
- **ENTÃO** o acesso é negado com a mensagem `"Acesso restrito — solicite autorização ao Administrador"` e a tentativa é registrada em `log_seguranca` (PRD US 9.1 Cen.2)
