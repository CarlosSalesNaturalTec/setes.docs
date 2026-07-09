# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão
* **Score de Prontidão:** 7/10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS apresenta uma estrutura sólida, com Histórias de Usuário bem detalhadas e critérios de aceitação em formato BDD consistentemente aplicados. O escopo do MVP está bem delimitado, e a seção "Fora de Escopo" é abrangente. No entanto, o documento contém vulnerabilidades que impedem seu envio direto à Engenharia: (1) o Épico 4 (Assinatura Digital) é condicional, mas essa condicionalidade não está refletida na seção de Escopo do MVP, gerando ambiguidade sobre o que o time deve ou não implementar; (2) existem lacunas na rastreabilidade entre Requisitos Funcionais e Histórias de Usuário — 7 USs não possuem RF correspondente; (3) alguns critérios de aceitação contêm detalhes de implementação (ex.: rota `/setup`, tecnologia Web PKI); (4) há casos de borda não cobertos em fluxos críticos como login com conta desativada e vínculo de Gestores a múltiplas unidades.

## 2. Pontos Críticos Identificados
* **Épico 4 condicional não sinalizado no Escopo:** O Épico 4 (Assinatura Digital) está listado como "Dentro do Escopo" na Seção 3, mas o próprio PRD estabelece uma "Decisão de produto" que condiciona sua implementação ao resultado de um Discovery Técnico. Se o Discovery falhar, o Épico 4 sai do MVP. A Engenharia precisa saber, ANTES de iniciar, se deve ou não planejar esse épico. Deixar essa decisão em aberto gera retrabalho e risco de cronograma.
* **Vazamento de implementação — rota `/setup`:** A US 8.0, Cenário 1, especifica literalmente a rota `/setup`. Definir URLs é prerrogativa da Engenharia/Arquitetura, não de Produto. O PM deve descrever O QUE o sistema faz (inicialização), não COMO se acessa (rota `/setup`).
* **Vazamento de implementação — tecnologia de assinatura:** A US 4.1, Cenário 1, menciona "Web PKI", "token/smart card" e "navegador possui suporte a Web PKI". Esses são detalhes técnicos que pertencem à fase de Discovery Técnico ou à especificação técnica, não ao PRD.
* **Lacuna de rastreabilidade US ↔ RF:** As seguintes Histórias de Usuário não possuem Requisito Funcional correspondente na Seção 5: US 1.9 (sessões concorrentes), US 2.8 (Kanban consolidado do Gestor), US 4.2 (verificação de assinatura), US 5.3 (notificação de conclusão), US 5.4 (alerta interno de prazo, sem ser e-mail), US 8.0 (inicialização do sistema), US 8.6 (vínculo servidor-unidade), US 10.2 (gestão de solicitações LGPD). Isso enfraquece a rastreabilidade e pode fazer com que a Engenharia deixe de implementar essas funcionalidades.
* **Caso de borda ausente — login com conta desativada:** A US 1.3 cobre senha incorreta, bloqueio temporário, recuperação de senha, mas não define o comportamento quando um usuário com status "Inativo" (desativado pelo Administrador conforme US 8.4) tenta fazer login.
* **Vínculo de Gestor a múltiplas unidades não especificado:** O RF 3 afirma que "Gestores e Administradores podem estar vinculados a uma ou mais unidades", mas nenhuma História de Usuário descreve COMO um Gestor é vinculado a múltiplas unidades. A US 8.6 (vínculo servidor-unidade) trata apenas de Servidores. Quem vincula o Gestor? É o próprio Gestor ou o Administrador? É na criação do usuário?
* **Ambiguidade no campo "prazo" da US 2.1:** A US 2.1 menciona "prazo em dias corridos" como campo obrigatório na criação do processo, mas não define se esse prazo se refere ao prazo TOTAL do processo ou ao prazo de permanência na unidade atual. Além disso, não há cenário que cubra a tentativa de criar um processo com prazo já vencido (data passada).
* **Critério de aceitação não mensurável — "destaque visual":** A US 2.3, Cenário 4, estabelece que "processos com prazo vencido aparecem no topo com destaque visual". O termo "destaque visual" é subjetivo e não testável. O que constitui "destaque"? Cor diferente? Ícone? Tarja? Badge? A Engenharia precisa de uma especificação objetiva.
* **Decisão de negócio não fundamentada — sigilo por Servidor:** A US 2.6 permite que qualquer Servidor da unidade atual marque um processo como sigiloso. Considerando que a persona "Servidor Operacional" é descrita como "executor do dia a dia", delegar a ele o poder de restringir a visibilidade pública de um processo administrativo é uma decisão de negócio que merece justificativa explícita ou reavaliação. Normalmente, essa prerrogativa caberia ao Gestor ou Administrador.
* **Colisão de nomes de arquivo não tratada:** A US 3.1 não especifica o comportamento quando um usuário anexa um documento com nome idêntico a um documento já existente no mesmo processo. O sistema sobrescreve? Renomeia automaticamente? Rejeita?
* **Prazo de expurgo de notificações não configurável:** A US 5.1 define 30 dias para expurgo de notificações lidas, mas a US 8.5 (configurações do sistema) só contempla prazo de arquivamento e timeout de sessão. A periodicidade das rotinas de arquivamento (diária) e anonimização (trimestral) também não são configuráveis. Se o órgão tiver política de retenção diferente, precisará de alteração de código.

## 3. Propostas de Correção Direta

### Correção 1: Épico 4 condicional — reflexo no Escopo do MVP
* **Como está no PRD original:** 
  > "Dentro do Escopo: (...) Assinatura digital com certificado ICP-Brasil (e-CPF/e-CNPJ) com validade jurídica plena"
* **Como deve ficar (Sugestão de Reescrita):**
  > "**Condicional ao Discovery Técnico:** Assinatura digital com certificado ICP-Brasil (e-CPF/e-CNPJ) com validade jurídica plena. Este item depende de confirmação técnica de compatibilidade dos certificados do cliente com as APIs de assinatura dos navegadores-alvo. Caso o Discovery Técnico identifique restrições impeditivas, este item será removido do MVP e migrado para a Fase 2."

### Correção 2: Remoção de rota `/setup` da US 8.0
* **Como está no PRD original:** 
  > "**Dado** que o sistema foi instalado e nunca foi inicializado
  > **Quando** acesso a rota de inicialização (`/setup`) e preencho os dados do Administrador root..."
* **Como deve ficar (Sugestão de Reescrita):**
  > "**Dado** que o sistema foi instalado e nunca foi inicializado
  > **Quando** acesso a funcionalidade de inicialização do sistema (disponível apenas enquanto o sistema não tiver nenhum Administrador cadastrado) e preencho os dados do Administrador root (nome, e-mail, senha) e a primeira unidade administrativa (nome, sigla)
  > **Então** o Administrador é criado com perfil "Administrador" e status "Ativo", a unidade é criada como ativa, e a funcionalidade de inicialização é desabilitada permanentemente."

### Correção 3: Remoção de detalhes técnicos da US 4.1
* **Como está no PRD original:** 
  > "**Dado** que um processo da minha unidade possui documentos pendentes de assinatura, eu possuo um certificado digital ICP-Brasil (e-CPF) válido armazenado em token/smart card, e o navegador possui suporte a Web PKI
  > **Quando** seleciono um documento e aciono "Assinar", o sistema detecta o certificado digital disponível, solicito o PIN e confirmo"
* **Como deve ficar (Sugestão de Reescrita):**
  > "**Dado** que um processo da minha unidade possui documentos pendentes de assinatura e eu possuo um certificado digital ICP-Brasil (e-CPF ou e-CNPJ) válido e acessível ao navegador
  > **Quando** seleciono um documento, aciono "Assinar", o sistema detecta o certificado digital disponível, solicito a credencial de acesso ao certificado e confirmo
  > **Então** o sistema aplica a assinatura digital ao documento, registra data/hora da assinatura, vincula ao meu usuário, e o documento aparece na seção "Documentos Assinados" do meu perfil e do processo"

### Correção 4: Caso de borda — login com conta desativada
* **Como está no PRD original:** (inexistente — a US 1.3 não contempla este cenário)
* **Como deve ficar (Sugestão de Reescrita):** Inserir novo cenário na US 1.3:
  > "*Cenário 6: Login com conta desativada*
  >   **Dado** que minha conta foi desativada por um Administrador
  >   **Quando** tento fazer login com minhas credenciais corretas
  >   **Então** o sistema rejeita a autenticação e exibe "Conta desativada. Entre em contato com o Administrador do sistema." NENHUM e-mail de alerta é enviado (pois a desativação é uma ação administrativa legítima, não uma tentativa de invasão)."

### Correção 5: Vínculo de Gestor a múltiplas unidades
* **Como está no PRD original:** Inexistente — o documento não descreve como um Gestor é vinculado a múltiplas unidades.
* **Como deve ficar (Sugestão de Reescrita):** Adicionar novo cenário à US 8.1 (ou criar US 8.6b):
  > "**US 8.6b:** Como Administrador, eu quero definir quais unidades um Gestor gerencia para que ele tenha visibilidade adequada à sua responsabilidade.
  > * **Critérios de Aceitação:**
  >   * *Cenário 1: Vinculação de Gestor a múltiplas unidades*
  >     **Dado** que estou autenticado como Administrador e o usuário Maria possui perfil de Gestor
  >     **Quando** acesso os dados de Maria e seleciono as unidades COFIN, AJUR e DIRAD como unidades gerenciadas
  >     **Então** Maria passa a visualizar o Kanban consolidado (US 2.8) e o Dashboard (US 6.1) com dados das três unidades, e pode cadastrar usuários (US 1.2) em qualquer uma delas
  >   * *Cenário 2: Gestor com apenas uma unidade*
  >     **Dado** que estou autenticado como Administrador
  >     **Quando** cadastro ou edito um usuário com perfil de Gestor e seleciono apenas uma unidade gerenciada
  >     **Então** o sistema aceita a configuração (um Gestor pode gerenciar uma ou mais unidades)"

### Correção 6: Critério de "destaque visual" mensurável
* **Como está no PRD original:** 
  > "**Então** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos com prazo vencido aparecem no topo com destaque visual"
* **Como deve ficar (Sugestão de Reescrita):**
  > "**Então** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos com prazo vencido aparecem no topo da coluna com os seguintes indicadores visuais: (a) o número de dias vencidos é exibido em cor vermelha com um ícone de relógio/calendário; (b) o texto do prazo no card utiliza peso de fonte bold; (c) a borda esquerda do card recebe uma barra vermelha de 4px de espessura"

### Correção 7: Colisão de nome de arquivo na US 3.1
* **Como está no PRD original:** (inexistente)
* **Como deve ficar (Sugestão de Reescrita):** Inserir novo cenário na US 3.1:
  > "*Cenário 5: Upload de arquivo com nome duplicado*
  >   **Dado** que um processo já possui um documento anexado chamado "parecer.pdf"
  >   **Quando** tento anexar outro arquivo com o mesmo nome "parecer.pdf"
  >   **Então** o sistema aceita o upload e renomeia automaticamente o novo arquivo para "parecer (1).pdf". O documento original não é sobrescrito. Ambos os arquivos aparecem na lista de documentos do processo, preservando a integridade de cada um."

### Correção 8: Requisitos Funcionais ausentes
Inserir na Seção 5 (Requisitos Funcionais) os seguintes itens para fechar as lacunas de rastreabilidade:
> 39. O sistema deve permitir que um mesmo usuário mantenha múltiplas sessões ativas simultaneamente em dispositivos diferentes, com expiração independente por inatividade (US 1.9)
> 40. O sistema deve permitir ao Gestor visualizar um quadro Kanban consolidado com os processos de todas as unidades que gerencia, com filtro por unidade (US 2.8)
> 41. O sistema deve permitir a verificação de integridade e validade de documentos assinados digitalmente, exibindo signatário, data, autoridade certificadora e status da assinatura (US 4.2)
> 42. O sistema deve gerar notificação interna quando um processo da unidade do usuário é concluído (US 5.3)
> 43. O sistema deve gerar notificação interna de alerta quando um processo da unidade do usuário está com prazo a vencer em 2 dias corridos ou menos (US 5.4)
> 44. O sistema deve permitir ao Administrador gerenciar solicitações LGPD recebidas, processando pedidos de exclusão ou anonimização de dados pessoais (US 10.2)

## 4. Próximos Passos
* O documento **NÃO está pronto para ser enviado à Engenharia ou para ferramentas de SDD (OpenSpec)**. O score 7/10 indica que há riscos de retrabalho e ambiguidade que precisam ser sanados antes da especificação técnica.
* **Ações recomendadas:**
  1. Aplicar as 8 correções propostas na Seção 3 deste relatório.
  2. Revisar a decisão de negócio sobre sigilo por Servidor (US 2.6) — confirmar com stakeholders se Servidores operacionais devem realmente ter esse poder.
  3. Definir e documentar o resultado do Discovery Técnico do Épico 4 ANTES de enviar o PRD à Engenharia, para que o escopo seja definitivo.
  4. Tornar configuráveis (via US 8.5) os prazos de expurgo de notificações e a periodicidade das rotinas automáticas (arquivamento e anonimização).
  5. Após as correções, reexecutar a auditoria (Fase 3) para confirmar que o score atingiu 8+ antes de avançar para a Fase 4 (Patcher) ou Fase 5 (Change Manager).
