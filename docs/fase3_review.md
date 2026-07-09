# Relatório de Revisão de PRD — Controle de Qualidade

<auditoria_interna>

## Análise de Critérios de Aceitação (BDD)

O formato Dado/Quando/Então está bem aplicado na maioria das US. O autor demonstrou cuidado com caminhos tristes — ex.: US 1.2 cobre tentativa de cadastro em unidade não gerenciada e com perfil privilegiado; US 1.3 cobre bloqueio por 3 tentativas, recuperação de senha, desbloqueio após timeout e e-mail não cadastrado. Isso é acima da média.

Porém, identifiquei lacunas relevantes:

1. **US 2.1** — Não especifica o formato do número único do processo (sequencial puro? ano+sequencial? padrão NUP?). A engenharia não tem como implementar sem essa definição.
2. **US 2.3 (Cenário 2)** — Diz "durante o uso do sistema" sem especificar se a atualização é em tempo real (WebSocket/SSE) ou se depende de refresh manual. Isso é ambíguo para a engenharia.
3. **US 3.2** — Fala em "visualização inline" de PDF e imagens, mas não define o comportamento para formatos DOC/DOCX (que não são renderizáveis inline em navegadores). A US 3.1 aceita upload de DOC/DOCX, então o usuário fará upload e depois não conseguirá visualizar? Lacuna de UX.
4. **US 4.1** — Não cobre o cenário de PIN incorreto. O sistema deve ter comportamento definido para tentativas erradas de PIN, similar ao bloqueio por senha da US 1.3.
5. **US 4.2** — Não cobre o cenário de falha na verificação (documento adulterado ou assinatura inválida). Só existe o cenário feliz.
6. **US 5.1** — Menciona que notificações "permanecem acessíveis no histórico por 30 dias", mas não há cenário BDD para o que ocorre após esse prazo (exclusão automática? arquivamento?).
7. **US 6.1 (Dashboard)** — Apenas UM cenário feliz. É a US mais subespecificada do documento. Não cobre: (a) dashboard vazio para gestor recém-cadastrado; (b) filtro por unidade específica dentro das gerenciadas; (c) filtro por período; (d) drill-down a partir de um KPI para a lista de processos correspondente. Para um dashboard que é a principal entrega de valor para o Gestor, isso é crítico.
8. **US 7.2** — O título e a descrição mencionam pesquisa por "assunto, tipo ou período", mas o único cenário BDD cobre apenas "assunto". Os filtros por tipo de processo e período não têm cenários de aceitação.
9. **US 8.1** — Cobre apenas o cadastro de unidade. O RF 26 menciona explicitamente "cadastrar, editar e desativar unidades e tipos de processo", mas não há cenários para edição nem desativação. O que acontece com usuários vinculados a uma unidade desativada? Processos em andamento?
10. **US 8.2 (Cenário 2)** — Cobre alteração de roteiro em uso, mas não cobre a desativação de tipo de processo (prevista no RF 26).

## Análise de Coesão de Escopo (RF vs US)

Mapeei todos os 28 Requisitos Funcionais contra as US:

- **RF 26** ("cadastrar, editar e desativar unidades e tipos de processo") está parcialmente descoberto:
  - Cadastrar unidade → US 8.1 ✅
  - Editar unidade → ❌ SEM US
  - Desativar unidade → ❌ SEM US
  - Cadastrar tipo de processo → US 8.2 (criação) ✅
  - Editar tipo de processo → US 8.2 (alteração de roteiro) ✅ (parcial — só roteiro, não outros atributos)
  - Desativar tipo de processo → ❌ SEM US

- **RF 23** ("Processos marcados como sigilosos não devem aparecer nos resultados da consulta pública") — A US 7.2 cobre o comportamento de filtragem, mas NÃO EXISTE US para o ato de marcar/desmarcar um processo como sigiloso. Quem pode fazer isso? Em que momento?

- **RF 27-28** (Auditor) — As US 9.1 e 9.2 cobrem, mas não existe US para o Administrador conceder/revogar permissão de auditoria, que é pré-condição para essas US funcionarem.

Os demais 25 RFs possuem cobertura adequada por US.

## Análise de Blindagem Tecnológica

O PRD está BEM BLINDADO. Não encontrei vazamentos de banco de dados, linguagem de programação, framework ou ferramenta específica. As menções a HTTPS, hash criptográfico e ICP-Brasil são requisitos de conformidade/segurança, não escolhas de implementação. O autor manteve disciplina de Product Manager.

Único ponto de atenção: a US 2.3 (Cenário 2) usa a expressão "durante o uso do sistema", que pode ser interpretada pela engenharia como necessidade de atualização em tempo real — isso beira uma decisão de arquitetura (polling vs WebSocket vs SSE). Deveria ser formulado como comportamento observável, não como mecanismo técnico.

## Cálculo do Score

Partindo de 10 e deduzindo por gravidade das falhas:

| Falha | Impacto | Dedução |
|-------|---------|---------|
| Dashboard (US 6.1) subespecificado — 1 cenário para feature central do Gestor | ALTO | -1.0 |
| US 8.1 e RF 26 — ausência de BDD para editar/desativar unidades | ALTO | -0.75 |
| US 4.2 — ausência de cenário de falha na verificação | MÉDIO | -0.5 |
| US 7.2 — filtros de tipo e período sem cenários BDD | MÉDIO | -0.5 |
| RF 23 — ausência de US para marcar processo como sigiloso | MÉDIO | -0.5 |
| US 2.1 — formato do número do processo não definido | MÉDIO | -0.25 |
| US 3.2 — comportamento para DOC/DOCX não definido | BAIXO | -0.25 |
| US 4.1 — ausência de cenário de PIN incorreto | BAIXO | -0.25 |
| US 5.1 — expurgo de notificações após 30 dias sem BDD | BAIXO | -0.25 |
| Ausência de US para concessão de permissão de auditoria | BAIXO | -0.25 |

**Score final: 6.5/10**

O documento tem estrutura sólida, BDD majoritariamente bem escrito e excelente blindagem tecnológica. As falhas são pontuais e corrigíveis, mas o dashboard subespecificado e a ausência de edição/desativação de unidades são lacunas que impedem o início do desenvolvimento.

</auditoria_interna>

---

# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 6.5/10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD apresenta estrutura macro bem organizada, 28 requisitos funcionais com rastreabilidade majoritariamente correta para 19 histórias de usuário com BDD e blindagem tecnológica exemplar — não há vazamento de banco, linguagem ou framework. Contudo, o documento possui lacunas que impedem o início do desenvolvimento: o dashboard de KPIs (US 6.1), que é a principal entrega de valor para a persona Gestor, está reduzido a um único cenário feliz sem filtros, drill-down ou tratamento de vazio; a US 8.1 não cobre edição e desativação de unidades, previstas no RF 26; a US 4.2 não possui cenário de falha na verificação de assinatura; e a US 7.2 anuncia filtros por tipo e período que não aparecem nos critérios de aceitação. As correções são pontuais e não estruturais — o documento tem boa fundação, mas precisa de uma rodada de refinamento antes de seguir para a engenharia.

## 2. Pontos Críticos Identificados

* **US 6.1 (Dashboard) subespecificada:** Apenas 1 cenário feliz. Não cobre dashboard vazio, filtro por unidade, filtro por período, drill-down a partir de KPIs ou tratamento de erro. Para a persona Gestor, o dashboard é a feature âncora do MVP.
* **US 8.1 não cobre edição e desativação de unidades:** O RF 26 determina "cadastrar, editar e desativar unidades e tipos de processo", mas a US 8.1 possui apenas cenário de cadastro. Não há definição do que ocorre com usuários e processos vinculados a uma unidade desativada.
* **RF 23 sem User Story correspondente para a ação de sigilo:** A US 7.2 filtra processos sigilosos da consulta pública, mas não existe US definindo quem pode marcar/desmarcar um processo como sigiloso, em que momento do ciclo de vida e com qual granularidade.
* **US 4.2 sem cenário de falha:** A verificação de assinatura cobre apenas o caminho feliz (assinatura válida). Não define o comportamento quando a assinatura é inválida ou o documento foi adulterado.
* **US 7.2 com critérios de aceitação incompletos:** O título e a descrição mencionam pesquisa por "assunto, tipo ou período", mas o único cenário BDD cobre apenas pesquisa por assunto. Os filtros de tipo de processo e período não têm comportamento definido.
* **US 2.1 não define o formato do número do processo:** A US diz "número único gerado automaticamente", sem especificar o padrão (sequencial puro? ano+sequencial? NUP?). Isso gera retrabalho na engenharia.
* **US 3.2 inconsistente com US 3.1:** A US 3.1 aceita upload de DOC/DOCX, mas a US 3.2 só define visualização inline para PDF e imagens — navegadores não renderizam DOC/DOCX nativamente. O comportamento para esses formatos precisa ser definido (download forçado? conversão server-side?).
* **US 4.1 não cobre erro de PIN:** Existe cenário para certificado expirado, mas não para PIN incorreto ou bloqueio do token após múltiplas tentativas erradas — comportamento análogo ao já definido na US 1.3.
* **Ausência de US para concessão de permissão de auditoria:** As US 9.1 e 9.2 dependem de "autorização concedida pelo Administrador", mas nenhuma US define como o Administrador concede ou revoga essa permissão.
* **US 5.1 com expurgo indefinido:** Menciona que notificações "permanecem acessíveis por 30 dias", mas não há cenário para o que ocorre após esse prazo (exclusão automática? arquivamento?).

## 3. Propostas de Correção Direta

### Correção 1: US 6.1 — Dashboard de KPIs (Expansão de Cenários)

* **Como está no PRD original:**
  > Apenas 1 cenário feliz listando os KPIs exibidos. Sem cenários de borda, vazio, filtro ou drill-down.

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 6.1:** Como Gestor, eu quero visualizar um dashboard de KPIs para monitorar a eficiência operacional das minhas unidades.
  > * **Cenário 1: Exibição do dashboard com indicadores**
  >   * **Dado** que estou autenticado como Gestor de ao menos uma unidade que possui processos
  >   * **Quando** acesso o Dashboard
  >   * **Então** visualizo: total de processos ativos, tempo médio de tramitação (em dias), quantidade de processos parados (sem movimentação há mais de 5 dias úteis), produtividade por unidade (processos concluídos no mês) e lista dos processos com prazo vencido ou próximo do vencimento
  > * **Cenário 2: Dashboard sem dados (gestor recém-cadastrado)**
  >   * **Dado** que estou autenticado como Gestor de unidades que ainda não possuem processos
  >   * **Quando** acesso o Dashboard
  >   * **Então** visualizo os cards de KPI com valor zero e a mensagem "Nenhum dado disponível para o período" em cada seção
  > * **Cenário 3: Filtro por unidade gerenciada**
  >   * **Dado** que estou autenticado como Gestor de três unidades (COFIN, AJUR, DIRAD)
  >   * **Quando** seleciono apenas a unidade COFIN no filtro do Dashboard
  >   * **Então** todos os KPIs e listas são recalculados considerando apenas os processos da COFIN
  > * **Cenário 4: Drill-down a partir de KPI**
  >   * **Dado** que o KPI "Processos Parados" exibe o valor 7
  >   * **Quando** clico sobre o número 7 no card de KPI
  >   * **Então** sou direcionado para a listagem filtrada dos 7 processos que estão sem movimentação há mais de 5 dias úteis, com número, assunto, unidade atual e dias parados de cada um

### Correção 2: US 8.1 — Edição e Desativação de Unidades

* **Como está no PRD original:**
  > A US 8.1 possui apenas o Cenário 1 (Cadastro de unidade). O RF 26 menciona "editar e desativar", mas não há BDD correspondente.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar os seguintes cenários à US 8.1:
  > * **Cenário 2: Edição de unidade existente**
  >   * **Dado** que estou autenticado como Administrador e a unidade COFIN já existe
  >   * **Quando** altero o nome, sigla ou gestor responsável da unidade COFIN
  >   * **Então** as alterações são salvas e passam a valer imediatamente para todas as telas e relatórios do sistema, sem afetar processos já concluídos ou em andamento
  > * **Cenário 3: Desativação de unidade**
  >   * **Dado** que estou autenticado como Administrador e a unidade COFIN ainda possui processos em andamento
  >   * **Quando** tento desativar a unidade COFIN
  >   * **Então** o sistema exibe a mensagem "Esta unidade possui X processo(s) em andamento. Para desativá-la, primeiro redistribua ou conclua todos os processos pendentes." e a desativação não é concluída
  > * **Cenário 4: Desativação de unidade sem processos pendentes**
  >   * **Dado** que estou autenticado como Administrador e a unidade COFIN não possui processos em andamento
  >   * **Quando** desativo a unidade COFIN
  >   * **Então** a unidade é marcada como inativa, seus usuários vinculados são automaticamente desvinculados (perdendo acesso ao sistema até serem realocados por um Administrador), e a unidade deixa de aparecer como opção em novos roteiros de tramitação, mas permanece no histórico de processos já tramitados

### Correção 3: US 4.2 — Cenário de Falha na Verificação

* **Como está no PRD original:**
  > Apenas Cenário 1 (Verificação de integridade com assinatura válida). Não há cenário para documento adulterado ou assinatura inválida.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar o seguinte cenário à US 4.2:
  > * **Cenário 2: Documento adulterado ou assinatura inválida**
  >   * **Dado** que um documento possui assinatura digital ICP-Brasil, mas o arquivo foi alterado após a assinatura OU o certificado do signatário foi revogado
  >   * **Quando** acesso o documento e aciono "Verificar Assinatura"
  >   * **Então** o sistema exibe: nome do signatário, CPF, data/hora da assinatura, autoridade certificadora e status "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado", com destaque visual de alerta (ícone ou cor de advertência)
  > * **Cenário 3: Certificado expirado no momento da verificação**
  >   * **Dado** que um documento foi assinado com certificado válido à época, mas o certificado expirou desde então
  >   * **Quando** verifico a assinatura
  >   * **Então** o sistema exibe "Assinatura válida — documento íntegro. Certificado expirado em [data], mas válido na data da assinatura."

### Correção 4: US 7.2 — Cenários para Filtros de Tipo e Período

* **Como está no PRD original:**
  > Apenas Cenário 1 (Pesquisa por assunto). Os filtros de tipo de processo e período, mencionados no título e no RF 22, não têm BDD.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar os seguintes cenários à US 7.2:
  > * **Cenário 2: Pesquisa combinada com múltiplos filtros**
  >   * **Dado** que estou na página de Consulta Pública
  >   * **Quando** preencho o tipo de processo "Licitação" e o período de "01/01/2026 a 31/03/2026" e clico em "Pesquisar"
  >   * **Então** visualizo a lista de processos do tipo Licitação criados no período informado, excluídos os processos marcados como sigilosos
  > * **Cenário 3: Pesquisa sem resultados**
  >   * **Dado** que estou na página de Consulta Pública
  >   * **Quando** preencho qualquer combinação de filtros que não retorna resultados
  >   * **Então** o sistema exibe a mensagem "Nenhum processo encontrado para os filtros informados"

### Correção 5: Nova US para Marcação de Sigilo (Cobertura do RF 23)

* **Como está no PRD original:**
  > O RF 23 determina que processos sigilosos não aparecem na consulta pública, mas não há US definindo quem, quando e como marca um processo como sigiloso.

* **Como deve ficar (Sugestão de Reescrita):**
  > Inserir nova US no Épico 2 (Gestão de Processos e Workflow):
  > **US 2.6:** Como Servidor ou Gestor, eu quero marcar um processo como sigiloso para restringir sua visibilidade na consulta pública.
  > * **Cenário 1: Marcação de processo como sigiloso**
  >   * **Dado** que estou autenticado como Servidor ou Gestor da unidade atual do processo
  >   * **Quando** acesso um processo e aciono "Marcar como Sigiloso"
  >   * **Então** o processo é marcado como sigiloso, a ação é registrada no histórico de tramitação e o processo deixa de aparecer nos resultados da consulta pública
  > * **Cenário 2: Desmarcação de sigilo**
  >   * **Dado** que um processo está marcado como sigiloso
  >   * **Quando** um usuário com permissão (Servidor ou Gestor da unidade atual) aciona "Remover Sigilo"
  >   * **Então** a marcação de sigilo é removida, a ação é registrada no histórico e o processo volta a aparecer na consulta pública
  > * **Cenário 3: Processo sigiloso visível internamente**
  >   * **Dado** que um processo está marcado como sigiloso
  >   * **Quando** um servidor da unidade atual do processo acessa o sistema
  >   * **Então** o processo aparece normalmente no Kanban da unidade, com um indicador visual de "Sigiloso" (ícone de cadeado ou tarja)

## 4. Próximos Passos

O PRD possui fundação sólida — a estrutura de épicos é coerente, 25 dos 28 RFs têm cobertura adequada por US com BDD, e a blindagem tecnológica está impecável. As 10 falhas identificadas são localizadas e corrigíveis.

**Ação recomendada:** Executar a Fase 4 (PRD Patcher) para aplicar as 5 correções propostas na Seção 3, complementadas pelas correções menores listadas abaixo. Após a repactuação, o documento deve ser revalidado para verificar se atinge o score mínimo de 8.0 antes de ser encaminhado à engenharia/OpenSpec.

**Correções menores adicionais que o Patcher deve aplicar (não detalhadas na Seção 3 por economia de espaço, mas igualmente necessárias):**

| # | Local | Problema | Ação |
|---|-------|----------|------|
| 6 | US 2.1 | Formato do número do processo não definido | Definir padrão explícito (ex.: AAAA/NNNNNN — ano com 4 dígitos + sequencial com 6 dígitos, reiniciado a cada ano) |
| 7 | US 3.2 | Comportamento para DOC/DOCX não definido | Adicionar cenário: "Dado que um documento está no formato DOC/DOCX, Quando clico sobre seu nome, Então o download é iniciado automaticamente, pois este formato não permite visualização inline no navegador" |
| 8 | US 4.1 | Ausência de cenário para PIN incorreto | Adicionar cenário: "Dado que estou tentando assinar um documento, Quando insiro PIN incorreto três vezes consecutivas, Então a operação é bloqueada por 30 minutos e recebo um e-mail de alerta" |
| 9 | US 5.1 | Expurgo de notificações após 30 dias sem BDD | Adicionar cenário: "Dado que uma notificação foi gerada há mais de 30 dias, Quando acesso o histórico de notificações, Então esta notificação não aparece mais na listagem" |
| 10 | — (Nova US) | Ausência de US para concessão de permissão de auditoria | Criar US 8.3: "Como Administrador, eu quero conceder e revogar permissão de auditoria a usuários específicos para que auditores autorizados possam acessar processos sigilosos conforme as US 9.1 e 9.2." |
