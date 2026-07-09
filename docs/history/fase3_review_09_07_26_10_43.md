# Relatório de Revisão de PRD — Controle de Qualidade

<auditoria_interna>

### 1. Critérios de Aceitação (BDD)
- **Pontos fortes:** A maioria das US aplica o formato Dado/Quando/Então corretamente. Os épicos 1, 4 e 6 são os mais maduros, com cenários alternativos e borda bem cobertos (ex.: US 1.3 tem 5 cenários; US 4.2 cobre certificado expirado na verificação).
- **Fragilidades:**
  - A US 1.1 Cenário 1 mistura múltiplas regras de negócio em um único "Então" (formato do login, tamanho da senha, obrigatoriedade de troca), violando o princípio de atomicidade do BDD.
  - A US 2.2 Cenário 2 descreve uma confirmação modal ("Deseja concluir o processo?") mas não cobre o caminho triste: o que acontece se o usuário clicar em "Cancelar"?
  - A US 2.3 Cenário 2 usa a expressão vaga "durante o uso do sistema" sem especificar o mecanismo de atualização (polling? websocket? refresh manual?), deixando uma decisão de arquitetura implícita.
  - A US 1.4 tem apenas 1 cenário e não cobre o caso de um servidor vinculado a múltiplas unidades (conflito com RF 3).
  - Falta cenário de primeira troca de senha obrigatória (citada na US 1.1 mas sem US dedicada).
  - Falta cenário para falha de rede/upload interrompido na US 3.1.

### 2. Coesão de Escopo (RF vs US)
- **Pontos fortes:** 27 dos 28 requisitos funcionais têm US correspondente direta. Boa rastreabilidade.
- **Fragilidades:**
  - RF 25 ("Toda movimentação de processo deve ser registrada em histórico imutável") é mencionado implicitamente em várias US, mas não há UMA US que estabeleça o contrato de imutabilidade como requisito testável. A US 2.4 cobre apenas a *leitura* do histórico, não a garantia de imutabilidade.
  - Não há US para busca/filtro interno de processos pelo Servidor (apenas o Kanban). Como um Servidor localiza um processo específico dentro da sua unidade sem navegar coluna por coluna?
  - Não há US para logout ou expiração de sessão.
  - Não há US para desativação/exclusão de usuário (apenas de unidade na US 8.1).
  - Não há US para troca voluntária de senha (apenas recuperação na US 1.3 e troca obrigatória no primeiro login mencionada na US 1.1).

### 3. Blindagem Tecnológica
- **Pontos fortes:** O PRD é notavelmente limpo. Não há menção a banco de dados (SQL/NoSQL), linguagens (Java/Python/JS), frameworks (React/Angular/Django), servidores de aplicação, nem provedores de nuvem.
- **Pequenas ressalvas:**
  - "Hash criptográfico" (NFR Segurança) é aceitável como requisito de segurança, não como decisão de implementação.
  - "HTTPS" é padrão de indústria e aceitável.
  - "ICP-Brasil" e "e-CPF/e-CNPJ" são requisitos de negócio/legais, não técnicos.
  - "20 MB" é um limite de negócio, não técnico.
  - **VEREDITO: Blindagem aprovada.** O PM anterior fez um bom trabalho mantendo-se no domínio do problema.

### 4. Conflitos e Ambiguidades
- **CONFLITO CRÍTICO:** A persona "Servidor Operacional" diz "ele só vê e movimenta processos da sua própria unidade" (singular). A US 1.4 reforça isso com "vinculado à unidade COFIN" (singular). Porém, o RF 3 afirma "Cada usuário deve pertencer a uma ou mais unidades administrativas". Se um Servidor pode pertencer a múltiplas unidades, seu escopo de visibilidade precisa ser redefinido. Isso é uma contradição que a engenharia não pode resolver sozinha.
- **Ambiguidade de "prazo":** US 2.1 menciona "prazo" como campo obrigatório, mas não define se são dias corridos ou dias úteis. A US 5.2 menciona "dias úteis", criando inconsistência interpretativa.
- **"Interessados":** Campo citado na US 2.1 como obrigatório, mas sem definição de formato: é texto livre? É uma lista de nomes+documentos estruturados? A engenharia não tem como implementar sem essa definição.
- **"Processos parados":** Definido como "sem movimentação há mais de 5 dias úteis" na US 6.1, mas não está claro se esse threshold é configurável pelo Administrador ou fixo.
- **Roteiro de tramitação:** A US 8.2 define roteiro como sequência linear. Isso exclui roteiros com bifurcações (ex.: "se valor > X, vá para COFIN; senão, vá para AJUR")? Se sim, deveria estar explícito no "Fora de Escopo".

### 5. Cálculo do Score

| Dimensão | Peso | Nota |
|---|---|---|
| Cobertura BDD (caminhos felizes e tristes) | 30% | 7.0 |
| Coesão RF ↔ US (rastreabilidade) | 20% | 7.5 |
| Clareza e não ambiguidade | 20% | 6.0 |
| Cobertura de borda e caminhos alternativos | 15% | 6.5 |
| Blindagem tecnológica | 15% | 9.5 |
| **Score ponderado** | | **7.2** |

**Arredondamento:** 7.0/10

</auditoria_interna>

---

## 1. Veredito e Score de Prontidão

- **Score de Prontidão:** 7.0 / 10
- **Status:** REQUER REFATORAÇÃO (Score < 8)
- **Resumo:** O PRD do SETES.DOCS é um documento com boa estrutura, épicos bem organizados e blindagem tecnológica exemplar — o PM anterior manteve-se consistentemente no domínio do problema, sem vazamento de bancos de dados, linguagens ou frameworks. Contudo, o documento apresenta um **conflito crítico de regra de negócio** entre a definição da persona Servidor (unidade única) e o RF 3 (uma ou mais unidades), além de lacunas relevantes na cobertura BDD: ausência de User Stories para busca interna, troca de senha, logout/expiração de sessão e ciclo de vida de usuários. Alguns critérios de aceitação usam linguagem vaga que delega decisões arquiteturais à engenharia. Essas falhas, se não corrigidas, gerarão retrabalho e dúvidas durante a implementação. **Recomenda-se aplicar as correções abaixo e reavaliar.**

---

## 2. Pontos Críticos Identificados

- **[CRÍTICO] Conflito de regra de negócio — Servidor x múltiplas unidades:** A persona "Servidor Operacional" e a US 1.4 definem que o servidor vê processos de apenas UMA unidade. O RF 3 diz que "cada usuário deve pertencer a uma ou mais unidades". A engenharia não tem como decidir qual regra implementar.
- **[ALTO] Campo "interessados" sem definição de formato (US 2.1):** É citado como obrigatório, mas não se sabe se é texto livre, lista estruturada com nome/CPF, ou seleção a partir de um cadastro prévio. A implementação depende dessa definição.
- **[ALTO] "Prazo" com unidade de medida ambígua:** US 2.1 trata "prazo" sem especificar dias corridos ou úteis. A US 5.2 usa "dias úteis" para alertas, criando inconsistência.
- **[ALTO] Ausência de User Story para busca/filtro interno de processos:** Nenhuma US cobre como um Servidor localiza um processo específico dentro da sua unidade sem navegar manualmente pelas colunas do Kanban.
- **[MÉDIO] US 2.2 Cenário 2 — Caminho triste da conclusão não coberto:** Descreve confirmação modal "Deseja concluir o processo?" mas não especifica o que ocorre se o usuário cancelar a ação.
- **[MÉDIO] US 2.3 Cenário 2 — Mecanismo de atualização vago:** "Durante o uso do sistema" não define se a atualização é em tempo real (websocket), polling ou refresh manual, deixando uma decisão de arquitetura implícita nos critérios de aceitação.
- **[MÉDIO] US 1.1 Cenário 1 — Critério de aceitação não atômico:** Um único "Então" acumula: criar usuário, enviar credenciais por e-mail, definir login como e-mail, definir senha com mínimo de 8 caracteres e obrigar troca no primeiro login. Isso viola o princípio BDD de um cenário = um comportamento testável.
- **[MÉDIO] US 1.4 — Cobertura insuficiente:** Apenas um cenário, sem cobrir o caso de servidor com múltiplas unidades (caso o RF 3 prevaleça).
- **[MÉDIO] Falta User Story para troca de senha (voluntária e primeiro login):** A troca obrigatória no primeiro login é mencionada na US 1.1 mas não possui cenário BDD próprio. Troca voluntária de senha não é coberta por nenhuma US.
- **[MÉDIO] Falta User Story para logout e expiração de sessão:** Nenhuma US cobre o término de sessão, seja por ação do usuário ou por inatividade.
- **[MÉDIO] Falta User Story para gestão de ciclo de vida de usuários:** Cadastro existe (US 1.1, 1.2), mas desativação, exclusão ou transferência de usuário entre unidades não tem US.
- **[BAIXO] US 3.1 — Falta cenário de falha de upload:** Não cobre interrupção de rede durante upload, timeouts ou nome de arquivo duplicado.
- **[BAIXO] Roteiro linear implícito — sem confirmação de escopo:** A US 8.2 define roteiro como sequência linear, mas não há declaração explícita no "Fora de Escopo" sobre roteiros condicionais (bifurcações baseadas em regras de negócio). Se isso for um requisito futuro, deveria estar documentado.

---

## 3. Propostas de Correção Direta

### Correção 1: Conflito Servidor × Unidades (Persona + US 1.4 + RF 3)

- **Como está no PRD original:**
  > "Servidor Operacional: (...) Ele só vê e movimenta processos da sua própria unidade." (Persona)
  > RF 3: "Cada usuário deve pertencer a uma ou mais unidades administrativas"

- **Como deve ficar (Sugestão de Reescrita):**
  > **[Decisão de negócio necessária]** Definir UMA das duas opções abaixo e aplicá-la consistentemente em Persona, US 1.4 e RF 3:
  >
  > **Opção A (Servidor = 1 unidade):** RF 3 deve ser reescrito como "Cada Servidor deve pertencer a exatamente uma unidade administrativa. Gestores e Administradores podem estar vinculados a uma ou mais unidades." A US 1.4 permanece como está.
  >
  > **Opção B (Servidor = N unidades):** US 1.4 deve ganhar um Cenário 2: "Servidor vinculado a múltiplas unidades" — Dado que estou autenticado como Servidor vinculado às unidades COFIN e COGEP / Quando acesso a listagem de processos / Então vejo os processos de ambas as unidades, com indicação visual de qual unidade cada processo pertence."

### Correção 2: Definição do campo "Interessados" (US 2.1)

- **Como está no PRD original:**
  > "Quando preencho todos os campos obrigatórios (assunto, tipo de processo, interessados, prazo) e confirmo a criação"

- **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar à US 2.1 ou à seção de Requisitos Funcionais:
  > "O campo 'interessados' aceita um ou mais nomes de pessoas físicas ou jurídicas, com os seguintes campos: nome completo (obrigatório, texto livre), CPF ou CNPJ (opcional, validado por algoritmo de dígito verificador) e tipo de participação (opcional, seleção entre: Requerente, Representado, Terceiro)."
  >
  > E adicionar Cenário 3 à US 2.1: "Interessado com CPF inválido" — Dado que estou criando um processo / Quando preencho um CPF com dígito verificador inválido no campo de interessado / Então o sistema exibe "CPF inválido — verifique o número informado" e não permite prosseguir.

### Correção 3: Unidade de medida do "Prazo" (US 2.1 + US 5.2)

- **Como está no PRD original:**
  > US 2.1: "preencho todos os campos obrigatórios (assunto, tipo de processo, interessados, prazo)"
  > US 5.2: "um processo da minha unidade tem prazo a vencer em 2 dias úteis"

- **Como deve ficar (Sugestão de Reescrita):**
  > Padronizar em todo o documento:
  > "Prazo = dias corridos. O sistema calculará dias restantes em dias corridos para exibição no Kanban. Para fins de alertas (US 5.2), o threshold será convertido para dias corridos equivalentes (ex.: '2 dias úteis' ≈ acionar alerta quando restarem 2 dias corridos ou menos, considerando que fins de semana e feriados não param a contagem de prazo)."
  >
  > OU, se a decisão for por dias úteis: alterar US 2.1 para "prazo (em dias úteis)".

### Correção 4: US 2.2 Cenário 2 — Caminho triste da conclusão

- **Como está no PRD original:**
  > "o sistema exibe a confirmação 'Este é o destino final do roteiro. Deseja concluir o processo?' e, ao confirmar, altera o status para 'Concluído'"

- **Como deve ficar (Sugestão de Reescrita):**
  > Adicionar Cenário 3: "Cancelamento da conclusão na última unidade"
  > **Dado** que um processo está na última unidade prevista no roteiro
  > **Quando** o servidor da unidade aciona "Despachar" e, na confirmação modal, clica em "Cancelar"
  > **Então** o processo permanece na unidade atual com o mesmo status, sem alteração no histórico, e o servidor retorna à tela de detalhes do processo

### Correção 5: US 2.3 Cenário 2 — Mecanismo de atualização

- **Como está no PRD original:**
  > "Quando eu estiver visualizando o Kanban (...) o processo aparece na coluna 'Aberto' da minha unidade durante o uso do sistema"

- **Como deve ficar (Sugestão de Reescrita):**
  > "**Quando** eu estiver visualizando o Kanban e um novo processo for despachado para minha unidade
  > **Então** o indicador de notificações no menu superior é incrementado, e o novo processo aparece na coluna 'Aberto' após eu realizar as ações de: clicar no ícone de notificações OU acionar o botão 'Atualizar' do Kanban OU navegar para outra tela e retornar."
  >
  > *(Isso remove a expectativa implícita de atualização em tempo real via websocket sem incluir escopo de infraestrutura.)*

### Correção 6: US 1.1 Cenário 1 — Decomposição de "Então" múltiplo

- **Como está no PRD original:**
  > "**Então** o novo usuário é criado e recebe credenciais de acesso no e-mail cadastrado (o login será o próprio e-mail; a senha provisória terá no mínimo 8 caracteres e o usuário será obrigado a trocá-la no primeiro login)"

- **Como deve ficar (Sugestão de Reescrita):**
  > Decompor em cenários independentes ou extrair regras para os Requisitos Funcionais:
  >
  > **Cenário 1 (cadastro):** Dado que estou autenticado como Administrador / Quando preencho nome, e-mail, unidade, perfil e confirmo / Então o novo usuário é criado com status "Ativo — pendente de primeiro acesso".
  >
  > **Cenário 1a (envio de credenciais):** Dado que um usuário foi cadastrado / Quando o cadastro é concluído / Então um e-mail é enviado ao endereço cadastrado contendo link de primeiro acesso com validade de 48 horas.
  >
  > **Cenário 1b (primeiro login — NOVA US 1.6):** Dado que sou um usuário recém-cadastrado com status "pendente de primeiro acesso" / Quando acesso o link de primeiro acesso / Então sou direcionado para tela de criação de senha (mínimo 8 caracteres) e, após defini-la, sou autenticado e meu status passa para "Ativo".

### Correção 7: User Stories ausentes — Inserções sugeridas

- **Como está no PRD original:**
  > *(Não existem estas US)*

- **Como deve ficar (Sugestão de Reescrita):**
  > Inserir as seguintes US:
  >
  > **US 1.6: Troca de senha (voluntária)** — Como Usuário autenticado, eu quero alterar minha senha para manter a segurança da minha conta.
  > - Cenário 1: Troca com senha atual correta e nova senha válida (≥8 caracteres).
  > - Cenário 2: Senha atual incorreta → rejeição com mensagem "Senha atual incorreta".
  > - Cenário 3: Nova senha igual à anterior → rejeição com mensagem "A nova senha não pode ser igual à senha atual".
  >
  > **US 1.7: Logout e expiração de sessão** — Como Usuário autenticado, eu quero encerrar minha sessão com segurança e que o sistema encerre sessões inativas automaticamente.
  > - Cenário 1: Logout manual → sessão encerrada, redirecionado à tela de login.
  > - Cenário 2: Inatividade por 30 minutos → sessão expirada, redirecionado à tela de login com mensagem "Sessão expirada por inatividade".
  >
  > **US 8.4: Desativação de usuário** — Como Administrador, eu quero desativar usuários para revogar acesso ao sistema quando necessário.
  > - Cenário 1: Desativação de usuário sem processos pendentes → usuário marcado como inativo, não consegue mais fazer login.
  > - Cenário 2: Desativação de usuário com processos sob sua responsabilidade → sistema alerta "Este usuário possui X processos em andamento. Reatribua os processos antes de desativar." e a desativação não é concluída.
  >
  > **US 2.7: Busca e filtro de processos (interno)** — Como Servidor, eu quero buscar processos da minha unidade por número, assunto ou período para localizar rapidamente um processo específico.
  > - Cenário 1: Busca por número exato → retorna o processo correspondente.
  > - Cenário 2: Busca por termo no assunto → retorna lista de processos cujo assunto contém o termo.
  > - Cenário 3: Filtro por período → retorna processos criados no intervalo informado.
  > - Cenário 4: Busca sem resultados → exibe "Nenhum processo encontrado para os filtros informados".

---

## 4. Próximos Passos

1. **Resolver o conflito de regra de negócio (Correção 1) ANTES de qualquer outra alteração.** Essa decisão impacta Persona, US 1.4, RF 3 e possivelmente o modelo de dados.
2. **Aplicar as 7 correções listadas na Seção 3** diretamente no arquivo `docs/fase2_prd.md`.
3. **Adicionar as 4 User Stories ausentes** (US 1.6, US 1.7, US 8.4, US 2.7) para cobrir as lacunas de cobertura funcional.
4. **Revisar todos os "Então" múltiplos** nas US restantes (US 4.1 Cenário 1, US 6.1 Cenário 1) e decompor onde necessário.
5. **Após as correções**, reexecutar a Fase 3 (este mesmo revisor) para reavaliar o score. O documento **não está pronto para ser enviado à Engenharia ou para ferramentas de SDD (OpenSpec)** até que o score atinja ≥ 8.0.
6. Uma vez aprovado (score ≥ 8), o PRD poderá seguir para a Fase 4 (Patcher) ou diretamente para especificação técnica.

---

*Relatório gerido pelo PRD Reviewer (Fase 3) — Natural Tecnologia.*
