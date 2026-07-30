## REMOVED Requirements

### Requirement: Definição de roteiro de tramitação
**Motivo**: o cliente rejeitou a tramitação automática por roteiro na avaliação da primeira entrega (`docs/Ajustes SETES DOCS.pdf`): *"a tramitação automática entre unidades conforme o tipo de processo deixará de existir"*. O destino de cada movimentação passa a ser escolhido explicitamente pelo servidor.
**Migração**: as tabelas `roteiro` e `roteiro_etapa` são removidas, junto com a seção de configuração de roteiro na tela de administração de tipos de processo. Nenhum dado precisa ser preservado — a base em avaliação contém apenas dados de teste, e o rastro real de tramitação vive no histórico imutável.

### Requirement: Versionamento de roteiro
**Motivo**: sem roteiro não há versão de roteiro a manter vigente ou histórica.
**Migração**: nenhuma. A coluna `roteiro.vigente` e a noção de roteiro histórico deixam de existir junto com as tabelas.

## MODIFIED Requirements

### Requirement: Validação de tipo de processo
O sistema SHALL exigir um **tipo de processo** válido e **ativo** na criação de todo processo, rejeitando a criação quando o tipo não existir ou estiver inativo. O tipo de processo NÃO SHALL determinar o fluxo de tramitação — ele permanece como classificação usada em filtros do quadro de processos, em agregações do dashboard e no prazo de anonimização LGPD. Nenhuma validação de roteiro SHALL ser aplicada.

#### Scenario: Criação com tipo de processo válido
- **DADO** que o tipo "Requerimento" está cadastrado e ativo
- **QUANDO** crio um processo desse tipo
- **ENTÃO** o processo é criado normalmente, sem qualquer verificação de fluxo ou roteiro associado ao tipo

#### Scenario: Criação com tipo inexistente é rejeitada
- **DADO** que informo um identificador de tipo de processo que não existe
- **QUANDO** tento criar o processo
- **ENTÃO** o sistema rejeita a criação informando que o tipo de processo não foi encontrado

#### Scenario: Tela de administração sem configuração de fluxo
- **DADO** que estou autenticado como Administrador na tela de tipos de processo
- **QUANDO** abro um tipo de processo para edição
- **ENTÃO** vejo apenas nome, situação e prazo de anonimização LGPD — nenhuma seção de roteiro, etapas ou ordenação de unidades é exibida
