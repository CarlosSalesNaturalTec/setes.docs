## ADDED Requirements

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
