## REMOVED Requirements

### Requirement: Despacho para a próxima unidade do roteiro
**Motivo**: o cliente rejeitou a tramitação automática por roteiro na avaliação da primeira entrega (`docs/Ajustes SETES DOCS.pdf`). O destino deixa de ser derivado do roteiro e passa a ser escolhido explicitamente pelo servidor. Substituído pelo requisito "Envio de processo com destino explícito".
**Migração**: nenhuma migração de comportamento é possível — o roteiro é removido do modelo de dados. Processos existentes na base de avaliação permanecem, passando a ser movimentados apenas pelas ações explícitas.

### Requirement: Devolução para a unidade anterior
**Motivo**: sem roteiro não existe "etapa anterior". A devolução passa a resolver o destino a partir do histórico imutável (o remetente anterior), não de uma posição ordinal. Substituído pelo requisito "Devolução ao remetente anterior".
**Migração**: nenhuma. A regra antiga de bloqueio "na unidade de origem do roteiro" é substituída pelo bloqueio "sem remetente anterior".

## MODIFIED Requirements

### Requirement: Máquina de estados do processo
O sistema SHALL modelar o status do processo como máquina de estados explícita com os estados "Aberto", "Em Tramitação", "Concluído" e "Arquivado", nunca como campo de texto livre. As transições permitidas SHALL ser exatamente: `Aberto → Em Tramitação` (Envio), `Aberto → Concluído` e `Em Tramitação → Concluído` (ação explícita de conclusão), `Em Tramitação → Em Tramitação` (Envio ou Devolução) e `Concluído → Arquivado` (exclusivamente pela rotina automática de arquivamento, nunca por ação de usuário). Qualquer transição fora dessa tabela SHALL ser rejeitada. A **Reatribuição** é um evento **ortogonal ao status**: registra no histórico o status corrente como resultante e NÃO SHALL provocar transição alguma. Ver PRD Épico 2.

#### Scenario: Transição inválida é rejeitada
- **DADO** que um processo está no status "Arquivado"
- **QUANDO** qualquer ação tenta movimentá-lo para outro status
- **ENTÃO** o sistema rejeita a operação por transição inválida e o status permanece "Arquivado"

#### Scenario: Reatribuição não altera o status
- **DADO** que um processo está no status "Aberto", ainda atribuído ao seu criador
- **QUANDO** ele é reatribuído para outro servidor da mesma unidade
- **ENTÃO** o processo permanece no status "Aberto", o evento de reatribuição é gravado no histórico com o status corrente como resultante, e nenhuma validação de transição de estado é acionada

#### Scenario: Arquivamento continua exclusivo da rotina automática
- **DADO** que um processo está "Concluído"
- **QUANDO** um usuário de qualquer perfil tenta arquivá-lo por ação direta
- **ENTÃO** a operação é rejeitada — apenas a rotina automática de arquivamento realiza a transição `Concluído → Arquivado`

### Requirement: Histórico de tramitação imutável
O sistema SHALL registrar cada movimentação como um **novo evento** na tabela de tramitação (INSERT), nunca como atualização de evento existente, e NÃO SHALL expor rota ou método de alteração ou exclusão de evento. Cada evento SHALL registrar o tipo de ação, unidade, **setor** e **servidor** de origem e de destino, o responsável pela ação, o status resultante, a mensagem ou justificativa e o instante de criação. O evento SHALL distinguir **quem agiu** (responsável) de **quem deteve** o processo (servidor de origem e de destino) — quando um Gestor reatribui um processo que nunca esteve sob sua responsabilidade, ele figura como responsável mas não como detentor. Ver PRD US 2.4.

#### Scenario: Linha do tempo completa de um processo
- **DADO** que um processo foi criado, enviado, devolvido, reenviado, reatribuído e concluído
- **QUANDO** consulto seu histórico
- **ENTÃO** vejo os eventos em ordem cronológica, cada um com tipo de ação, servidor de origem e destino, setor, unidade, responsável, mensagem ou justificativa e data/hora

#### Scenario: Histórico não é alterável
- **DADO** que existem eventos registrados no histórico de um processo
- **QUANDO** procuro uma forma de editar ou excluir qualquer evento, pela interface ou pela API
- **ENTÃO** não existe nenhuma rota, botão ou método que permita alterar ou remover um evento já gravado

#### Scenario: Gestor que reatribui é responsável, não detentor
- **DADO** que o Gestor da unidade COFIN reatribui um processo do Servidor B para o Servidor C, sem nunca tê-lo detido
- **QUANDO** consulto o evento de reatribuição
- **ENTÃO** o responsável é o Gestor, o servidor de origem é B e o servidor de destino é C — o Gestor não aparece como detentor em nenhum momento da cadeia

### Requirement: Feedback ao Servidor após ação de tramitação bem-sucedida
O sistema SHALL exibir mensagem de confirmação após cada ação de tramitação concluída com sucesso, identificando a ação e o destino: no Envio, o servidor e a unidade de destino; na Devolução, o servidor para quem o processo retornou; na Reatribuição, o novo servidor responsável e a informação de que o **prazo foi mantido**; na Conclusão, a confirmação do encerramento. Ver PRD US 2.2.

#### Scenario: Confirmação após envio
- **DADO** que enviei um processo para o Servidor "Maria Silva" da unidade AJUR
- **QUANDO** a operação é concluída com sucesso
- **ENTÃO** vejo mensagem confirmando o envio, nomeando Maria Silva e a AJUR, e o processo deixa de estar sob minha responsabilidade

#### Scenario: Confirmação após reatribuição informa prazo mantido
- **DADO** que reatribuí um processo para o Servidor "João Souza" do setor Protocolo
- **QUANDO** a operação é concluída com sucesso
- **ENTÃO** vejo mensagem confirmando a reatribuição para João Souza e informando explicitamente que o prazo do processo foi mantido

## ADDED Requirements

### Requirement: Envio de processo com destino explícito
O sistema SHALL permitir ao servidor responsável **enviar** o processo escolhendo explicitamente a **unidade**, o **setor** e o **servidor** de destino, acompanhados de uma **mensagem**. O setor escolhido SHALL pertencer à unidade escolhida, e o servidor SHALL pertencer ao setor escolhido e estar **ativo**. O servidor de destino SHALL ser diferente do servidor atualmente responsável — não é permitido enviar um processo para si mesmo. O envio SHALL transicionar o processo para "Em Tramitação", transferir a responsabilidade ao servidor de destino e gravar o evento correspondente no histórico imutável. O prazo do processo NÃO SHALL ser alterado pelo envio.

#### Scenario: Envio com destino válido
- **DADO** que sou o servidor responsável por um processo "Aberto" na unidade COFIN
- **QUANDO** envio o processo para o setor "Análise" da unidade AJUR, servidor "Maria Silva", com a mensagem "Segue para parecer jurídico"
- **ENTÃO** o processo passa a "Em Tramitação", Maria Silva passa a ser a responsável, a unidade e o setor atuais passam a ser AJUR/Análise, o evento é gravado no histórico com a mensagem, e o prazo permanece inalterado

#### Scenario: Envio para si mesmo é rejeitado
- **DADO** que sou o servidor responsável por um processo
- **QUANDO** tento enviá-lo escolhendo a mim mesmo como servidor de destino
- **ENTÃO** o sistema rejeita a operação informando que o destino deve ser um servidor diferente do responsável atual, e nada é alterado

#### Scenario: Setor fora da unidade escolhida é rejeitado
- **DADO** que estou preenchendo o destino de um envio com a unidade AJUR
- **QUANDO** informo um setor que pertence à unidade COFIN
- **ENTÃO** o sistema rejeita a operação como dado inconsistente e nenhum evento é gravado

#### Scenario: Servidor inativo não é destino válido
- **DADO** que o servidor "Carlos" do setor de destino está inativo
- **QUANDO** monto o destino do envio
- **ENTÃO** Carlos não aparece na lista de servidores selecionáveis, e uma tentativa direta de enviá-lo o processo é rejeitada

#### Scenario: Envio por quem não é o responsável atual — acesso negado
- **DADO** que um processo está sob responsabilidade do Servidor B e eu sou o Servidor D da mesma unidade
- **QUANDO** tento enviar esse processo
- **ENTÃO** o sistema rejeita a operação com acesso negado, nada é alterado, e a tentativa é registrada em log de segurança

### Requirement: Devolução ao remetente anterior
O sistema SHALL permitir ao servidor responsável **devolver** o processo, retornando-o ao **remetente anterior** — o servidor que lhe encaminhou o processo, resolvido automaticamente a partir do último evento de envio ou reatribuição do histórico. O destino NÃO SHALL ser escolhido pelo usuário nem aceito da requisição. A devolução SHALL exigir **motivo** e **justificativa**, transicionar o processo para "Em Tramitação" e gravar o evento no histórico. Quando não existir remetente anterior — processo ainda com seu criador, nunca tramitado — a devolução SHALL ser bloqueada. A devolução é a ação apropriada quando a **unidade** de destino estava errada. O prazo NÃO SHALL ser alterado.

#### Scenario: Devolução retorna ao remetente correto
- **DADO** que o Servidor A me enviou um processo e eu sou o responsável atual
- **QUANDO** devolvo o processo informando motivo "Documentação insuficiente" e uma justificativa
- **ENTÃO** o processo retorna ao Servidor A, à unidade e ao setor dele, o evento de devolução é gravado com motivo e justificativa, e o prazo permanece inalterado

#### Scenario: Destino da devolução não é informado pelo usuário
- **DADO** que estou na tela de devolução de um processo
- **QUANDO** visualizo os campos disponíveis
- **ENTÃO** o destino é apresentado apenas como leitura ("devolver para <servidor>"), sem campo editável; uma requisição que tente informar destino tem o valor ignorado ou rejeitado

#### Scenario: Devolução sem remetente anterior é bloqueada
- **DADO** que criei um processo e ele nunca foi enviado a ninguém — ainda estou como responsável
- **QUANDO** tento devolvê-lo
- **ENTÃO** o sistema bloqueia a operação informando que não há remetente anterior para o qual devolver, e nada é alterado

#### Scenario: Devolução sem motivo é rejeitada
- **DADO** que estou devolvendo um processo
- **QUANDO** submeto sem selecionar um motivo
- **ENTÃO** o sistema rejeita a operação com "Selecione um motivo para a devolução" e nenhum evento é gravado

### Requirement: Reatribuição de processo por atribuição indevida
O sistema SHALL permitir **reatribuir** um processo quando um servidor foi designado indevidamente. A reatribuição SHALL permanecer na **mesma unidade** em que o processo se encontra — a unidade de destino é fixa e não editável — podendo trocar de **setor** dentro dela, e SHALL obrigatoriamente designar um **servidor diferente** do responsável atual. A reatribuição SHALL exigir **justificativa**, NÃO SHALL alterar o status do processo e NÃO SHALL alterar o prazo. Quando a **unidade** estiver errada, a ação correta é a Devolução, não a Reatribuição.

Podem reatribuir: o **servidor responsável atual**, o **remetente da última tramitação** (quem cometeu o erro de destino) e o **Gestor da unidade atual**. Qualquer outro usuário SHALL receber acesso negado com registro em log de segurança. A verificação de papel SHALL ser aplicada **após** a autorização por unidade já existente, nunca em substituição a ela.

#### Scenario: Servidor que recebeu indevidamente reatribui
- **DADO** que recebi um processo por engano e o servidor correto é "João Souza", do setor Protocolo da mesma unidade
- **QUANDO** reatribuo o processo para João Souza informando a justificativa
- **ENTÃO** João Souza passa a ser o responsável, o setor atual passa a Protocolo, a unidade permanece a mesma, o status e o prazo permanecem inalterados, e o evento de reatribuição é gravado no histórico com a justificativa

#### Scenario: Remetente que errou o destino corrige
- **DADO** que enviei um processo para o Servidor B por engano, quando o correto era o Servidor C da mesma unidade
- **QUANDO** reatribuo o processo de B para C
- **ENTÃO** a operação é aceita — sou o remetente da última tramitação — e C passa a ser o responsável

#### Scenario: Gestor da unidade reatribui
- **DADO** que sou Gestor da unidade em que o processo se encontra e identifico uma atribuição indevida
- **QUANDO** reatribuo o processo para o servidor correto
- **ENTÃO** a operação é aceita, o evento registra a mim como responsável e os servidores de origem e destino como detentores — eu não figuro como detentor

#### Scenario: Reatribuição para outra unidade é rejeitada
- **DADO** que estou reatribuindo um processo que se encontra na unidade COFIN
- **QUANDO** tento designar um servidor da unidade AJUR
- **ENTÃO** o sistema rejeita a operação informando que a reatribuição não muda de unidade e que devolução é a ação apropriada nesse caso; nada é alterado

#### Scenario: Reatribuição para o mesmo servidor é rejeitada
- **DADO** que sou o responsável atual por um processo
- **QUANDO** tento reatribuí-lo para mim mesmo
- **ENTÃO** o sistema rejeita a operação informando que o destino deve ser um servidor diferente do responsável atual

#### Scenario: Reatribuição sem justificativa é rejeitada
- **DADO** que estou reatribuindo um processo
- **QUANDO** submeto sem preencher a justificativa
- **ENTÃO** o sistema rejeita a operação informando que a justificativa é obrigatória, e nenhum evento é gravado

#### Scenario: Reatribuição por servidor sem papel autorizado — acesso negado
- **DADO** que sou Servidor da mesma unidade do processo, mas não sou o responsável atual, nem o remetente da última tramitação, nem Gestor da unidade
- **QUANDO** tento reatribuir o processo
- **ENTÃO** o sistema rejeita a operação com acesso negado, nada é alterado, e a tentativa é registrada em log de segurança

#### Scenario: Reatribuição em processo concluído ou arquivado é bloqueada
- **DADO** que um processo está "Concluído" ou "Arquivado"
- **QUANDO** tento reatribuí-lo
- **ENTÃO** o sistema bloqueia a operação — a reatribuição só se aplica a processos em andamento

### Requirement: Conclusão como ação explícita
O sistema SHALL oferecer a **conclusão** do processo como ação própria, acionada por botão dedicado com confirmação, independente de qualquer ação de envio. A conclusão SHALL transicionar o processo de "Aberto" ou "Em Tramitação" para "Concluído", registrar o instante de conclusão, congelar o prazo de arquivamento a partir do parâmetro vigente em configuração do sistema e gravar o evento no histórico. Podem concluir o **servidor responsável atual** e o **Gestor da unidade atual**; qualquer outro usuário SHALL receber acesso negado com registro em log de segurança.

#### Scenario: Conclusão a partir de Em Tramitação
- **DADO** que sou o servidor responsável por um processo "Em Tramitação"
- **QUANDO** aciono "Concluir" e confirmo
- **ENTÃO** o processo passa a "Concluído", o instante de conclusão é registrado, o prazo de arquivamento é congelado e o evento de conclusão é gravado no histórico

#### Scenario: Conclusão a partir de Aberto
- **DADO** que criei um processo, ainda sou o responsável e ele nunca foi enviado
- **QUANDO** aciono "Concluir" e confirmo
- **ENTÃO** o processo passa diretamente de "Aberto" a "Concluído" — não é necessário enviá-lo a ninguém antes

#### Scenario: Cancelar a confirmação não altera nada
- **DADO** que acionei "Concluir" e a confirmação foi exibida
- **QUANDO** cancelo
- **ENTÃO** o processo permanece no status anterior e nenhum evento é gravado

#### Scenario: Conclusão por quem não é responsável nem gestor — acesso negado
- **DADO** que sou Servidor da mesma unidade mas não sou o responsável atual pelo processo
- **QUANDO** tento concluí-lo
- **ENTÃO** o sistema rejeita a operação com acesso negado, o status permanece inalterado, e a tentativa é registrada em log de segurança
