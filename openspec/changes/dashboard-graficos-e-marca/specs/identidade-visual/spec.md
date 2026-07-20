## ADDED Requirements

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
