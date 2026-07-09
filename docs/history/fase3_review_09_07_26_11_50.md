# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 7/10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS é um documento bem estruturado, com 9 épicos e 30+ histórias de usuário razoavelmente detalhadas em formato BDD (Dado/Quando/Então). A cobertura de caminhos tristes e cenários de borda está acima da média para um PRD de primeira iteração. No entanto, o documento possui **duas lacunas estruturais graves**: os Requisitos Funcionais 37 e 38 (LGPD — canal de solicitação do titular e anonimização de dados arquivados) carecem completamente de histórias de usuário e critérios de aceitação correspondentes. Além disso, há inconsistências pontuais de cobertura (drill-down no dashboard, cenários de link de primeiro acesso já utilizado, ausência de cenário de validação de CNPJ apesar de ser um subcampo documentado) e uma ambiguidade relevante sobre expurgo de notificações não lidas. O documento **não está pronto para ser entregue à engenharia** sem que essas correções sejam aplicadas.

---

## 2. Pontos Críticos Identificados

### Lacunas Estruturais (Bloqueantes)

* **RF 37 e RF 38 sem User Stories correspondentes:** Os requisitos funcionais 37 ("canal de solicitação para que titulares de dados pessoais requeiram a exclusão ou anonimização de seus dados, em conformidade com a LGPD") e 38 ("dados pessoais de processos arquivados devem ser mantidos pelo prazo legal aplicável; após esse prazo, o sistema deve anonimizar ou excluir os dados pessoais automaticamente") não possuem nenhuma História de Usuário, épico, persona responsável ou critério de aceitação BDD. Trata-se de funcionalidades complexas com impacto legal significativo que estão listadas como requisitos mas não são endereçadas em nenhum épico. A engenharia não terá especificação para implementar estes itens.

* **RF 36 sem cenário BDD explícito na User Story da Consulta Pública:** O RF 36 estabelece que "dados pessoais de interessados (CPF/CNPJ) não devem ser exibidos na consulta pública; apenas o nome do interessado será visível ao cidadão". Embora a US 7.1 liste os campos exibidos, nenhum cenário BDD valida explicitamente que CPF/CNPJ NÃO aparecem na consulta pública — é uma verificação de ausência que precisa ser testável.

### Inconsistências e Cobertura Insuficiente

* **US 1.6 — Cenário ausente: link de primeiro acesso já utilizado:** A US 1.6 cobre link expirado (Cenário 2), mas não cobre o caso em que o usuário tenta reutilizar um link de primeiro acesso que já foi consumido com sucesso. O que acontece? Exibe "Link já utilizado"? Redireciona para login?

* **US 1.3 — Cenário ausente: tentativa de login durante bloqueio:** O Cenário 2 define bloqueio de 30 minutos após 3 tentativas incorretas. Porém, não há cenário BDD que defina o que acontece quando o usuário tenta fazer login com a senha CORRETA durante o período de bloqueio. O sistema rejeita com "Conta bloqueada. Tente novamente em X minutos"? Ou aceita a senha correta e ignora o bloqueio? O Cenário 4 cobre apenas o pós-bloqueio.

* **US 2.1 — Cenário ausente: validação de CNPJ inválido:** A definição do campo "Interessados" menciona que CPF ou CNPJ é "opcional, validado por algoritmo de dígito verificador". O Cenário 3 valida CPF inválido, mas não há cenário equivalente para CNPJ inválido. A engenharia pode implementar validação de CPF e esquecer do CNPJ, ou implementar validações diferentes das esperadas.

* **US 5.1 — Ambiguidade no expurgo de notificações não lidas:** O Cenário 2 afirma que "notificações lidas permanecem acessíveis no histórico por 30 dias". O Cenário 4 afirma que "uma notificação foi gerada há mais de 30 dias" → "esta notificação não aparece mais na listagem". O Cenário 4 NÃO distingue entre notificações lidas e não lidas. Se uma notificação crítica NÃO LIDA expirar em 30 dias e for expurgada, o servidor pode perder um alerta importante sem nunca tê-lo visto. O comportamento intencional precisa ser esclarecido.

* **US 6.1 — Drill-down inconsistente:** O Cenário 4 define drill-down apenas para o KPI "Processos Parados". Os KPIs "Processos Ativos", "Tempo Médio de Tramitação" e "Produtividade por Unidade" não possuem drill-down definido. Isso é uma decisão de produto legítima, mas a assimetria não está justificada. Além disso, "Processos Ativos" provavelmente deveria ter drill-down (é a ação mais natural: clicar no número para ver quais são). Se a decisão for consciente, deve estar documentada.

* **US 3.1 Cenário 3 — Edge case não coberto: remoção de documento após devolução:** O Cenário 3 permite remover documento se o processo "ainda não foi despachado". Mas e se o processo foi despachado, devolvido (US 2.2b) e voltou para a unidade? O servidor pode remover o documento nesse momento? A lógica atual diria "não" (já foi despachado), mas semanticamente o processo retornou para correções — a remoção de documento anexado por engano seria esperada nesse fluxo.

* **US 2.1 — Limites do campo "prazo em dias corridos" não definidos:** O campo prazo é aceito em dias corridos, mas não há validação de valor mínimo (1 dia? zero?) ou máximo (999 dias? ilimitado?). Sem isso, a engenharia precisará adivinhar limites.

### Observações de Qualidade (Não Bloqueantes)

* **US 4.1 — Dependência de validação técnica prévia:** A premissa de produto da assinatura digital estabelece corretamente que a viabilidade técnica deve ser validada pela engenharia antes do desenvolvimento. Isso é uma boa prática de PRD, mas o documento não define o que acontece se a premissa for invalidada (ex.: certificados do cliente não são compatíveis com Web PKI). Um plano de contingência ou nota de risco seria desejável.

* **RF 3 — Restrição de 1 unidade por Servidor sem cenário de violação:** O RF 3 estabelece que cada Servidor pertence a exatamente uma unidade. Nenhuma US cobre o cenário de um Administrador tentando cadastrar ou editar um usuário Servidor com múltiplas unidades. O Cenário 1 da US 1.1 lista "unidade" (singular) como campo, mas não há validação explícita contra múltiplas unidades.

---

## 3. Propostas de Correção Direta

### Correção 1: Inserir User Stories para RF 37 e RF 38 (LGPD)

* **Como está no PRD original:**
  > "37. O sistema deve disponibilizar canal de solicitação para que titulares de dados pessoais requeiram a exclusão ou anonimização de seus dados, em conformidade com a LGPD"
  > "38. Dados pessoais de processos arquivados devem ser mantidos pelo prazo legal aplicável; após esse prazo, o sistema deve anonimizar ou excluir os dados pessoais automaticamente"

  Os requisitos existem na lista de RFs, mas não há épico, história de usuário ou critério BDD correspondente.

* **Como deve ficar (Sugestão de Reescrita):**

  **Novo Épico 10: Conformidade LGPD e Privacidade**

  **US 10.1:** Como Cidadão / Titular de Dados, eu quero solicitar a exclusão ou anonimização dos meus dados pessoais dos processos para exercer meus direitos previstos na LGPD.

  * **Critérios de Aceitação:**
    * *Cenário 1: Solicitação de exclusão com dados válidos*
      * **Dado** que sou um titular de dados pessoais (ou meu representante legal) e possuo o número do processo e meus dados de identificação
      * **Quando** acesso o canal de solicitação (página pública, sem autenticação) e preencho: número do processo, meu nome completo, CPF, e-mail para resposta, tipo de solicitação ("Exclusão de dados" ou "Anonimização de dados") e anexo documento de identificação com foto
      * **Então** o sistema registra a solicitação com um número de protocolo, exibe "Solicitação registrada com sucesso. Protocolo: XXXX. Você receberá a resposta no e-mail informado em até 15 dias." e envia um e-mail de confirmação ao solicitante com o número de protocolo
    * *Cenário 2: Campos obrigatórios não preenchidos*
      * **Dado** que estou preenchendo o formulário de solicitação LGPD
      * **Quando** tento enviar sem preencher nome, CPF, número do processo ou e-mail
      * **Então** o sistema destaca os campos obrigatórios e exibe "Preencha todos os campos obrigatórios"
    * *Cenário 3: Documento de identificação com formato inválido*
      * **Dado** que estou preenchendo o formulário de solicitação LGPD
      * **Quando** anexo um arquivo que não é PDF, JPG ou PNG
      * **Então** o sistema exibe "Formato de arquivo não permitido. Anexe documento de identificação nos formatos PDF, JPG ou PNG."
    * *Cenário 4: Número de processo inexistente*
      * **Dado** que estou preenchendo o formulário
      * **Quando** informo um número de processo que não existe na base
      * **Então** o sistema exibe "Nenhum processo encontrado com o número informado. Verifique o número e tente novamente."

  **US 10.2:** Como Administrador, eu quero gerenciar as solicitações LGPD recebidas para processar os pedidos dos titulares de dados.

  * **Critérios de Aceitação:**
    * *Cenário 1: Visualização da fila de solicitações*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso "Solicitações LGPD" no menu de administração
      * **Então** visualizo a lista de solicitações com: número do protocolo, data, nome do solicitante, número do processo, tipo de solicitação e status (Pendente / Em análise / Atendida / Rejeitada)
    * *Cenário 2: Processamento de solicitação de exclusão*
      * **Dado** que uma solicitação LGPD está com status "Pendente" e o tipo é "Exclusão de dados"
      * **Quando** valido a identidade do solicitante e aciono "Atender Solicitação"
      * **Então** o sistema anonimiza os dados pessoais do titular no processo indicado (substitui CPF/CNPJ por hash irreversível e nome do interessado por "Titular Anonimizado") e envia e-mail automático ao solicitante informando a conclusão
    * *Cenário 3: Rejeição de solicitação*
      * **Dado** que uma solicitação LGPD está em análise e o Administrador identifica que o solicitante não é o titular dos dados
      * **Quando** aciono "Rejeitar Solicitação" e preencho a justificativa
      * **Então** o status muda para "Rejeitada" e um e-mail é enviado ao solicitante informando a decisão com a justificativa

  **US 10.3:** Como Sistema, eu devo anonimizar automaticamente dados pessoais de processos arquivados após o prazo legal para garantir conformidade contínua com a LGPD.

  * **Critérios de Aceitação:**
    * *Cenário 1: Anonimização automática após prazo legal*
      * **Dado** que um processo está arquivado há 5 anos (prazo legal configurado para o tipo de processo)
      * **Quando** a rotina trimestral de anonimização é executada
      * **Então** todos os dados pessoais de interessados (nome completo, CPF, CNPJ, endereço) são substituídos por valores anonimizados irreversíveis, mantendo-se o número do processo, datas, unidades, status e histórico de tramitação íntegros. O evento é registrado em log de conformidade.
    * *Cenário 2: Configuração do prazo de anonimização por tipo de processo*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso as configurações de um tipo de processo e defino o prazo de anonimização LGPD em 5 anos
      * **Então** o sistema registra a configuração e exibe "Prazo de anonimização configurado: 5 anos. A partir desta data, processos deste tipo serão anonimizados após 5 anos de arquivamento."

---

### Correção 2: Cenário BDD para RF 36 (Ocultação de CPF/CNPJ na Consulta Pública)

* **Como está no PRD original:**
  > "36. Dados pessoais de interessados (CPF/CNPJ) não devem ser exibidos na consulta pública; apenas o nome do interessado será visível ao cidadão"

  O requisito existe apenas na lista de RFs, sem cenário de validação.

* **Como deve ficar (Sugestão de Reescrita):**

  Adicionar à **US 7.1** o seguinte cenário:

  * *Cenário 3: Ocultação de dados pessoais na consulta pública*
    * **Dado** que estou na página de Consulta Pública e um processo existe com interessados cadastrados (nome e CPF/CNPJ)
    * **Quando** consulto o processo pelo número
    * **Então** visualizo o nome do interessado, mas CPF e CNPJ NÃO aparecem em nenhum campo da tela de resultado. Apenas o nome do interessado é exibido. O dado completo (CPF/CNPJ) permanece acessível apenas internamente no sistema, por usuários autenticados e autorizados.

---

### Correção 3: Cenário de link de primeiro acesso já utilizado (US 1.6)

* **Como está no PRD original:**
  > A US 1.6 cobre apenas Cenário 1 (link válido) e Cenário 2 (link expirado). Não há cenário para link já consumido.

* **Como deve ficar (Sugestão de Reescrita):**

  Adicionar à **US 1.6** o seguinte cenário:

  * *Cenário 3: Link de primeiro acesso já utilizado*
    * **Dado** que sou um usuário que já realizou o primeiro acesso com sucesso (status "Ativo")
    * **Quando** tento acessar novamente o link de primeiro acesso que já foi utilizado
    * **Então** o sistema exibe "Link já utilizado. Se você já definiu sua senha, faça login normalmente. Caso tenha esquecido sua senha, utilize a opção 'Esqueci minha senha'." e meu status não é alterado

---

### Correção 4: Cenário de tentativa de login durante bloqueio (US 1.3)

* **Como está no PRD original:**
  > O Cenário 2 define o bloqueio, mas não especifica o comportamento quando o usuário tenta a senha correta durante o período de bloqueio.

* **Como deve ficar (Sugestão de Reescrita):**

  Adicionar à **US 1.3** o seguinte cenário:

  * *Cenário 2b: Tentativa de login com senha correta durante bloqueio*
    * **Dado** que minha conta está bloqueada temporariamente (menos de 30 minutos desde o bloqueio) após 3 tentativas incorretas
    * **Quando** tento fazer login com a senha correta durante o período de bloqueio
    * **Então** o sistema rejeita a autenticação e exibe "Conta bloqueada temporariamente. Tente novamente em X minutos.", onde X é o tempo restante de bloqueio. O contador de tentativas não é alterado, e o tempo de bloqueio não é reiniciado.

---

### Correção 5: Cenário de validação de CNPJ (US 2.1)

* **Como está no PRD original:**
  > O Cenário 3 valida CPF inválido. Não há cenário equivalente para CNPJ.

* **Como deve ficar (Sugestão de Reescrita):**

  Adicionar à **US 2.1** o seguinte cenário:

  * *Cenário 3b: Interessado com CNPJ inválido*
    * **Dado** que estou criando um processo e seleciono tipo de interessado "Pessoa Jurídica"
    * **Quando** preencho um CNPJ com dígito verificador inválido no campo de interessado
    * **Então** o sistema exibe "CNPJ inválido — verifique o número informado" e não permite prosseguir

---

### Correção 6: Expurgo de notificações não lidas (US 5.1)

* **Como está no PRD original:**
  > Cenário 4: "Dado que uma notificação foi gerada há mais de 30 dias / Quando acesso o histórico de notificações / Então esta notificação não aparece mais na listagem, sendo removida automaticamente pelo sistema"

  O cenário não distingue entre notificações lidas e não lidas.

* **Como deve ficar (Sugestão de Reescrita):**

  Reescrever o **Cenário 4 da US 5.1** e adicionar Cenário 4b:

  * *Cenário 4: Expurgo de notificações lidas antigas*
    * **Dado** que eu li uma notificação há mais de 30 dias
    * **Quando** acesso o histórico de notificações
    * **Então** esta notificação não aparece mais na listagem, sendo removida automaticamente pelo sistema
  * *Cenário 4b: Notificações não lidas não são expurgadas*
    * **Dado** que uma notificação foi gerada há mais de 30 dias e eu ainda NÃO a li
    * **Quando** acesso a lista de notificações
    * **Então** esta notificação permanece visível NORMALMENTE como "não lida" (com indicador visual de não lida). O expurgo automático NÃO remove notificações não lidas. Notificações não lidas só são removidas após serem lidas E decorridos 30 dias da leitura. O contador do sino continua refletindo esta notificação não lida.

---

### Correção 7: Drill-down consistente no Dashboard (US 6.1)

* **Como está no PRD original:**
  > Apenas o KPI "Processos Parados" possui drill-down (Cenário 4). Os demais KPIs não têm comportamento de clique definido.

* **Como deve ficar (Sugestão de Reescrita):**

  Substituir o Cenário 4 existente e adicionar Cenários 5 e 6 à **US 6.1**:

  * *Cenário 4: Drill-down a partir do KPI "Processos Parados"*
    * *(mantido como está no original)*
  * *Cenário 5: Drill-down a partir do KPI "Processos Ativos"*
    * **Dado** que o KPI "Total de Processos Ativos" exibe o valor 42
    * **Quando** clico sobre o número 42 no card de KPI
    * **Então** sou direcionado para a listagem filtrada dos 42 processos ativos (Aberto + Em Tramitação), com número, assunto, unidade atual e dias restantes de cada um
  * *Cenário 6: KPIs sem drill-down*
    * **Dado** que estou visualizando o dashboard
    * **Quando** clico sobre os cards de KPI "Tempo Médio de Tramitação" ou "Produtividade por Unidade"
    * **Então** nenhuma ação de drill-down é disparada. Estes KPIs são apenas indicadores numéricos informativos, não clicáveis. Apenas "Processos Ativos" e "Processos Parados" possuem drill-down para lista detalhada.

---

### Correção 8: Remoção de documento após devolução (US 3.1)

* **Como está no PRD original:**
  > Cenário 4: "Dado que um documento foi anexado a um processo que já foi despachado para a próxima unidade / Quando tento acionar 'Remover' / Então o sistema exibe 'Não é possível remover documentos de um processo que já foi despachado'"

  Não cobre o caso de devolução.

* **Como deve ficar (Sugestão de Reescrita):**

  Adicionar à **US 3.1** o seguinte cenário:

  * *Cenário 4b: Exclusão de documento após devolução do processo*
    * **Dado** que um processo da minha unidade foi despachado, devolvido pela unidade seguinte (US 2.2b) e agora está novamente na minha unidade com a justificativa "Correção de dados"
    * **Quando** aciono a opção "Remover" sobre um documento que havia sido anexado antes do despacho original
    * **Então** o sistema exibe confirmação "Tem certeza que deseja remover este documento?" e, ao confirmar, o documento é removido da lista de anexos, o arquivo físico é excluído do armazenamento, e a exclusão é registrada no histórico do processo. O processo permanece na unidade atual com o mesmo status ("Em Tramitação").

---

## 4. Próximos Passos

O documento **não está aprovado para envio à engenharia ou ferramentas de SDD (OpenSpec)**. O score 7/10 reflete duas lacunas estruturais (RFs LGPD sem User Stories) que impedem a implementação, além de ambiguidades pontuais que gerariam retrabalho.

**Ação recomendada:**

1. **Aplicar as Correções 1 e 2** (LGPD e RF 36) — são as de maior criticidade. Sem elas, a engenharia não tem especificação para implementar funcionalidades com obrigação legal.
2. **Aplicar as Correções 3 a 8** — complementam cenários de borda e eliminam ambiguidades que gerariam dúvidas durante a sprint.
3. Após as correções, **reprocessar este PRD na Fase 3** (revisão) para confirmar a elevação do score. O patamar mínimo para aprovação é **8/10**.
4. Com score ≥ 8, o PRD estará apto para ser encaminhado ao **OpenSpec (Fase 4)** para geração da especificação técnica detalhada.
