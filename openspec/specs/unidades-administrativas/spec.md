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

### Requirement: Cadastro de setores vinculados à unidade
O sistema SHALL permitir ao Administrador cadastrar **Setores** vinculados a uma Unidade (relação 1:N), com nome, sigla e situação (ativo/inativo). A sigla SHALL ser única **dentro da unidade** — a mesma sigla pode existir em unidades diferentes. Setores NÃO SHALL ser excluídos fisicamente em nenhuma circunstância, apenas desativados, porque o histórico imutável de tramitação passa a referenciá-los. O cadastro de setores SHALL ser restrito ao perfil Administrador; qualquer outro perfil SHALL receber acesso negado com registro em log de segurança.

#### Scenario: Cadastro de setor em uma unidade
- **DADO** que estou autenticado como Administrador e a unidade "Coordenação Financeira (COFIN)" existe
- **QUANDO** cadastro o setor "Gabinete" com sigla "GAB" na COFIN
- **ENTÃO** o setor é criado como ativo, vinculado à COFIN, e passa a aparecer na lista de setores dessa unidade

#### Scenario: Sigla duplicada na mesma unidade é rejeitada
- **DADO** que a unidade COFIN já possui um setor com sigla "GAB"
- **QUANDO** tento cadastrar outro setor com sigla "GAB" na COFIN
- **ENTÃO** o sistema rejeita a operação informando que a sigla já existe nessa unidade, e nenhum setor é criado

#### Scenario: Mesma sigla em unidades diferentes é permitida
- **DADO** que a unidade COFIN possui o setor "GAB"
- **QUANDO** cadastro um setor com sigla "GAB" na unidade "Assessoria Jurídica (AJUR)"
- **ENTÃO** o setor é criado normalmente — a unicidade da sigla é por unidade, não global

#### Scenario: Setor não pode ser excluído
- **DADO** que existe um setor cadastrado
- **QUANDO** consulto as ações disponíveis para o setor
- **ENTÃO** não há qualquer ação de exclusão na interface nem endpoint de exclusão na API — apenas desativar e reativar

#### Scenario: Cadastro de setor por perfil não autorizado — acesso negado
- **DADO** que estou autenticado como Servidor ou como Gestor
- **QUANDO** tento cadastrar, editar, desativar ou reativar um setor por qualquer rota
- **ENTÃO** o sistema rejeita a operação com "Acesso negado — você não tem permissão para esta operação", nenhum setor é alterado, e a tentativa é registrada em log de segurança

### Requirement: Desativação de setor com guarda de servidores ativos
O sistema SHALL bloquear a desativação de um Setor enquanto existir ao menos um Servidor **ativo** vinculado a ele, informando a quantidade de servidores impedindo a operação. A desativação de uma **Unidade** SHALL desativar em cascata todos os seus Setores; a reativação da Unidade NÃO SHALL reativar os setores automaticamente — a reativação de cada setor é ação administrativa explícita.

#### Scenario: Desativação bloqueada por servidor ativo vinculado
- **DADO** que o setor "Gabinete" da COFIN possui 3 servidores ativos vinculados
- **QUANDO** tento desativar esse setor
- **ENTÃO** o sistema rejeita a operação informando que há 3 servidores ativos vinculados ao setor, e o setor permanece ativo

#### Scenario: Desativação de unidade cascateia para seus setores
- **DADO** que a unidade COFIN possui os setores "Gabinete" e "Protocolo", ambos ativos e sem servidores ativos vinculados
- **QUANDO** desativo a unidade COFIN, confirmando o aviso que exibe a quantidade de setores afetados
- **ENTÃO** a unidade e os dois setores passam a inativos

#### Scenario: Reativação de unidade não reativa setores
- **DADO** que a unidade COFIN foi desativada e seus setores foram desativados em cascata
- **QUANDO** reativo a unidade COFIN
- **ENTÃO** a unidade volta a ativa e os setores permanecem inativos, exigindo reativação individual explícita

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

### Requirement: Leitura do catálogo de unidades por qualquer usuário autenticado

O sistema SHALL permitir que qualquer usuário autenticado (Servidor, Gestor ou
Administrador) liste o catálogo de unidades administrativas (nome, sigla,
situação ativa/inativa) via `GET /unidades`. Este é um dado não sensível,
necessário para o Servidor resolver o nome de uma unidade (ex.: ao exibir a
unidade de destino de um despacho/devolução, ver capability `workflow-tramitacao`).
Cadastro, edição, desativação e reativação de unidade permanecem restritos ao
Administrador (Requirement "Gestão de unidades restrita ao Administrador").

#### Scenario: Servidor comum lista o catálogo de unidades
- **DADO** que sou Servidor, sem permissão de auditoria
- **QUANDO** solicito o catálogo de unidades
- **ENTÃO** recebo a lista de unidades (nome, sigla, ativo) com sucesso

#### Scenario: Servidor tenta cadastrar unidade a partir do catálogo — acesso negado
- **DADO** que sou Servidor e tenho acesso de leitura ao catálogo de unidades
- **QUANDO** tento cadastrar, editar, desativar ou reativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança (Requirement "Gestão de unidades restrita ao Administrador")
