# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão
* **Score de Prontidão:** 7.0
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS apresenta estrutura sólida, BDD bem aplicado na maioria das User Stories e excelente definição de escopo MVP com exclusões explícitas. Não há vazamento relevante de decisões de arquitetura técnica. No entanto, o documento sofre de um problema sistêmico: **thresholds de negócio estão hardcoded nos cenários BDD sem a devida contrapartida de configurabilidade**. Parâmetros como "7 dias para processos parados", "48h para link de primeiro acesso", "3 tentativas de bloqueio", entre outros, são regras de negócio que deveriam ser administráveis via interface (US 8.5), mas não estão listados como configuráveis. Além disso, há lacunas funcionais relevantes (ausência de reset de senha pelo Admin, decisão de hard delete sem soft-delete) e omissões em requisitos não funcionais (paginação, degradação de performance). O documento **não está pronto para a engenharia** e requer uma rodada de correções antes do handoff para o OpenSpec.

---

## 2. Pontos Críticos Identificados

* **CRÍTICO — Thresholds de negócio não configuráveis (Sistêmico):** Múltiplos parâmetros de negócio aparecem como valores fixos nos cenários BDD, mas a US 8.5 (Configurações do Sistema) cobre apenas "prazo de arquivamento" e "timeout de sessão". Os seguintes parâmetros deveriam ser configuráveis e não estão: (a) dias para considerar processo "parado" (7 dias — US 6.1); (b) validade do link de primeiro acesso (48h — US 1.6); (c) validade do link de reset de senha (2h — US 1.3); (d) período de retenção de notificações lidas (30 dias — US 5.1); (e) profundidade do histórico de senhas (6 — US 1.7); (f) número de tentativas antes do bloqueio (3 — US 1.3); (g) duração do bloqueio (30 min — US 1.3 e US 4.1). Sem esses parâmetros na tela de configuração, qualquer ajuste futuro exigirá alteração de código.

* **CRÍTICO — Ausência de User Story para reset de senha pelo Administrador:** O PRD cobre auto-recuperação de senha pelo usuário (US 1.3, Cenário 3), mas não prevê o cenário administrativo em que um Administrador precisa resetar a senha de um usuário (ex.: servidor incapacitado, conta comprometida). Esta é uma função administrativa básica e sua ausência é uma lacuna de escopo.

* **CRÍTICO — Decisão de Hard Delete em documentos (US 3.1):** Os Cenários 3, 4b e 4c especificam que a exclusão de documentos remove permanentemente o arquivo físico do armazenamento ("o arquivo físico é excluído"). Para um sistema de processos administrativos com requisitos de auditoria (RNF de Segurança exige "histórico de tramitação imutável e à prova de adulteração"), a ausência de soft-delete (exclusão lógica com possibilidade de recuperação) é uma decisão de produto de alto risco. O PRD deveria ao menos justificar essa escolha ou propor um mecanismo de lixeira com expurgo programado.

* **ALTO — Vazamento de implementação em US 8.0:** O Cenário 2 menciona o caminho de URL `/setup`. Este é um detalhe de implementação (rota HTTP) que não pertence ao PRD. Deve ser substituído por descrição funcional: "tentar acessar a funcionalidade de inicialização".

* **ALTO — Formato do número de processo sem tratamento de overflow:** A US 2.1 define o formato `AAAA/NNNNNN` (6 dígitos sequenciais, reiniciado a cada ano). Não há especificação do comportamento quando o sequencial anual ultrapassar 999.999. Embora seja um cenário extremo, sistemas de governo podem ter volumes imprevisíveis e o PRD deve definir o comportamento esperado.

* **ALTO — RNF de Performance sem definição de degradação:** O RNF de Performance especifica "até 3 segundos para unidades com até 500 processos ativos", mas não define o comportamento esperado acima desse limite. A engenharia precisa saber: acima de 500 processos, deve-se implementar paginação? Qual o tempo de resposta aceitável? O SLA é por unidade ou por sistema?

* **MÉDIO — Ausência de especificação de paginação nas buscas (US 2.7 e US 7.2):** Nenhum cenário aborda o comportamento quando uma busca retorna dezenas ou centenas de resultados. A paginação é implícita, mas não especificada — quantos itens por página? Ordenação padrão? O usuário pode escolher quantos resultados por página?

* **MÉDIO — Sem warning de expiração de sessão (US 1.8):** O Cenário 2 especifica que após 30 minutos de inatividade a sessão é encerrada e o usuário é redirecionado ao login. Não há menção a um aviso prévio (ex.: modal "Sua sessão expirará em 2 minutos. Deseja continuar?"). Isso representa risco de perda de trabalho não salvo e degradação da experiência do usuário.

* **MÉDIO — Falta de comportamento para roteiro com 1 unidade (US 2.2):** O Cenário 2 cobre "última unidade do roteiro", mas não especifica o comportamento quando o roteiro tem uma única unidade. Um processo criado nessa unidade já está na última? Deve ser criado como "Aberto" e o primeiro despacho o conclui? Essa clareza é necessária.

* **MÉDIO — US 8.6 Cenário 1 (desativação de unidade):** A desvinculação automática de usuários ao desativar uma unidade é especificada, mas não há menção a envio de e-mail notificando os usuários afetados. Sem notificação, servidores podem descobrir que perderam acesso apenas ao tentar fazer login.

* **BAIXO — US 10.3: Prazo de anonimização sem base legal explícita:** O prazo de 5 anos para anonimização de dados de processos arquivados é mencionado como "prazo legal", mas não referencia qual norma ou lei fundamenta esse prazo. Além disso, não especifica se o sistema deve impedir que o Administrador configure prazo inferior ao mínimo legal.

* **BAIXO — Consulta pública sem proteção anti-bot além de rate limit:** O RNF de Segurança define limite de 60 consultas/minuto por IP, mas não menciona CAPTCHA ou outras proteções contra bots determinados. Para um portal público, o rate limit por IP pode ser insuficiente (bots podem rotacionar IPs).

---

## 3. Propostas de Correção Direta

### Correção 1: Thresholds de Negócio Configuráveis (US 8.5)

* **Como está no PRD original (US 8.5):** 
  > A US 8.5 lista apenas dois parâmetros configuráveis: prazo de arquivamento e timeout de sessão. Nenhum outro threshold de negócio aparece como configurável.

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 8.5 (Expandida):** Como Administrador, eu quero configurar os parâmetros operacionais do sistema para adequá-lo às políticas do órgão.
  > 
  > *Parâmetros adicionais que devem ser incluídos na tela de Configurações do Sistema:*
  > * **Prazo para "Processos Parados"** (padrão: 7 dias) — afeta US 6.1
  > * **Validade do link de primeiro acesso** (padrão: 48 horas) — afeta US 1.6
  > * **Validade do link de recuperação de senha** (padrão: 2 horas) — afeta US 1.3
  > * **Retenção de notificações lidas** (padrão: 30 dias) — afeta US 5.1
  > * **Profundidade do histórico de senhas** (padrão: 6) — afeta US 1.7
  > * **Tentativas máximas de login antes do bloqueio** (padrão: 3) — afeta US 1.3
  > * **Duração do bloqueio por tentativas excedidas** (padrão: 30 minutos) — afeta US 1.3 e US 4.1
  > * **Dias de antecedência para alerta de prazo** (padrão: 2 dias corridos) — afeta US 5.2 e US 5.4
  > 
  > Para cada parâmetro, aplicar os cenários de validação padrão: valor positivo obrigatório, confirmação visual da alteração, e aplicação a novos eventos (não retroativo, exceto quando explicitamente especificado o contrário na US correspondente).

### Correção 2: Reset de Senha pelo Administrador (Nova US 1.10)

* **Como está no PRD original:** 
  > (Inexistente — lacuna de escopo)

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 1.10:** Como Administrador, eu quero resetar a senha de um usuário para restaurar o acesso em casos de conta comprometida ou impossibilidade de auto-recuperação.
  > 
  > * **Cenário 1: Reset de senha de usuário ativo**
  >   * **Dado** que estou autenticado como Administrador e acesso um usuário com status "Ativo"
  >   * **Quando** aciono "Resetar Senha" e confirmo a operação
  >   * **Então** a senha atual do usuário é invalidada, um link de redefinição com validade de 2 horas é enviado ao e-mail cadastrado, e o evento é registrado em log de auditoria com data, hora e Administrador responsável
  > * **Cenário 2: Reset de senha de usuário inativo**
  >   * **Dado** que estou autenticado como Administrador e acesso um usuário com status "Inativo"
  >   * **Quando** aciono "Resetar Senha"
  >   * **Então** o sistema exibe "Não é possível resetar a senha de um usuário inativo. Reative o usuário antes de prosseguir."

### Correção 3: Deleção de Documentos — Substituir Hard Delete por Soft Delete

* **Como está no PRD original (US 3.1):** 
  > "o documento é removido da lista de anexos do processo, o arquivo físico é excluído do armazenamento, e a exclusão é registrada no histórico do processo"

* **Como deve ficar (Sugestão de Reescrita):**
  > "o documento é removido da lista de anexos visíveis do processo, o arquivo é preservado em área de retenção (soft delete) por 30 dias, e a exclusão lógica é registrada no histórico do processo com data, hora e responsável. Durante o período de retenção, o Administrador pode restaurar o documento. Após 30 dias, o arquivo físico é excluído permanentemente de forma automática."

### Correção 4: Remover Vazamento de Implementação (US 8.0)

* **Como está no PRD original (US 8.0, Cenário 2):** 
  > "Quando qualquer pessoa tenta acessar `/setup`"

* **Como deve ficar (Sugestão de Reescrita):**
  > "Quando qualquer pessoa tenta acessar a funcionalidade de inicialização do sistema após a conclusão do setup"

### Correção 5: Tratamento de Overflow do Número de Processo (US 2.1)

* **Como está no PRD original (US 2.1, Cenário 1):** 
  > "um número único gerado automaticamente no formato AAAA/NNNNNN (ano com 4 dígitos + sequencial com 6 dígitos, reiniciado a cada ano, ex.: 2026/000001)"

* **Como deve ficar (Sugestão de Reescrita):**
  > "um número único gerado automaticamente no formato AAAA/NNNNNN (ano com 4 dígitos + sequencial com 6 dígitos, reiniciado a cada ano, ex.: 2026/000001). Caso o sequencial anual atinja o limite de 999.999, o sistema deve expandir automaticamente para 7 dígitos (AAAA/NNNNNNN), registrando o evento em log de sistema."

### Correção 6: RNF de Performance com Degradação

* **Como está no PRD original (RNF — Performance):** 
  > "O quadro Kanban deve carregar em até 3 segundos para unidades com até 500 processos ativos."

* **Como deve ficar (Sugestão de Reescrita):**
  > "O quadro Kanban deve carregar em até 3 segundos para unidades com até 500 processos ativos. Para unidades com mais de 500 processos ativos, o sistema deve implementar paginação automática (50 cards por página) mantendo o tempo de carregamento abaixo de 3 segundos. A consulta pública deve retornar resultados paginados (20 resultados por página) em até 5 segundos."

### Correção 7: Warning de Expiração de Sessão (US 1.8)

* **Como está no PRD original (US 1.8, Cenário 2):** 
  > (Apenas define o timeout e redirecionamento)

* **Como deve ficar (Sugestão de Reescrita — adicionar Cenário 2b):**
  > * **Cenário 2b: Aviso prévio de expiração de sessão**
  >   * **Dado** que estou autenticado no sistema e estou inativo há 28 minutos (2 minutos antes do timeout de 30 minutos)
  >   * **Quando** o sistema detecta a proximidade da expiração
  >   * **Então** exibo um modal com a mensagem "Sua sessão expirará em 2 minutos por inatividade. Deseja continuar?" com as opções "Continuar Sessão" (mantém a sessão ativa e reseta o contador) e "Sair" (encerra a sessão imediatamente). Se o usuário não responder em 2 minutos, a sessão é expirada conforme Cenário 2.

### Correção 8: Comportamento de Roteiro com 1 Unidade (US 2.2)

* **Como está no PRD original (US 2.2):** 
  > (Não aborda o caso de roteiro com uma única unidade)

* **Como deve ficar (Sugestão de Reescrita — adicionar Cenário 4):**
  > * **Cenário 4: Roteiro com unidade única**
  >   * **Dado** que um tipo de processo possui roteiro com apenas uma unidade e um processo desse tipo foi criado nessa mesma unidade (status "Aberto")
  >   * **Quando** o servidor da unidade aciona "Despachar"
  >   * **Então** o sistema exibe a mensagem "Esta é a unidade de origem e destino final do roteiro. Deseja concluir o processo?" (equivalente ao Cenário 2). Ao confirmar, o status é alterado para "Concluído".

---

## 4. Próximos Passos

1. **Aplicar as correções listadas na Seção 3 deste relatório**, priorizando os itens Críticos e Altos.
2. Após as correções, **re-executar a auditoria** (Fase 3) para verificar se o Score de Prontidão atingiu 8.0 ou superior.
3. Somente com Score ≥ 8.0, prosseguir para a **Fase 4 (Patcher)** para transformar o PRD em especificações no formato OpenSpec ou ferramenta de SDD equivalente.
4. **Recomendação adicional:** Validar com o cliente ou stakeholder de negócio os valores padrão dos thresholds agora tornados configuráveis (Correção 1), para garantir que os defaults reflitam a política real do órgão.

---
*Relatório gerado em 09/07/2026 — Fase 3 (PRD Reviewer) do pipeline de produto SETES.DOCS.*
