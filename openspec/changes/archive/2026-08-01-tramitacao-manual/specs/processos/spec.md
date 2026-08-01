## REMOVED Requirements

### Requirement: Snapshot do roteiro na criação
**Motivo**: a tramitação automática por roteiro foi rejeitada pelo cliente na avaliação da primeira entrega. Sem roteiro não há snapshot a congelar — o processo passa a registrar diretamente unidade, setor e servidor atuais.
**Migração**: as colunas `processo.roteiro_id` e `processo.ordem_atual` são removidas, assim como as tabelas `roteiro` e `roteiro_etapa`. O rastro de por onde o processo passou permanece integralmente no histórico imutável de tramitação, que passa a registrar setor e servidor.

## MODIFIED Requirements

### Requirement: Criação de processo com número único
O sistema SHALL permitir ao Servidor criar um processo informando tipo de processo, assunto, prazo em dias e interessados, atribuindo um **número único** no formato `AAAA/NNNNNN`. Na criação, o processo SHALL nascer com status "Aberto", com a **unidade, o setor e o servidor do criador** como unidade, setor e servidor atuais — ou seja, **atribuído ao próprio criador** — de modo que passe a constar imediatamente na sua área de trabalho, antes de qualquer tramitação. A unidade de origem SHALL ser registrada e permanecer imutável. A criação NÃO SHALL depender de roteiro nem de qualquer configuração de fluxo do tipo de processo. Ver PRD US 2.1.

#### Scenario: Criação atribui o processo ao criador
- **DADO** que sou Servidor da unidade COFIN, setor "Protocolo"
- **QUANDO** crio um processo informando tipo, assunto, prazo e interessados
- **ENTÃO** o processo é criado com número único no formato `AAAA/NNNNNN`, status "Aberto", unidade atual COFIN, setor atual Protocolo e **eu** como servidor responsável

#### Scenario: Criação não exige roteiro configurado
- **DADO** que o tipo de processo escolhido não possui nenhuma configuração de fluxo
- **QUANDO** crio o processo
- **ENTÃO** a criação é concluída normalmente — nenhuma validação de roteiro é aplicada, porque roteiros não existem mais no sistema

#### Scenario: Criação por usuário sem setor é rejeitada
- **DADO** que sou um Servidor cujo cadastro não possui setor vinculado
- **QUANDO** tento criar um processo
- **ENTÃO** o sistema rejeita a operação informando que é necessário estar vinculado a um setor, e nenhum processo é criado

#### Scenario: Unidade de origem é imutável
- **DADO** que um processo foi criado na unidade COFIN e depois enviado para AJUR e DIRAD
- **QUANDO** consulto o processo
- **ENTÃO** a unidade de origem continua sendo COFIN, independentemente da unidade atual

## ADDED Requirements

### Requirement: Responsável atual do processo
O sistema SHALL registrar, em cada processo, o **setor atual** e o **servidor atualmente responsável**, atualizados a cada ação de tramitação (Envio, Devolução, Reatribuição). O servidor responsável SHALL ser sempre um usuário existente — o processo nunca fica sem responsável. Além do responsável corrente, o sistema SHALL preservar de forma permanente o **servidor criador** e, por meio do histórico imutável de tramitação, a **sequência completa de servidores** que detiveram o processo.

#### Scenario: Responsável acompanha a tramitação
- **DADO** que um processo foi criado por A, enviado para B, reatribuído para C e devolvido para A
- **QUANDO** consulto o processo em cada momento
- **ENTÃO** o servidor responsável é, respectivamente, A, B, C e A — sempre exatamente um servidor

#### Scenario: Sequência de detentores recuperável do histórico
- **DADO** que um processo passou pelos servidores A, B e C
- **QUANDO** consulto seu histórico de tramitação
- **ENTÃO** consigo reconstruir a sequência completa de detentores a partir dos servidores de origem e destino dos eventos, somada ao criador registrado no processo

#### Scenario: Criador preservado após a saída do processo
- **DADO** que criei um processo e o enviei para outra unidade há meses
- **QUANDO** consulto o processo
- **ENTÃO** continuo registrado como seu criador, ainda que não seja mais o responsável atual
