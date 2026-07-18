## ADDED Requirements

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

## MODIFIED Requirements

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
