# tipos-processo

## Purpose

Cadastro de tipos de processo — classificação usada em filtros do quadro de
processos, agregações do dashboard e no prazo de anonimização LGPD — com
gestão restrita ao perfil Administrador. Change tramitacao-manual: os
requisitos de roteiro (definição, versionamento, validação de sequência de
unidades) foram removidos — o tipo de processo não determina mais o fluxo de
tramitação (ver capability `workflow-tramitacao`).

## Requirements

### Requirement: Validação de tipo de processo
O sistema SHALL exigir um **tipo de processo** válido e **ativo** na criação de todo processo, rejeitando a criação quando o tipo não existir ou estiver inativo. O tipo de processo NÃO SHALL determinar o fluxo de tramitação — ele permanece como classificação usada em filtros do quadro de processos, em agregações do dashboard e no prazo de anonimização LGPD. Nenhuma validação de roteiro SHALL ser aplicada. Ver PRD US 8.2.

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

### Requirement: Nome de tipo de processo único
O sistema SHALL rejeitar nomes de tipo de processo duplicados. Ver PRD US 8.2.

#### Scenario: Nome de tipo de processo duplicado
- **DADO** que já existe um tipo de processo chamado "Licitação"
- **QUANDO** tento criar outro tipo de processo com o mesmo nome
- **ENTÃO** o sistema rejeita a operação exibindo "Já existe um tipo de processo com este nome" (PRD US 8.2 Cen.2)

### Requirement: Gestão de tipos de processo restrita ao Administrador
O sistema SHALL restringir o cadastro e a edição de tipos de processo ao perfil Administrador.

#### Scenario: Gestor tenta gerenciar tipo de processo — acesso negado
- **DADO** que estou autenticado como Gestor
- **QUANDO** tento criar ou editar um tipo de processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar tipos de processo" e registra a tentativa em log de segurança

#### Scenario: Servidor tenta gerenciar tipo de processo — acesso negado
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento criar ou editar um tipo de processo
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar tipos de processo" e registra a tentativa em log de segurança

### Requirement: Prazo de anonimização LGPD configurável por tipo de processo
O sistema SHALL permitir que o Administrador configure, para cada tipo de processo, o
prazo legal de anonimização LGPD (em anos), usado pela rotina automática trimestral
(capability `anonimizacao-lgpd`) para determinar quando processos arquivados desse tipo
se tornam elegíveis para anonimização. O valor SHALL ser um número inteiro positivo, com
padrão de 5 anos quando não configurado, e a alteração SHALL se aplicar apenas a partir
da data da mudança, sem efeito retroativo sobre a contagem de processos já arquivados.
Ver PRD US 10.3 Cen.2.

#### Scenario: Configuração do prazo de anonimização de um tipo de processo
- **DADO** que estou autenticado como Administrador
- **QUANDO** acesso as configurações de um tipo de processo e defino o prazo de anonimização LGPD em 5 anos
- **ENTÃO** o sistema registra a configuração e exibe "Prazo de anonimização configurado: 5 anos. A partir desta data, processos deste tipo serão anonimizados após 5 anos de arquivamento." (PRD US 10.3 Cen.2)

#### Scenario: Valor padrão quando nunca configurado
- **DADO** que um tipo de processo nunca teve o prazo de anonimização LGPD alterado
- **QUANDO** a rotina trimestral de anonimização avalia processos arquivados desse tipo
- **ENTÃO** ela usa o valor padrão de 5 anos

#### Scenario: Valor inválido rejeitado
- **DADO** que estou autenticado como Administrador configurando o prazo de anonimização LGPD de um tipo de processo
- **QUANDO** informo um valor zero ou negativo
- **ENTÃO** o sistema rejeita a configuração exibindo que o valor deve ser um número inteiro positivo

#### Scenario: Acesso negado — perfil não-Administrador
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento configurar o prazo de anonimização LGPD de um tipo de processo
- **ENTÃO** a operação é rejeitada com acesso negado e o parâmetro permanece inalterado
