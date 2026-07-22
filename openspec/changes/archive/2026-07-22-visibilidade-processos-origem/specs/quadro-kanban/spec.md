## MODIFIED Requirements

### Requirement: Quadro Kanban da unidade (Servidor)
O sistema SHALL exibir ao Servidor um quadro Kanban **de visualização** (não manipulável por drag-and-drop) com as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo os processos **atualmente na sua unidade** e também os processos **cuja unidade de origem é a sua unidade** e que já tramitaram para outras unidades — estes em modo **somente leitura**, com card **acinzentado** (fundo cinza e opacidade reduzida), clicável para o detalhe. Processos **sigilosos** que estejam em outra unidade NÃO SHALL aparecer no acompanhamento por origem; o sigiloso na própria unidade atual continua exibido com o indicador 🔒, como hoje. Cada card SHALL exibir número, **tipo de processo**, assunto, **unidade atual por extenso** (nome completo, não sigla), **data de criação** ("Criado em dd/mm/aaaa hh:mm"), prazo e dias restantes, ordenados por prazo, e SHALL expor os atributos `sigiloso`, `somente_leitura` e `devolvido`. Ver PRD US 2.3, US 2.6 (Cen.3) e US 1.4 (revisada por este change).

#### Scenario: Exibição do Kanban por colunas de status
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" com os cards dos processos da COFIN, cada card com número, tipo de processo, assunto, unidade atual por extenso, data de criação, prazo e dias restantes; os cards NÃO são arrastáveis — as transições ocorrem apenas por ações explícitas (PRD US 2.3 Cen.1)

#### Scenario: Ordenação dos cards por prazo com destaque de vencidos
- **DADO** que minha unidade possui múltiplos processos em uma mesma coluna
- **QUANDO** visualizo o Kanban
- **ENTÃO** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos vencidos aparecem no topo com destaque visual: dias vencidos em vermelho com ícone de prazo, texto em negrito e barra vermelha de 4px na borda esquerda do card (PRD US 2.3 Cen.4)

#### Scenario: Novo processo despachado aparece após atualização
- **DADO** que um processo foi despachado para minha unidade por outra unidade
- **QUANDO** eu aciono o botão "Atualizar" do Kanban ou navego para outra tela e retorno
- **ENTÃO** o novo processo aparece na coluna "Aberto" da minha unidade (PRD US 2.3 Cen.2). **Nota de escopo**: o incremento do indicador de notificações citado no PRD US 2.3 Cen.2 depende de notificações internas (Épico 5) e não faz parte deste change.

#### Scenario: Kanban vazio
- **DADO** que estou autenticado como Servidor de uma unidade sem processos
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas vazias com a mensagem "Nenhum processo encontrado nesta unidade" (PRD US 2.3 Cen.3)

#### Scenario: Card de processo sigiloso com indicador
- **DADO** que a minha unidade possui um processo marcado como sigiloso
- **QUANDO** visualizo o Kanban da unidade
- **ENTÃO** o card do processo sigiloso aparece normalmente na sua coluna de status, com o indicador visual de "Sigiloso" (ícone de cadeado 🔒); cards de processos não sigilosos não exibem esse indicador (PRD US 2.6 Cen.3)

#### Scenario: Processo despachado permanece visível como acompanhamento da origem
- **DADO** que estou autenticado como Servidor da unidade COFIN e um processo criado na COFIN foi despachado para a AJUR
- **QUANDO** visualizo o Kanban ou a Lista da tela de Processos
- **ENTÃO** o processo aparece na coluna/linha correspondente ao seu status (ex.: "Em Tramitação") com o card acinzentado, `somente_leitura` verdadeiro e a unidade atual "Assessoria Jurídica" por extenso; o card permanece clicável e abre o detalhe em modo leitura

#### Scenario: Card somente leitura não expõe ações
- **DADO** que um processo com origem na minha unidade está atualmente em outra unidade
- **QUANDO** abro o seu detalhe a partir do card acinzentado
- **ENTÃO** os controles "Despachar", "Devolver", alternar sigilo e anexar/remover documentos NÃO são exibidos, e qualquer tentativa direta dessas ações é rejeitada pelo backend com registro em log de segurança

#### Scenario: Processo sigiloso em outra unidade não aparece no acompanhamento — acesso negado
- **DADO** que um processo com origem na COFIN foi despachado para a AJUR e lá foi marcado como sigiloso
- **QUANDO** o Servidor da COFIN visualiza o Kanban/Lista ou tenta acessar o detalhe por URL direta
- **ENTÃO** o card NÃO aparece no acompanhamento por origem e o acesso direto é rejeitado com "Acesso restrito — solicite autorização ao Administrador", registrando a tentativa em log de segurança (PRD US 2.6)

### Requirement: Quadro Kanban consolidado (Gestor)
O sistema SHALL exibir ao Gestor um quadro Kanban consolidado com os processos de **todas as unidades que ele gerencia** — incluindo, em modo **somente leitura** (card acinzentado), os processos cuja **unidade de origem** é uma das geridas e que estejam atualmente em unidade não gerida, exceto sigilosos — com número, tipo de processo, assunto, **nome da unidade atual por extenso**, **data de criação**, prazo e dias restantes em cada card, e a possibilidade de filtrar por unidade, sem exibir processos de unidades que ele não gerencia nem originados nelas. Ver PRD US 2.8 e US 8.6b.

#### Scenario: Kanban multi-unidade
- **DADO** que estou autenticado como Gestor das unidades COFIN, AJUR e DIRAD
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo um Kanban consolidado com colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado" contendo os cards das três unidades, cada card exibindo número, tipo de processo, assunto, unidade atual por extenso, data de criação, prazo e dias restantes (PRD US 2.8 Cen.1)

#### Scenario: Filtro por unidade no Kanban do Gestor
- **DADO** que estou visualizando o Kanban consolidado com processos de três unidades
- **QUANDO** seleciono uma unidade específica no filtro
- **ENTÃO** o Kanban passa a exibir apenas os processos da unidade selecionada (PRD US 2.8 Cen.2)

#### Scenario: Kanban consolidado vazio
- **DADO** que estou autenticado como Gestor de unidades sem processos
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas vazias com a mensagem "Nenhum processo encontrado nas unidades gerenciadas" (PRD US 2.8 Cen.3)

#### Scenario: Gestor acompanha processo originado em unidade gerida
- **DADO** que estou autenticado como Gestor da COFIN e um processo criado na COFIN foi despachado para a DIRAD (unidade que não gerencio)
- **QUANDO** visualizo o Kanban consolidado
- **ENTÃO** o card do processo aparece acinzentado (`somente_leitura`), exibindo a DIRAD como unidade atual por extenso

#### Scenario: Gestor não visualiza processos de unidade que não gerencia — acesso negado
- **DADO** que estou autenticado como Gestor das unidades COFIN e AJUR
- **QUANDO** o Kanban consolidado é montado ou tento filtrar/acessar processos da unidade DIRAD (que não gerencio e que não é origem de processos das minhas unidades)
- **ENTÃO** o sistema não inclui nem retorna processos originados e localizados fora do meu escopo; uma tentativa de acesso direto é rejeitada com "Acesso negado — você não tem permissão para esta unidade" e registrada em log de segurança (PRD US 1.4 Cen.2 adaptado ao Gestor)

## ADDED Requirements

### Requirement: Destaque de processo devolvido
O sistema SHALL destacar, no Kanban e na Lista, os processos cujo **último evento do histórico de tramitação é uma devolução** e que estão **atualmente na unidade do usuário** (atributo `devolvido` do card): badge "↩ Devolvido" e borda esquerda âmbar de 4px no card/linha. O destaque SHALL cessar automaticamente quando um novo evento de tramitação for registrado (ex.: novo despacho) — derivação exclusiva do histórico imutável, sem estado adicional. Quando o processo devolvido também estiver vencido, a borda vermelha de vencido SHALL prevalecer, mantendo o badge "↩ Devolvido". Processos devolvidos à unidade são acionáveis normalmente (não são somente leitura). Ver PRD US 2.2b.

#### Scenario: Card devolvido destacado no Kanban da unidade
- **DADO** que um processo foi devolvido pela AJUR para a minha unidade COFIN e nenhum evento de tramitação ocorreu depois
- **QUANDO** visualizo o Kanban ou a Lista
- **ENTÃO** o card do processo exibe o badge "↩ Devolvido" com borda esquerda âmbar, na coluna "Em Tramitação", e as ações da unidade (despachar/devolver) permanecem disponíveis no detalhe

#### Scenario: Destaque cessa após novo despacho
- **DADO** que um processo devolvido à minha unidade foi novamente despachado adiante
- **QUANDO** o Kanban é recarregado
- **ENTÃO** o card não exibe mais o destaque de devolução (o último evento do histórico deixou de ser uma devolução)

#### Scenario: Devolução não destaca fora da unidade atual
- **DADO** que um processo com origem na minha unidade foi devolvido da DIRAD para a AJUR (o processo não está na minha unidade)
- **QUANDO** visualizo meu Kanban
- **ENTÃO** o card aparece como acompanhamento somente leitura, sem o destaque "↩ Devolvido" — o destaque pertence à unidade que recebeu a devolução

### Requirement: Filtro de exibição de concluídos e arquivados
O sistema SHALL exibir no topo da tela de Processos um checkbox "Exibir concluídos e arquivados", **desmarcado por padrão**, válido para **todos os perfis** (Servidor, Gestor, Administrador) e nos dois modos de visualização (Kanban e Lista). Desmarcado, os processos com status "Concluído" e "Arquivado" NÃO SHALL ser retornados nem exibidos (colunas/linhas correspondentes vazias ou ocultas) e o contador do cabeçalho SHALL refletir apenas o total visível; marcado, os processos finalizados voltam a compor o quadro. A preferência SHALL ser persistida no navegador (localStorage) e reaplicada nas visitas seguintes. O filtro NÃO SHALL ampliar nem reduzir o escopo de autorização — apenas oculta/exibe status finais dentro do escopo já autorizado.

#### Scenario: Padrão oculta concluídos e arquivados
- **DADO** que meu escopo possui processos em todos os status e nunca alterei o checkbox
- **QUANDO** acesso a tela de Processos
- **ENTÃO** o checkbox "Exibir concluídos e arquivados" aparece desmarcado, apenas os processos "Aberto" e "Em Tramitação" são exibidos e o contador reflete somente eles

#### Scenario: Marcar o checkbox exibe os finalizados
- **DADO** que estou na tela de Processos com o checkbox desmarcado
- **QUANDO** marco "Exibir concluídos e arquivados"
- **ENTÃO** os processos "Concluído" e "Arquivado" do meu escopo passam a ser exibidos nas suas colunas/linhas, o contador é atualizado e a preferência é lembrada na próxima visita à tela

#### Scenario: Checkbox não amplia o escopo de autorização — acesso negado
- **DADO** que estou autenticado como Servidor da COFIN
- **QUANDO** marco "Exibir concluídos e arquivados"
- **ENTÃO** vejo apenas processos concluídos/arquivados do meu escopo (unidade atual ou origem COFIN, sem sigilosos fora da unidade); processos de outras unidades continuam inacessíveis e tentativas diretas seguem rejeitadas com registro em log de segurança
