# notificacoes-internas

## Purpose

Notificação interna (sino) por servidor/unidade — geração nos eventos de despacho e conclusão
e no alerta diário de prazo, com estado lido/não-lido, contador persistente por usuário,
retenção de 30 dias para lidas e cenários de acesso negado (só o próprio destinatário lê/marca
suas notificações). Cobre PRD US 5.1, 5.3 e 5.4.

## Requirements

### Requirement: Notificação interna de novo processo recebido
O sistema SHALL gerar, ao concluir um despacho (`Tramitacao` com `tipo_evento = DESPACHO`)
para uma unidade destino, uma notificação interna do tipo `novo_processo` para **cada
servidor vinculado à unidade destino**, contendo número do processo, assunto e unidade de
origem. A notificação nasce como **não lida**. Ver PRD US 5.1.

#### Scenario: Despacho gera notificação aos servidores do destino
- **DADO** que um processo é despachado da unidade A para a unidade B
- **QUANDO** o despacho é concluído
- **ENTÃO** cada servidor da unidade B passa a ter uma notificação `novo_processo` não lida
  com número do processo, assunto e unidade de origem (A), refletida no contador do sino

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
O sistema SHALL gerar, ao registrar a conclusão de um processo (`Tramitacao` com
`tipo_evento = CONCLUSAO`, transição de estado para `Concluído`), uma notificação interna do
tipo `concluido` para **cada servidor da unidade em que o processo foi concluído**, contendo
número do processo, assunto e data de conclusão. Ver PRD US 5.3.

#### Scenario: Conclusão notifica os servidores da unidade de conclusão
- **DADO** que um processo na unidade C atinge a última etapa do roteiro e é concluído
- **QUANDO** a transição para `Concluído` é registrada
- **ENTÃO** cada servidor da unidade C recebe uma notificação `concluido` não lida com
  número do processo, assunto e data de conclusão

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
