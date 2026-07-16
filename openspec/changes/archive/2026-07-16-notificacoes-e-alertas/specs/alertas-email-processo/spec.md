## ADDED Requirements

### Requirement: E-mail de novo processo recebido
O sistema SHALL enfileirar, ao concluir um despacho para uma unidade destino, uma tarefa de
e-mail na fila Cloud Tasks existente (`emails`) para **cada servidor da unidade destino**,
com assunto "Novo processo recebido — [Número do Processo]" e corpo contendo número,
assunto, unidade de origem e link direto para o processo. Ver PRD US 5.2 Cen.1.

#### Scenario: Despacho enfileira e-mail aos servidores do destino
- **DADO** que um processo é despachado para a unidade B
- **QUANDO** o despacho é concluído
- **ENTÃO** uma tarefa de e-mail "Novo processo recebido — [Nº]" é enfileirada para cada
  servidor da unidade B, com número, assunto, unidade de origem e link de acesso

### Requirement: E-mail de alerta de prazo próximo
O sistema SHALL enfileirar, quando a rotina diária de verificação de prazos identifica um
processo dentro da janela de antecedência configurada, uma tarefa de e-mail para **cada
servidor da unidade atual** do processo, com assunto "Prazo próximo — [Número do Processo]"
e corpo contendo número, prazo e dias restantes. Ver PRD US 5.2 Cen.2.

#### Scenario: Rotina diária enfileira e-mail de prazo aos servidores da unidade atual
- **DADO** que um processo na unidade D tem `prazo_em` dentro da janela de antecedência
- **QUANDO** a rotina diária de verificação de prazos é executada
- **ENTÃO** uma tarefa de e-mail "Prazo próximo — [Nº]" é enfileirada para cada servidor da
  unidade D, com número, prazo e dias restantes

### Requirement: Falha de entrega não redespacha nem afeta a notificação interna
O sistema SHALL, em caso de falha na entrega do e-mail, registrar a falha em log do sistema
(acessível ao Administrador) com data, hora, destinatário e motivo, confirmar a tarefa (ACK)
sem redespacho automático (fila `maxAttempts=1`) e NÃO impactar a notificação interna
correspondente. Ver PRD US 5.2 Cen.3.

#### Scenario: Falha de e-mail registra log, ACK e preserva o sino
- **DADO** que o e-mail cadastrado de um servidor está inacessível (caixa cheia/servidor
  rejeita) e há um evento que dispara e-mail e notificação interna
- **QUANDO** o endpoint interno tenta enviar o e-mail e a entrega falha
- **ENTÃO** a falha é registrada em log com data/hora/destinatário/motivo, a tarefa é
  confirmada sem nova tentativa, e a notificação interna do mesmo evento permanece intacta
  no sino do servidor

### Requirement: E-mails de processo não expõem dados pessoais de interessados
O sistema SHALL limitar o corpo dos e-mails de evento de processo a número do processo,
assunto, unidade e (quando aplicável) prazo/dias restantes e link, NÃO incluindo CPF, CNPJ
ou qualquer dado pessoal de interessado. Os destinatários são servidores autenticados
(dados funcionais). Conformidade LGPD.

#### Scenario: Corpo do e-mail sem CPF/CNPJ de interessado
- **DADO** que um processo possui interessados com CPF/CNPJ cadastrados
- **QUANDO** um e-mail de novo processo ou de alerta de prazo é gerado para os servidores
- **ENTÃO** o corpo do e-mail contém apenas número, assunto, unidade, prazo/link, e nenhum
  CPF/CNPJ ou dado pessoal de interessado é incluído
