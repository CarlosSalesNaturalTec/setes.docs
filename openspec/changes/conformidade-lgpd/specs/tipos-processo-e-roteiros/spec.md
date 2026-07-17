## ADDED Requirements

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
