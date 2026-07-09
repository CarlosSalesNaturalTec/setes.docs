# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 6.5 / 10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS apresenta uma base sólida: personas bem definidas, escopo de MVP claro e a maioria das Histórias de Usuário segue o formato BDD com caminhos tristes relevantes. No entanto, o documento contém lacunas estruturais graves: a persona "Auditor / Controlador Interno" foi descrita na Seção 2 mas não possui UMA única História de Usuário sequer — isso configura uma persona órfã. O Requisito Funcional 24 (Perfil do Usuário) também não possui US correspondente. Além disso, diversas USs possuem apenas um cenário (feliz), sem cobertura de borda, e há microvazamentos de decisão técnica (real-time updates, visualização inline de PDF). O documento **não está pronto para a engenharia** e requer uma rodada de correções antes de seguir para OpenSpec/SDD.

---

## 2. Pontos Críticos Identificados

* **Persona órfã — Auditor / Controlador Interno:** A Seção 2 descreve detalhadamente a persona "Auditor / Controlador Interno" com dores específicas (dificuldade de rastrear cadeia completa, extrair dados para fiscalização), mas não existe NENHUMA História de Usuário ou Épico dedicado a ela. Ou a persona é necessária (e precisa de USs) ou deve ser removida do documento para não gerar expectativas falsas na engenharia.

* **Requisito Funcional 24 sem História de Usuário correspondente:** O RF 24 ("O perfil do usuário deve exibir a relação de processos em que atuou e documentos assinados") está listado nos Requisitos Funcionais e no escopo do MVP, mas não há US que o implemente. A engenharia não tem de onde extrair critérios de aceitação para construir essa funcionalidade.

* **US 1.1 — Cenário insuficiente para formato de e-mail e geração de senha:** O Cenário 1 afirma que o sistema "envia credenciais de acesso (login e senha provisória)", mas não especifica: (a) o login é o próprio e-mail ou um nome de usuário separado? (b) a senha provisória é gerada com quais regras (tamanho, complexidade)? (c) o usuário é forçado a trocar a senha no primeiro login? Não há cenário para formato de e-mail inválido.

* **US 1.2 — Perfis que o Chefe de Unidade pode atribuir não estão definidos:** O Cenário 1 menciona "perfil de Servidor", mas o PRD não estabelece se o Chefe pode criar outros Gestores ou Administradores. Sem essa restrição, um Chefe mal-intencionado poderia escalar privilégios.

* **US 1.3 — Comportamento pós-bloqueio e recuperação com e-mail inexistente:** O Cenário 2 define bloqueio de 30 minutos, mas não diz o que acontece depois: o contador de tentativas reseta? A conta desbloqueia automaticamente? O Cenário 3 não cobre o caminho triste: o que acontece quando o usuário informa um e-mail que não existe na base?

* **US 1.4 — Servidor com múltiplas unidades e visibilidade de processos já despachados:** A US cobre apenas servidor vinculado a UMA unidade. O RF 3 diz que "cada usuário deve pertencer a uma ou mais unidades". Como fica o Kanban de um servidor com múltiplas unidades? Processos que já passaram pela unidade mas foram despachados continuam visíveis?

* **US 2.1 — Validação de prazo e formato do número do processo:** O Cenário 1 menciona "número único gerado automaticamente", mas não especifica a regra de negócio para o formato (sequencial puro? ano/sequencial? com dígito verificador?). Não há cenário para criação com prazo no passado ou prazo excessivamente longo.

* **US 2.2 — Unidade desativada no meio do roteiro:** Não há cenário que contemple o que ocorre se uma unidade que faz parte de um roteiro for desativada enquanto há processos em andamento naquele caminho.

* **US 2.3 — Cenários de borda do Kanban ausentes:** Não há cenários para: (a) Kanban vazio (zero processos na unidade), (b) unidade com grande volume (500+ processos) — paginação? scroll?, (c) ordenação dos cards dentro de cada coluna.

* **US 2.5 — Periodicidade da rotina de arquivamento não definida:** O cenário menciona "rotina automática de arquivamento é executada" sem especificar se é diária, horária ou em tempo real. Se for diária, um processo com 30 dias pode levar até 31 dias para ser arquivado — isso é aceitável?

* **US 3.1 — Uploads múltiplos e arquivos de borda:** Não cobre: (a) é possível anexar múltiplos arquivos de uma vez? (b) o que acontece com arquivo de 0 byte? (c) arquivo sem extensão ou com extensão incorreta (ex.: .pdf renomeado para .doc)?

* **US 5.1 — Comportamento do contador de notificações entre sessões:** O cenário único não define: (a) o contador de notificações persiste entre sessões?, (b) quando o contador é resetado (ao clicar no ícone? ao abrir cada item? ao acessar o processo?), (c) o que ocorre se múltiplos processos chegarem simultaneamente?

* **US 5.2 — Comportamento de prazos em fins de semana e horário da rotina:** O Cenário 2 fala em "2 dias úteis" mas não especifica como o sistema trata sábados, domingos e feriados. A "rotina diária" não tem horário definido — se rodar às 23h59 e o prazo vencer à meia-noite, o alerta chega tarde demais?

* **US 6.1 — Dashboard sem cenários de borda e sem definição de período:** Um único cenário cobre o dashboard. Faltam: (a) o que exibir quando não há dados (gestor novo, unidade sem processos)?, (b) qual o período-base dos indicadores (mês corrente, últimos 30 dias)?, (c) "processos parados há mais de 5 dias úteis" — os 5 dias são configuráveis? Isso é um requisito funcional ou um parâmetro?

* **US 7.2 — Pesquisa sem cenários de borda:** Falta: (a) resultado vazio ("Nenhum processo encontrado"), (b) pesquisa por período sem informar datas, (c) paginação para muitos resultados, (d) o que acontece quando o termo de pesquisa tem menos de 2 caracteres?

* **US 8.1 — Edição, desativação e duplicidade de unidades não cobertas:** O RF 26 menciona "editar e desativar unidades", mas a US 8.1 só cobre o cadastro (criação). Faltam cenários para: (a) edição de unidade existente, (b) desativação de unidade (o que acontece com os usuários vinculados? e com os processos em andamento?), (c) tentativa de cadastrar unidade com sigla duplicada.

* **US 8.2 — Roteiros com borda inválida:** Não cobre: (a) roteiro com apenas uma unidade (a unidade despacha para si mesma?), (b) roteiro vazio (zero unidades), (c) roteiro circular (COFIN → AJUR → COFIN).

* **Microvazamentos de decisão técnica:**
  * US 2.3 Cenário 2 e US 5.1: "sem necessidade de recarregar a página" — implica WebSocket/SSE/polling. A decisão de implementação de real-time updates é da engenharia, não do PM.
  * US 3.2 Cenário 1: "pré-visualização do documento diretamente no navegador" — implica um renderizador de PDF/ imagem no frontend. Deveria ser expresso como "consigo visualizar o conteúdo do documento" sem prescrever o mecanismo.
  * Seção 6 (Requisitos Não Funcionais): "algoritmo RSA com chave mínima de 2048 bits ou ECDSA" — embora isso seja parcialmente ditado pela ICP-Brasil, a especificação do algoritmo é uma decisão de arquitetura. Deveria ser expresso como "em conformidade com os padrões da ICP-Brasil vigentes" e deixar a escolha do algoritmo para a engenharia.

---

## 3. Propostas de Correção Direta

### Correção 1: Persona "Auditor / Controlador Interno" — Incluir Épico ou Remover

* **Como está no PRD original (Seção 2):** 
  > "Auditor / Controlador Interno: Pessoa que precisa extrair dados para fiscalização e prestação de contas. Possui acesso a relatórios consolidados e, quando autorizado, pode visualizar processos de qualquer unidade, inclusive restritos ou sigilosos. Sua principal dor é a dificuldade de rastrear a cadeia completa de tramitação e decisões de um processo."

* **Como deve ficar (Sugestão de Reescrita):**
  > Incluir um Épico 9 — "Auditoria e Relatórios Avançados" com ao menos duas USs:
  > * **US 9.1:** Como Auditor, eu quero visualizar qualquer processo do sistema mediante autorização para rastrear a cadeia completa de tramitação.
  >   * Cenário 1: Acesso autorizado — Dado que sou Auditor autenticado com permissão de auditoria, Quando acesso um processo de qualquer unidade, Então visualizo o processo completo incluindo histórico de tramitação, documentos e assinaturas.
  >   * Cenário 2: Acesso negado — Dado que sou Auditor sem permissão explícita, Quando tento acessar um processo sigiloso, Então o sistema exibe "Acesso restrito — solicite autorização ao Administrador".
  > * **US 9.2:** Como Auditor, eu quero extrair relatórios consolidados de tramitação para fins de fiscalização.
  >   * Cenário 1: Extração de relatório — Dado que sou Auditor autenticado, Quando solicito um relatório filtrando por período, unidade ou tipo de processo, Então o sistema gera um relatório consolidado com: total de processos, tempo médio de tramitação, lista de processos com status e unidade atual.

  > OU, se Auditoria for deliberadamente fora do MVP: **remover** a persona "Auditor / Controlador Interno" da Seção 2 e adicionar explicitamente na Seção 3 (Fora de Escopo): "Relatórios avançados para auditoria e controle interno — o MVP fornecerá dashboards gerenciais básicos."

### Correção 2: Perfil do Usuário — Criar US para o RF 24

* **Como está no PRD original (Seção 5):** 
  > "24. O perfil do usuário deve exibir a relação de processos em que atuou e documentos assinados"

* **Como deve ficar (Sugestão de Reescrita):**
  > Incluir no Épico 1 (ou criar Épico próprio):
  > * **US 1.5:** Como Usuário, eu quero acessar meu perfil para visualizar meu histórico de atuação no sistema.
  >   * *Cenário 1: Visualização do perfil com histórico*
  >     * **Dado** que estou autenticado no sistema
  >     * **Quando** acesso a tela "Meu Perfil"
  >     * **Então** visualizo meus dados cadastrais, a lista de processos em que atuei (com número, assunto, data da ação e tipo de ação realizada) e a lista de documentos que assinei digitalmente (com nome do documento, processo vinculado e data da assinatura)
  >   * *Cenário 2: Perfil sem histórico*
  >     * **Dado** que sou um usuário recém-cadastrado que nunca atuou em nenhum processo
  >     * **Quando** acesso a tela "Meu Perfil"
  >     * **Então** visualizo meus dados cadastrais e as seções de histórico exibem a mensagem "Nenhum processo registrado" e "Nenhum documento assinado"

### Correção 3: US 1.2 — Restringir perfis atribuíveis pelo Chefe de Unidade

* **Como está no PRD original:** 
  > "Quando cadastro um novo usuário vinculado à unidade COFIN com perfil de Servidor"

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar Cenário 3:
  > * *Cenário 3: Tentativa de cadastro com perfil privilegiado*
  >   * **Dado** que estou autenticado como Chefe da COFIN
  >   * **Quando** tento cadastrar um usuário com perfil de Gestor ou Administrador
  >   * **Então** o sistema rejeita a operação e exibe "Você não tem permissão para atribuir este perfil. Apenas o Administrador pode cadastrar Gestores e Administradores."
  
  > E alterar o Cenário 1 para explicitar a restrição:
  > * "Quando cadastro um novo usuário vinculado à unidade COFIN com perfil de Servidor **(único perfil que posso atribuir)**"

### Correção 4: US 1.3 — Completar caminhos tristes de login e recuperação

* **Como está no PRD original:** 
  > Cenário 2: "[...] minha conta é bloqueada temporariamente por 30 minutos e recebo um e-mail de alerta"
  > Cenário 3: "[...] recebo um link de redefinição de senha com validade de 2 horas"

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar Cenário 4 e Cenário 5:
  > * *Cenário 4: Desbloqueio após tempo de penalidade*
  >   * **Dado** que minha conta foi bloqueada por 3 tentativas incorretas há mais de 30 minutos
  >   * **Quando** tento fazer login com a senha correta
  >   * **Então** sou autenticado com sucesso e o contador de tentativas é resetado para zero
  > * *Cenário 5: Recuperação com e-mail não cadastrado*
  >   * **Dado** que informei um e-mail que não está na base do sistema
  >   * **Quando** solicito recuperação de senha
  >   * **Então** o sistema exibe a mensagem genérica "Se o e-mail informado estiver cadastrado, um link de redefinição será enviado" (para não vazar informações de cadastro) e NENHUM e-mail é enviado

  > Detalhar na US 1.1 o formato das credenciais:
  > * "o login do usuário será o próprio e-mail cadastrado"
  > * "a senha provisória terá no mínimo 8 caracteres e o usuário será obrigado a trocá-la no primeiro login"

### Correção 5: US 2.3 — Cenários de borda do Kanban

* **Como está no PRD original:** 
  > Apenas cenários felizes de exibição e atualização.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar cenários de borda:
  > * *Cenário 3: Kanban vazio*
  >   * **Dado** que estou autenticado como Servidor de uma unidade recém-criada
  >   * **Quando** acesso a tela de Processos e não há nenhum processo na unidade
  >   * **Então** visualizo as colunas do Kanban vazias com a mensagem "Nenhum processo encontrado nesta unidade"
  > * *Cenário 4: Ordenação dos cards*
  >   * **Dado** que minha unidade possui múltiplos processos em uma mesma coluna
  >   * **Quando** visualizo o Kanban
  >   * **Então** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos com prazo vencido aparecem no topo com destaque visual

### Correção 6: US 5.1 — Comportamento do contador de notificações

* **Como está no PRD original:** 
  > "[...] vejo um indicador de notificação no ícone de sininho do menu superior com a quantidade de novos processos"

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar cenários:
  > * *Cenário 2: Reset do contador de notificações*
  >   * **Dado** que tenho 3 notificações não lidas no ícone do menu
  >   * **Quando** clico no ícone do sino para abrir o painel de notificações
  >   * **Então** o contador é zerado e as notificações são marcadas como lidas, mas permanecem acessíveis no histórico de notificações por 30 dias
  > * *Cenário 3: Persistência entre sessões*
  >   * **Dado** que eu tinha 2 notificações não lidas quando fiz logout
  >   * **Quando** faço login novamente
  >   * **Então** o contador ainda exibe 2 notificações pendentes

### Correção 7: Remover microvazamentos técnicos

* **Como está no PRD original:** 
  > US 2.3: "o processo aparece automaticamente [...] sem necessidade de recarregar a página"
  > US 5.1: mesmo padrão
  > US 3.2: "o sistema exibe uma pré-visualização do documento diretamente no navegador, sem necessidade de baixar o arquivo"
  > Seção 6: "algoritmo RSA com chave mínima de 2048 bits ou ECDSA"

* **Como deve ficar (Sugestão de Reescrita):**
  > US 2.3 e US 5.1 — substituir por:
  > * "o processo aparece na coluna 'Aberto' da minha unidade durante o uso do sistema"
  > US 3.2 — substituir por:
  > * "consigo visualizar o conteúdo do documento na própria tela do processo"
  > Seção 6 — substituir por:
  > * "As assinaturas digitais devem seguir os padrões e algoritmos criptográficos vigentes da ICP-Brasil (MP 2.200-2/2001 e normas correlatas)"

---

## 4. Próximos Passos

1. **Aplicar as correções propostas na Seção 3** — especialmente as estruturais (Correção 1, 2 e 3) que preenchem lacunas de escopo e segurança de perfis.
2. **Revisar as USs com apenas 1 cenário** (US 1.4, US 2.4, US 5.1, US 6.1, US 8.1) e adicionar ao menos um caminho triste ou cenário de borda para cada uma.
3. **Realizar uma nova auditoria** após as correções. O score alvo para liberação para engenharia é ≥ 8.0.
4. Uma vez atingido o score de aprovação, o PRD estará apto para ser convertido em especificações executáveis via OpenSpec ou ferramenta de SDD equivalente.
5. **Recomendação adicional:** avaliar se a persona "Cidadão" realmente se beneficiaria de pesquisa por período (US 7.2) no MVP. Se for um requisito real, incluir cenário específico; caso contrário, simplificar a US ou mover para fora de escopo.
