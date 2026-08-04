## ADDED Requirements

### Requirement: Nome do produto e subtítulo de cliente

O nome do produto exibido ao usuário SHALL ser **"Despapelize"** em toda a
interface, e **"SETES"** SHALL ser apresentado como **subtítulo de cliente** —
identificação da instituição contratante — subordinado visualmente ao nome do
produto, nunca concatenado a ele. A composição "SETES.DOCS" NÃO SHALL aparecer em
nenhuma tela.

O nome do produto SHALL ser consistente em todas as superfícies de apresentação: o
título do documento (aba do navegador), a tela de Login, a sidebar do shell
autenticado, a tela de inicialização do sistema, a página inicial e a tela de
primeiro acesso. Nenhuma tela SHALL exibir um nome de produto divergente das demais.

Esta é uma mudança **exclusivamente de apresentação**: nenhum comportamento de
autenticação, autorização, navegação ou fluxo de dados SHALL ser alterado.

#### Scenario: Nome do produto consistente entre as telas

- **DADO** um visitante ou usuário navegando pelas telas que exibem a marca (Login,
  shell autenticado, inicialização, página inicial, primeiro acesso)
- **QUANDO** cada tela é renderizada
- **ENTÃO** todas SHALL exibir "Despapelize" como nome do produto
- **E** nenhuma delas SHALL exibir "SETES.DOCS"

#### Scenario: Subtítulo de cliente subordinado ao nome do produto

- **DADO** uma tela que exibe a marca com subtítulo (Login ou sidebar)
- **QUANDO** ela é renderizada
- **ENTÃO** "SETES" SHALL aparecer como subtítulo, em hierarquia visual inferior ao
  nome do produto
- **E** NÃO SHALL aparecer concatenado ao nome do produto na mesma linha de título

#### Scenario: Comportamento preservado após a renomeação

- **DADO** um usuário que realiza login, navega pelo menu e encerra a sessão
- **QUANDO** executa esses fluxos após a renomeação
- **ENTÃO** o comportamento SHALL ser idêntico ao anterior — mesma chamada de API,
  mesmo redirecionamento por perfil, mesmas mensagens de erro, mesma visibilidade de
  itens de menu por perfil

## MODIFIED Requirements

### Requirement: Apresentação do Login sem SSO

A tela de Login SHALL apresentar um card centrado com borda e sombra, contendo:
logo navy arredondado, título "Despapelize", subtítulo de cliente "SETES",
subtítulo "Acesse sua conta", campo de e-mail com ícone de envelope, campo de senha
com ícone de cadeado, botão primário navy "Entrar" e link "Esqueci minha senha". A
tela NÃO SHALL exibir qualquer opção de login via Google ou outro SSO — o MVP
autentica apenas por e-mail/senha (ver capability `autenticacao`). A renomeação NÃO
altera a lógica de autenticação, a validação dos campos nem o comportamento de erro
existentes.

#### Scenario: Login renderiza credenciais sem opção de SSO

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** ele SHALL ver o card de login com os campos de e-mail e senha, o
  botão "Entrar" e o link "Esqueci minha senha"
- **E** a página NÃO SHALL exibir nenhum botão "Continue with Google" ou divisor
  "ou"

#### Scenario: Login exibe o nome do produto e o cliente

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o card SHALL exibir "Despapelize" como título, "SETES" como subtítulo de
  cliente e "Acesse sua conta" como chamada de ação, nessa ordem visual

#### Scenario: Login preserva o comportamento de autenticação

- **DADO** um usuário na tela de login renomeada
- **QUANDO** informa credenciais válidas e aciona "Entrar"
- **ENTÃO** o fluxo de autenticação SHALL se comportar exatamente como antes da
  renomeação (mesma chamada de API, mesmo redirecionamento por perfil, mesma
  mensagem de erro em falha)

### Requirement: Navegação em sidebar preservando o RBAC por perfil

O shell autenticado (`components/protected-shell.tsx`) SHALL apresentar a
navegação como uma **sidebar vertical à esquerda**: logo + nome do produto
"Despapelize" com o subtítulo de cliente "SETES" no topo, e cada item de menu com
um ícone. O subtítulo "SISTEMA ELETRÔNICO" NÃO SHALL mais ser exibido. A
visibilidade de cada item SHALL permanecer condicionada ao perfil e às permissões do
usuário exatamente como na navegação anterior (servidor, gestor, administrador,
`pode_auditar`) — a renomeação é de apresentação, não de autorização. Um item cuja
condição de visibilidade não é satisfeita NÃO SHALL aparecer na sidebar.

#### Scenario: Servidor vê apenas os itens do seu perfil

- **DADO** um usuário autenticado com perfil `servidor`
- **QUANDO** a sidebar é renderizada
- **ENTÃO** ele SHALL ver os itens permitidos ao seu perfil (ex.: Meu Perfil,
  Processos)
- **E** NÃO SHALL ver itens restritos a administrador (Unidades, Tipos de
  Processo, Solicitações LGPD, Documentos Removidos) nem o Dashboard de gestor

#### Scenario: Item restrito continua oculto para perfil sem acesso (acesso negado)

- **DADO** um usuário sem a permissão `pode_auditar`
- **QUANDO** a sidebar é renderizada
- **ENTÃO** o item "Relatório de Auditoria" NÃO SHALL aparecer
- **E** caso o usuário acesse a rota protegida diretamente, o shell SHALL exibir
  a mensagem de acesso negado já existente ("Acesso negado — permissão de
  auditoria necessária." / "Acesso negado para o seu perfil."), sem regressão

#### Scenario: Administrador vê os itens administrativos

- **DADO** um usuário autenticado com perfil `administrador`
- **QUANDO** a sidebar é renderizada
- **ENTÃO** ele SHALL ver, além dos itens comuns, os itens administrativos
  (Unidades, Tipos de Processo, Usuários, Documentos Removidos, Solicitações LGPD)

#### Scenario: Topo da sidebar exibe produto e cliente

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** SHALL ver "Despapelize" como nome do produto e "SETES" como subtítulo
- **E** NÃO SHALL ver "SETES.DOCS" nem "SISTEMA ELETRÔNICO"

### Requirement: Marca institucional exibe o ícone do favicon

O "logo navy arredondado" da tela de Login e o chip da sidebar SHALL exibir o
**ícone institucional do favicon** (`apps/web/app/icon.svg`) — o mesmo símbolo de
documento em fundo navy — em vez da letra "S". O **formato de chip circular**
SHALL ser preservado nos dois locais. O ícone SHALL ser fornecido por um único
componente reutilizável `IconMarca` (`components/icons.tsx`), sem duplicação de
markup SVG entre Login e sidebar. Nenhum outro elemento de apresentação (cores,
comportamento) SHALL mudar além do texto da marca.

#### Scenario: Chip do Login mostra o ícone da marca

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o chip circular acima do título "Despapelize" SHALL exibir o ícone
  institucional (favicon), e NÃO a letra "S"
- **E** o chip SHALL permanecer circular

#### Scenario: Chip da sidebar mostra o ícone da marca

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** o chip circular ao lado de "Despapelize" SHALL exibir o ícone
  institucional (favicon), e NÃO a letra "S"
- **E** o chip SHALL permanecer circular

#### Scenario: Marca vem de um componente único reutilizável

- **DADO** o Login e a sidebar renderizando a marca
- **QUANDO** ambos exibem o chip
- **ENTÃO** ambos SHALL consumir o mesmo componente `IconMarca`, sem duplicar o
  SVG do ícone em cada tela
