## MODIFIED Requirements

### Requirement: Quadro pessoal de processos (Servidor)
O sistema SHALL exibir ao Servidor um quadro de visualização (não manipulável por drag-and-drop) com as colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo **exclusivamente os processos que lhe dizem respeito** — aqueles em que ele é o **responsável atual**, os que ele **criou** e aqueles pelos quais ele **já passou** (foi detentor em algum evento do histórico de tramitação). O quadro NÃO SHALL mais exibir os processos da unidade inteira.

Um usuário que apenas **agiu** sobre o processo sem tê-lo detido — como um Gestor que reatribuiu — NÃO SHALL passar a vê-lo no quadro pessoal por esse motivo. Processos **sigilosos** que estejam fora da unidade atual do usuário NÃO SHALL aparecer, ainda que ele os tenha detido no passado. Cada card SHALL exibir número, tipo de processo, assunto, unidade atual por extenso, **servidor atualmente responsável**, data de criação, prazo e dias restantes, e SHALL expor os atributos `sigiloso`, `acao_requerida`, `somente_leitura` e `devolvido`. Ver PRD US 1.4 e US 2.3 (revisadas por este change).

#### Scenario: Quadro contém processos criados, detidos e em acompanhamento
- **DADO** que criei o processo P1, sou o responsável atual de P2, e já detive P3 antes de enviá-lo adiante
- **QUANDO** acesso a tela de Processos
- **ENTÃO** P1, P2 e P3 aparecem no quadro, cada um na coluna correspondente ao seu status

#### Scenario: Processo da própria unidade nunca tocado não aparece
- **DADO** que sou Servidor da unidade COFIN e um colega da COFIN criou e tramita um processo que eu nunca detive nem criei
- **QUANDO** acesso a tela de Processos
- **ENTÃO** esse processo NÃO aparece no meu quadro — o recorte é pessoal, não mais por unidade

#### Scenario: Visão estreita não estreita a autorização
- **DADO** que um processo da minha unidade não aparece no meu quadro porque nunca o toquei
- **QUANDO** acesso o detalhe desse processo por URL direta ou pela busca interna
- **ENTÃO** o acesso é **permitido** — a autorização continua sendo por unidade; apenas a composição do quadro foi estreitada

#### Scenario: Gestor que apenas reatribuiu não carrega o processo no quadro pessoal
- **DADO** que sou Gestor e reatribuí um processo do Servidor B para o Servidor C, sem nunca tê-lo detido
- **QUANDO** acesso meu quadro
- **ENTÃO** o processo aparece pelo meu escopo de **unidades geridas**, e não por participação pessoal — não sou tratado como detentor

#### Scenario: Sigiloso em outra unidade some do quadro de ex-detentor — acesso negado
- **DADO** que detive um processo, enviei-o para a AJUR e lá ele foi marcado como sigiloso
- **QUANDO** acesso meu quadro ou tento abrir o detalhe por URL direta
- **ENTÃO** o card NÃO aparece e o acesso direto é rejeitado com "Acesso restrito — solicite autorização ao Administrador", registrando a tentativa em log de segurança

#### Scenario: Quadro pessoal vazio
- **DADO** que sou um Servidor recém-cadastrado, sem processos criados nem recebidos
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo as colunas vazias com mensagem informando que não há processos relacionados a mim

### Requirement: Quadro consolidado (Gestor)
O sistema SHALL exibir ao Gestor um quadro consolidado com os processos de **todas as unidades que ele gerencia** — mantendo o escopo por unidade, **sem** o estreitamento pessoal aplicado ao Servidor — incluindo, em modo somente leitura, os processos cuja unidade de origem é uma das geridas e que estejam atualmente em unidade não gerida, exceto sigilosos. A regra vale igualmente para processos **arquivados**. Cada card SHALL exibir número, tipo de processo, assunto, unidade atual por extenso, servidor responsável, data de criação, prazo e dias restantes, com possibilidade de filtrar por unidade. Ver PRD US 2.8 e US 8.6b.

#### Scenario: Gestor mantém a visão por unidades geridas
- **DADO** que sou Gestor das unidades COFIN, AJUR e DIRAD
- **QUANDO** acesso a tela de Processos
- **ENTÃO** visualizo os processos das três unidades, independentemente de os ter criado ou detido — o estreitamento pessoal não se aplica ao meu perfil

#### Scenario: Gestor visualiza arquivados das unidades geridas
- **DADO** que sou Gestor e marco "Exibir Arquivados"
- **QUANDO** o quadro é recarregado
- **ENTÃO** os processos arquivados das unidades que gerencio passam a ser exibidos, com o mesmo escopo por unidade

#### Scenario: Gestor não visualiza processos de unidade que não gerencia — acesso negado
- **DADO** que sou Gestor das unidades COFIN e AJUR
- **QUANDO** o quadro é montado ou tento filtrar processos da unidade DIRAD, que não gerencio e que não é origem de processos das minhas unidades
- **ENTÃO** o sistema não inclui nem retorna esses processos; uma tentativa de acesso direto é rejeitada com "Acesso negado — você não tem permissão para esta unidade" e registrada em log de segurança

### Requirement: Filtro de exibição de arquivados
O sistema SHALL exibir no topo da tela de Processos um checkbox **"Exibir Arquivados"**, **desmarcado por padrão**, válido para todos os perfis e nos dois modos de visualização (Kanban e Lista). Processos com status **"Concluído" SHALL ser sempre exibidos**; processos "Arquivado" SHALL ser omitidos enquanto o checkbox estiver desmarcado. O contador do cabeçalho SHALL refletir apenas o conjunto visível. A preferência SHALL ser persistida no navegador. O filtro NÃO SHALL ampliar nem reduzir o escopo de autorização — apenas oculta ou exibe processos arquivados dentro do escopo já autorizado.

#### Scenario: Padrão oculta apenas arquivados
- **DADO** que meu escopo possui processos em todos os status e nunca alterei o checkbox
- **QUANDO** acesso a tela de Processos
- **ENTÃO** o checkbox "Exibir Arquivados" aparece desmarcado, os processos "Aberto", "Em Tramitação" e **"Concluído"** são exibidos, os "Arquivado" são omitidos, e o contador reflete apenas os visíveis

#### Scenario: Marcar o checkbox exibe os arquivados
- **DADO** que estou na tela de Processos com o checkbox desmarcado
- **QUANDO** marco "Exibir Arquivados"
- **ENTÃO** os processos arquivados do meu escopo passam a ser exibidos na sua coluna, o contador é atualizado e a preferência é lembrada na próxima visita

#### Scenario: Checkbox não amplia o escopo — acesso negado
- **DADO** que sou Servidor e meu quadro é pessoal
- **QUANDO** marco "Exibir Arquivados"
- **ENTÃO** vejo apenas os arquivados que criei, detive ou pelos quais passei; processos arquivados de colegas que nunca toquei continuam ausentes do quadro, e tentativas de acesso fora do escopo de unidade seguem rejeitadas com registro em log de segurança

## ADDED Requirements

### Requirement: Distinção entre ação requerida e acompanhamento
O sistema SHALL distinguir, no quadro e na lista, os processos que **exigem ação do usuário** — aqueles em que ele é o **responsável atual** (atributo `acao_requerida`) — dos processos que ele apenas **acompanha**, por tê-los criado ou detido, mas que estão sob responsabilidade de outro servidor. Cards com ação requerida SHALL receber destaque visual sólido; cards de acompanhamento SHALL ser apresentados de forma discreta e SHALL exibir o **nome do servidor** que detém o processo. Os atributos `acao_requerida`, `somente_leitura` e `devolvido` são independentes entre si e podem coexistir no mesmo card.

#### Scenario: Processo sob minha responsabilidade é destacado
- **DADO** que sou o servidor responsável atual por um processo
- **QUANDO** visualizo o quadro
- **ENTÃO** o card aparece com destaque sólido e `acao_requerida` verdadeiro, sinalizando que a próxima ação é minha

#### Scenario: Processo enviado adiante vira acompanhamento
- **DADO** que criei um processo e o enviei para a Servidora "Maria Silva"
- **QUANDO** visualizo o quadro
- **ENTÃO** o card continua presente, porém com apresentação discreta, `acao_requerida` falso, e exibindo "Maria Silva" como responsável atual

#### Scenario: Processo devolvido a mim volta a exigir ação
- **DADO** que enviei um processo e ele foi devolvido para mim
- **QUANDO** o quadro é recarregado
- **ENTÃO** o card volta a `acao_requerida` verdadeiro, com destaque sólido, exibindo também o destaque de devolução

#### Scenario: Gestor vê a maior parte do quadro como acompanhamento
- **DADO** que sou Gestor de unidades com muitos processos, nenhum atribuído pessoalmente a mim
- **QUANDO** visualizo o quadro consolidado
- **ENTÃO** todos os cards aparecem como acompanhamento, exibindo o servidor responsável de cada um; apenas processos atribuídos pessoalmente a mim teriam `acao_requerida` verdadeiro

### Requirement: Filtros de busca no quadro de processos
O sistema SHALL oferecer, no quadro de processos, filtros por **tipo de processo**, por **assunto** (busca de texto **parcial**, insensível a maiúsculas/minúsculas) e por **data** (período de criação, com data inicial e final). Os filtros SHALL ser combináveis entre si e com o checkbox "Exibir Arquivados", e SHALL ser aplicados **após** o recorte de escopo — nunca ampliando o conjunto de processos que o usuário pode ver.

#### Scenario: Filtro por tipo de processo
- **DADO** que meu quadro contém processos de tipos variados
- **QUANDO** seleciono o tipo "Requerimento" no filtro
- **ENTÃO** o quadro passa a exibir apenas os processos desse tipo, mantendo a distribuição por colunas de status

#### Scenario: Filtro por assunto com texto parcial
- **DADO** que meu quadro contém um processo com assunto "Solicitação de diária para capacitação"
- **QUANDO** digito "diária" no filtro de assunto
- **ENTÃO** esse processo é exibido, junto de outros cujo assunto contenha o mesmo fragmento, sem exigir correspondência exata

#### Scenario: Filtro por período de criação
- **DADO** que meu quadro contém processos criados ao longo de vários meses
- **QUANDO** informo um período de data inicial e final
- **ENTÃO** apenas os processos criados dentro do período são exibidos, incluindo integralmente os criados no dia final

#### Scenario: Filtros combinados
- **DADO** que apliquei simultaneamente tipo "Requerimento", assunto "diária" e um período de datas, com "Exibir Arquivados" marcado
- **QUANDO** o quadro é montado
- **ENTÃO** apenas os processos que satisfazem **todas** as condições são exibidos, arquivados incluídos

#### Scenario: Filtro não amplia o escopo — acesso negado
- **DADO** que sou Servidor com quadro pessoal
- **QUANDO** aplico qualquer combinação de filtros
- **ENTÃO** nenhum processo fora do meu conjunto pessoal é retornado, e uma requisição direta com filtros apontando para processos alheios não os revela

### Requirement: Busca interna mantém o escopo por unidade
O sistema SHALL manter a **busca interna** de processos com escopo por **unidade** (unidade atual ∪ unidade de origem, sem sigilosos fora da unidade atual), **sem** aplicar o estreitamento pessoal do quadro. A divergência entre o escopo do quadro e o escopo da busca é deliberada: o quadro é a área de trabalho pessoal do servidor, enquanto a busca é investigativa e serve para localizar processos da unidade sob tratamento de colegas. Como a autorização permanece por unidade, a busca não revela nada que o usuário não pudesse abrir por acesso direto. Ver PRD US 2.7.

#### Scenario: Busca localiza processo de colega da mesma unidade
- **DADO** que sou Servidor da COFIN e um colega da COFIN trata um processo que eu nunca toquei
- **QUANDO** busco esse processo por número ou assunto
- **ENTÃO** o processo é encontrado e posso abri-lo, ainda que ele não conste do meu quadro pessoal

#### Scenario: Busca não alcança outra unidade — acesso negado
- **DADO** que sou Servidor da COFIN
- **QUANDO** busco um processo que está e sempre esteve na unidade DIRAD
- **ENTÃO** a busca não o retorna, e uma tentativa de acesso direto é rejeitada com registro em log de segurança
