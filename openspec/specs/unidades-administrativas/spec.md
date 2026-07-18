# unidades-administrativas

## Purpose

Cadastro, edição, desativação e reativação de unidades administrativas, incluindo as regras de desvinculação/preservação de histórico na desativação, restritos ao perfil Administrador. O vínculo de gestão de uma unidade é estabelecido pela atribuição de "Unidades geridas" a um Gestor (capability `gestao-usuarios`), não pelo cadastro da unidade.

## Requirements

### Requirement: Cadastro de unidade administrativa
O sistema SHALL permitir que um Administrador cadastre unidades administrativas com
nome e sigla, disponibilizando-as para vinculação de usuários e composição de
roteiros de tramitação. O cadastro de unidade NÃO define gestor responsável: o
vínculo de gestão de uma unidade é estabelecido exclusivamente pela atribuição de
"Unidades geridas" a um Gestor (capability `gestao-usuarios`, tabela
`UnidadeGestor`). Ver PRD US 8.1.

#### Scenario: Cadastro de unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** cadastro uma nova unidade com nome e sigla
- **ENTÃO** a unidade é criada como ativa e fica disponível para vinculação de usuários e para composição de roteiros (PRD US 8.1 Cen.1)

### Requirement: Edição de unidade administrativa
O sistema SHALL permitir a edição de nome e sigla de uma unidade existente,
aplicando a alteração imediatamente sem afetar processos já concluídos ou em
andamento. A edição de unidade NÃO define gestor responsável — a gestão da
unidade é controlada por "Unidades geridas" (`UnidadeGestor`). Ver PRD US 8.1.

#### Scenario: Edição de unidade existente
- **DADO** que estou autenticado como Administrador e a unidade COFIN já existe
- **QUANDO** altero o nome ou a sigla da unidade COFIN
- **ENTÃO** as alterações são salvas e passam a valer imediatamente em todas as telas e relatórios (PRD US 8.1 Cen.2)

### Requirement: Desativação de unidade administrativa
O sistema SHALL impedir a desativação de uma unidade que possua processos em andamento, e SHALL, ao desativar uma unidade sem pendências, desvincular automaticamente seus usuários e removê-la das opções de novos roteiros, preservando seu histórico. Agora que a entidade `processo` existe, a contagem de processos em andamento (status "Aberto" ou "Em Tramitação") na unidade é **efetiva**. Ver PRD US 8.1.

#### Scenario: Desativação bloqueada com processos pendentes
- **DADO** que a unidade COFIN possui processos em andamento (status "Aberto" ou "Em Tramitação")
- **QUANDO** o Administrador tenta desativar a unidade COFIN
- **ENTÃO** o sistema exibe "Esta unidade possui X processo(s) em andamento. Para desativá-la, primeiro redistribua ou conclua todos os processos pendentes." e a desativação não é concluída (PRD US 8.1 Cen.3)

#### Scenario: Desativação sem processos pendentes
- **DADO** que a unidade COFIN não possui processos em andamento
- **QUANDO** o Administrador desativa a unidade COFIN
- **ENTÃO** a unidade é marcada como inativa, seus usuários vinculados são automaticamente desvinculados (perdendo acesso até serem realocados), a unidade deixa de ser opção em novos roteiros, mas permanece no histórico de processos já tramitados (PRD US 8.1 Cen.4)

### Requirement: Reativação de unidade administrativa
O sistema SHALL permitir que um Administrador reative uma unidade inativa,
tornando-a novamente ativa e disponível para vinculação de usuários e composição
de novos roteiros. A reativação NÃO repovoa automaticamente o vínculo dos
usuários que foram desvinculados na desativação — o revínculo permanece manual,
feito pelo Administrador. A operação é idempotente para uma unidade já ativa.
Ver PRD US 8.1.

#### Scenario: Reativação de unidade inativa
- **DADO** que estou autenticado como Administrador e a unidade COFIN está inativa
- **QUANDO** reativo a unidade COFIN
- **ENTÃO** a unidade volta a ser ativa, fica novamente disponível para vinculação de usuários e para composição de novos roteiros

#### Scenario: Reativação não revincula servidores automaticamente
- **DADO** que a unidade COFIN foi desativada e seus servidores foram desvinculados
- **QUANDO** o Administrador reativa a unidade COFIN
- **ENTÃO** os servidores anteriormente vinculados permanecem sem unidade até serem realocados manualmente — a reativação não restaura os vínculos

#### Scenario: Reativação de unidade já ativa é idempotente
- **DADO** que a unidade COFIN já está ativa
- **QUANDO** o Administrador aciona a reativação da unidade COFIN
- **ENTÃO** a unidade permanece ativa e nenhum erro é gerado

### Requirement: Gestão de unidades restrita ao Administrador
O sistema SHALL restringir o cadastro, edição, desativação e reativação de
unidades administrativas ao perfil Administrador.

#### Scenario: Gestor tenta cadastrar unidade — acesso negado
- **DADO** que estou autenticado como Gestor
- **QUANDO** tento cadastrar, editar, desativar ou reativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança

#### Scenario: Servidor tenta cadastrar unidade — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento cadastrar, editar, desativar ou reativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança
