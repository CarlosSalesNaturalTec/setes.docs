# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 8.0 / 10
* **Status:** APROVADO PARA ENGENHARIA (Score 8+)
* **Resumo:** O PRD do SETES.DOCS apresenta estrutura sólida, com 30+ histórias de usuário cobrindo adequadamente o escopo do MVP. Os critérios de aceitação em formato BDD (Dado/Quando/Então) são, em sua maioria, bem redigidos e mensuráveis, com boa cobertura de caminhos felizes e tristes. O documento demonstra maturidade de produto ao antecipar cenários de borda relevantes (ex.: conta bloqueada, links expirados, devolução de processos, LGPD). Foram identificados 7 pontos de melhoria, todos de gravidade baixa ou moderada — nenhum deles bloqueante para o início do trabalho da engenharia. As correções sugeridas são refinamentos pontuais, não reestruturações. O documento está apto a seguir para a fase de OpenSpec / especificação técnica, desde que as correções críticas (Itens 1 e 2 abaixo) sejam aplicadas previamente.

---

## 2. Pontos Críticos Identificados

* **Crítica 1 — Bootstrap do sistema (bootstrapping):** Nenhuma história de usuário ou requisito funcional cobre a criação do primeiro Administrador do sistema. Como o sistema nasce? Quem cadastra a primeira unidade, o primeiro tipo de processo e o primeiro administrador? Sem este cenário, a engenharia precisará improvisar um script de seed ou um fluxo de instalação inicial não especificado.

* **Crítica 2 — Requisito Funcional 3 sem lastro em US:** O RF 3 ("Cada Servidor deve pertencer a exatamente uma unidade administrativa") é uma regra de integridade de dados importante, mas não possui uma história de usuário ou cenário BDD que o valide. Nenhum cenário cobre a tentativa de vincular um servidor a duas unidades simultaneamente, ou a transferência de um servidor entre unidades (mencionada apenas indiretamente em US 1.4, Cenário 3, mas sem o ato administrativo de transferência).

* **Crítica 3 — Vazamento técnico na especificação do arquivamento automático:** O Cenário 3 da US 2.5 prescreve "diariamente às 02:00 (horário de menor uso do sistema)" como horário de execução da rotina. Esta é uma decisão de scheduling operacional que pertence à engenharia/DevOps, não ao PRD. Além disso, o cenário não especifica o comportamento quando o sistema está indisponível no horário programado (retry? skip? execução assim que disponível?).

* **Crítica 4 — Sessões concorrentes não especificadas:** Nenhuma história de usuário define o comportamento quando um mesmo usuário tenta autenticar-se em dois dispositivos simultaneamente. O sistema permite múltiplas sessões? A segunda sessão invalida a primeira? Este é um ponto de segurança e usabilidade que impacta diretamente a arquitetura de autenticação.

* **Crítica 5 — Vazamento técnico na premissa do Épico 4 (Assinatura Digital):** A "Premissa de Produto" antes do Épico 4 menciona "Web PKI", "token/smart card", "driver" e define um plano de contingência que condiciona o escopo do MVP a uma validação técnica. Embora a intenção de produto seja correta (mitigar risco de dependência externa), o texto cruza a fronteira para especificação de solução técnica. A decisão de postergar ou não o épico deve ser de produto, não condicionada a uma prova de conceito técnica descrita no PRD.

* **Crítica 6 — Vazamento técnico em requisitos LGPD:** As US 10.2 (Cenário 2) e US 10.3 (Cenário 1) prescrevem "substitui CPF/CNPJ por hash irreversível" como mecanismo de anonimização. "Hash irreversível" é uma decisão de implementação criptográfica. O PRD deveria especificar o **resultado esperado** (dados tornam-se irrecuperáveis e não reversíveis), não o **mecanismo** (hash).

* **Crítica 7 — Ausência de cenário de rate limiting na consulta pública:** A US 7.1 (Consulta Pública) não contempla proteção contra scraping massivo ou abuso. Um requisito não funcional ou cenário BDD deveria definir limite de requisições por IP ou mecanismo similar, especialmente relevante para um sistema de governo que expõe dados públicos.

---

## 3. Propostas de Correção Direta

### Correção 1: Bootstrap do sistema (nova US no Épico 8)

* **Como está no PRD original:**
  > (Não existe — lacuna identificada)

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 8.0:** Como operador responsável pela implantação, eu quero executar a inicialização do sistema para criar a estrutura administrativa mínima e o primeiro Administrador.
  > * **Critérios de Aceitação:**
  >   * *Cenário 1: Inicialização do sistema vazio*
  >     * **Dado** que o sistema foi instalado e nunca foi inicializado
  >     * **Quando** acesso a rota de inicialização (`/setup`) e preencho os dados do Administrador root (nome, e-mail, senha) e a primeira unidade administrativa (nome, sigla)
  >     * **Então** o Administrador é criado com perfil "Administrador" e status "Ativo", a unidade é criada como ativa, e a rota de inicialização é desabilitada permanentemente. O Administrador recebe e-mail de confirmação e pode fazer login imediatamente.
  >   * *Cenário 2: Tentativa de acessar inicialização após concluída*
  >     * **Dado** que o sistema já foi inicializado
  >     * **Quando** qualquer pessoa tenta acessar `/setup`
  >     * **Então** o sistema exibe "Sistema já inicializado. Faça login para continuar." e redireciona para a tela de login.

### Correção 2: Lastro para o RF 3 (nova US no Épico 8)

* **Como está no PRD original:**
  > RF 3 — "Cada Servidor deve pertencer a exatamente uma unidade administrativa. Gestores e Administradores podem estar vinculados a uma ou mais unidades." (sem história de usuário correspondente que valide a unicidade)

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 8.6:** Como Administrador, eu quero gerenciar o vínculo de servidores às suas unidades para que cada servidor esteja alocado a exatamente uma unidade por vez.
  > * **Critérios de Aceitação:**
  >   * *Cenário 1: Transferência de servidor entre unidades*
  >     * **Dado** que estou autenticado como Administrador e o servidor João está vinculado à unidade COFIN
  >     * **Quando** altero a unidade do servidor João de COFIN para AJUR
  >     * **Então** o vínculo anterior com COFIN é removido, o novo vínculo com AJUR é estabelecido, e o servidor João passa a enxergar apenas processos da unidade AJUR (mantendo seu histórico de atuação na COFIN conforme US 1.4, Cenário 3)
  >   * *Cenário 2: Tentativa de vínculo duplo como Servidor*
  >     * **Dado** que o servidor João já está vinculado à unidade COFIN
  >     * **Quando** tento adicioná-lo também à unidade AJUR mantendo o perfil de Servidor
  >     * **Então** o sistema rejeita a operação e exibe "Servidores só podem estar vinculados a uma unidade por vez. Para transferir o servidor, altere a unidade atual."

### Correção 3: Remoção de decisão de scheduling da US 2.5

* **Como está no PRD original:**
  > *Cenário 3: Execução da rotina de arquivamento*
  >   * **Dado** que a rotina automática de arquivamento está configurada
  >   * **Quando** a rotina é executada diariamente às 02:00 (horário de menor uso do sistema)
  >   * **Então** todos os processos concluídos cujo prazo de arquivamento [...] expirou são movidos [...]

* **Como deve ficar (Sugestão de Reescrita):**
  > *Cenário 3: Execução da rotina de arquivamento*
  >   * **Dado** que a rotina automática de arquivamento está configurada
  >   * **Quando** a rotina diária de arquivamento é executada
  >   * **Então** todos os processos concluídos cujo prazo de arquivamento (contado a partir da data de conclusão) já expirou são movidos para a coluna "Arquivado" em lote, e cada movimentação é registrada individualmente no histórico do respectivo processo
  >
  > *Cenário 4: Recuperação de execução perdida por indisponibilidade*
  >   * **Dado** que a rotina de arquivamento não pôde ser executada em um ou mais dias por indisponibilidade do sistema
  >   * **Quando** o sistema retorna à operação normal e a rotina é executada
  >   * **Então** todos os processos cujo prazo de arquivamento expirou durante o período de indisponibilidade são arquivados nesta execução, sem perda de eventos de arquivamento

### Correção 4: Sessões concorrentes (nova US no Épico 1)

* **Como está no PRD original:**
  > (Não existe — lacuna identificada)

* **Como deve ficar (Sugestão de Reescrita):**
  > **US 1.9:** Como Usuário, eu quero que o sistema gerencie sessões concorrentes de forma previsível para proteger minha conta contra uso indevido.
  > * **Critérios de Aceitação:**
  >   * *Cenário 1: Login em segundo dispositivo (comportamento padrão)*
  >     * **Dado** que estou autenticado no sistema no Dispositivo A
  >     * **Quando** realizo login com as mesmas credenciais no Dispositivo B
  >     * **Então** ambas as sessões permanecem ativas (sessões independentes). O sistema não invalida a sessão anterior. Cada sessão expira independentemente por inatividade conforme US 1.8, Cenário 2.

### Correção 5: Blindagem da premissa do Épico 4

* **Como está no PRD original:**
  > **Premissa de Produto:** O usuário deve conseguir assinar documentos utilizando seu certificado digital ICP-Brasil (e-CPF/e-CNPJ) armazenado em token ou smart card, diretamente pelo navegador, sem necessidade de instalar software adicional no computador. [...] A viabilidade técnica desta premissa deve ser validada pela engenharia ANTES do início do desenvolvimento do épico, considerando os modelos de certificado em uso pelo cliente.

* **Como deve ficar (Sugestão de Reescrita):**
  > **Premissa de Produto:** O usuário deve conseguir assinar documentos utilizando seu certificado digital ICP-Brasil (e-CPF/e-CNPJ), diretamente pelo navegador, sem necessidade de instalar software adicional no computador. **Decisão de produto:** O Épico 4 (Assinatura Digital) está condicionado à confirmação, durante a fase de Discovery Técnico, de que os certificados em uso pelo cliente são compatíveis com as APIs de assinatura disponíveis nos navegadores-alvo (Chrome, Firefox, Edge — versões estáveis mais recentes). **Plano de contingência:** Caso o Discovery Técnico identifique restrições impeditivas, o Épico 4 será movido para a Fase 2 do produto, e o MVP será lançado sem assinatura digital. Neste cenário, a interface não exibirá o botão "Assinar", e os documentos tramitarão sem assinatura digital até a Fase 2.

### Correção 6: Remoção de jargão criptográfico das US LGPD

* **Como está no PRD original:**
  > US 10.2, Cenário 2: "[...] o sistema anonimiza os dados pessoais do titular no processo indicado (**substitui CPF/CNPJ por hash irreversível** e nome do interessado por "Titular Anonimizado")"
  >
  > US 10.3, Cenário 1: "[...] todos os dados pessoais de interessados (nome completo, CPF, CNPJ, endereço) são substituídos por **valores anonimizados irreversíveis**"

* **Como deve ficar (Sugestão de Reescrita):**
  > US 10.2, Cenário 2: "[...] o sistema anonimiza os dados pessoais do titular no processo indicado (**substitui CPF/CNPJ por identificador anonimizado irreversível, sem possibilidade de reversão ao dado original**, e nome do interessado por "Titular Anonimizado")"
  >
  > US 10.3, Cenário 1: "[...] todos os dados pessoais de interessados (nome completo, CPF, CNPJ, endereço) são substituídos por **identificadores anonimizados, sem possibilidade técnica de recuperação do dado original**, mantendo-se o número do processo, datas, unidades, status e histórico de tramitação íntegros."

### Correção 7: Rate limiting na consulta pública (NFR adicional)

* **Como está no PRD original:**
  > (Não existe — lacuna identificada)

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar à Seção 6 (Requisitos Não Funcionais), sub-item **Segurança**:
  >
  > * **Proteção contra Abuso:** A consulta pública deve implementar limite de requisições por endereço IP de no máximo 60 consultas por minuto. Ao exceder o limite, o sistema deve retornar a mensagem "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente." e liberar o acesso automaticamente após 60 segundos. Este mecanismo visa prevenir scraping massivo sem prejudicar o uso legítimo do cidadão.

---

## 4. Próximos Passos

1. **Aplicar as correções 1 a 7** listadas na Seção 3 acima, com atenção prioritária para:
   - **Correção 1** (Bootstrap) — indispensável para que a engenharia saiba como entregar um sistema funcional "do zero".
   - **Correção 2** (Lastro do RF 3) — fecha a lacuna de rastreabilidade entre requisitos funcionais e histórias de usuário.

2. **Submeter o PRD corrigido a uma nova rodada de revisão** (re-executar a Fase 3) para confirmar que as correções foram incorporadas adequadamente e reavaliar o score.

3. **Após confirmação do score ≥ 8.5**, o documento estará pronto para seguir para:
   - **Fase 4 (Patcher):** Aplicação automatizada das correções aprovadas.
   - **Ferramentas de SDD / OpenSpec:** Geração de especificações técnicas a partir do PRD validado.

4. **Recomendação adicional:** Durante a transição para engenharia, agendar uma sessão de 30 minutos de alinhamento entre PM e tech lead para dirimir dúvidas sobre os cenários mais complexos (Épico 4 — Assinatura Digital e Épico 10 — LGPD), garantindo que não haja interpretações divergentes sobre o comportamento esperado.
