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

A sidebar SHALL admitir, além dos itens de rota interna, um **item de navegação
externo** — que aponta para uma URL absoluta fora da aplicação em vez de uma rota
Next.js. Um item externo SHALL abrir em **nova aba** (`target="_blank"`) com
`rel="noopener noreferrer"`, e SHALL ser **visível a todos os perfis** — não está
sujeito às mesmas condições de RBAC dos itens internos, pois não expõe dado ou
funcionalidade do sistema, apenas um link de saída. As regras de visibilidade por
perfil dos itens internos permanecem inalteradas por esta extensão.

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

#### Scenario: Item Manual aparece para os três perfis

- **DADO** um usuário autenticado, de qualquer perfil (servidor, gestor,
  administrador)
- **QUANDO** a sidebar é renderizada
- **ENTÃO** o item "Manual" SHALL aparecer na navegação, independentemente do
  perfil e das permissões do usuário

#### Scenario: Item Manual abre o site do manual em nova aba

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** ele aciona o item "Manual"
- **ENTÃO** o site do manual SHALL abrir em uma **nova aba**, preservando a tela
  atual do usuário
- **E** o link SHALL usar `rel="noopener noreferrer"`

#### Scenario: Item externo não é elegível ao destaque de item ativo (acesso negado ao destaque)

- **DADO** um usuário autenticado navegando em qualquer rota interna da aplicação
- **QUANDO** a sidebar é renderizada
- **ENTÃO** o item "Manual" NÃO SHALL aparecer no estado ativo destacado, mesmo
  que nenhuma outra rota corresponda à rota atual

### Requirement: Item de navegação ativo destacado

A sidebar SHALL destacar visualmente o item correspondente à rota atual (fundo
navy suave e/ou texto navy), de modo que o usuário identifique em que seção está.
Este destaque se aplica exclusivamente a itens de rota interna: um item de
navegação externo nunca corresponde à rota corrente do Next.js e, portanto, nunca
SHALL ser marcado como ativo.

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

Em **viewport estreito**, toda tabela dessas telas SHALL permanecer legível e
navegável: quando a largura disponível não comporta o conjunto de colunas, a
tabela SHALL rolar horizontalmente **dentro do seu próprio contêiner**, sem
comprimir as colunas e sem provocar rolagem horizontal da página inteira. A
superfície de card, o radius e a sombra SHALL ser preservados nesse contêiner —
adaptar a tabela ao viewport NÃO SHALL custar a identidade visual do card.

Como no restyle, esta adaptação é exclusivamente de apresentação: o conjunto de
colunas, os registros exibidos e as ações disponíveis por perfil SHALL permanecer
idênticos em qualquer largura de viewport.

#### Scenario: Cards e tabelas adotam a superfície de card

- **DADO** um usuário em uma página interna com cards ou tabelas (ex.: Dashboard,
  Admin › Unidades)
- **QUANDO** a página é renderizada
- **ENTÃO** os contêineres SHALL usar a superfície de card, o radius e a sombra
  dos tokens
- **E** o conjunto de dados e as ações disponíveis SHALL permanecer idêntico ao
  anterior ao restyle

#### Scenario: Tabela larga rola dentro do próprio contêiner

- **DADO** um Administrador em viewport de smartphone (360 px) numa tela de
  administração cuja tabela tem mais colunas do que a largura comporta
  (ex.: Admin › Usuários, com nome, e-mail, perfil, status, unidade e ações)
- **QUANDO** a página é renderizada
- **ENTÃO** a tabela SHALL rolar horizontalmente dentro do seu contêiner
- **E** a página como um todo NÃO SHALL rolar horizontalmente
- **E** todas as colunas SHALL permanecer alcançáveis por essa rolagem, nenhuma
  omitida nem comprimida a ponto de ficar ilegível

#### Scenario: Contêiner rolável preserva a identidade visual

- **DADO** a mesma tabela adaptada ao viewport estreito
- **QUANDO** ela é renderizada em qualquer largura
- **ENTÃO** o contêiner SHALL manter a superfície de card, o radius padrão e a
  sombra de card definidos nos tokens

#### Scenario: Acesso negado permanece inalterado em tela estreita

- **DADO** um usuário sem permissão para uma tela administrativa
- **QUANDO** acessa a rota diretamente em viewport estreito
- **ENTÃO** ele SHALL ver a mesma mensagem de acesso negado exibida no desktop
- **E** a adaptação de viewport NÃO SHALL expor nenhuma tabela, coluna ou ação
  que o seu perfil não pode ver

### Requirement: Largura mínima de viewport suportada

A aplicação SHALL permanecer operável em viewport de **360 px de largura** — o
piso prático de smartphones em uso — em todas as telas do produto. "Operável"
significa, nessa largura: nenhum conteúdo é cortado sem meio de alcançá-lo,
nenhum controle de ação (botão, link, campo) fica inacessível, e a página NÃO
SHALL produzir rolagem horizontal do documento inteiro — a rolagem horizontal,
quando necessária, SHALL ficar contida no elemento que a exige (ver o requisito
de tabelas).

Este é um requisito de apresentação: em nenhuma largura de viewport o conjunto de
dados exibidos, as colunas das tabelas, os campos dos formulários ou as ações
disponíveis por perfil SHALL diferir do que o mesmo usuário vê no desktop. Não há
"versão móvel reduzida" — há a mesma aplicação, adaptada.

#### Scenario: Página não rola horizontalmente em tela estreita

- **DADO** um usuário autenticado em viewport de 360 px de largura
- **QUANDO** abre qualquer tela do produto (Dashboard, Processos, detalhe de
  processo, telas de administração, Meu Perfil)
- **ENTÃO** o documento NÃO SHALL apresentar rolagem horizontal da página inteira
- **E** todo controle de ação da tela SHALL ser alcançável por rolagem vertical
  e/ou pela rolagem interna do contêiner que o comporta

#### Scenario: Mesmos dados e ações em qualquer largura

- **DADO** o mesmo usuário e a mesma tela
- **QUANDO** ela é aberta em viewport estreito (360 px) e em desktop
- **ENTÃO** as colunas, os registros e as ações disponíveis SHALL ser
  exatamente os mesmos nas duas larguras
- **E** nenhuma informação SHALL ser omitida em função da largura

### Requirement: Diálogos modais permanecem operáveis em viewport estreito

Todo diálogo modal do sistema SHALL permanecer inteiramente operável quando seu
conteúdo for mais alto que o viewport. O contêiner do modal SHALL permitir
rolagem vertical do próprio diálogo, de modo que os controles de confirmação e
cancelamento sejam sempre alcançáveis. Um modal cujo conteúdo exceda a altura da
tela NÃO SHALL ficar centrado de forma a empurrar seus botões para fora da área
visível sem meio de alcançá-los.

Isto se aplica a todos os modais, incluindo os de tramitação (envio, devolução,
reatribuição) e o de confirmação de conclusão — os mais altos do sistema, por
conterem seleção de unidade, setor, servidor e mensagem.

#### Scenario: Modal de tramitação mais alto que a tela é rolável

- **DADO** um Servidor em viewport de smartphone (360 × 640 px) na tela de
  detalhe de um processo sob sua responsabilidade
- **QUANDO** abre o modal de tramitação e seleciona a ação "Enviar", que exibe os
  campos de unidade, setor, servidor e mensagem
- **ENTÃO** ele SHALL conseguir alcançar e acionar o botão de confirmação
  rolando o conteúdo do diálogo
- **E** o botão de cancelamento SHALL permanecer igualmente alcançável

#### Scenario: Tramitação se completa a partir de um smartphone

- **DADO** um Servidor autenticado em viewport de smartphone com um processo sob
  sua responsabilidade
- **QUANDO** executa um envio para outra unidade preenchendo o modal de tramitação
- **ENTÃO** o envio SHALL ser registrado exatamente como no desktop, com o novo
  evento acrescentado ao histórico
- **E** o histórico SHALL permanecer imutável — o evento é acrescentado, nunca
  substituindo os anteriores

### Requirement: Listas de definição colapsam em coluna única em tela estreita

As listas de definição (rótulo + valor) usadas para resumir um processo — na
consulta pública e no detalhe do processo — SHALL apresentar rótulo e valor
empilhados em coluna única em viewport estreito, em vez de manter duas colunas
fixas que comprimem o valor a ponto de quebrá-lo caractere a caractere. Em
viewport largo elas SHALL manter a apresentação em duas colunas.

#### Scenario: Consulta pública legível em smartphone sem login

- **DADO** um visitante **não autenticado** em viewport de smartphone (360 px)
- **QUANDO** consulta um processo por número em `/consulta-publica` e obtém
  resultado
- **ENTÃO** os pares rótulo/valor (tipo de processo, status, unidade atual, data
  de criação) SHALL aparecer empilhados e legíveis, sem compressão de coluna
- **E** o conjunto de campos exibidos SHALL ser exatamente o mesmo do desktop —
  nenhum dado adicional é revelado por conta da largura

### Requirement: Marca institucional exibe o ícone do favicon

O "logo navy arredondado" da tela de Login e o chip da sidebar SHALL exibir o
**símbolo da marca Despapelize** — a árvore com raízes de circuito, derivada do
material fornecido pelo cliente — em vez do desenho genérico de folha de documento.
O mesmo símbolo SHALL ser o ícone do favicon (`apps/web/app/icon.svg`), mantendo aba e
interface alinhadas. O **formato de chip circular** SHALL ser preservado nos dois
locais. O símbolo SHALL ser fornecido por um único componente reutilizável `IconMarca`
(`components/icons.tsx`), sem duplicação de markup SVG entre Login e sidebar. Nenhum
outro elemento de apresentação (cores do chip, tamanhos, posicionamento,
comportamento) SHALL mudar além do desenho exibido.

#### Scenario: Chip do Login mostra o ícone da marca

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o chip circular acima do título "Despapelize" SHALL exibir o símbolo da
  marca Despapelize, e NÃO o desenho genérico de folha de documento
- **E** o chip SHALL permanecer circular

#### Scenario: Chip da sidebar mostra o ícone da marca

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** o chip circular ao lado de "Despapelize" SHALL exibir o símbolo da marca
  Despapelize, e NÃO o desenho genérico de folha de documento
- **E** o chip SHALL permanecer circular

#### Scenario: Marca vem de um componente único reutilizável

- **DADO** o Login e a sidebar renderizando a marca
- **QUANDO** ambos exibem o chip
- **ENTÃO** ambos SHALL consumir o mesmo componente `IconMarca`, sem duplicar o
  SVG do ícone em cada tela

### Requirement: Símbolo derivado da marca fornecida pelo cliente

O símbolo da marca exibido pela interface SHALL ser derivado do material fornecido
pelo cliente (`docs/images/logo_despapelize.jpeg`) — a **árvore com raízes de
circuito** — e SHALL ser distribuído como **ativo vetorial (SVG) de fundo
transparente**.

O fundo azul texturizado do material de origem é arte de peça gráfica, não parte da
marca: NÃO SHALL aparecer em nenhuma superfície da interface. O wordmark
"Despapelize®" NÃO SHALL fazer parte do símbolo isolado — o nome do produto continua
sendo composto como texto ao lado do símbolo, a partir de `lib/marca.ts`, conforme o
requisito "Nome do produto e subtítulo de cliente".

O símbolo SHALL permanecer legível no menor slot em que é usado (32×32, chip da
sidebar): traços e vazados que colapsem nesse tamanho SHALL ser simplificados no
ativo, não corrigidos por escala em cada tela.

#### Scenario: Símbolo não carrega o fundo do material de origem

- **DADO** o símbolo renderizado sobre o card branco do Login ou sobre o navy da
  sidebar
- **QUANDO** a tela é exibida
- **ENTÃO** NÃO SHALL aparecer nenhum retângulo, mancha ou textura de fundo em volta
  do desenho
- **E** o fundo da superfície hospedeira SHALL permanecer visível através das áreas
  vazadas do símbolo

#### Scenario: Símbolo legível no menor slot

- **DADO** o chip de 32×32 da sidebar
- **QUANDO** o símbolo é renderizado nesse tamanho
- **ENTÃO** a árvore e as raízes de circuito SHALL permanecer distinguíveis
- **E** o desenho NÃO SHALL degradar em um borrão sem forma reconhecível

#### Scenario: Símbolo isolado não contém o wordmark

- **DADO** o ativo do símbolo isolado
- **QUANDO** ele é inspecionado
- **ENTÃO** NÃO SHALL conter o wordmark "Despapelize" nem o símbolo de marca
  registrada
- **E** o nome do produto exibido ao lado do símbolo SHALL continuar vindo de
  `lib/marca.ts` como texto

### Requirement: Símbolo funciona sobre fundo claro e sobre fundo escuro

O símbolo SHALL ser legível tanto sobre a **superfície de card branca** (chip do
Login) quanto sobre o **navy institucional** (chip da sidebar), sem que cada tela
precise de um ativo próprio ou de correção pontual de cor. Esta é uma propriedade que
o ícone atual já possui por ser monocromático e herdar a cor do contexto, e que NÃO
SHALL ser perdida na troca pelo símbolo real.

O contraste entre o símbolo e o fundo do chip SHALL atender ao mínimo de 3:1 exigido
pela WCAG 2.1 AA para elementos gráficos não textuais, nos dois casos.

#### Scenario: Símbolo sobre o card branco do Login

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o símbolo no chip SHALL ser legível contra o fundo do chip
- **E** o contraste SHALL ser de no mínimo 3:1

#### Scenario: Símbolo sobre o navy da sidebar

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** o símbolo no chip SHALL ser legível contra o fundo do chip
- **E** o contraste SHALL ser de no mínimo 3:1

### Requirement: Marca horizontal disponível para superfícies com largura

Além do símbolo isolado, SHALL existir um ativo de **marca horizontal** — símbolo +
wordmark "Despapelize" — destinado a superfícies que disponham de largura, onde o
símbolo sozinho não identificaria o produto. O ativo SHALL ser vetorial, de fundo
transparente, e SHALL ser distinto do símbolo isolado: uma superfície NÃO SHALL
produzir a marca horizontal esticando, recompondo ou justapondo manualmente o símbolo
a um texto.

Nenhuma tela da aplicação consome este ativo neste momento; a exigência é que ele
exista e esteja correto, para que a próxima superfície que precisar dele não volte a
improvisar a composição.

#### Scenario: Marca horizontal existe como ativo distinto

- **DADO** o conjunto de ativos de marca do repositório
- **QUANDO** ele é inspecionado
- **ENTÃO** SHALL conter a marca horizontal como arquivo próprio, separado do símbolo
  isolado
- **E** ambos SHALL ter fundo transparente e nenhuma textura do material de origem

### Requirement: Favicon do produto é entregue ao navegador

A aba do navegador SHALL exibir o símbolo da marca como favicon, em todas as rotas da
aplicação — autenticadas e públicas. O caminho declarado nos metadados do documento
SHALL resolver para o ativo real: uma requisição direta a esse caminho NÃO SHALL
retornar 404.

Favicon e símbolo da interface SHALL ser o mesmo desenho — a aba e a tela não SHALL
divergir.

#### Scenario: Aba do navegador exibe o símbolo

- **DADO** um visitante em qualquer rota da aplicação (`/login`, `/processos`,
  `/consulta-publica`)
- **QUANDO** a página carrega
- **ENTÃO** a aba SHALL exibir o símbolo da marca Despapelize
- **E** NÃO SHALL exibir o ícone genérico default do navegador

#### Scenario: Caminho declarado do favicon resolve

- **DADO** o caminho de ícone declarado nos metadados do documento
- **QUANDO** ele é requisitado diretamente
- **ENTÃO** SHALL responder com o ativo do símbolo
- **E** NÃO SHALL responder 404

### Requirement: Material de origem não é consumido pela aplicação

O arquivo `docs/images/logo_despapelize.jpeg` SHALL permanecer no repositório como
**material de origem** da marca — o registro do que o cliente forneceu, do qual os
ativos de interface foram derivados. Nenhum código de aplicação SHALL referenciá-lo:
não SHALL ser importado, servido, embutido em página nem usado como favicon.

#### Scenario: Nenhuma tela carrega o material de origem

- **DADO** qualquer tela da aplicação
- **QUANDO** os recursos que ela carrega são inspecionados
- **ENTÃO** NÃO SHALL haver requisição a `logo_despapelize.jpeg`
- **E** o arquivo SHALL continuar existindo no repositório como material de origem
