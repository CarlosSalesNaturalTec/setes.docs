# gestao-usuarios

## Purpose

Cadastro de usuários por Administrador (qualquer unidade/perfil) e por Gestor (escopo restrito), vínculo de Servidor a exatamente uma unidade e definição das unidades geridas por um Gestor.

## Requirements

### Requirement: Cadastro de usuário por Administrador
O sistema SHALL permitir que um Administrador cadastre novos usuários em qualquer unidade, com qualquer perfil (Servidor, Gestor ou Administrador), informando nome, e-mail, perfil, unidade, **setor** (obrigatório para Servidor) e, opcionalmente, telefone, cargo e chefia direta, disparando o envio de link de primeiro acesso. O cadastro SHALL ser apresentado em **modal**, acionado por um botão "Novo usuário" — não mais como formulário permanentemente renderizado no índice da tela. O índice de usuários SHALL exibir, no espaço antes ocupado pelo formulário, um **campo de filtro por nome**. Ver PRD US 1.1.

#### Scenario: Cadastro de servidor com sucesso
- **DADO** que estou autenticado como Administrador
- **QUANDO** preencho nome, e-mail, unidade e perfil e confirmo o cadastro
- **ENTÃO** o novo usuário é criado com status "Ativo — pendente de primeiro acesso" e um e-mail com link de primeiro acesso (validade 48h) é enviado (PRD US 1.1 Cen.1, Cen.1a)

#### Scenario: E-mail duplicado
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com um e-mail já em uso
- **ENTÃO** o sistema rejeita o cadastro exibindo "E-mail já cadastrado no sistema" (PRD US 1.1 Cen.2)

#### Scenario: E-mail com formato inválido
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com e-mail em formato inválido
- **ENTÃO** o sistema rejeita o cadastro exibindo "Formato de e-mail inválido" (PRD US 1.1 Cen.3)

#### Scenario: Nome vazio ou apenas espaços
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário com o campo nome vazio ou só espaços
- **ENTÃO** o sistema rejeita o cadastro exibindo "Nome é obrigatório" (PRD US 1.1 Cen.4)

#### Scenario: Unidade inexistente ou inativa
- **DADO** que estou autenticado como Administrador
- **QUANDO** tento cadastrar um usuário vinculado a uma unidade que não existe ou está desativada
- **ENTÃO** o sistema rejeita o cadastro exibindo "Unidade inválida ou inativa" (PRD US 1.1 Cen.5)

#### Scenario: Cadastro por modal
- **DADO** que estou autenticado como Administrador na tela de administração de usuários
- **QUANDO** aciono o botão "Novo usuário"
- **ENTÃO** um modal de cadastro é aberto sobre a listagem; ao submeter com sucesso, o modal fecha, a listagem é atualizada com o novo usuário e o e-mail de primeiro acesso é disparado como hoje

#### Scenario: Índice sem formulário inline
- **DADO** que estou na tela de administração de usuários
- **QUANDO** a tela é carregada
- **ENTÃO** nenhum formulário de cadastro é renderizado no corpo da página — apenas a listagem, o campo de filtro por nome e o botão "Novo usuário"

#### Scenario: Cascata de unidade para setor no formulário
- **DADO** que estou no modal de cadastro com a unidade COFIN selecionada e um setor dela escolhido
- **QUANDO** troco a unidade para AJUR
- **ENTÃO** o campo de setor é limpo e passa a listar apenas os setores **ativos** da AJUR

### Requirement: Listagem de usuários pelo Administrador
O sistema SHALL listar os usuários cadastrados ao Administrador e SHALL oferecer **filtro por nome** com busca parcial e insensível a maiúsculas/minúsculas, aplicado no **backend**. O filtro NÃO SHALL alterar o escopo de autorização — apenas restringe o conjunto exibido dentro do que o Administrador já pode ver. Ver PRD US 1.1 Cen.9.

#### Scenario: Filtro por fragmento de nome
- **DADO** que existem os usuários "Maria Silva", "Mariana Costa" e "João Souza"
- **QUANDO** digito "mari" no campo de filtro por nome
- **ENTÃO** a listagem exibe "Maria Silva" e "Mariana Costa" e omite "João Souza", sem recarregar a página

#### Scenario: Filtro vazio restaura a listagem completa
- **DADO** que apliquei um filtro por nome
- **QUANDO** limpo o campo de filtro
- **ENTÃO** a listagem volta a exibir todos os usuários do escopo do Administrador

#### Scenario: Filtro por nome não amplia o escopo — acesso negado
- **DADO** que estou autenticado como Gestor ou Servidor
- **QUANDO** tento acessar a listagem de usuários com ou sem filtro por nome
- **ENTÃO** o sistema rejeita a operação com "Acesso negado — você não tem permissão para esta operação" e registra a tentativa em log de segurança

### Requirement: Cadastro de usuário por Gestor com escopo restrito
O sistema SHALL permitir que um Gestor cadastre usuários com perfil Servidor apenas nas unidades que gerencia, e SHALL negar o cadastro em unidades não geridas ou com perfil privilegiado. Ver PRD US 1.2.

#### Scenario: Cadastro na unidade gerenciada
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** cadastro um novo usuário vinculado à COFIN com perfil de Servidor
- **ENTÃO** o cadastro é realizado com sucesso (PRD US 1.2 Cen.1)

#### Scenario: Tentativa de cadastro em unidade não gerenciada — acesso negado
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** tento cadastrar um usuário vinculado a uma unidade que não gerencio
- **ENTÃO** o sistema rejeita a operação exibindo "Você não tem permissão para cadastrar usuários nesta unidade" (PRD US 1.2 Cen.2)

#### Scenario: Tentativa de cadastro com perfil privilegiado — acesso negado
- **DADO** que estou autenticado como Gestor da unidade COFIN
- **QUANDO** tento cadastrar um usuário com perfil de Gestor ou Administrador
- **ENTÃO** o sistema rejeita a operação exibindo que apenas o Administrador pode atribuir esses perfis (PRD US 1.2 Cen.3)

### Requirement: Vínculo de Servidor a exatamente uma unidade
O sistema SHALL manter, para cada usuário com perfil Servidor, o vínculo com exatamente uma unidade por vez, substituindo o vínculo anterior em caso de transferência. Ver PRD US 8.6.

#### Scenario: Transferência de servidor entre unidades
- **DADO** que o servidor João está vinculado à unidade COFIN
- **QUANDO** o Administrador altera a unidade de João para AJUR
- **ENTÃO** o vínculo com COFIN é removido, o vínculo com AJUR é estabelecido, e João passa a enxergar apenas dados da unidade AJUR, mantendo seu histórico de atuação na COFIN (PRD US 8.6 Cen.1)

#### Scenario: Tentativa de vínculo duplo como Servidor
- **DADO** que o servidor João já está vinculado à unidade COFIN
- **QUANDO** o Administrador tenta também vinculá-lo à unidade AJUR mantendo o perfil de Servidor
- **ENTÃO** o sistema rejeita a operação exibindo que Servidores só podem estar vinculados a uma unidade por vez (PRD US 8.6 Cen.2)

### Requirement: Unidades geridas por Gestor
O sistema SHALL permitir que um Administrador defina uma ou mais unidades geridas por um usuário com perfil Gestor. Ver PRD US 8.6b.

#### Scenario: Vinculação de Gestor a múltiplas unidades
- **DADO** que o usuário Maria possui perfil de Gestor
- **QUANDO** o Administrador seleciona as unidades COFIN, AJUR e DIRAD como unidades geridas por Maria
- **ENTÃO** Maria passa a ter visibilidade consolidada e permissão de cadastro de usuários nas três unidades (PRD US 8.6b Cen.1)

#### Scenario: Gestor com apenas uma unidade
- **DADO** que estou autenticado como Administrador
- **QUANDO** cadastro ou edito um Gestor selecionando apenas uma unidade gerenciada
- **ENTÃO** o sistema aceita a configuração normalmente (PRD US 8.6b Cen.2)

### Requirement: Vínculo do usuário a unidade e setor
O sistema SHALL vincular o usuário a uma **Unidade** e a um **Setor** dessa unidade. O setor SHALL ser **obrigatório para o perfil Servidor** e opcional para Gestor e Administrador. O setor informado SHALL pertencer à unidade do próprio usuário — um setor de outra unidade SHALL ser rejeitado como dado inconsistente (não como acesso negado). A validação SHALL incidir sobre o cadastro e sobre **toda** edição, inclusive a transferência de unidade.

#### Scenario: Cadastro de Servidor exige setor
- **DADO** que estou autenticado como Administrador cadastrando um novo usuário com perfil Servidor
- **QUANDO** submeto o cadastro informando unidade mas sem informar setor
- **ENTÃO** o sistema rejeita o cadastro informando que o setor é obrigatório para o perfil Servidor, e nenhum usuário é criado

#### Scenario: Gestor e Administrador podem não ter setor
- **DADO** que estou cadastrando um usuário com perfil Gestor ou Administrador
- **QUANDO** submeto o cadastro sem informar setor
- **ENTÃO** o usuário é criado normalmente — a obrigatoriedade de setor é exclusiva do perfil Servidor

#### Scenario: Setor de outra unidade é rejeitado
- **DADO** que estou cadastrando um Servidor na unidade COFIN
- **QUANDO** informo um setor que pertence à unidade AJUR
- **ENTÃO** o sistema rejeita a operação informando que o setor não pertence à unidade do usuário, e nenhum usuário é criado

#### Scenario: Transferência de unidade exige setor coerente
- **DADO** que um Servidor está vinculado à COFIN, setor "Gabinete"
- **QUANDO** o transfiro para a unidade AJUR sem informar um setor da AJUR
- **ENTÃO** o sistema rejeita a transferência informando que o setor informado não pertence à nova unidade, e o vínculo original permanece inalterado

### Requirement: Campos complementares do cadastro de usuário
O sistema SHALL registrar, no cadastro de usuário, os campos **telefone**, **cargo** e **chefia direta**, todos opcionais. A **chefia direta** SHALL ser texto livre, não vinculada a um usuário do sistema — a chefia pode ser pessoa externa ao sistema. Esses campos SHALL ser exibidos na tela "Meu Perfil" do próprio usuário e na administração de usuários, e NÃO SHALL ser expostos na consulta pública.

#### Scenario: Cadastro com campos complementares
- **DADO** que estou cadastrando um novo Servidor
- **QUANDO** informo telefone, cargo e chefia direta além dos campos obrigatórios
- **ENTÃO** o usuário é criado com os três campos persistidos, e eles aparecem na tela "Meu Perfil" desse usuário

#### Scenario: Campos complementares são opcionais
- **DADO** que estou cadastrando um novo Servidor
- **QUANDO** submeto o cadastro sem telefone, cargo nem chefia direta
- **ENTÃO** o usuário é criado normalmente e a tela "Meu Perfil" omite os campos vazios em vez de exibir valores nulos

#### Scenario: Chefia direta aceita pessoa externa ao sistema
- **DADO** que estou cadastrando um Servidor cuja chefia não possui conta no sistema
- **QUANDO** informo o nome dessa chefia no campo "Chefia Direta"
- **ENTÃO** o valor é aceito e persistido como texto, sem exigir que a pessoa exista como usuário

#### Scenario: Dados pessoais de servidor fora da consulta pública
- **DADO** que um processo tramitou por servidores com telefone e cargo cadastrados
- **QUANDO** um cidadão consulta esse processo pela consulta pública
- **ENTÃO** telefone, cargo e chefia direta dos servidores NÃO são exibidos em nenhum ponto da resposta pública

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

### Requirement: Edição do próprio nome pelo usuário autenticado
O sistema SHALL permitir que qualquer usuário autenticado altere o **próprio nome**
na tela "Meu Perfil", com edição livre limitada a 200 caracteres (conforme o
campo `nome` do modelo). O usuário NÃO pode alterar por auto-serviço o próprio
e-mail nem o próprio perfil — esses permanecem sob gestão do Administrador. A
alteração vale imediatamente em todas as telas e no cabeçalho de sessão. Ver
PRD US 1.5.

#### Scenario: Alteração do próprio nome com sucesso
- **DADO** que estou autenticado como Servidor com o nome "Maria Souza"
- **QUANDO** edito o meu nome em "Meu Perfil" para "Maria Souza Lima" e salvo
- **ENTÃO** o sistema persiste o novo nome, retorna o perfil atualizado e o novo nome passa a aparecer em "Meu Perfil" e no cabeçalho de sessão

#### Scenario: Nome vazio ou apenas espaços rejeitado
- **DADO** que estou autenticado
- **QUANDO** tento salvar o meu nome vazio ou contendo apenas espaços
- **ENTÃO** o sistema rejeita a alteração e mantém o nome anterior

#### Scenario: Nome acima do limite rejeitado
- **DADO** que estou autenticado
- **QUANDO** tento salvar um nome com mais de 200 caracteres
- **ENTÃO** o sistema rejeita a alteração com erro de validação e mantém o nome anterior

#### Scenario: Auto-serviço não altera e-mail nem perfil
- **DADO** que estou autenticado como Servidor
- **QUANDO** uso o endpoint de edição do próprio perfil
- **ENTÃO** somente o nome pode ser alterado; e-mail e perfil não são afetados por esta operação

### Requirement: Tela "Meu Perfil" organizada em abas
O sistema SHALL organizar a tela "Meu Perfil" em quatro abas: **Meu perfil**, **Trocar senha**, **Processos em que atuei** e **Documentos assinados**. A aba **Meu perfil** SHALL exibir os dados do usuário autenticado — nome, e-mail, perfil, unidade, setor, cargo, telefone e chefia direta — omitindo os campos não preenchidos, e SHALL manter a edição do próprio nome sem alteração de regra. A aba ativa SHALL ser refletida na URL, de modo que a recarga da página e o compartilhamento do endereço preservem a aba escolhida; um valor ausente ou inválido SHALL recair na aba "Meu perfil". A navegação entre abas SHALL ser acessível por teclado.

#### Scenario: Navegação entre as abas
- **DADO** que estou autenticado e acesso a tela "Meu Perfil"
- **QUANDO** a tela é carregada
- **ENTÃO** vejo as quatro abas com "Meu perfil" ativa, exibindo meus dados; ao selecionar outra aba, o conteúdo correspondente é exibido sem que a página seja recarregada

#### Scenario: Aba ativa preservada na recarga
- **DADO** que selecionei a aba "Processos em que atuei"
- **QUANDO** recarrego a página ou abro novamente o mesmo endereço
- **ENTÃO** a aba "Processos em que atuei" continua ativa

#### Scenario: Endereço inválido recai na aba padrão
- **DADO** que acesso a tela "Meu Perfil" com um identificador de aba desconhecido no endereço
- **QUANDO** a página é carregada
- **ENTÃO** a aba "Meu perfil" é exibida, sem mensagem de erro

#### Scenario: Campos não preenchidos são omitidos
- **DADO** que meu cadastro não possui telefone nem chefia direta
- **QUANDO** acesso a aba "Meu perfil"
- **ENTÃO** esses campos não são exibidos, em vez de aparecerem vazios ou com valores nulos

#### Scenario: Edição do próprio nome preservada
- **DADO** que estou na aba "Meu perfil"
- **QUANDO** edito o meu nome e salvo
- **ENTÃO** o nome é persistido e passa a aparecer na aba e no cabeçalho de sessão, exatamente como antes da reorganização em abas

#### Scenario: Navegação por teclado entre abas
- **DADO** que o foco está sobre a lista de abas
- **QUANDO** navego com as setas esquerda e direita e ativo uma aba com Enter ou Espaço
- **ENTÃO** a aba correspondente é ativada, o foco permanece visível e não fica preso em nenhum elemento

### Requirement: Aba de documentos assinados como marcador de fase futura
O sistema SHALL exibir a aba "Documentos assinados" com uma mensagem informando que a assinatura digital de documentos será disponibilizada em fase futura do produto e orientando o usuário a solicitar seu Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora. A orientação SHALL deixar claro que se trata de providência **externa ao sistema** e preparatória, NÃO de uma ação disponível na tela. A aba NÃO SHALL exibir botão de assinatura, campo de certificado digital, formulário de solicitação, link de emissão nem qualquer elemento que sugira funcionalidade disponível. A assinatura digital (Épico 4) permanece **fora do escopo do MVP**, e este requisito NÃO SHALL ser interpretado como retomada do épico.

#### Scenario: Aba informa fase futura em vez de vazio silencioso
- **DADO** que acesso a aba "Documentos assinados"
- **QUANDO** a aba é exibida
- **ENTÃO** vejo uma mensagem explicando que a assinatura digital de documentos será disponibilizada em fase futura, e nenhuma lista vazia sem explicação

#### Scenario: Aba orienta a obtenção prévia do certificado digital
- **DADO** que estou na aba "Documentos assinados"
- **QUANDO** leio a mensagem exibida
- **ENTÃO** ela me orienta a solicitar o Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora, como preparação para a fase futura
- **E** deixa claro que essa solicitação é feita fora do sistema, não por esta tela

#### Scenario: Nenhum controle de assinatura é oferecido
- **DADO** que estou na aba "Documentos assinados"
- **QUANDO** examino os controles disponíveis
- **ENTÃO** não há botão "Assinar", seleção de certificado digital nem qualquer ação que sugira que a assinatura já esteja implementada

#### Scenario: A orientação não introduz nenhum controle
- **DADO** que a aba passou a orientar a solicitação do certificado digital
- **QUANDO** examino os controles disponíveis
- **ENTÃO** a orientação é apenas texto — não há botão de solicitação, formulário, campo de upload de certificado nem link de emissão dentro do sistema
