## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Cadastro de novo usuário pelo Administrador
O sistema SHALL permitir ao Administrador cadastrar novos usuários informando nome, e-mail, perfil, unidade, **setor** (obrigatório para Servidor) e, opcionalmente, telefone, cargo e chefia direta. O cadastro SHALL ser apresentado em **modal**, acionado por um botão "Novo usuário" — não mais como formulário permanentemente renderizado no índice da tela. O índice de usuários SHALL exibir, no espaço antes ocupado pelo formulário, um **campo de filtro por nome**. Ver PRD US 8.1.

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
O sistema SHALL listar os usuários cadastrados ao Administrador e SHALL oferecer **filtro por nome** com busca parcial e insensível a maiúsculas/minúsculas, aplicado no **backend**. O filtro NÃO SHALL alterar o escopo de autorização — apenas restringe o conjunto exibido dentro do que o Administrador já pode ver. Ver PRD US 8.2.

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
