# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 7.0/10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS apresenta uma estrutura sólida, com personas bem definidas, escopo de MVP claro e a maioria das Histórias de Usuário coberta por cenários BDD de boa qualidade. No entanto, foram identificados problemas que impedem a aprovação imediata para a engenharia: (1) vazamento de decisão de arquitetura na premissa técnica do Épico 4, que sugere tecnologia específica (Web PKI/WebCrypto); (2) duas funcionalidades listadas no escopo do MVP sem a devida cobertura por Histórias de Usuário (notificações internas de processo concluído e prazo próximo); (3) ausência de visão Kanban para o Gestor, quebrando a promessa da persona; (4) definições ambíguas em KPIs críticos como "tempo médio de tramitação"; e (5) tratamento superficial de requisitos LGPD, sem US para consentimento ou exclusão de dados pessoais. O documento voltará para a Fase 4 (Patcher) para correção dos apontamentos antes de seguir para a engenharia.

---

## 2. Pontos Críticos Identificados

* **Vazamento de Arquitetura no Épico 4 (Premissa Técnica):** O PRD prescreve "Web PKI (WebCrypto ou similar)" como solução de implementação, violando o princípio de que o PM define O QUÊ, não COMO. A decisão da tecnologia de acesso ao certificado digital é prerrogativa da engenharia após o spike técnico.
* **Funcionalidade do Escopo sem US: notificação interna de "processo concluído":** O item "Notificações internas (ícone no sistema) e por e-mail para eventos relevantes (novo processo recebido, processo concluído, prazo próximo)" do escopo MVP lista três eventos, mas o Épico 5 cobre apenas "novo processo recebido" (US 5.1). Faltam US para notificação interna de processo concluído e alerta interno de prazo próximo.
* **Funcionalidade do Escopo sem US: notificação interna de "prazo próximo":** Mesmo ponto acima — a US 5.2 cobre apenas o alerta por e-mail, mas não a notificação interna (ícone no sistema) para prazo próximo.
* **Persona do Gestor sem visão tática de processos:** A persona define que o Gestor "Pode ver todos os processos das unidades que gerencia", mas a US 2.3 (Kanban) é escrita apenas da perspectiva do Servidor, mostrando processos de uma única unidade. Falta uma US que entregue ao Gestor a visão Kanban multi-unidade ou consolidada.
* **KPI "tempo médio de tramitação" sem definição precisa (US 6.1):** O dashboard exibe este indicador, mas o PRD não define a métrica: é medido da criação até a conclusão? Do primeiro despacho até a conclusão? É por unidade (tempo que o processo ficou em cada unidade) ou end-to-end? Essa ambiguidade impede a engenharia de implementar o cálculo corretamente e inviabiliza a testabilidade.
* **US 4.1 sem cenário para token/certificado não detectado:** O Cenário 1 assume que "o sistema detecta o certificado digital disponível", mas não cobre o caminho triste mais comum: o usuário não inseriu o token USB / smart card no computador. Sem esse cenário, a engenharia não sabe qual mensagem exibir ou como tratar a falha.
* **US 1.4 — contradição sobre visibilidade de processos que "passaram" pela unidade:** O Cenário 1 afirma que o servidor vê "processos que estão ou passaram pela unidade", mas a US 2.3 (Kanban) só exibe processos ATUAIS da unidade. A palavra "passaram" sugere visibilidade de processos históricos que já saíram, o que contradiz a mecânica do Kanban descrita na US 2.3. É preciso definir se o servidor vê processos passados na busca/filtro (US 2.7) ou apenas no histórico do perfil (US 1.5).
* **LGPD tratado apenas como RNF, sem requisitos funcionais:** O RNF de Conformidade Legal menciona a LGPD, mas não há nenhuma US ou RF que trate de: (a) consentimento do titular dos dados (interessados com CPF/CNPJ); (b) mecanismo para o cidadão solicitar exclusão ou anonimização de seus dados; (c) política de retenção e expurgo de dados pessoais. A menção genérica no RNF é insuficiente para a engenharia implementar conformidade.
* **US 3.1 Cenário 5 — falha parcial em upload múltiplo não especificada:** O cenário cobre upload de até 10 arquivos, mas não define o comportamento se 1 dos 10 falhar (formato inválido ou tamanho excedido): o lote inteiro é rejeitado ou apenas o arquivo inválido?
* **US 5.2 Cenário 2 — destinatário do e-mail de prazo ambíguo:** "Recebo um e-mail" — em uma unidade com múltiplos servidores, não está especificado se o alerta de prazo próximo é enviado a todos os servidores da unidade ou apenas ao servidor responsável pelo processo. A engenharia precisa dessa definição para implementar a lógica de disparo.
* **Concorrência na geração do número de processo (US 2.1):** O formato AAA/NNNNNN com sequencial reiniciado a cada ano não aborda o cenário de dois usuários criando processos simultaneamente. Sem especificação, a engenharia pode implementar uma solução que gera números duplicados sob carga.
* **Métrica de sucesso sem mecanismo de coleta:** A métrica "índice de satisfação dos cidadãos... medido por pesquisa opcional de feedback na consulta pública" referencia um mecanismo de pesquisa/feedback que não está no escopo do MVP e não possui US correspondente. Ou a métrica é removida do MVP, ou o mecanismo de coleta é adicionado ao escopo.

---

## 3. Propostas de Correção Direta

### Correção 1: Premissa Técnica do Épico 4 (Remoção de Vazamento Tecnológico)

* **Como está no PRD original:**
  > "Premissa Técnica: A assinatura digital será realizada via Web PKI (WebCrypto ou similar), permitindo que o navegador acesse o certificado digital armazenado no token/smart card do usuário sem necessidade de instalação de software adicional. O sistema deve ser compatível com os principais navegadores (Chrome, Firefox, Edge) em suas versões estáveis mais recentes. Esta abordagem será validada por meio de um spike técnico de 3 dias ANTES do início do desenvolvimento do épico, para confirmar a viabilidade com os modelos de certificado em uso pelo cliente."

* **Como deve ficar (Sugestão de Reescrita):**
  > "Premissa de Produto: O usuário deve conseguir assinar documentos utilizando seu certificado digital ICP-Brasil (e-CPF/e-CNPJ) armazenado em token ou smart card, diretamente pelo navegador, sem necessidade de instalar software adicional no computador. O sistema deve ser compatível com os principais navegadores (Chrome, Firefox, Edge) em suas versões estáveis mais recentes. A viabilidade técnica desta premissa deve ser validada pela engenharia ANTES do início do desenvolvimento do épico, considerando os modelos de certificado em uso pelo cliente."

### Correção 2: Definição do KPI "Tempo Médio de Tramitação" (US 6.1)

* **Como está no PRD original:**
  > "visualizo: total de processos ativos, tempo médio de tramitação (em dias), quantidade de processos parados..."

* **Como deve ficar (Sugestão de Reescrita):**
  > "visualizo: total de processos ativos, tempo médio de tramitação (em dias corridos, medido da data de criação do processo até a data de conclusão, considerando apenas processos concluídos nos últimos 12 meses), quantidade de processos parados..."

### Correção 3: US 4.1 — Cenário Faltante (Certificado Não Detectado)

* **Como está no PRD original:**
  > (Não existe cenário para token/certificado não detectado)

* **Como deve ficar (Sugestão de Reescrita — adicionar como Cenário 5):**
  > *Cenário 5: Certificado digital não detectado*
  > * **Dado** que estou tentando assinar um documento
  > * **Quando** aciono "Assinar" e não há token/smart card conectado ao computador ou o navegador não detecta o certificado digital
  > * **Então** o sistema exibe "Certificado digital não detectado. Conecte o token/smart card ao computador e certifique-se de que o driver está instalado corretamente." e a operação de assinatura não é concluída

### Correção 4: US 1.4 Cenário 1 — Eliminação da Contradição com US 2.3

* **Como está no PRD original:**
  > "vejo exclusivamente os processos que estão ou passaram pela unidade COFIN"

* **Como deve ficar (Sugestão de Reescrita):**
  > "vejo exclusivamente os processos que estão atualmente na unidade COFIN (colunas Aberto, Em Tramitação, Concluído e Arquivado do Kanban da COFIN). Processos que já tramitaram para outras unidades não aparecem mais no meu Kanban, mas permanecem acessíveis no meu histórico pessoal (US 1.5) e nos resultados de busca restritos à unidade COFIN (US 2.7)."

### Correção 5: US 3.1 — Comportamento de Falha Parcial em Upload Múltiplo

* **Como está no PRD original:**
  > (Cenário 5 não especifica comportamento de falha parcial)

* **Como deve ficar (Sugestão de Reescrita — adicionar como Cenário 6):**
  > *Cenário 6: Falha parcial em upload múltiplo*
  > * **Dado** que selecionei 10 arquivos para upload múltiplo
  > * **Quando** um ou mais arquivos possuem formato não permitido ou tamanho excedido, e os demais são válidos
  > * **Então** o sistema rejeita apenas os arquivos inválidos, exibindo a mensagem de erro específica ao lado de cada arquivo rejeitado (ex.: "Formato não permitido", "Excede 20 MB"), e processa normalmente o upload dos arquivos válidos. Ao final, exibe o resumo: "X arquivo(s) enviado(s) com sucesso. Y arquivo(s) rejeitado(s)."

### Correção 6: US 5.2 Cenário 2 — Definição do Destinatário do Alerta de Prazo

* **Como está no PRD original:**
  > "recebo um e-mail de alerta com assunto 'Prazo próximo — [Número do Processo]'"

* **Como deve ficar (Sugestão de Reescrita):**
  > "todos os servidores da unidade atual do processo recebem um e-mail de alerta com assunto 'Prazo próximo — [Número do Processo]'"

---

## 4. Próximos Passos

1. **Aplicar as correções listadas na Seção 3** — em especial a remoção do vazamento tecnológico (Correção 1) e a definição precisa do KPI (Correção 2).
2. **Criar as Histórias de Usuário faltantes:**
   - US para notificação interna de "processo concluído" (seguindo o mesmo padrão da US 5.1)
   - US para notificação interna de "prazo próximo" (ícone no sistema, complementar ao e-mail da US 5.2)
   - US para visão Kanban do Gestor (multi-unidade ou consolidada), cumprindo a promessa da persona
3. **Adicionar requisitos funcionais LGPD:** Criar ao menos uma US ou RF especificando: (a) que dados pessoais de interessados são exibidos na consulta pública ou não; (b) mecanismo de solicitação de exclusão/anonimização pelo titular; (c) prazo de retenção de dados pessoais após arquivamento.
4. **Revisar a métrica de satisfação do cidadão:** Ou remover a métrica "pesquisa opcional de feedback" das Métricas de Sucesso do MVP (já que o mecanismo não está no escopo), ou adicionar ao escopo uma US para o formulário de feedback na consulta pública.
5. **Após as correções, reexecutar a Fase 3 (Review)** para reavaliar o score de prontidão antes de enviar para a Fase 4 (Patcher) ou diretamente para a engenharia.
