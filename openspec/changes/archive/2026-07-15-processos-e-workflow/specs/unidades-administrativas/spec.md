# unidades-administrativas

## MODIFIED Requirements

### Requirement: Desativação de unidade administrativa
O sistema SHALL impedir a desativação de uma unidade que possua processos em andamento, e SHALL, ao desativar uma unidade sem pendências, desvincular automaticamente seus usuários e removê-la das opções de novos roteiros, preservando seu histórico. Agora que a entidade `processo` existe, a contagem de processos em andamento (status "Aberto" ou "Em Tramitação") na unidade é **efetiva**, tornando o cenário de bloqueio observável. Ver PRD US 8.1.

#### Scenario: Desativação bloqueada com processos pendentes
- **DADO** que a unidade COFIN possui processos em andamento (status "Aberto" ou "Em Tramitação")
- **QUANDO** o Administrador tenta desativar a unidade COFIN
- **ENTÃO** o sistema exibe "Esta unidade possui X processo(s) em andamento. Para desativá-la, primeiro redistribua ou conclua todos os processos pendentes." e a desativação não é concluída (PRD US 8.1 Cen.3)

#### Scenario: Desativação sem processos pendentes
- **DADO** que a unidade COFIN não possui processos em andamento
- **QUANDO** o Administrador desativa a unidade COFIN
- **ENTÃO** a unidade é marcada como inativa, seus usuários vinculados são automaticamente desvinculados (perdendo acesso até serem realocados), a unidade deixa de ser opção em novos roteiros, mas permanece no histórico de processos já tramitados (PRD US 8.1 Cen.4)
