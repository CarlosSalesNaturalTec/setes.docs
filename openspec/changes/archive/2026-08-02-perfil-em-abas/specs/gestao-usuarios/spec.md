## ADDED Requirements

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
O sistema SHALL exibir a aba "Documentos assinados" com uma mensagem informando que a assinatura digital de documentos será disponibilizada em fase futura do produto. A aba NÃO SHALL exibir botão de assinatura, campo de certificado digital nem qualquer elemento que sugira funcionalidade disponível. A assinatura digital (Épico 4) permanece **fora do escopo do MVP**, e este requisito NÃO SHALL ser interpretado como retomada do épico.

#### Scenario: Aba informa fase futura em vez de vazio silencioso
- **DADO** que acesso a aba "Documentos assinados"
- **QUANDO** a aba é exibida
- **ENTÃO** vejo uma mensagem explicando que a assinatura digital de documentos será disponibilizada em fase futura, e nenhuma lista vazia sem explicação

#### Scenario: Nenhum controle de assinatura é oferecido
- **DADO** que estou na aba "Documentos assinados"
- **QUANDO** examino os controles disponíveis
- **ENTÃO** não há botão "Assinar", seleção de certificado digital nem qualquer ação que sugira que a assinatura já esteja implementada
