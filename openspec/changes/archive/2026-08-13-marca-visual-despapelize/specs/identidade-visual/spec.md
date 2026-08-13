## ADDED Requirements

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

## MODIFIED Requirements

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
