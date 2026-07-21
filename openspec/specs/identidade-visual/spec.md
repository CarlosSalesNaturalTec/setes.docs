# identidade-visual

## Purpose

Identidade visual do frontend (`apps/web`): define os tokens de marca (paleta
navy institucional, superfícies, radius e sombra de card) e os requisitos de
apresentação do Login, do shell de navegação (sidebar com ícones, item ativo,
cabeçalho com identidade do usuário) e do conteúdo das páginas internas. Escopo
exclusivamente de apresentação — o RBAC de navegação e o fluxo de autenticação
permanecem como especificados em `controle-acesso-por-unidade` e `autenticacao`.

## Requirements

### Requirement: Tokens de marca disponíveis para toda a UI

O sistema SHALL expor, na configuração do Tailwind (`tailwind.config.ts`), um
conjunto de tokens de identidade visual consumíveis por qualquer tela: a paleta
navy institucional (cor primária `#1e3a5f` e derivados para hover/ativo/superfície
suave), cores de superfície (fundo da aplicação e superfície de card), um radius
padrão de card e uma sombra de card. Nenhuma tela SHALL depender da paleta default
do Tailwind (`blue-600`, `gray-*`) para expressar a cor primária da marca.

#### Scenario: Cor primária vem do token de marca

- **DADO** qualquer componente que use a cor primária (botão "Entrar", item de
  menu ativo, logo)
- **QUANDO** ele é renderizado
- **ENTÃO** a cor aplicada SHALL ser o navy institucional (`#1e3a5f`), definido
  como token no `tailwind.config.ts`, e não a cor `blue-600` default do Tailwind

#### Scenario: Superfícies e cantos arredondados consistentes

- **DADO** um card de conteúdo (card do dashboard, card do formulário de login,
  contêiner de tabela de admin)
- **QUANDO** ele é renderizado
- **ENTÃO** ele SHALL usar a superfície de card, o radius padrão e a sombra de
  card definidos como tokens — o mesmo visual em todas as telas

### Requirement: Apresentação do Login sem SSO

A tela de Login SHALL apresentar um card centrado com borda e sombra, contendo:
logo navy arredondado, título "SETES.DOCS", subtítulo "Acesse sua conta", campo
de e-mail com ícone de envelope, campo de senha com ícone de cadeado, botão
primário navy "Entrar" e link "Esqueci minha senha". A tela NÃO SHALL exibir
qualquer opção de login via Google ou outro SSO — o MVP autentica apenas por
e-mail/senha (ver capability `autenticacao`). A reestilização NÃO altera a lógica
de autenticação, a validação dos campos nem o comportamento de erro existentes.

#### Scenario: Login renderiza credenciais sem opção de SSO

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** ele SHALL ver o card de login com os campos de e-mail e senha, o
  botão "Entrar" e o link "Esqueci minha senha"
- **E** a página NÃO SHALL exibir nenhum botão "Continue with Google" ou divisor
  "ou"

#### Scenario: Login preserva o comportamento de autenticação

- **DADO** um usuário na tela de login reestilizada
- **QUANDO** informa credenciais válidas e aciona "Entrar"
- **ENTÃO** o fluxo de autenticação SHALL se comportar exatamente como antes do
  restyle (mesma chamada de API, mesmo redirecionamento por perfil, mesma
  mensagem de erro em falha)

### Requirement: Navegação em sidebar preservando o RBAC por perfil

O shell autenticado (`components/protected-shell.tsx`) SHALL apresentar a
navegação como uma **sidebar vertical à esquerda**: logo + subtítulo "SISTEMA
ELETRÔNICO" no topo, e cada item de menu com um ícone. A visibilidade de cada
item SHALL permanecer condicionada ao perfil e às permissões do usuário
exatamente como na navegação anterior (servidor, gestor, administrador,
`pode_auditar`) — o restyle é de apresentação, não de autorização. Um item cuja
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

### Requirement: Item de navegação ativo destacado

A sidebar SHALL destacar visualmente o item correspondente à rota atual (fundo
navy suave e/ou texto navy), de modo que o usuário identifique em que seção está.

#### Scenario: Rota atual reflete no item ativo

- **DADO** um usuário navegando em `/processos`
- **QUANDO** a sidebar é renderizada
- **ENTÃO** o item "Processos" SHALL aparecer no estado ativo destacado
- **E** os demais itens SHALL aparecer no estado normal

### Requirement: Cabeçalho com identidade do usuário e ações

O shell SHALL apresentar, no cabeçalho superior direito, a identidade do usuário
(nome · perfil), o sino de notificações e a ação "Sair" — preservando o
comportamento de logout e de notificações já existente.

#### Scenario: Cabeçalho exibe usuário e permite sair

- **DADO** um usuário autenticado no shell
- **QUANDO** o cabeçalho é renderizado
- **ENTÃO** ele SHALL exibir o nome e o perfil do usuário, o sino de notificações
  e o botão "Sair"
- **QUANDO** o usuário aciona "Sair"
- **ENTÃO** a sessão SHALL ser encerrada e o usuário redirecionado para `/login`,
  como antes do restyle

### Requirement: Conteúdo das páginas internas herda o tema

As páginas internas autenticadas — cards do dashboard (`app/dashboard`) e tabelas das telas de administração e de processos (`app/admin/*`, `app/processos/*`) — SHALL usar os tokens de marca: superfícies de card com borda arredondada e sombra, e cores de estado (sucesso, alerta, erro, primária) coerentes com a paleta. O
restyle NÃO SHALL alterar os dados exibidos, as colunas das tabelas nem as ações
disponíveis por perfil.

#### Scenario: Cards e tabelas adotam a superfície de card

- **DADO** um usuário em uma página interna com cards ou tabelas (ex.: Dashboard,
  Admin › Unidades)
- **QUANDO** a página é renderizada
- **ENTÃO** os contêineres SHALL usar a superfície de card, o radius e a sombra
  dos tokens
- **E** o conjunto de dados e as ações disponíveis SHALL permanecer idêntico ao
  anterior ao restyle

### Requirement: Marca institucional exibe o ícone do favicon

O "logo navy arredondado" da tela de Login e o chip da sidebar SHALL exibir o
**ícone institucional do favicon** (`apps/web/app/icon.svg`) — o mesmo símbolo de
documento em fundo navy — em vez da letra "S". O **formato de chip circular**
SHALL ser preservado nos dois locais. O ícone SHALL ser fornecido por um único
componente reutilizável `IconMarca` (`components/icons.tsx`), sem duplicação de
markup SVG entre Login e sidebar. Nenhum outro elemento de apresentação (título,
subtítulo, cores, comportamento) SHALL mudar.

#### Scenario: Chip do Login mostra o ícone da marca

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o chip circular acima do título "SETES.DOCS" SHALL exibir o ícone
  institucional (favicon), e NÃO a letra "S"
- **E** o chip SHALL permanecer circular

#### Scenario: Chip da sidebar mostra o ícone da marca

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** o chip circular ao lado de "SETES.DOCS" SHALL exibir o ícone
  institucional (favicon), e NÃO a letra "S"
- **E** o chip SHALL permanecer circular

#### Scenario: Marca vem de um componente único reutilizável

- **DADO** o Login e a sidebar renderizando a marca
- **QUANDO** ambos exibem o chip
- **ENTÃO** ambos SHALL consumir o mesmo componente `IconMarca`, sem duplicar o
  SVG do ícone em cada tela
