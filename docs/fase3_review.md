# Relatório de Revisão de PRD — Controle de Qualidade

## 1. Veredito e Score de Prontidão

* **Score de Prontidão:** 7.0 / 10
* **Status:** REQUER REFATORAÇÃO (Score < 8)
* **Resumo:** O PRD do SETES.DOCS é um documento notavelmente abrangente, com 10 épicos, 44 requisitos funcionais e cobertura extensiva de cenários BDD (mais de 130 cenários mapeados). As personas são bem definidas, o escopo do MVP está claramente delimitado (com itens "dentro" e "fora" explícitos) e há atenção louvável a temas espinhosos como LGPD, sessões concorrentes e devolução de processos. Contudo, o documento não atinge o patamar de prontidão para engenharia devido a **6 falhas pontuais mas bloqueantes**: (1) conflito entre valores _hardcoded_ e parâmetros configuráveis nas US 5.2/5.4; (2) funcionalidade de restauração de documentos (soft delete) citada mas sem História de Usuário correspondente; (3) US 8.5 agrupa 10 parâmetros críticos sem cenários de aceitação individuais; (4) _typo_ na US 4.1; (5) _overflow_ do sequencial de processo não tratado; e (6) ausência de cenário para upload de arquivo vazio. Com as 6 correções propostas na Seção 3, este documento atingirá nota ≥ 8.5 e estará apto para a fase de OpenSpec/SDD.

---

## 2. Pontos Críticos Identificados

* **[CRÍTICO] Conflito de especificação — valor hardcoded vs. parâmetro configurável (US 5.2 e US 5.4):** Os cenários de aceitação da US 5.2 (Cenário 2) e US 5.4 (Cenário 1) referem-se a "2 dias corridos" como gatilho para alerta de prazo. Entretanto, a US 8.5 (Cenário 4) define "Dias de antecedência para alerta de prazo" como parâmetro configurável com padrão de 2 dias. Se um Administrador alterar o parâmetro para 5 dias, o comportamento esperado torna-se ambíguo: o sistema deve seguir o valor configurado (US 8.5) ou os "2 dias" descritos nos critérios de aceitação (US 5.2/5.4)? A engenharia não terá como decidir qual especificação prevalece.

* **[CRÍTICO] Funcionalidade de restauração de documentos sem História de Usuário (US 3.1):** O Cenário 3 da US 3.1 descreve soft delete com retenção de 30 dias e afirma textualmente: _"Durante o período de retenção, o Administrador pode restaurar o documento."_ Esta é uma funcionalidade explícita (restauração de documento por Administrador) que não possui nenhuma História de Usuário correspondente no Épico 8 (Administração do Sistema) nem em qualquer outro épico. A engenharia receberá um requisito implícito sem critérios de aceitação — quem pode restaurar? Como se acessa a área de retenção? O que acontece se o processo já foi arquivado?

* **[ALTO] US 8.5 — Agrupamento excessivo de parâmetros sem cenários individuais:** O Cenário 4 da US 8.5 lista 10 parâmetros configuráveis em bloco, com uma única validação genérica ("deve ser um número inteiro positivo"). Parâmetros com impacto de segurança distinto — como "Número máximo de tentativas de login antes do bloqueio", "Duração do bloqueio temporário" e "Profundidade do histórico de senhas" — não possuem cenários de borda individuais. Exemplos de cenários ausentes: o que ocorre se o Admin tentar configurar 0 tentativas de login (bloquearia todos os usuários no primeiro erro)? E se configurar timeout de sessão para 10 segundos (tornaria o sistema inutilizável)?

* **[ALTO] US 4.1 Cenário 1 — Erro de digitação com impacto semântico:** O texto contém a frase _"eu possuo um certificado digital ICP-Brasil (e-CPF) válido válido"_ — a duplicação da palavra "válido" é um erro de revisão. Embora simples de corrigir, demonstra falta de revisão final e pode gerar dúvida sobre se havia intenção de qualificar diferentemente as duas ocorrências (ex.: "válido e acessível").

* **[MÉDIO] US 2.1 Cenário 1 — Overflow do sequencial de processo sem limite máximo:** O cenário define que o número sequencial no formato AAAA/NNNNNN (6 dígitos) deve expandir para 7 dígitos ao atingir 999.999. Porém, não há especificação do que ocorre quando o sequencial de 7 dígitos também atingir o limite (9.999.999). Embora seja um cenário de altíssimo volume, um sistema de processos administrativos que tramita 10 milhões de processos/ano é uma possibilidade em esferas como União ou estados populosos. A ausência de um limite superior documentado ou de uma regra de expansão adicional é uma lacuna de especificação.

* **[MÉDIO] US 3.1 — Ausência de cenário para upload de arquivo vazio (0 byte):** Os cenários cobrem formato inválido e tamanho máximo excedido, mas não contemplam o caso de um arquivo com 0 byte (arquivo corrompido ou erro de seleção). O sistema deve rejeitar uploads de 0 byte? Se sim, com qual mensagem? A omissão força a engenharia a tomar uma decisão de produto que deveria estar no PRD.

* **[BAIXO] Inconsistência terminológica na US 4.1:** O Cenário 1 menciona "solicito a credencial de acesso ao certificado" enquanto o Cenário 3 utiliza o termo "PIN". A terminologia deveria ser unificada para "PIN do certificado" em todos os cenários, eliminando ambiguidade sobre o que constitui a "credencial de acesso".

---

## 3. Propostas de Correção Direta

### Correção 1: Conflito de valor hardcoded vs. configurável (US 5.2 e US 5.4)

* **Como está no PRD original (US 5.2, Cenário 2):**
  > "**Dado** que um processo da minha unidade tem prazo (dias corridos) a vencer em 2 dias corridos ou menos"

* **Como está no PRD original (US 5.4, Cenário 1):**
  > "**Dado** que um processo da minha unidade tem prazo (dias corridos) a vencer em 2 dias corridos ou menos"

* **Como deve ficar (Sugestão de Reescrita — aplicar em ambos os cenários):**
  > "**Dado** que um processo da minha unidade tem prazo (dias corridos) a vencer dentro do limite configurado pelo Administrador para alerta de prazo (parâmetro 'Dias de antecedência para alerta de prazo', valor padrão: 2 dias corridos — US 8.5)"

---

### Correção 2: Restauração de documentos — Nova US necessária (US 8.7)

* **Como está no PRD original (US 3.1, Cenário 3, trecho):**
  > "Durante o período de retenção, o Administrador pode restaurar o documento."

* **Como deve ficar (Sugestão de Reescrita):**
  > Inserir nova US no Épico 8 (após US 8.6b):

  **US 8.7:** Como Administrador, eu quero restaurar documentos que foram removidos por engano (soft delete) para recuperar informações excluídas indevidamente.

  * **Critérios de Aceitação:**
    * *Cenário 1: Restauração de documento dentro do período de retenção*
      * **Dado** que um documento foi removido (soft delete) de um processo há menos de 30 dias e estou autenticado como Administrador
      * **Quando** acesso a área de "Documentos Removidos" no menu de administração, localizo o documento e aciono "Restaurar"
      * **Então** o documento volta a aparecer na lista de anexos do processo de origem, a restauração é registrada no histórico do processo com data, hora e Administrador responsável, e o documento é removido da área de retenção
    * *Cenário 2: Tentativa de restauração após expiração do prazo de retenção*
      * **Dado** que um documento foi removido (soft delete) há mais de 30 dias
      * **Quando** acesso a área de "Documentos Removidos"
      * **Então** o documento não aparece mais na listagem (foi excluído permanentemente), e o sistema exibe no rodapé da tela: "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados"
    * *Cenário 3: Área de retenção vazia*
      * **Dado** que estou autenticado como Administrador e não há documentos em período de retenção
      * **Quando** acesso a área de "Documentos Removidos"
      * **Então** visualizo a mensagem "Nenhum documento em período de retenção"

  E alterar o trecho na US 3.1, Cenário 3 para:
  > "Durante o período de retenção, o Administrador pode restaurar o documento conforme US 8.7."

---

### Correção 3: Parâmetros configuráveis — Cenários de borda individuais (US 8.5)

* **Como está no PRD original:**
  > O Cenário 4 da US 8.5 cobre 10 parâmetros com uma única validação ("deve ser um número inteiro positivo").

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar os seguintes cenários à US 8.5:

  * *Cenário 5: Configuração de tentativas de login com valor zero*
    * **Dado** que estou na tela de configurações do sistema
    * **Quando** configuro o "Número máximo de tentativas de login antes do bloqueio" com valor 0 (zero)
    * **Então** o sistema exibe "O número máximo de tentativas deve ser no mínimo 1 e no máximo 10" e não salva a configuração
  * *Cenário 6: Configuração de timeout de sessão com valor extremamente baixo*
    * **Dado** que estou na tela de configurações do sistema
    * **Quando** configuro o "Timeout de sessão por inatividade" com valor inferior a 5 minutos
    * **Então** o sistema exibe "O timeout de sessão deve ser no mínimo 5 minutos" e não salva a configuração
  * *Cenário 7: Configuração de profundidade do histórico de senhas com valor excessivo*
    * **Dado** que estou na tela de configurações do sistema
    * **Quando** configuro a "Profundidade do histórico de senhas" com valor 0 (zero)
    * **Então** o sistema exibe "A profundidade do histórico de senhas deve ser no mínimo 3 e no máximo 24" e não salva a configuração. O valor 0 permitiria que o usuário reutilizasse a mesma senha indefinidamente, o que viola a política de segurança.

---

### Correção 4: Typo na US 4.1, Cenário 1

* **Como está no PRD original:**
  > "eu possuo um certificado digital ICP-Brasil (e-CPF) válido válido e acessível ao navegador"

* **Como deve ficar (Sugestão de Reescrita):**
  > "eu possuo um certificado digital ICP-Brasil (e-CPF) válido e acessível ao navegador"

---

### Correção 5: Overflow do sequencial de processo (US 2.1)

* **Como está no PRD original (US 2.1, Cenário 1, trecho):**
  > "Caso o sequencial anual atinja o limite de 999.999, o sistema deve expandir automaticamente para 7 dígitos (AAAA/NNNNNNN), registrando o evento em log de sistema"

* **Como deve ficar (Sugestão de Reescrita):**
  > "Caso o sequencial anual atinja o limite de 999.999, o sistema deve expandir automaticamente para 7 dígitos (AAAA/NNNNNNN), registrando o evento em log de sistema. Caso o sequencial de 7 dígitos atinja o limite de 9.999.999, o sistema deve expandir para 8 dígitos (AAAA/NNNNNNNN), registrando o evento em log de sistema. O formato segue o padrão AAAA/N..., sem limite superior de dígitos. Atingir 10 milhões de processos em um ano implica alerta administrativo automático ao Administrador para avaliação da capacidade do sistema."

---

### Correção 6: Upload de arquivo vazio (US 3.1)

* **Como está no PRD original:**
  > Não há cenário para arquivo com 0 byte.

* **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar novo cenário à US 3.1 (após Cenário 2):
  >
  > *Cenário 2b: Upload de arquivo vazio (0 byte)*
  >   * **Dado** que estou anexando documentos a um processo
  >   * **Quando** tento fazer upload de um arquivo com tamanho de 0 byte (arquivo vazio ou corrompido)
  >   * **Então** o sistema rejeita o upload e exibe a mensagem "Não é possível anexar arquivo vazio. Selecione um arquivo com conteúdo."

---

### Correção 7 (Bônus — Baixa Severidade): Unificação terminológica na US 4.1

* **Como está no PRD original (US 4.1, Cenário 1):**
  > "solicito a credencial de acesso ao certificado e confirmo"

* **Como deve ficar (Sugestão de Reescrita):**
  > "insiro o PIN do certificado e confirmo"

---

## 4. Próximos Passos

O PRD está **bem construído em sua espinha dorsal** — o trabalho de elicitação e estruturação foi de alta qualidade. As 6 falhas identificadas são pontuais e circunscritas, não estruturais.

**Ações recomendadas:**

1. Aplicar as 7 correções propostas na Seção 3 diretamente no arquivo `docs/fase2_prd.md`.
2. Após as correções, executar novamente o revisor (Fase 3) para reavaliação. Com as correções aplicadas, o score esperado é **≥ 8.5**.
3. Com score ≥ 8, o documento estará apto para avançar à **Fase 4 (PRD Patcher)** ou diretamente para ferramentas de **OpenSpec / SDD (Specification-Driven Development)** para decomposição em tarefas de engenharia.

**Não recomendado:** Enviar este documento _como está_ para a engenharia. O conflito de especificação entre valores hardcoded e parâmetros configuráveis (Correção 1) e a funcionalidade implícita de restauração de documentos (Correção 2) gerariam retrabalho e dúvidas durante a implementação.

---

## Anexo A — Tabela de Verificação Rápida

| Dimensão | Resultado | Observações |
|---|---|---|
| Formato BDD (Given/When/Then) | ✅ Adequado | 130+ cenários mapeados, formato consistente |
| Caminhos tristes / Casos de borda | ⚠️ Bom, com lacunas | Faltam: arquivo vazio, overflow sequencial, bordas de parâmetros |
| Cobertura RF ↔ US | ✅ Completo | Todos os 44 RFs possuem US correspondente |
| Blindagem tecnológica | ✅ Exemplar | Nenhuma menção a banco de dados, linguagem ou framework |
| Consistência entre US | ⚠️ Conflito | US 5.2/5.4 hardcoded vs. US 8.5 configurável |
| Funcionalidades implícitas | ⚠️ 1 caso | Restauração de documentos (soft delete) sem US |
| Clareza terminológica | ⚠️ Pequena variação | "credencial" vs. "PIN" na US 4.1 |
| Qualidade de revisão textual | ⚠️ 1 typo | "válido válido" na US 4.1 |
