# Relatório de Revisão de PRD — Controle de Qualidade

<auditoria_interna>

## Análise Crítica — Chain of Thought

### 1. Critérios de Aceitação (BDD)
O PRD aplica o formato BDD (Dado/Quando/Então) com consistência notável em praticamente todas as 35+ Histórias de Usuário. A cobertura de caminhos tristes é ampla: e-mails duplicados, senhas incorretas, bloqueios temporários, unidades inexistentes, formatos inválidos, permissões insuficientes, certificados expirados, PINs incorretos, arquivos não permitidos, devoluções na primeira unidade, etc. O nível de detalhe é superior à média de PRDs que costumo auditar.

**Porém, identifiquei as seguintes fragilidades:**

a) **US 2.1 (Cenário 3): Erro de duplicação de linha** — O texto "Dado que estou criando um processo" aparece duas vezes consecutivas (linha 202 do original). É claramente um erro de copy-paste que precisa ser corrigido.

b) **US 2.4: Apenas um cenário feliz** — Falta o cenário de borda de um processo recém-criado, sem nenhuma tramitação, cujo histórico estaria vazio. O que o sistema exibe? "Nenhuma movimentação registrada"? Isso é uma lacuna BDD.

c) **US 1.6 (Cenário 1): Senha sem complexidade** — A US define "mínimo 8 caracteres", mas não há cenário para rejeitar senhas triviais como "12345678" ou "password". Não está claro se o sistema deve aplicar política de complexidade (maiúsculas, números, símbolos). Essa ambiguidade vai gerar pergunta da engenharia.

d) **US 2.1: Falta cenário para tipo de processo sem roteiro definido** — O que acontece se o servidor seleciona um tipo de processo cujo roteiro está vazio (sem unidades)? O sistema deveria rejeitar a criação, mas não há BDD para isso.

e) **US 5.2 (Notificações por e-mail): Falta cenário de falha de entrega** — O que acontece quando o e-mail do usuário é inválido, a caixa está cheia, ou o servidor SMTP rejeita? O sistema registra a falha? Tenta reenviar? Silencia?

f) **US 7.1 (Consulta Pública): Falta cenário explícito para processo sigiloso** — Embora o FR 23 e a US 2.6 estabeleçam que processos sigilosos não aparecem na consulta pública, a própria US 7.1 não tem um cenário BDD que cubra "consulta por número de processo sigiloso → acesso negado ou 'não encontrado'". Essa redundância de segurança é esperada em um PRD de sistema público.

g) **US 9.1 (Auditor): Falta cenário de acesso a processo não sigiloso** — O Auditor sem permissão explícita consegue ver processos não sigilosos? Ou a permissão de auditoria é binária (ou vê tudo, ou não vê nada além do que seu perfil base permitiria)? O BDD só cobre os extremos.

h) **US 9.2 (Relatórios do Auditor): Saída não especificada** — Os relatórios são gerados em tela? Exportáveis? Em que formato? O BDD não define o formato de saída, o que é uma lacuna para a engenharia estimar esforço.

i) **US 6.1: Tempo Médio de Tramitação com devoluções** — O KPI "tempo médio de tramitação" é definido como "da data de criação até a conclusão", mas se um processo foi devolvido (US 2.2b) e ficou parado por semanas, esse tempo infla artificialmente a métrica? Isso é por design ou é uma distorção? A engenharia vai perguntar.

### 2. Coesão de Escopo (FR ↔ US)

Verifiquei exaustivamente o mapeamento de todos os 38 Requisitos Funcionais contra as Histórias de Usuário. **Todos os FRs possuem cobertura de US correspondente.** O rastreamento é completo e bidirecional. Não há requisitos órfãos.

Porém, identifiquei dois FRs que poderiam ser mais explícitos:

- **FR 25** ("histórico imutável") é coberto pela US 2.4, mas a palavra "imutável" e "à prova de adulteração" que aparece no FR 25 e nos NFRs de Segurança não tem um cenário BDD que demonstre COMO verificar essa imutabilidade. Isso é mais um desejo do que um requisito testável.
- **FR 38** (anonimização automática LGPD) é coberto pela US 10.3, mas o Cenário 1 menciona "prazo legal configurado para o tipo de processo" — essa configuração é feita onde? A US 8.5 (configurações do sistema) não inclui esse parâmetro. É uma dependência cruzada não explicitada.

### 3. Blindagem Tecnológica

O PRD está **excepcionalmente limpo** nesse quesito. Não identifiquei:
- Nenhuma menção a banco de dados específico (MySQL, PostgreSQL, MongoDB, etc.)
- Nenhuma sugestão de linguagem de programação ou framework
- Nenhuma decisão de arquitetura (monolito vs. microsserviços, REST vs. GraphQL, etc.)
- Nenhuma imposição de provedor de infraestrutura ou nuvem

As menções técnicas são exclusivamente de domínio de produto e conformidade:
- "Web PKI" (na premissa de produto do Épico 4) — é uma exigência de compatibilidade de produto, não de arquitetura. A biblioteca/implementação específica fica a cargo da engenharia.
- "HTTPS", "hash criptográfico" (NFRs de Segurança) — são requisitos de segurança, não decisões de implementação.
- "ICP-Brasil", "MP 2.200-2/2001" — são exigências legais, não técnicas.

**Único ponto de atenção:** A premissa do Épico 4 coloca uma dependência externa forte ("assinatura digital via navegador sem software adicional") cuja viabilidade técnica é delegada à engenharia validar. Se a validação falhar, o Épico 4 inteiro fica comprometido. O PRD não prevê contingência (ex.: applet auxiliar, plugin, ou adiamento para fase 2). Isso não é vazamento tecnológico — é um risco de produto não mitigado.

### 4. Cálculo do Score

O PRD é de alta qualidade: cobertura BDD extensa, escopo bem delimitado, personas bem definidas, métricas de sucesso mensuráveis, e rigorosa separação entre o "o quê" e o "como". Não há débitos técnicos estruturais.

As falhas identificadas são pontuais e de fácil correção:
- 1 erro de copy-paste (duplicação de linha)
- ~3 cenários de borda BDD ausentes (complexidade de senha, tipo sem roteiro, falha de e-mail)
- 2 cenários de borda com clareza insuficiente (auditor não sigiloso, formato de saída de relatório)
- 1 métrica ambígua (tempo médio com devoluções)
- 1 risco de produto sem fallback (Épico 4)

**Score: 8.5/10**

Justificativa: O documento está acima do limiar de 8.0 e pode seguir para a engenharia, mas as correções sugeridas na Seção 3 DEVEM ser aplicadas ANTES do início do desenvolvimento para evitar perguntas bloqueantes durante a sprint planning.

</auditoria_interna>

---

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 8.5 / 10
* **Status:** APROVADO PARA ENGENHARIA (Score 8+)
* **Resumo:** O PRD do SETES.DOCS é um documento de alta qualidade, com BDD consistente em 35+ Histórias de Usuário distribuídas em 10 épicos, personas bem caracterizadas, escopo de MVP claramente delimitado (com seção explícita de "Fora de Escopo"), e rastreabilidade completa entre Requisitos Funcionais e User Stories. Não há vazamento de decisões arquiteturais — o documento mantém-se rigorosamente no domínio do "o quê", sem invadir o "como". As falhas encontradas são pontuais: um erro de copy-paste, algumas lacunas de cenários de borda no BDD, e um risco de produto não mitigado no Épico 4 (assinatura digital). **Recomenda-se aplicar as 6 correções da Seção 3 antes da sprint planning** para eliminar ambiguidades que gerariam perguntas bloqueantes da engenharia.

---

## 2. Pontos Críticos Identificados

* **P1 — Erro de copy-paste na US 2.1 (Cenário 3):** A linha "Dado que estou criando um processo" aparece duplicada. Erro de edição que pode confundir a leitura.
* **P2 — US 1.6: Política de complexidade de senha não definida:** A US define apenas "mínimo 8 caracteres", sem especificar se há requisitos de complexidade (maiúsculas, números, caracteres especiais). A engenharia vai perguntar se "12345678" ou "password" são senhas aceitáveis para um sistema governamental.
* **P3 — US 2.1: Falta cenário para criação de processo com tipo sem roteiro:** Se o Administrador cadastrar um tipo de processo mas esquecer de definir o roteiro (ou definir roteiro vazio), e um Servidor tentar criar um processo desse tipo, o sistema deve rejeitar. Não há BDD para este cenário.
* **P4 — US 2.4: Falta cenário de histórico vazio:** Um processo recém-criado, sem tramitação, deve exibir mensagem de "Nenhuma movimentação registrada". O BDD atual só cobre o cenário feliz com múltiplas unidades.
* **P5 — US 5.2: Falta cenário de falha na entrega de e-mail:** O BDD cobre o envio, mas não o que acontece quando o e-mail não é entregue (endereço inválido, caixa cheia, rejeição SMTP). O sistema deve registrar a falha para diagnóstico.
* **P6 — US 7.1: Falta cenário explícito de consulta de processo sigiloso:** Embora o FR 23 e a US 2.6 estabeleçam a regra, a US 7.1 não inclui um cenário BDD redundante que cubra "Cidadão consulta número de processo sigiloso → sistema responde 'Nenhum processo encontrado'". Essa redundância é importante para sistemas públicos com requisitos de auditoria.
* **P7 — US 9.2: Formato de saída do relatório do Auditor não definido:** O BDD diz "o sistema gera um relatório consolidado contendo: (...)", mas não especifica se é exibido em tela, exportável como PDF, CSV, ou ambos. A engenharia precisa desta definição para estimar esforço.
* **P8 — Risco de produto não mitigado no Épico 4:** A premissa do épico de Assinatura Digital delega a validação de viabilidade técnica à engenharia, mas não há plano de contingência caso a premissa se mostre inviável (ex.: certificados do cliente exigem software adicional, ou Web PKI não funciona nos navegadores do órgão).

---

## 3. Propostas de Correção Direta

### Correção 1: US 2.1 — Remover linha duplicada (P1)

* **Como está no PRD original:**
  > *Cenário 3: Interessado com CPF inválido*
  >   * **Dado** que estou criando um processo
  >   * **Dado** que estou criando um processo
  >   * **Quando** preencho um CPF com dígito verificador inválido no campo de interessado

* **Como deve ficar (Sugestão de Reescrita):**
  > *Cenário 3: Interessado com CPF inválido*
  >   * **Dado** que estou criando um processo
  >   * **Quando** preencho um CPF com dígito verificador inválido no campo de interessado

---

### Correção 2: US 1.6 — Adicionar cenário de complexidade mínima de senha (P2)

* **Como está no PRD original (Cenário 1):**
  > *Cenário 1: Primeiro acesso com link válido*
  >   * **Dado** que sou um usuário recém-cadastrado com status "pendente de primeiro acesso"
  >   * **Quando** acesso o link de primeiro acesso recebido por e-mail dentro do prazo de 48 horas
  >   * **Então** sou direcionado para tela de criação de senha (mínimo 8 caracteres) e, após defini-la, sou autenticado e meu status passa para "Ativo"

* **Como deve ficar (Sugestão de Reescrita):**
  > *Cenário 1: Primeiro acesso com link válido e senha forte*
  >   * **Dado** que sou um usuário recém-cadastrado com status "pendente de primeiro acesso"
  >   * **Quando** acesso o link de primeiro acesso recebido por e-mail dentro do prazo de 48 horas e defino uma senha com no mínimo 8 caracteres, contendo pelo menos 1 letra maiúscula, 1 letra minúscula e 1 número
  >   * **Então** a senha é aceita, sou autenticado e meu status passa para "Ativo"
  >
  > *Cenário 1b: Tentativa de senha fraca no primeiro acesso*
  >   * **Dado** que estou na tela de criação de senha do primeiro acesso
  >   * **Quando** defino uma senha que não atende aos critérios (menos de 8 caracteres, ou sem maiúscula, ou sem minúscula, ou sem número)
  >   * **Então** o sistema rejeita a senha e exibe "A senha deve ter no mínimo 8 caracteres, incluindo letras maiúsculas, minúsculas e números"

> **Nota do Revisor:** A mesma regra de complexidade deve ser replicada na US 1.7 (alteração de senha) e na US 1.3 (recuperação de senha — Cenário 3).

---

### Correção 3: US 2.1 — Adicionar cenário de tipo de processo sem roteiro (P3)

* **Como está no PRD original:**
  > *(Não há cenário correspondente)*

* **Como deve ficar (Sugestão de Adição após Cenário 3b):**
  > *Cenário 3c: Tipo de processo sem roteiro definido*
  >   * **Dado** que estou autenticado como Servidor da unidade COFIN
  >   * **Quando** tento criar um processo selecionando um tipo de processo cujo roteiro de tramitação está vazio (sem unidades definidas)
  >   * **Então** o sistema exibe "Este tipo de processo não possui roteiro de tramitação configurado. Entre em contato com o Administrador." e não permite a criação

---

### Correção 4: US 2.4 — Adicionar cenário de histórico vazio (P4)

* **Como está no PRD original:**
  > *(Apenas Cenário 1 — Visualização do histórico com 3 unidades)*

* **Como deve ficar (Sugestão de Adição como Cenário 2):**
  > *Cenário 2: Histórico de processo recém-criado sem movimentações*
  >   * **Dado** que um processo foi criado mas ainda não foi despachado para nenhuma unidade
  >   * **Quando** acesso a tela de detalhes do processo e clico em "Histórico"
  >   * **Então** visualizo a mensagem "Nenhuma movimentação registrada" e a data de criação do processo como informação complementar

---

### Correção 5: US 5.2 — Adicionar cenário de falha na entrega de e-mail (P5)

* **Como está no PRD original:**
  > *(Apenas cenários felizes de envio)*

* **Como deve ficar (Sugestão de Adição como Cenário 3):**
  > *Cenário 3: Falha na entrega do e-mail de notificação*
  >   * **Dado** que um processo foi despachado para minha unidade e meu e-mail cadastrado está incorreto ou inacessível (caixa cheia, servidor rejeita)
  >   * **Quando** o sistema tenta enviar o e-mail de notificação e a entrega falha
  >   * **Então** o sistema registra a falha de entrega em log interno (acessível ao Administrador na tela de "Logs do Sistema") com data, hora, destinatário e motivo da falha. A notificação interna (ícone de sininho) NÃO é afetada — o usuário ainda recebe a notificação no sistema normalmente. O sistema NÃO realiza novas tentativas automáticas de envio para o mesmo evento.

---

### Correção 6: US 7.1 — Adicionar cenário explícito de consulta de processo sigiloso (P6)

* **Como está no PRD original:**
  > *(Não há cenário cobrindo sigilo na própria US 7.1)*

* **Como deve ficar (Sugestão de Adição como Cenário 4):**
  > *Cenário 4: Consulta de processo marcado como sigiloso*
  >   * **Dado** que um processo está marcado como sigiloso (US 2.6) e estou na página de Consulta Pública, sem autenticação
  >   * **Quando** informo o número exato desse processo e clico em "Consultar"
  >   * **Então** o sistema exibe "Nenhum processo encontrado com o número informado" (mesma mensagem do Cenário 2, para não revelar a existência de processos sigilosos)

---

### Recomendação Adicional: Correção 7 — US 9.2 (P7)

* **Como está no PRD original:**
  > *Cenário 1: Geração de relatório com filtros*
  >   * **Então** o sistema gera um relatório consolidado contendo: total de processos no período, tempo médio de tramitação, lista de processos com status atual e unidade atual

* **Como deve ficar (Sugestão de Reescrita):**
  > *Cenário 1: Geração de relatório com filtros*
  >   * **Então** o sistema exibe em tela um relatório consolidado contendo: total de processos no período, tempo médio de tramitação, lista de processos com status atual e unidade atual. O relatório é visualizado na própria interface, com opção de exportação em formato PDF ao clicar no botão "Exportar PDF".

---

### Recomendação Adicional: Correção 8 — Épico 4, Premissa de Produto (P8)

* **Como está no PRD original:**
  > "A viabilidade técnica desta premissa deve ser validada pela engenharia ANTES do início do desenvolvimento do épico, considerando os modelos de certificado em uso pelo cliente."

* **Como deve ficar (Sugestão de Adição):**
  > "A viabilidade técnica desta premissa deve ser validada pela engenharia ANTES do início do desenvolvimento do épico, considerando os modelos de certificado em uso pelo cliente. **Plano de contingência:** Caso a validação identifique restrições impeditivas (ex.: certificados incompatíveis com Web PKI, necessidade de software adicional não autorizado pelos endpoints do órgão), o Épico 4 será replanejado como funcionalidade da Fase 2 do produto, e o MVP será lançado com assinatura digital postergada. Neste cenário, o botão 'Assinar' não estará disponível na interface do MVP, e os documentos serão tramitados sem assinatura digital até a resolução da dependência técnica."

---

## 4. Próximos Passos

1. **Aplicar as correções 1 a 6** (obrigatórias) no PRD original (`docs/fase2_prd.md`) antes de iniciar a sprint planning. As correções 7 e 8 são recomendadas, mas não bloqueiam a transição para a engenharia.
2. **Após aplicar as correções**, o PRD estará em condições ideais para ser consumido por ferramentas de SDD (Specification-Driven Development) como OpenSpec ou similares.
3. **Para o Épico 4 (Assinatura Digital):** Recomenda-se agendar uma sessão de validação técnica com a engenharia ANTES de iniciar qualquer desenvolvimento deste épico, conforme a própria premissa do documento. O resultado desta validação deve ser documentado e anexado ao PRD como adendo.
4. **Executar a Fase 4 (PRD Patcher)** para aplicar as correções de forma sistemática e rastreável.
