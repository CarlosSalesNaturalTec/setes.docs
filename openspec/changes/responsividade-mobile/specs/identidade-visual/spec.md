## ADDED Requirements

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

## MODIFIED Requirements

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
