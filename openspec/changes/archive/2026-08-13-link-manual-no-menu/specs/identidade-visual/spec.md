## MODIFIED Requirements

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
