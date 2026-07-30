## MODIFIED Requirements

### Requirement: Notificação interna de novo processo recebido
O sistema SHALL gerar uma notificação interna dirigida ao **servidor de destino** sempre que um processo lhe for enviado, e NÃO SHALL mais notificar todos os servidores da unidade de destino. A notificação SHALL conter número do processo, assunto, unidade de origem e o servidor remetente, e SHALL alimentar o contador do sino do destinatário. Ver PRD US 5.1.

#### Scenario: Apenas o destinatário é notificado
- **DADO** que a unidade AJUR possui cinco servidores e um processo é enviado especificamente para "Maria Silva"
- **QUANDO** o envio é concluído
- **ENTÃO** apenas Maria Silva recebe a notificação interna e vê o contador do sino incrementado; os demais servidores da AJUR não recebem notificação alguma

#### Scenario: Notificação identifica o remetente
- **DADO** que recebi um processo enviado pelo Servidor "João Souza" da COFIN
- **QUANDO** abro a lista de notificações
- **ENTÃO** a notificação informa o número do processo, o assunto, a unidade COFIN e João Souza como remetente

### Requirement: Notificação interna de processo concluído
O sistema SHALL gerar uma notificação interna quando um processo for concluído, dirigida ao **servidor criador** do processo — que tem interesse direto no desfecho — quando ele não for o próprio autor da conclusão. Ver PRD US 5.3.

#### Scenario: Criador é avisado da conclusão
- **DADO** que criei um processo e ele tramitou até ser concluído por outro servidor
- **QUANDO** a conclusão é registrada
- **ENTÃO** recebo notificação interna informando que o processo que criei foi concluído

#### Scenario: Autor da conclusão não é notificado de si mesmo
- **DADO** que criei um processo e eu mesmo o concluo
- **QUANDO** a conclusão é registrada
- **ENTÃO** nenhuma notificação de conclusão é gerada para mim

## ADDED Requirements

### Requirement: Notificação de processo recebido por reatribuição
O sistema SHALL gerar uma notificação interna ao **servidor que passou a deter o processo** por reatribuição, distinguindo-a da notificação de envio comum — o servidor precisa saber que o processo lhe chegou por correção de uma atribuição indevida, e não por encaminhamento regular. A notificação SHALL conter número do processo, assunto e a justificativa da reatribuição.

#### Scenario: Novo responsável é notificado da reatribuição
- **DADO** que o Servidor B reatribuiu para mim um processo que havia recebido indevidamente
- **QUANDO** a reatribuição é concluída
- **ENTÃO** recebo notificação interna identificando o processo como recebido por reatribuição, com a justificativa informada, e o contador do meu sino é incrementado

### Requirement: Notificação de destino corrigido ao remetente original
O sistema SHALL gerar uma notificação interna ao **remetente original** — o servidor que encaminhou o processo ao destinatário indevido — informando que sua atribuição foi corrigida e para qual servidor o processo foi reatribuído. O texto SHALL ser factual, sem juízo de valor. A notificação NÃO SHALL ser gerada quando o remetente original for o próprio autor da reatribuição, nem quando não houver remetente original identificável.

#### Scenario: Remetente é informado da correção
- **DADO** que enviei um processo ao Servidor B e ele o reatribuiu ao Servidor C
- **QUANDO** a reatribuição é concluída
- **ENTÃO** recebo notificação interna informando que o processo que encaminhei foi reatribuído para o Servidor C

#### Scenario: Autor da correção não é notificado de si mesmo
- **DADO** que enviei um processo ao Servidor B por engano e eu mesmo o reatribuí ao Servidor C
- **QUANDO** a reatribuição é concluída
- **ENTÃO** recebo apenas a confirmação da ação em tela; nenhuma notificação de destino corrigido é gerada para mim

#### Scenario: Reatribuição sem remetente original não gera aviso
- **DADO** que criei um processo, nunca o enviei, e o Gestor da unidade o reatribuiu para outro servidor
- **QUANDO** a reatribuição é concluída
- **ENTÃO** o novo responsável é notificado da reatribuição, e nenhuma notificação de destino corrigido é gerada — não houve remetente que tenha errado o destino
