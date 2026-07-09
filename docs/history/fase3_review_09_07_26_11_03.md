# Relatório de Revisão de PRD — Controle de Qualidade

<auditoria_interna>

## 1. Critérios de Aceitação (BDD)

**Pontos fortes:** O formato Dado/Quando/Então é aplicado de forma consistente em praticamente todas as US. A maioria das US cobre ao menos um caminho triste (ex.: US 1.2 cobrindo tentativa de cadastro em unidade não gerenciada e com perfil privilegiado; US 1.3 cobrindo senha incorreta, recuperação, desbloqueio, e-mail não cadastrado). A granularidade dos cenários está razoável.

**Fragilidades detectadas:**
- **US 1.1 (Cadastro de usuário por Admin):** Faltam cenários de borda: e-mail com formato inválido, nome vazio ou apenas com espaços, unidade inexistente. O Cenário 1 menciona "preencho nome, e-mail, unidade, perfil" mas não especifica validação de formato do e-mail.
- **US 1.4 (Visibilidade restrita):** Apenas 1 cenário (caminho feliz). Faltam: tentativa de acesso direto por URL manipulada a processo de outra unidade; o que o servidor vê ao ser transferido de unidade (processos da unidade anterior no histórico?).
- **US 2.2 (Despacho):** Fluxo crítico AUSENTE — rejeição/devolução de processo para unidade anterior. Em processos administrativos reais, é comum uma unidade devolver o processo para correções. O PRD só modela o fluxo "para frente". Isso é uma lacuna de negócio grave.
- **US 2.3 (Kanban):** O termo "Kanban" sugere drag-and-drop, mas o PRD não especifica se a transição entre colunas é feita por arrastar cards ou exclusivamente via botão de ação. Ambiguidade que impacta diretamente a estimativa de esforço da engenharia.
- **US 2.5 (Arquivamento automático):** Apenas 1 cenário. Faltam: o que ocorre se o Administrador alterar o prazo de arquivamento enquanto há processos concluídos? O novo prazo se aplica a processos já concluídos? A rotina automática é executada em qual periodicidade?
- **US 3.1 (Upload de documentos):** Falta cenário de remoção/exclusão de documento anexado por engano. Upload múltiplo simultâneo também não é coberto.
- **US 4.1 (Assinatura digital):** O mecanismo de interface com o certificado ICP-Brasil NÃO é especificado — Web PKI? Plugin de navegador? Aplicativo local? Esta é uma das maiores incógnitas arquiteturais do MVP e impacta profundamente a viabilidade técnica.
- **US 5.1 (Notificações):** Cenário 2 diz que abrir o painel zera o contador e marca TODAS como lidas. Isso é uma decisão de produto questionável (e não tratada como tal) — o usuário pode abrir o painel para ver a lista sem querer marcar tudo como lido.
- **US 6.1 (Dashboard):** O KPI "tempo médio de tramitação" não especifica se considera apenas processos concluídos ou também os em andamento. Isso altera completamente o cálculo e a interpretação do número.
- **US 8.2 (Roteiros):** Falta cenário: criação de tipo de processo com roteiro vazio (sem unidades) ou com nome duplicado.

## 2. Coesão de Escopo (Requisitos Funcionais × Histórias de Usuário)

**Pontos fortes:** A rastreabilidade é boa. Os 33 RFs são cobertos por USs correspondentes. RFs 29-33 (primeiro acesso, troca de senha, sessão, busca, desativação de usuário) estão todos cobertos.

**Fragilidades:**
- **RF 10:** "O sistema deve alterar automaticamente o status do processo conforme seu avanço" — a palavra "automaticamente" é ambígua. O status muda como efeito colateral do despacho (US 2.2), mas não há US explícita cobrindo transições manuais de status, se existirem.
- **RF 24:** "O perfil do usuário deve exibir a relação de processos em que atuou e documentos assinados" — a US 1.5 cobre isso, mas apenas para o próprio usuário. E se um Gestor quiser ver o histórico de atuação de um servidor da sua unidade? Lacuna não coberta.
- **Configurações do sistema:** Os RFs não incluem requisitos para parametrização de constantes do sistema (prazo de arquivamento, tempo de sessão, periodicidade da rotina de arquivamento). Não há US para o Administrador configurar esses parâmetros — eles aparecem "mágicos" no texto ("padrão: 30 dias", "30 minutos de inatividade").
- **Relacionamento Gestor × unidade:** RF 3 diz que "Gestores e Administradores podem estar vinculados a uma ou mais unidades", mas nenhuma US cobre o Administrador vinculando/desvinculando um Gestor a múltiplas unidades. A US 8.1 cobre o cadastro de unidade com "gestor responsável", mas e a gestão de múltiplos vínculos?

## 3. Blindagem Tecnológica

**Pontos fortes:** O PRD é notavelmente limpo de vazamentos de arquitetura. Não menciona banco de dados, linguagem de programação, framework ou infraestrutura específica. Termos como "hash criptográfico", "HTTPS", "ICP-Brasil" são requisitos de conformidade, não escolhas técnicas.

**Fragilidades pontuais:**
- **"armazenados no próprio sistema"** (RF 14 e Escopo): Sugere implicitamente armazenamento local/on-premises em oposição a cloud/object storage (ex.: S3). Embora a intenção provavelmente seja "não depende de sistema externo de gestão documental", a redação pode ser interpretada como decisão de infraestrutura.
- **"rotina automática de arquivamento"** (US 2.5): O termo "rotina" pode ser lido como cron job / scheduled task, mas é aceitável como linguagem de negócio. Não chega a ser vazamento grave.
- **US 3.2 menciona "visualização inline" de PDF** e **US 4.1 menciona "seleciono um documento e aciono 'Assinar', insiro meu certificado digital e PIN"** — embora não nomeiem tecnologias, a engenharia precisará de esclarecimentos sobre o mecanismo de integração com certificados (Web PKI, extensão, applet). Isso é mais uma lacuna de requisito do que vazamento.

## 4. Cálculo do Score

**Resumo das falhas por severidade:**

| Severidade | Falhas |
|---|---|
| **Crítica (bloqueante)** | 1 — Fluxo de devolução/rejeição de processo ausente (US 2.2) |
| **Alta** | 3 — Mecanismo de assinatura digital não especificado (US 4.1); inconsistência "dias corridos" vs. "dias úteis" (US 2.1 vs. 6.1); ausência de US para parametrização do sistema |
| **Média** | 6 — Cenários de borda faltantes (US 1.1, 1.4, 2.3, 2.5, 3.1, 8.2); ambiguidade do Kanban (drag-and-drop vs. botão); comportamento questionável de marcação de notificações como lidas (US 5.1) |
| **Baixa** | 4 — Definição ambígua de "tempo médio" (US 6.1); RF 10 com "automaticamente" vago; falta de US para vínculo Gestor-múltiplas-unidades; redação "armazenados no próprio sistema" |

O documento é estruturalmente sólido, cobre 9 épicos e 33 RFs com BDD consistente, mas carrega uma lacuna funcional crítica (devolução de processos), uma incógnita arquitetural de alto risco (mecanismo de assinatura ICP-Brasil), e omite completamente a parametrização do sistema — três fatores que, combinados, gerariam retrabalho significativo na fase de engenharia.

**Nota: 6.5 / 10**

</auditoria_interna>

---

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 6.5 / 10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS é estruturalmente bem organizado, com 9 épicos, 33 requisitos funcionais e aplicação consistente do formato BDD. No entanto, o documento apresenta uma **lacuna funcional crítica** (ausência do fluxo de devolução/rejeição de processos, essencial em qualquer trâmite administrativo real), **uma incógnita arquitetural de alto risco** (o mecanismo de integração com certificados ICP-Brasil — Web PKI? Plug-in? Applet? — não é endereçado) e **omite completamente as histórias de usuário para parametrização do sistema** (prazos de arquivamento, timeout de sessão, periodicidade de rotinas). Some-se a isso inconsistências entre "dias corridos" e "dias úteis" e cenários de borda insuficientes. O documento **não está pronto para ser entregue à engenharia** e requer uma rodada de correções direcionadas antes de avançar para OpenSpec/SDD.

---

## 2. Pontos Críticos Identificados

* **🔴 CRÍTICO — Fluxo de devolução/rejeição de processos ausente (US 2.2):** O PRD modela apenas o despacho "para frente" no roteiro. Em processos administrativos reais, é extremamente comum que uma unidade precise devolver o processo à unidade anterior para correções, diligências ou complementação de documentos. Sem esse fluxo, o sistema não atende à realidade operacional de nenhum órgão público.

* **🔴 CRÍTICO — Mecanismo de assinatura digital ICP-Brasil não especificado (US 4.1):** O PRD diz "insiro meu certificado digital e PIN", mas não define COMO o sistema se comunica com o certificado. É via Web PKI (componente de navegador)? É um applet Java? É uma aplicação desktop auxiliar? Esta decisão impacta profundamente arquitetura, segurança e experiência do usuário. Sem essa definição, a engenharia não tem como estimar o épico de assinatura digital.

* **🔴 ALTA — Inconsistência entre "dias corridos" e "dias úteis":** A US 2.1 define o campo "prazo" como "dias corridos". A US 5.2 alerta sobre prazo a vencer em "2 dias corridos". Mas a US 6.1 define "processos parados" como "sem movimentação há mais de 5 dias úteis". Essa mistura de referências temporais (corridos vs. úteis) em diferentes partes do sistema vai gerar confusão na implementação e nos relatórios.

* **🔴 ALTA — Ausência de US para parametrização do sistema:** O PRD menciona "padrão: 30 dias" para arquivamento e "30 minutos de inatividade" para expiração de sessão, mas não existe UMA história de usuário sequer para o Administrador configurar esses valores. Sem isso, ou os valores ficam hardcoded (débito técnico), ou a engenharia inventa a interface de configuração sem especificação.

* **🟡 MÉDIA — Cenários de borda insuficientes em múltiplas US:** A US 1.1 (cadastro de usuário) não valida formato de e-mail ou nome vazio. A US 1.4 (visibilidade restrita) só tem o caminho feliz — não cobre tentativa de acesso direto por URL manipulada. A US 2.5 (arquivamento automático) não especifica o impacto da alteração do prazo sobre processos já concluídos, nem a periodicidade da rotina.

* **🟡 MÉDIA — Ambiguidade do termo "Kanban" (US 2.3):** O termo "Kanban" sugere drag-and-drop, mas o PRD não especifica se os cards são arrastáveis entre colunas ou se a mudança de status ocorre exclusivamente via botões de ação. Essa ambiguidade pode facilmente dobrar a estimativa de esforço do frontend.

* **🟡 MÉDIA — Comportamento questionável na marcação de notificações (US 5.1):** O Cenário 2 define que abrir o painel de notificações zera o contador e marca TODAS como lidas. Isso é uma decisão de UX questionável — o usuário pode abrir o painel apenas para ver a lista, sem querer marcar tudo como lido. Deveria haver distinção entre "abrir o painel" e "marcar como lida".

* **🟡 MÉDIA — Definição ambígua de "tempo médio de tramitação" (US 6.1):** O PRD não especifica se o cálculo considera apenas processos concluídos ou também os que estão em andamento. O denominador muda completamente o número exibido e sua interpretação gerencial.

* **🟢 BAIXA — Faltam cenários de exclusão de documentos (US 3.1) e upload múltiplo.**

* **🟢 BAIXA — Ausência de US para gestão de vínculo Gestor ↔ múltiplas unidades:** O RF 3 afirma que Gestores podem estar vinculados a mais de uma unidade, mas não há US que cubra o Administrador gerenciando esses vínculos.

---

## 3. Propostas de Correção Direta

### Correção 1: Adicionar fluxo de devolução/rejeição de processos (US 2.2)

* **Como está no PRD original:** 
  > A US 2.2 cobre apenas o despacho para a próxima unidade do roteiro (fluxo "para frente"). Não há qualquer menção a devolução, rejeição ou retorno de processo à unidade anterior.

* **Como deve ficar (Sugestão de Reescrita):**
  > **Adicionar NOVA US 2.2b — Devolução de processo:**
  > 
  > * **US 2.2b:** Como Servidor, eu quero devolver um processo para a unidade anterior para solicitar correções ou diligências antes de prosseguir com a tramitação.
  >   * **Critérios de Aceitação:**
  >     * *Cenário 1: Devolução para a unidade anterior:* **Dado** que um processo está na minha unidade e veio da unidade COFIN. **Quando** aciono a ação "Devolver", seleciono um motivo (opções predefinidas: "Documentação insuficiente", "Correção de dados", "Diligência complementar") e, opcionalmente, adiciono uma justificativa em texto livre. **Então** o processo retorna para a unidade COFIN com status "Em Tramitação", a devolução é registrada no histórico com data/hora, responsável, motivo e justificativa, e os servidores da COFIN recebem notificação de devolução.
  >     * *Cenário 2: Tentativa de devolução na primeira unidade do roteiro:* **Dado** que um processo está na primeira unidade do roteiro. **Quando** o servidor tenta acionar "Devolver". **Então** o sistema exibe "Não é possível devolver um processo que está na unidade de origem do roteiro" e a ação não é concluída.
  >     * *Cenário 3: Devolução sem seleção de motivo:* **Dado** que estou devolvendo um processo. **Quando** tento confirmar a devolução sem selecionar um motivo. **Então** o sistema exibe "Selecione um motivo para a devolução" e não conclui a ação.

### Correção 2: Especificar mecanismo de assinatura digital (US 4.1)

* **Como está no PRD original:** 
  > "Quando seleciono um documento e aciono 'Assinar', insiro meu certificado digital e PIN"

* **Como deve ficar (Sugestão de Reescrita):**
  > **Adicionar premissa técnica ao Épico 4:**
  > 
  > "A assinatura digital será realizada via Web PKI (WebCrypto ou similar), permitindo que o navegador acesse o certificado digital armazenado no token/smart card do usuário sem necessidade de instalação de software adicional. O sistema deve ser compatível com os principais navegadores (Chrome, Firefox, Edge) em suas versões estáveis mais recentes. Esta abordagem será validada por meio de um spike técnico de 3 dias ANTES do início do desenvolvimento do épico, para confirmar a viabilidade com os modelos de certificado em uso pelo cliente."
  > 
  > **Adicionar ao Cenário 1 da US 4.1:**
  > "**Dado** que um processo da minha unidade possui documentos pendentes de assinatura, eu possuo um certificado digital ICP-Brasil (e-CPF) válido armazenado em token/smart card, e o navegador possui suporte a Web PKI. **Quando** seleciono um documento e aciono 'Assinar', o sistema detecta o certificado digital disponível, solicito o PIN e confirmo. **Então** o sistema aplica a assinatura digital..."

### Correção 3: Unificar referência temporal — "dias corridos" vs. "dias úteis"

* **Como está no PRD original:** 
  > US 2.1: "prazo em dias corridos" | US 6.1: "sem movimentação há mais de 5 dias úteis"

* **Como deve ficar (Sugestão de Reescrita):**
  > **Padronizar todas as referências temporais para "dias corridos":**
  > 
  > * US 2.1 — Manter "prazo em dias corridos" ✅
  > * US 5.2 — Manter "2 dias corridos" ✅
  > * US 6.1 — Alterar "sem movimentação há mais de 5 dias úteis" para **"sem movimentação há mais de 7 dias corridos"** (7 dias corridos ≈ 5 dias úteis, mantendo a intenção original de ~1 semana de inatividade)
  > 
  > **Justificativa:** "Dias corridos" é inequívoco para sistemas que operam 24/7 e evita ambiguidades com feriados regionais, pontos facultativos e calendários administrativos que variam entre órgãos.

### Correção 4: Adicionar US para parametrização do sistema

* **Como está no PRD original:** 
  > O PRD menciona "padrão: 30 dias" e "30 minutos de inatividade" sem nenhuma US para o Administrador configurar.

* **Como deve ficar (Sugestão de Reescrita):**
  > **Adicionar NOVA US 8.5 — Configuração de parâmetros do sistema:**
  > 
  > * **US 8.5:** Como Administrador, eu quero configurar os parâmetros operacionais do sistema para adequá-lo às políticas do órgão.
  >   * **Critérios de Aceitação:**
  >     * *Cenário 1: Configuração do prazo de arquivamento:* **Dado** que estou autenticado como Administrador. **Quando** acesso "Configurações do Sistema" e altero o prazo de arquivamento de 30 para 60 dias. **Então** o novo prazo se aplica apenas a processos concluídos a partir desta data; processos já concluídos mantêm o prazo vigente no momento da conclusão. O sistema exibe mensagem de confirmação: "Novo prazo de arquivamento configurado: 60 dias. Este prazo se aplica apenas a processos concluídos a partir de hoje."
  >     * *Cenário 2: Configuração do timeout de sessão:* **Dado** que estou autenticado como Administrador. **Quando** altero o tempo de inatividade de 30 para 60 minutos. **Então** a nova configuração passa a valer imediatamente para todas as novas sessões. Sessões já ativas mantêm o timeout original até o próximo login.
  >     * *Cenário 3: Valor inválido:* **Dado** que estou na tela de configurações. **Quando** informo um valor negativo ou zero para qualquer parâmetro. **Então** o sistema exibe "O valor deve ser um número inteiro positivo" e não salva a configuração.

### Correção 5: Esclarecer interação do Kanban (US 2.3)

* **Como está no PRD original:** 
  > "visualizo um quadro com colunas 'Aberto', 'Em Tramitação', 'Concluído' e 'Arquivado', cada uma contendo os cards dos processos correspondentes"

* **Como deve ficar (Sugestão de Reescrita):**
  > **Adicionar ao Cenário 1 da US 2.3:**
  > 
  > "O Kanban é um quadro de **visualização**, não de manipulação direta. As transições de status ocorrem exclusivamente por meio de ações explícitas: o botão 'Despachar' move o card de 'Aberto' para 'Em Tramitação' (ou para fora da unidade, se despachado para a próxima); o botão 'Concluir' na última unidade move para 'Concluído'; a rotina automática move de 'Concluído' para 'Arquivado'. Os cards **NÃO são arrastáveis** entre colunas no MVP."

### Correção 6: Refinar marcação de notificações como lidas (US 5.1)

* **Como está no PRD original:** 
  > "Quando clico no ícone do sino para abrir o painel de notificações. Então o contador é zerado e as notificações são marcadas como lidas"

* **Como deve ficar (Sugestão de Reescrita):**
  > * *Cenário 2 (reescrito) — Abertura do painel sem zerar contador:* **Dado** que tenho 3 notificações não lidas. **Quando** clico no ícone do sino para abrir o painel de notificações. **Então** visualizo a lista de notificações, o contador permanece em 3, e cada notificação exibe um indicador visual de "não lida" (bola azul ou destaque). O contador só é decrementado e a notificação marcada como lida quando EU clicar sobre uma notificação específica OU quando eu clicar no botão "Marcar todas como lidas" disponível no topo do painel. Notificações lidas permanecem acessíveis no histórico por 30 dias.

---

## 4. Próximos Passos

1. **Aplicar as 6 correções propostas** na Seção 3 deste relatório, com atenção prioritária para: (a) adicionar o fluxo de devolução de processos, (b) especificar o mecanismo de assinatura digital, e (c) criar a US de parametrização do sistema.
2. **Revisar as US com cenários de borda insuficientes** (US 1.1, 1.4, 2.5, 3.1, 8.2) e complementá-las com caminhos tristes.
3. **Padronizar a nomenclatura** das personas: usar consistentemente "Gestor" (não alternar com "Chefe de Unidade").
4. Após as correções, **reprocessar este PRD pela Fase 3** para reavaliação do Score de Prontidão. O documento **não deve** ser encaminhado para OpenSpec/SDD enquanto o score for inferior a 8.
5. Recomenda-se também um **spike técnico de 3 dias** para validação do mecanismo de assinatura digital via Web PKI com os certificados ICP-Brasil em uso pelo cliente, ANTES do início do desenvolvimento do Épico 4.
