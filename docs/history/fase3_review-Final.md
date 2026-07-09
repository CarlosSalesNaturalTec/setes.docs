# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 8.0 / 10
* **Status:** APROVADO PARA ENGENHARIA (Score ≥ 8)
* **Resumo:** O PRD do SETES.DOCS é um documento robusto, com excelente rastreabilidade entre Requisitos Funcionais e Histórias de Usuário, cobertura abrangente de cenários alternativos e de borda em BDD, e blindagem tecnológica impecável — em nenhum momento o PM anterior "escorregou" sugerindo bancos, linguagens ou frameworks. A gestão de premissas condicionais (Épico 4 — Assinatura Digital) demonstra maturidade de produto. No entanto, foram identificadas 5 lacunas pontuais: duas em cenários de borda do fluxo de despacho (US 2.2), uma inconsistência na US 10.3, a ausência de uma US de fallback para o cenário sem assinatura digital, um caso de borda no Dashboard (US 6.1) e a omissão completa de requisitos de backup e disaster recovery nos RNFs. Essas pendências são contornáveis na fase de refinamento com a engenharia e não bloqueiam o início do desenvolvimento. **O documento está apto a seguir para OpenSpec / SDD, desde que os 5 pontos críticos abaixo sejam endereçados antes ou durante a sprint de inception.**

---

## 2. Pontos Críticos Identificados

* **US 2.2 — Cenário de borda ausente: despacho de processo já concluído ou arquivado.** O PRD não define o comportamento quando um servidor tenta despachar um processo cujo status já é "Concluído" ou "Arquivado". Como o Kanban mantém cards nessas colunas, um servidor poderia acidentalmente clicar em "Despachar" sobre um processo concluído. A engenharia ficará sem especificação para este caso.

* **US 2.2 — Cenário de segurança ausente: tentativa de despacho por servidor de outra unidade.** Embora a US 1.4 cubra que o servidor só vê processos da sua unidade, não há cenário cobrindo a tentativa maliciosa (ex.: requisição direta via API ou URL manipulada) de despachar um processo que está em outra unidade. O Cenário 2 da US 1.4 cobre apenas visualização, não ação de despacho. Isso é uma brecha de especificação de segurança.

* **US 10.3 — Inconsistência entre Cenário e Configuração.** O Cenário 1 diz "arquivado há 5 anos (prazo legal configurado para o tipo de processo)", mas o sistema prevê prazos de anonimização configuráveis por tipo de processo (Cenário 2). O valor "5 anos" está hardcoded no texto do cenário quando deveria referenciar o parâmetro configurável. A engenharia pode interpretar incorretamente que 5 anos é um valor fixo.

* **Épico 4 (Assinatura Digital) — Ausência de US de fallback.** O próprio PRD define que o Épico 4 é condicional ao Discovery Técnico. Se a feature for removida do MVP (plano de contingência), não há NENHUMA História de Usuário descrevendo como a interface e o fluxo se comportam sem assinatura digital. O PRD menciona apenas que "o botão 'Assinar' não será exibido", mas não especifica: o que aparece no perfil do usuário na seção "Documentos Assinados"? Como o fluxo de despacho lida com a ausência de assinatura? Isso deixa a engenharia sem especificação para o caminho alternativo.

* **Requisitos Não Funcionais — Omissão de Backup e Disaster Recovery.** Para um sistema que substitui processos administrativos em papel — com exigência legal de imutabilidade e integridade documental — é uma lacuna grave a ausência total de requisitos de backup, retenção, recuperação de desastres e continuidade operacional. Os RNFs atuais cobrem segurança, disponibilidade, performance, usabilidade, conformidade, escalabilidade e manutenibilidade, mas ignoram completamente a resiliência dos dados armazenados.

---

## 3. Propostas de Correção Direta

### Correção 1: Cenários de borda e segurança no despacho (US 2.2)

* **Como está no PRD original:** 
  > A US 2.2 contém apenas os cenários: despacho para próxima unidade (Cenário 1), processo na última unidade (Cenário 2), cancelamento da conclusão (Cenário 3) e roteiro com unidade única (Cenário 4).

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar os seguintes cenários à US 2.2:
  >
  > *Cenário 5: Tentativa de despacho de processo já concluído ou arquivado*
  > * **Dado** que um processo está com status "Concluído" ou "Arquivado" e está visível no Kanban da minha unidade
  > * **Quando** eu, servidor da unidade, seleciono o processo e aciono "Despachar"
  > * **Então** o sistema exibe "Não é possível despachar um processo com status [Concluído/Arquivado]" e a ação não é concluída
  >
  > *Cenário 6: Tentativa de despacho de processo que não está na unidade do servidor (requisição direta)*
  > * **Dado** que um processo está na unidade AJUR e eu sou servidor da unidade COFIN
  > * **Quando** tento despachar esse processo por meio de requisição direta (ex.: API, URL manipulada)
  > * **Então** o sistema rejeita a operação, exibe "Acesso negado — você não tem permissão para movimentar este processo" e registra a tentativa de acesso indevido em log de segurança

### Correção 2: Inconsistência na US 10.3 (Anonimização LGPD)

* **Como está no PRD original:** 
  > *Cenário 1: Anonimização automática após prazo legal*
  > * **Dado** que um processo está arquivado há 5 anos (prazo legal configurado para o tipo de processo)

* **Como deve ficar (Sugestão de Reescrita):**
  > *Cenário 1: Anonimização automática após prazo legal*
  > * **Dado** que um processo está arquivado e o prazo de anonimização LGPD configurado para o seu tipo de processo (parâmetro 'Prazo de anonimização LGPD', definido pelo Administrador por tipo de processo) já expirou, contado a partir da data de arquivamento
  > * **Quando** a rotina trimestral de anonimização é executada
  > * **Então** todos os dados pessoais de interessados [...] são substituídos por identificadores anonimizados [...]
  >
  > *Cenário 3: Prazo de anonimização não configurado para o tipo de processo*
  > * **Dado** que um tipo de processo não possui prazo de anonimização LGPD configurado (valor nulo ou zero)
  > * **Quando** a rotina trimestral de anonimização é executada
  > * **Então** nenhum processo deste tipo é anonimizado, e o evento "Tipo de processo X sem prazo de anonimização configurado" é registrado em log de conformidade

### Correção 3: US de fallback para ausência de assinatura digital

* **Como está no PRD original:** 
  > A premissa do Épico 4 menciona apenas que "a interface não exibirá o botão 'Assinar', e os documentos tramitarão sem assinatura digital até a Fase 2", mas não há US correspondente.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar a seguinte US ao Épico 3 (Gestão Documental) ou ao Épico 4:
  >
  > **US 3.3:** Como Servidor, eu quero tramitar documentos sem assinatura digital quando o módulo de assinatura não está disponível, para que o fluxo de trabalho não seja interrompido.
  > * **Critérios de Aceitação:**
  >   * *Cenário 1: Despacho de processo com documentos não assinados (assinatura digital indisponível)*
  >     * **Dado** que o módulo de assinatura digital NÃO está habilitado no sistema (conforme decisão pós-Discovery Técnico) e um processo da minha unidade possui documentos anexados sem assinatura
  >     * **Quando** aciono "Despachar" para enviar o processo à próxima unidade
  >     * **Então** o despacho é concluído normalmente. O sistema NÃO exige assinatura como pré-condição para despacho. Nenhum botão "Assinar" é exibido na interface. A seção "Documentos Assinados" no perfil do usuário não é exibida. Os documentos tramitam sem metadados de assinatura.
  >   * *Cenário 2: Ativação futura do módulo de assinatura digital*
  >     * **Dado** que o módulo de assinatura digital foi ativado na Fase 2 e o sistema já possui processos e documentos tramitados sem assinatura na Fase 1 (MVP)
  >     * **Quando** um servidor acessa um documento que tramitou sem assinatura
  >     * **Então** o documento aparece sem indicador de assinatura e o botão "Verificar Assinatura" exibe "Este documento não possui assinatura digital — foi tramitado antes da ativação do módulo de assinatura"

### Correção 4: Cenário de borda no Dashboard (US 6.1)

* **Como está no PRD original:** 
  > O Cenário 2 cobre "Dashboard sem dados (gestor recém-cadastrado)" com unidades sem processos, mas não cobre o caso de unidades COM processos mas NENHUM concluído nos últimos 12 meses — o que tornaria o "tempo médio de tramitação" uma divisão por zero.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar à US 6.1:
  >
  > *Cenário 7: KPI de tempo médio sem dados no período*
  > * **Dado** que minhas unidades possuem processos ativos e em tramitação, mas nenhum processo foi concluído nos últimos 12 meses
  > * **Quando** acesso o Dashboard
  > * **Então** o KPI "Tempo Médio de Tramitação" exibe o valor "—" (indisponível) com a mensagem auxiliar "Nenhum processo concluído nos últimos 12 meses". Os demais KPIs (Processos Ativos, Processos Parados, Produtividade) são exibidos normalmente com seus valores calculados.

### Correção 5: Requisitos de Backup e Disaster Recovery (RNF)

* **Como está no PRD original:** 
  > Os RNFs não mencionam backup, retenção ou disaster recovery.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar a seguinte seção aos Requisitos Não Funcionais:
  >
  > * **Resiliência e Continuidade Operacional:** Os dados do sistema (processos, documentos, histórico de tramitação, assinaturas digitais, logs de auditoria) devem ser submetidos a backup completo diário, com retenção mínima de 30 dias para backups diários e 12 meses para backups mensais. O processo de restauração completo (full restore) deve ser possível em até 4 horas. O RPO (Recovery Point Objective) máximo aceitável é de 24 horas (pior caso: perda de até 1 dia de dados). O RTO (Recovery Time Objective) máximo aceitável é de 8 horas para retorno à operação. Os backups devem ser armazenados em local fisicamente distinto do ambiente de produção. Deve ser realizado teste de restauração ao menos uma vez a cada 6 meses, com registro do resultado em log de auditoria.

---

## 4. Próximos Passos

1. **Aplicar as 5 correções** listadas na Seção 3 deste relatório diretamente no PRD (`docs/fase2_prd.md`). As correções são cirúrgicas e não alteram a estrutura ou o escopo do documento — são acréscimos pontuais de cenários e um RNF.

2. **Após aplicar as correções**, execute a Fase 4 (PRD Patcher) para validar que as alterações foram incorporadas corretamente e que o score de prontidão subiu para ≥ 8.5, eliminando as ressalvas para a engenharia.

3. **Estando o score ≥ 8.5 após o patch**, o documento estará em condições ideais para ser encaminhado ao time de engenharia e utilizado como insumo para especificação técnica (OpenSpec, SDD, ou cerimônia de refinamento).

4. **Recomendação adicional:** Durante a sprint de inception, agendar uma sessão de 30 minutos com a engenharia exclusivamente para revisar o tratamento do Épico 4 (Assinatura Digital) e sua condicionalidade, alinhando expectativas sobre o Discovery Técnico e o plano de contingência.
