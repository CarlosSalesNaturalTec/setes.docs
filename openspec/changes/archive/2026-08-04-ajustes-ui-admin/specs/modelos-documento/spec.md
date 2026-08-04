## ADDED Requirements

### Requirement: Administração do catálogo de modelos organizada em abas

A tela de administração do catálogo de modelos de documento SHALL ser organizada em
duas abas: **"Novo modelo"**, contendo a ficha de cadastro, e **"Modelos
cadastrados"**, contendo os filtros e a listagem do catálogo. A aba ativa SHALL ser
refletida na URL, de modo que a recarga da página e o compartilhamento do endereço
preservem a aba escolhida; um valor ausente ou inválido SHALL recair na aba padrão,
sem mensagem de erro. A navegação entre abas SHALL ser acessível por teclado.

Após o cadastro bem-sucedido de um modelo, o sistema SHALL alternar para a aba
"Modelos cadastrados", de modo que o modelo recém-criado seja visível na listagem —
o resultado da ação SHALL ser observável sem que o usuário precise navegar
manualmente.

A reorganização é **exclusivamente de apresentação**: os campos da ficha, as regras
de validação, os filtros disponíveis, as ações por modelo (editar, desativar,
reativar) e a restrição de acesso ao perfil Administrador permanecem inalterados.

#### Scenario: Navegação entre as abas

- **DADO** que estou autenticado como Administrador e acesso a tela de modelos de
  documento
- **QUANDO** a tela é carregada
- **ENTÃO** vejo as duas abas com a aba padrão ativa; ao selecionar a outra aba, o
  conteúdo correspondente é exibido sem que a página seja recarregada

#### Scenario: Aba ativa preservada na recarga

- **DADO** que selecionei a aba "Modelos cadastrados"
- **QUANDO** recarrego a página ou abro novamente o mesmo endereço
- **ENTÃO** a aba "Modelos cadastrados" continua ativa

#### Scenario: Endereço inválido recai na aba padrão

- **DADO** que acesso a tela de modelos com um identificador de aba desconhecido no
  endereço
- **QUANDO** a página é carregada
- **ENTÃO** a aba padrão é exibida, sem mensagem de erro

#### Scenario: Cadastro bem-sucedido leva à listagem

- **DADO** que estou na aba "Novo modelo" com a ficha preenchida validamente
- **QUANDO** confirmo o cadastro e ele é aceito
- **ENTÃO** a aba "Modelos cadastrados" passa a ser a ativa e o modelo recém-criado
  consta na listagem
- **E** a ficha de cadastro é reiniciada, sem reter o conteúdo enviado

#### Scenario: Cadastro rejeitado permanece na ficha

- **DADO** que estou na aba "Novo modelo" e o cadastro é rejeitado pelo backend
- **QUANDO** o erro é retornado
- **ENTÃO** permaneço na aba "Novo modelo" com os dados preenchidos preservados e a
  mensagem de erro visível, sem alternância de aba

#### Scenario: Filtros continuam operando na aba de listagem

- **DADO** que estou na aba "Modelos cadastrados"
- **QUANDO** aplico os filtros de tipo e de situação
- **ENTÃO** a listagem é filtrada exatamente como antes da reorganização em abas

#### Scenario: Navegação por teclado entre abas

- **DADO** que o foco está sobre a lista de abas
- **QUANDO** navego com as setas esquerda e direita e ativo uma aba com Enter ou
  Espaço
- **ENTÃO** a aba correspondente é ativada, o foco permanece visível e não fica preso
  em nenhum elemento

#### Scenario: Acesso por não-Administrador continua negado

- **DADO** que estou autenticado como Servidor ou como Gestor
- **QUANDO** acesso a rota de administração de modelos
- **ENTÃO** o acesso é negado exatamente como antes da reorganização, sem que
  nenhuma das abas seja renderizada
