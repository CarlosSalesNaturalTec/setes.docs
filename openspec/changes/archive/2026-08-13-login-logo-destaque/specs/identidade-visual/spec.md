## ADDED Requirements

### Requirement: Hero de marca do Login usa o material de origem do cliente

O Login SHALL exibir, no lugar do chip circular da marca, uma imagem estática
derivada de `docs/images/logo_despapelize.jpeg` (cópia em
`apps/web/public/marca/login-hero.jpg`), incluindo o fundo texturizado, a árvore,
as raízes de circuito e o wordmark "Despapelize®" tal como fornecidos pelo cliente,
sem recorte, remoção de fundo ou alteração de cor. A imagem NÃO SHALL ser exibida
dentro de um chip ou container circular.

A imagem SHALL ter largura máxima de 130px, preservando a proporção original do
material de origem (~0,59). A imagem SHALL levar `alt="Despapelize"` e SHALL estar
contida em um elemento de heading (`<h1>`), servindo como o heading acessível do
nome do produto na tela — a tela NÃO SHALL exibir, além dela, um nó de texto solto
duplicando "Despapelize".

Esta imagem é exclusiva do Login: nenhuma outra tela (sidebar, favicon, página
inicial, primeiro acesso, etc.) SHALL exibi-la ou referenciá-la.

#### Scenario: Login exibe a imagem de marca original, sem chip

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** ele SHALL ver a imagem `login-hero.jpg`, com fundo, árvore, raízes e
  wordmark do material de origem, sem chip ou container circular ao redor
- **E** a largura da imagem SHALL ser no máximo 130px, na proporção original

#### Scenario: Imagem funciona como heading acessível do nome do produto

- **DADO** um leitor de tela navegando a rota `/login`
- **QUANDO** alcança a região da marca no topo do card
- **ENTÃO** SHALL anunciar um heading com o texto "Despapelize", proveniente do
  atributo `alt` da imagem
- **E** NÃO SHALL haver um segundo nó de texto "Despapelize" duplicado na mesma
  região

#### Scenario: Imagem exclusiva do Login

- **DADO** a sidebar, o favicon e qualquer outra tela autenticada ou pública
- **QUANDO** são renderizados
- **ENTÃO** NÃO SHALL referenciar nem exibir `login-hero.jpg`

### Requirement: Fundo de página do Login usa tom derivado da marca

O `<main>` da tela de Login SHALL usar, como cor de fundo de página, o token
`marca.destaque` — uma cor sólida derivada do tom predominante de `login-hero.jpg`
(azul), ajustada em luminosidade para manter contraste de pelo menos 3:1 contra a
superfície de card branca, conforme o piso de contraste para elementos gráficos não
textuais já adotado pela capability. A cor SHALL ser um valor sólido: a textura, o
gradiente ou qualquer detalhe fotográfico do material de origem NÃO SHALL ser usado
como imagem ou textura de fundo de página — apenas a cor sólida derivada dele.

Este fundo é exclusivo do `<main>` da tela de Login. Nenhuma outra tela — shell
autenticado, página inicial, primeiro acesso, consulta pública — SHALL adotar o
token `marca.destaque`; todas as demais continuam usando `superficie.app`.

#### Scenario: Login exibe fundo de página no tom da marca

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** o `<main>` SHALL exibir o token de cor `marca.destaque` como fundo
- **E** o card branco de credenciais SHALL permanecer com contraste de pelo menos
  3:1 contra esse fundo

#### Scenario: Fundo do Login não vaza para outras telas

- **DADO** o shell autenticado, a página inicial, a tela de primeiro acesso ou a
  consulta pública
- **QUANDO** são renderizados
- **ENTÃO** NÃO SHALL usar o token `marca.destaque`
- **E** SHALL continuar usando `superficie.app` como fundo, sem alteração

## MODIFIED Requirements

### Requirement: Apresentação do Login sem SSO

A tela de Login SHALL apresentar um card centrado com borda e sombra, contendo: a
imagem de marca em destaque que já inclui o wordmark "Despapelize" (ver requisito
"Hero de marca do Login usa o material de origem do cliente"), subtítulo de cliente
"SETES", campo de e-mail com ícone de envelope, campo de senha com ícone de
cadeado, botão primário navy "Entrar" e link "Esqueci minha senha". A tela NÃO
SHALL exibir qualquer opção de login via Google ou outro SSO — o MVP autentica
apenas por e-mail/senha (ver capability `autenticacao`). A troca da imagem de marca
NÃO altera a lógica de autenticação, a validação dos campos nem o comportamento de
erro existentes.

**Adendo (D8):** o subtítulo "Acesse sua conta" é removido do card — a imagem de
marca em destaque já comunica a marca e o contexto, tornando a chamada de ação
textual redundante. Nenhum texto substitui "Acesse sua conta"; o card passa
diretamente da identificação de marca para o formulário.

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
- **ENTÃO** o card SHALL exibir a imagem de marca (com "Despapelize" legível nela e
  `alt="Despapelize"` associado a um heading acessível) e "SETES" como subtítulo de
  cliente, nessa ordem visual, imediatamente seguidos pelo formulário
- **E** NÃO SHALL exibir um nó de texto solto duplicando o nome do produto
- **E** NÃO SHALL exibir o subtítulo "Acesse sua conta" (removido, ver adendo D8)

#### Scenario: Login preserva o comportamento de autenticação

- **DADO** um usuário na tela de login com a imagem de marca em destaque
- **QUANDO** informa credenciais válidas e aciona "Entrar"
- **ENTÃO** o fluxo de autenticação SHALL se comportar exatamente como antes da
  troca da imagem (mesma chamada de API, mesmo redirecionamento por perfil, mesma
  mensagem de erro em falha)

### Requirement: Marca institucional exibe o ícone do favicon

O chip da sidebar SHALL exibir o símbolo da marca Despapelize — a árvore com raízes
de circuito, derivada do material fornecido pelo cliente — em vez do desenho
genérico de folha de documento. O mesmo símbolo SHALL ser o ícone do favicon
(`apps/web/app/icon.svg`), mantendo aba e interface alinhadas. O formato de chip
circular SHALL ser preservado no chip da sidebar. O símbolo da sidebar e do favicon
SHALL ser fornecido por um único componente reutilizável `IconMarca`
(`components/icons.tsx`), sem duplicação de markup SVG entre os dois.

**Exceção explícita — Login**: a tela de Login NÃO SHALL usar o chip circular nem o
componente `IconMarca`; em seu lugar, exibe a imagem de marca descrita no requisito
"Hero de marca do Login usa o material de origem do cliente". Essa exceção é
escopada exclusivamente ao Login — nenhum outro elemento de apresentação do chip da
sidebar ou do favicon (cores, tamanhos, posicionamento, comportamento) SHALL mudar
além do já descrito.

#### Scenario: Chip do Login mostra o ícone da marca

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** a página carrega
- **ENTÃO** este cenário NÃO SHALL mais se aplicar ao Login — por exceção explícita
  (ver acima), o Login exibe a imagem de marca do requisito "Hero de marca do Login
  usa o material de origem do cliente" em vez do chip circular com `IconMarca`
- **E** a sidebar SHALL continuar mostrando o chip circular com o ícone da marca,
  sem qualquer alteração

#### Scenario: Chip da sidebar mostra o ícone da marca

- **DADO** um usuário autenticado com a sidebar renderizada
- **QUANDO** observa o topo da navegação
- **ENTÃO** o chip circular ao lado de "Despapelize" SHALL exibir o símbolo da marca
  Despapelize, e NÃO o desenho genérico de folha de documento
- **E** o chip SHALL permanecer circular

#### Scenario: Marca vem de um componente único reutilizável

- **DADO** a sidebar e o favicon renderizando a marca
- **QUANDO** ambos exibem o símbolo
- **ENTÃO** ambos SHALL consumir o mesmo componente `IconMarca`, sem duplicar o SVG
  do ícone entre eles
- **E** essa regra NÃO SHALL se estender ao Login, que passa a usar um asset
  diferente (a imagem de marca do requisito "Hero de marca do Login usa o material
  de origem do cliente"), por exceção explícita

### Requirement: Símbolo derivado da marca fornecida pelo cliente

O símbolo isolado da marca (`IconMarca`, usado no chip da sidebar e no favicon)
SHALL ser derivado do material fornecido pelo cliente
(`docs/images/logo_despapelize.jpeg`) — a árvore com raízes de circuito — e SHALL
ser distribuído como ativo vetorial (SVG) de fundo transparente.

O fundo azul texturizado do material de origem é arte de peça gráfica, não parte do
símbolo isolado: NÃO SHALL aparecer no chip da sidebar nem no favicon. O wordmark
"Despapelize®" NÃO SHALL fazer parte do símbolo isolado — o nome do produto
continua sendo composto como texto ao lado do símbolo na sidebar, a partir de
`lib/marca.ts`, conforme o requisito "Nome do produto e subtítulo de cliente".

O símbolo SHALL permanecer legível no menor slot em que é usado (32×32, chip da
sidebar): traços e vazados que colapsem nesse tamanho SHALL ser simplificados no
ativo, não corrigidos por escala em cada tela.

**Exceção explícita — Login**: este requisito não se aplica à imagem de marca do
Login, que é um asset distinto (a arte original completa, com fundo e wordmark)
regido pelo requisito "Hero de marca do Login usa o material de origem do cliente".

#### Scenario: Símbolo não carrega o fundo do material de origem

- **DADO** o símbolo `IconMarca` renderizado sobre o navy da sidebar (o Login não
  usa mais este símbolo — ver exceção explícita acima)
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

- **DADO** o ativo do símbolo isolado (`IconMarca`)
- **QUANDO** ele é inspecionado
- **ENTÃO** NÃO SHALL conter o wordmark "Despapelize" nem o símbolo de marca
  registrada
- **E** o nome do produto exibido ao lado do símbolo na sidebar SHALL continuar
  vindo de `lib/marca.ts` como texto

### Requirement: Material de origem não é consumido pela aplicação

O arquivo `docs/images/logo_despapelize.jpeg` SHALL permanecer no repositório como
material de origem da marca — o registro do que o cliente forneceu, do qual os
ativos de interface foram derivados. Nenhum código de aplicação SHALL referenciá-lo
diretamente: não SHALL ser importado, servido a partir de `docs/`, embutido em
página nem usado como favicon.

**Exceção explícita — Login**: `apps/web/public/marca/login-hero.jpg` é uma
**cópia** do material de origem, mantida como asset separado porque o Next.js só
serve estático a partir de `apps/web/public/`. Esta cópia SHALL ser consumida
exclusivamente pelo Login (ver requisito "Hero de marca do Login usa o material de
origem do cliente") e SHALL levar comentário no código apontando
`docs/images/logo_despapelize.jpeg` como origem. O arquivo em `docs/images/`
continua nunca sendo referenciado diretamente por código de aplicação.

#### Scenario: Nenhuma tela carrega o material de origem

- **DADO** qualquer tela da aplicação, **exceto o Login** (ver exceção explícita
  acima)
- **QUANDO** os recursos que ela carrega são inspecionados
- **ENTÃO** NÃO SHALL haver requisição a `logo_despapelize.jpeg` nem à cópia
  `login-hero.jpg`
- **E** o arquivo `docs/images/logo_despapelize.jpeg` SHALL continuar existindo no
  repositório como material de origem, nunca referenciado diretamente por código

#### Scenario: Login carrega a cópia do material de origem, não o arquivo original

- **DADO** um visitante não autenticado na rota `/login`
- **QUANDO** os recursos que a página carrega são inspecionados
- **ENTÃO** a requisição SHALL ser à cópia `apps/web/public/marca/login-hero.jpg`
- **E** NÃO SHALL haver requisição direta a `docs/images/logo_despapelize.jpeg`
