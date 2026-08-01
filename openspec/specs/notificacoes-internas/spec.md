# notificacoes-internas

## Purpose

Notificação interna (sino) dirigida à pessoa — geração nos eventos de envio, reatribuição e
conclusão e no alerta diário de prazo, com estado lido/não-lido, contador persistente por
usuário, retenção de 30 dias para lidas e cenários de acesso negado (só o próprio destinatário
lê/marca suas notificações). Cobre PRD US 5.1, 5.3 e 5.4.

## Requirements

### Requirement: Notificação interna de novo processo recebido
O sistema SHALL gerar uma notificação interna dirigida ao **servidor de destino** sempre que um processo lhe for enviado, e NÃO SHALL mais notificar todos os servidores da unidade de destino. A notificação SHALL conter número do processo, assunto, unidade de origem e o servidor remetente, e SHALL alimentar o contador do sino do destinatário. A notificação nasce como **não lida**. Ver PRD US 5.1.

#### Scenario: Apenas o destinatário é notificado
- **DADO** que a unidade AJUR possui cinco servidores e um processo é enviado especificamente para "Maria Silva"
- **QUANDO** o envio é concluído
- **ENTÃO** apenas Maria Silva recebe a notificação interna e vê o contador do sino incrementado; os demais servidores da AJUR não recebem notificação alguma

#### Scenario: Notificação identifica o remetente
- **DADO** que recebi um processo enviado pelo Servidor "João Souza" da COFIN
- **QUANDO** abro a lista de notificações
- **ENTÃO** a notificação informa o número do processo, o assunto, a unidade COFIN e João Souza como remetente

#### Scenario: Abertura do painel não zera o contador (US 5.1 Cen.2)
- **DADO** que um servidor tem 3 notificações não lidas
- **QUANDO** ele abre o painel do sino
- **ENTÃO** as 3 notificações são exibidas com indicador visual de "não lida" e o contador
  permanece em 3 — a leitura só ocorre por ação explícita (clicar na notificação ou "Marcar
  todas como lidas")

#### Scenario: Persistência entre sessões (US 5.1 Cen.3)
- **DADO** que um servidor tinha 2 notificações não lidas ao fazer logout
- **QUANDO** ele faz login novamente
- **ENTÃO** o contador ainda exibe 2 notificações pendentes

#### Scenario: Acesso negado — notificação é visível apenas ao destinatário
- **DADO** que existe uma notificação endereçada ao servidor X
- **QUANDO** o servidor Y (outra pessoa, ainda que da mesma unidade destino tenha a sua
  própria) solicita a listagem de notificações
- **ENTÃO** ele recebe apenas as próprias notificações; a notificação de X nunca aparece na
  resposta de Y

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

### Requirement: Notificação interna de alerta de prazo
O sistema SHALL gerar, quando a rotina diária de verificação de prazos identifica um
processo cujo `prazo_em` está a vencer dentro da janela configurada (parâmetro "Dias de
antecedência para alerta de prazo"), uma notificação interna do tipo `alerta_prazo` para
**cada servidor da unidade atual do processo**, contendo número, assunto, prazo e dias
restantes. Ver PRD US 5.4.

#### Scenario: Rotina diária gera alerta interno aos servidores da unidade atual
- **DADO** que um processo na unidade D tem `prazo_em` dentro da janela de antecedência
  configurada e ainda não está concluído/arquivado
- **QUANDO** a rotina diária de verificação de prazos é executada
- **ENTÃO** cada servidor da unidade D recebe uma notificação `alerta_prazo` não lida com
  número, assunto, prazo e dias restantes

#### Scenario: Sem alerta interno para processo fora da janela
- **DADO** que um processo tem `prazo_em` além da janela de antecedência configurada
- **QUANDO** a rotina diária é executada
- **ENTÃO** nenhuma notificação `alerta_prazo` é gerada para esse processo

### Requirement: Marcação de leitura e contador do sino
O sistema SHALL manter, por notificação, um estado lido/não-lido (`lida_em` nullable) e
expor as operações de marcar **uma** notificação como lida e marcar **todas** as próprias
como lidas. O contador do sino SHALL refletir apenas as notificações não lidas do próprio
usuário. Ver PRD US 5.1 Cen.2.

#### Scenario: Marcar uma notificação como lida decrementa o contador
- **DADO** que um servidor tem 3 notificações não lidas
- **QUANDO** ele aciona a leitura de uma notificação específica
- **ENTÃO** aquela notificação passa a `lida` e o contador do sino passa a 2

#### Scenario: Marcar todas como lidas zera o contador
- **DADO** que um servidor tem notificações não lidas
- **QUANDO** ele aciona "Marcar todas como lidas"
- **ENTÃO** todas as suas notificações não lidas passam a `lida` e o contador do sino passa a 0

#### Scenario: Acesso negado — não é possível marcar notificação de outro usuário
- **DADO** que existe uma notificação pertencente ao servidor X
- **QUANDO** o servidor Y tenta marcá-la como lida
- **ENTÃO** a operação é rejeitada (a notificação de X permanece inalterada) e o registro de
  rejeição segue o padrão de acesso negado do sistema

### Requirement: Retenção e visibilidade da lista de notificações
O sistema SHALL listar as notificações do próprio usuário mantendo as **lidas** acessíveis
no histórico por 30 dias após a leitura; notificações **não lidas** SHALL permanecer sempre
visíveis, independentemente da idade. Ver PRD US 5.1 Cen.4/Cen.4b. (A remoção física das
lidas antigas é executada pela rotina diária — ver capability `rotinas-agendadas`.)

#### Scenario: Notificação lida há mais de 30 dias não aparece na lista (US 5.1 Cen.4)
- **DADO** que um servidor leu uma notificação há mais de 30 dias
- **QUANDO** ele acessa o histórico de notificações
- **ENTÃO** essa notificação não aparece mais na listagem

#### Scenario: Notificação não lida antiga permanece visível (US 5.1 Cen.4b)
- **DADO** que uma notificação foi gerada há mais de 30 dias e ainda NÃO foi lida
- **QUANDO** o servidor acessa a lista de notificações
- **ENTÃO** ela permanece visível normalmente como "não lida" e continua contando no sino;
  o expurgo automático NÃO a remove
