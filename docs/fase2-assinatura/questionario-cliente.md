# Despapelize — Fase 2: Assinatura de Documentos
## Questionário de definições para a SETES

**Data de envio:** 08/10/2026
**Respondido por:** ______________________________  **Cargo:** ______________________
**Data da resposta:** ____/____/______

---

## Como responder

São **33 perguntas**, organizadas em 8 blocos. Cada pergunta traz:

- um **contexto curto** (2 ou 3 frases, sem termos técnicos),
- as **opções** de resposta, com o que muda em cada uma,
- uma **sugestão nossa**, quando temos uma recomendação.

> **Você não precisa ter opinião sobre tudo.** Onde houver uma sugestão nossa e você
> não tiver preferência, basta marcar **"Concordo com a sugestão"**. Isso já é uma
> resposta completa e válida.

As perguntas marcadas com 🔴 **bloqueiam o início do desenvolvimento** — sem elas não
conseguimos começar. As marcadas com 🟡 podem ser respondidas depois, mas atrasam
partes do trabalho.

No fim do documento há um resumo de **quem na SETES deveria responder cada bloco**,
caso você queira distribuir.

---

## Em uma página: o que estamos decidindo

O Despapelize foi entregue sem assinatura de documentos. Isso foi uma decisão
planejada: na avaliação técnica descobrimos que **não é possível** usar o
certificado digital de cartão ou pendrive (aquele token USB) diretamente pelo
navegador — nenhum navegador do mercado permite isso, e não é uma limitação que vá
mudar.

Agora, na Fase 2, vamos implementar a assinatura. Mas antes precisamos de decisões
que **não são técnicas** — são decisões de negócio, jurídicas e de custo. As
principais:

1. **Qual o "peso jurídico" necessário.** Existe mais de um nível de assinatura
   eletrônica válida no Brasil. O mais forte custa dinheiro por pessoa, todo ano.
   O mais simples é gratuito e a SETES já tem quase tudo pronto para ele.
   **A diferença entre eles muda o custo do projeto em uma ordem de grandeza.**

2. **Quem assina o quê.** Nem todo documento precisa de assinatura.

3. **Por quanto tempo os documentos assinados devem ser guardados**, e o que fazer
   quando alguém pedir para apagá-los.

Este questionário existe para que essas escolhas sejam **da SETES**, registradas e
conscientes — não suposições nossas.

---

## Glossário — 6 termos que aparecem no questionário

| Termo | O que significa, em palavras simples |
|---|---|
| **Certificado Digital ICP-Brasil** | É a "identidade digital oficial" brasileira. É o mesmo tipo de certificado que a empresa usa para emitir nota fiscal. Pode ser de pessoa (chamado **e-CPF**) ou de empresa (**e-CNPJ**). É emitido por empresas autorizadas pelo governo e **é pago, com renovação periódica**. |
| **Certificado em cartão ou pendrive** | O certificado fica num objeto físico que você conecta ao computador. **Não funciona pelo navegador** — foi exatamente isso que nos bloqueou. |
| **Certificado em nuvem** | O mesmo certificado oficial, mas guardado num cofre eletrônico do fornecedor em vez de num pendrive. Para usar, a pessoa autoriza pelo **aplicativo do fornecedor no celular** (digital ou senha). **É a única forma que funciona pelo navegador.** |
| **Assinatura eletrônica do próprio sistema** | O Despapelize registra quem assinou, quando, e garante que o documento não foi alterado depois — usando senha, confirmação extra e o registro de auditoria que já existe. **Não precisa de certificado pago.** A lei reconhece essa modalidade (Lei 14.063/2020), com uma diferença importante explicada no Bloco A. |
| **Carimbo de data e hora** | Um serviço independente, de fora da SETES, que atesta oficialmente o momento em que o documento foi assinado — em vez de confiarmos no relógio do nosso próprio sistema. **É cobrado por assinatura.** |
| **Trilha de auditoria** | O registro que o Despapelize já guarda hoje: quem fez o quê, quando, em qual processo. Já existe e já funciona. |

---

# BLOCO A — Qual o peso jurídico necessário
### 👤 Quem deveria responder: **Jurídico / Direção**

Este é **o bloco mais importante do questionário**. A resposta aqui define o
tamanho, o custo e o prazo de todo o resto.

### O que você precisa saber antes de responder

A lei brasileira reconhece **duas** formas de assinatura eletrônica que servem para a
SETES. As duas são **juridicamente válidas**. A diferença não é "vale" ou "não vale" —
é **quem tem que provar o quê se alguém negar ter assinado**:

**Opção 1 — Assinatura eletrônica do próprio sistema** (a lei chama de "avançada")

- Gratuita. Sem certificado para comprar, sem renovação anual.
- A SETES **já tem quase tudo pronto** — o sistema já registra autor, data, hora e
  já detecta se um documento foi alterado.
- Faltariam duas coisas pequenas: uma **confirmação extra no momento de assinar**
  (um código, por exemplo) e um **termo que cada funcionário aceita** reconhecendo
  essa assinatura como válida.
- **A diferença que importa:** se um funcionário disser *"não fui eu que assinei"*,
  **a SETES tem que provar que foi ele** — apresentando os registros do sistema. Os
  registros são bons e normalmente bastam. Mas o esforço da prova é nosso.

**Opção 2 — Certificado Digital ICP-Brasil** (a lei chama de "qualificada")

- Cada pessoa que assina precisa de um certificado **pago, renovado periodicamente**.
- Precisa de **celular com aplicativo** do fornecedor (veja Bloco C).
- Exige a SETES **contratar um fornecedor** e comprar também um certificado da
  empresa, só para o sistema conseguir conversar com esse fornecedor (veja Bloco D).
- **A diferença que importa:** se alguém disser *"não fui eu"*, **a lei presume que
  foi** — quem nega é que precisa provar o contrário. A proteção é automática.

**Resumindo a diferença em uma frase:** a Opção 2 inverte o ônus da prova a favor da
SETES, e custa dinheiro por pessoa por ano. A Opção 1 é gratuita e exige que a SETES
apresente seus registros caso algo seja contestado.

---

### 🔴 A1. Os documentos assinados no Despapelize serão, algum dia, apresentados a alguém **de fora** da SETES?

Pense em: tribunal, cartório, banco, órgão regulador, cliente, fornecedor, sindicato,
ex-funcionário em processo trabalhista, auditoria externa.

- [ ] **Não, praticamente nunca.** São documentos internos, entre funcionários, para
      organizar o trabalho e registrar decisões administrativas.
- [ ] **Sim, alguns.** A maioria é interna, mas certos documentos podem sair.
      → Quais? _______________________________________________
- [ ] **Sim, com frequência.** Boa parte dos documentos sai da instituição.
- [ ] **Não sei dizer.** Precisaríamos consultar o jurídico.

> **Por que perguntamos:** se a resposta é "praticamente nunca", a Opção 1 (gratuita)
> resolve e o projeto fica muito menor. Se é "alguns", conseguimos fazer um modelo
> misto — veja A4.

---

### 🔴 A2. Existe alguma **lei, norma de regulador ou cláusula de contrato** que obrigue a SETES a usar especificamente o Certificado Digital ICP-Brasil nesses documentos?

- [ ] **Não, que eu saiba.**
- [ ] **Sim.** → Qual norma ou contrato? ______________________________________
- [ ] **Preciso verificar com o jurídico.**

> **Por que perguntamos:** se existe obrigação legal, a decisão está tomada e os
> blocos C e D passam a ser obrigatórios. Se não existe, a SETES tem liberdade de
> escolha.

---

### 🟡 A3. Algum documento do Despapelize vai para **registro público** (cartório, registro de imóveis) ou é usado para **transferir bens**?

- [ ] Não.
- [ ] Sim. → Quais? ______________________________________

> **Por que perguntamos:** nesses casos específicos o Certificado ICP-Brasil é
> exigido por lei, sem alternativa.

---

### 🔴 A4. Caso o certificado pago seja necessário só para **parte** dos documentos, a SETES aceita um **modelo misto**?

Funcionaria assim: a assinatura do próprio sistema (gratuita) vale para o dia a dia;
e os documentos de uma lista específica exigem o Certificado ICP-Brasil. Só as
pessoas que assinam esses documentos precisariam comprar certificado.

- [ ] **Sim, o modelo misto nos interessa.** ← *sugestão nossa, se A1 for "alguns"*
- [ ] **Não — preferimos um único padrão para tudo.**
      → Qual? [ ] só o do sistema  [ ] só o ICP-Brasil
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** o modelo misto normalmente reduz muito o custo — em geral
> poucas pessoas assinam os documentos "pesados". Tecnicamente dá no mesmo trabalho
> construir os dois, desde que decidido desde o início.

---

### 🔴 A5. Quem na SETES **aprova formalmente** esta decisão jurídica?

Precisamos de um nome, porque essa definição fica registrada na documentação do
sistema como decisão do cliente.

Nome: _________________________________ Cargo: _________________________________

---

# BLOCO B — O que é assinado, e por quem
### 👤 Quem deveria responder: **Direção / Responsável pela operação**

### 🔴 B1. Quais documentos devem poder ser assinados?

Hoje o sistema aceita anexos (PDF, Word, imagens) e também **gera documentos a
partir de modelos** cadastrados.

- [ ] **Somente os documentos gerados pelo próprio sistema** a partir dos modelos
      (pareceres, despachos, ofícios). ← *sugestão nossa*
- [ ] **Também os arquivos PDF anexados** pelos funcionários.
- [ ] **Todos os anexos**, inclusive Word e imagens.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** documentos em Word e imagens exigem uma técnica diferente,
> que dobra o trabalho. Como os documentos de decisão da SETES são justamente os
> gerados pelos modelos, começar por eles entrega o essencial com metade do esforço.
> Se necessário, ampliamos depois.

---

### 🔴 B2. Assinar será **obrigatório** ou **opcional**?

- [ ] **Opcional** — o funcionário assina quando julgar necessário, e o processo
      segue normalmente mesmo sem assinatura. ← *sugestão nossa*
- [ ] **Obrigatório para alguns tipos** de documento. → Quais?
      _______________________________________________
- [ ] **Obrigatório sempre** — nenhum processo avança com documento não assinado.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** tornar obrigatório significa que uma falha no fornecedor do
> certificado **travaria a tramitação** de toda a instituição. É um risco
> operacional real que precisa ser aceito conscientemente.

---

### 🟡 B3. **Mais de uma pessoa** pode precisar assinar o mesmo documento?

Exemplo: um parecer assinado pelo técnico e também pelo chefe do setor.

- [ ] **Sim, isso é comum na SETES.**
- [ ] **Sim, mas é raro.**
- [ ] **Não, cada documento tem um único signatário.**

> **Por que perguntamos:** múltiplas assinaturas no mesmo arquivo funcionam, mas são
> uma etapa separada de desenvolvimento. Saber se é comum ou raro define se entra
> agora ou depois.

---

### 🟡 B4. Quantas pessoas, aproximadamente, precisariam assinar documentos?

Não precisa ser exato — uma faixa já ajuda.

- [ ] Até 5 pessoas
- [ ] 6 a 20
- [ ] 21 a 50
- [ ] Mais de 50 → quantas, aproximadamente? __________

> **Por que perguntamos:** é o principal item de custo, caso a SETES opte pelo
> Certificado ICP-Brasil — paga-se por pessoa.

---

### 🟡 B5. A **SETES como instituição** precisa assinar algum documento, em vez de uma pessoa específica?

Seria uma assinatura "da empresa", não "do João" — usando o certificado da pessoa
jurídica (e-CNPJ).

- [ ] **Não** — toda assinatura é de uma pessoa, em nome próprio. ← *sugestão nossa*
- [ ] **Sim.** → Em quais casos? ______________________________________
- [ ] Concordo com a sugestão.

---

### 🟡 B6. Um funcionário pode assinar um documento de um processo que **já saiu da sua unidade**?

Hoje, o funcionário perde o direito de remover anexos quando o processo é enviado
adiante.

- [ ] **Não** — só pode assinar enquanto o processo estiver com ele. ← *sugestão nossa*
- [ ] **Sim** — pode assinar depois, a qualquer momento.
- [ ] Concordo com a sugestão.

---

### 🔴 B7. Depois de assinado, um documento ainda pode ser **removido** do processo?

Hoje documentos removidos ficam 30 dias recuperáveis e depois são apagados
definitivamente.

- [ ] **Não** — ao ser assinado, o documento fica permanente e não pode mais ser
      removido por ninguém. ← *sugestão nossa*
- [ ] **Sim, mas só pelo Administrador**, com registro.
- [ ] **Sim, pelas mesmas regras de hoje.**
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** um documento assinado é prova de um ato. Se ele puder ser
> apagado, a assinatura perde boa parte do sentido. Mas essa é uma restrição real
> ao trabalho do dia a dia — se alguém assinar o documento errado, não haverá volta,
> só a emissão de um novo documento corrigindo.

---

# BLOCO C — Celulares e aparelhos
### 👤 Quem deveria responder: **RH / TI interno**

> **Este bloco só importa se a SETES escolher o Certificado Digital ICP-Brasil.**
> Se a escolha for a assinatura do próprio sistema, pule para o Bloco E.

### 🔴 C1. As pessoas que vão assinar têm **celular com aplicativo** (smartphone)?

Com o certificado em nuvem, assinar exige autorizar por um **aplicativo do fornecedor
do certificado** — Bird ID, VIDaaS, SafeID, conforme o fornecedor escolhido — com
biometria ou um código de uso único. Hoje **todos** os fornecedores do mercado fazem
isso por aplicativo de celular. (Em teoria, o código poderia vir de um chaveirinho
eletrônico em vez do celular; vamos confirmar com os fornecedores se algum oferece
essa opção — mas **não conte com isso** ao responder.)

- [ ] **Sim, todas têm.**
- [ ] **A maioria tem**, algumas não. → quantas não têm, aproximadamente? _______
- [ ] **Muitas não têm.**
- [ ] **Não sei — preciso verificar.**

> **Por que perguntamos:** esta é a pergunta que pode **inviabilizar** o Certificado
> ICP-Brasil na prática. Se parte das pessoas não tem celular com aplicativo, elas
> simplesmente não conseguirão assinar — e precisaremos de outro plano para elas.

---

### 🟡 C2. Seria **celular da SETES** ou **celular pessoal** do funcionário?

- [ ] A SETES fornece o aparelho.
- [ ] Celular pessoal do funcionário.
- [ ] Depende da pessoa / dos dois jeitos.

> **Por que perguntamos:** usar o celular pessoal para um ato de trabalho costuma
> exigir uma política interna e o consentimento do funcionário. É uma conversa de RH,
> não de tecnologia, mas é melhor saber antes.

---

### 🟡 C3. A SETES tem alguém de TI que possa **apoiar os funcionários** na instalação do aplicativo e no primeiro acesso ao certificado?

- [ ] Sim, temos TI interno.
- [ ] Temos apoio terceirizado.
- [ ] Não temos — precisaríamos de apoio nosso.

---

# BLOCO D — Custo e contratação
### 👤 Quem deveria responder: **Financeiro / Compras / Direção**

> **Também só importa se a escolha for o Certificado Digital ICP-Brasil.**

### 🟡 D1. A SETES **já possui** algum certificado digital hoje?

Praticamente toda empresa brasileira tem um e-CNPJ para nota fiscal e obrigações
fiscais. Vale verificar com a contabilidade.

- [ ] Sim, temos e-CNPJ. → Com qual fornecedor? ___________________________
- [ ] Sim, temos certificados de pessoas (e-CPF). → Quantos? _______
- [ ] Não temos nenhum.
- [ ] Não sei — vou verificar com a contabilidade.

> **Por que perguntamos:** se já existe relacionamento com um fornecedor, a
> contratação fica muito mais rápida. E um dos certificados que o projeto precisa
> pode já existir.

---

### 🟡 D2. Quem **paga** o certificado de cada pessoa?

- [ ] A SETES paga para todos. ← *sugestão nossa*
- [ ] Cada funcionário paga o seu.
- [ ] Depende do cargo.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** se o funcionário paga, haverá recusas, e precisamos
> planejar o que acontece com quem não tiver certificado.

---

### 🟡 D3. Há **preferência ou restrição** de fornecedor?

Os fornecedores autorizados mais conhecidos são Serpro, Valid, Certisign, Soluti e
Safeweb.

- [ ] Sem preferência — escolham o mais adequado tecnicamente. ← *sugestão nossa*
- [ ] Preferimos: _______________________________________
- [ ] Não podemos usar: _________________________________
- [ ] Concordo com a sugestão.

---

### 🔴 D4. Quem na SETES pode **assinar o contrato** com o fornecedor e fornecer os documentos da empresa?

Além dos certificados das pessoas, o projeto precisa de **um certificado da própria
SETES**, usado só para autorizar o sistema a conversar com o fornecedor. Ele não
assina nada — é como uma credencial de acesso. A emissão exige documentos da empresa
e validação do fornecedor, o que **leva de alguns dias a algumas semanas**.

Nome: _________________________________ Cargo: _________________________________

- [ ] Esse processo pode ser iniciado desde já.
- [ ] Precisa de aprovação interna antes. → Prazo estimado: ______________

> **Por que perguntamos:** este é o item de **prazo mais longo** de todo o projeto, e
> é administrativo, não técnico. Se começar tarde, atrasa tudo o resto, por mais que
> o desenvolvimento esteja pronto.

---

### 🟡 D5. A SETES aceita um **custo recorrente por assinatura emitida** (alguns centavos a alguns reais por documento)?

Isso se refere ao carimbo de data e hora — detalhado no Bloco E.

- [ ] Sim, dentro do razoável.
- [ ] Preferimos evitar qualquer custo por uso.
- [ ] Depende do valor. → Limite aceitável: ______________

---

# BLOCO E — Prova da data e hora
### 👤 Quem deveria responder: **Jurídico**

### Contexto

Quando um documento é assinado, registramos a data e a hora. A pergunta é **de quem
é o relógio**:

- **Relógio do nosso sistema:** gratuito. Mas é o nosso próprio registro dizendo
  quando aconteceu. Se alguém contestar a data, é a nossa palavra.
- **Carimbo de uma autoridade independente:** uma empresa autorizada atesta
  oficialmente o momento. **Custa por assinatura**, mas a data passa a ser
  comprovável por terceiro.

Isso importa num caso específico e nada raro: o certificado de uma pessoa vence
depois de alguns anos. Anos à frente, ao verificar um documento antigo, o sistema
precisa dizer *"a assinatura é válida — o certificado venceu em 2029, mas estava
válido na data em que foi assinado"*. **Sem o carimbo independente, não há como
provar essa data.**

### 🔴 E1. A SETES quer o carimbo de data e hora independente?

- [ ] **Sim** — vale o custo por assinatura. ← *sugestão nossa, se a escolha for o Certificado ICP-Brasil*
- [ ] **Não** — o registro do próprio sistema basta.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** se a resposta for "não", precisamos **retirar do escopo**
> a tela que informa "válido na data da assinatura" — ela estaria prometendo algo
> que não conseguimos comprovar. É melhor não exibir do que exibir sem base.

---

### 🟡 E2. Por quantos anos um documento assinado precisa continuar **verificável**?

Verificar uma assinatura muito antiga exige guardar informações extras ao longo do
tempo. Quanto maior o prazo, mais cuidado — e custo — envolvido.

- [ ] Até 5 anos
- [ ] Até 10 anos
- [ ] Mais de 10 anos → quantos? ________
- [ ] Permanentemente
- [ ] Não sei — depende do tipo de documento.

---

# BLOCO F — Guarda, exclusão e LGPD
### 👤 Quem deveria responder: **Jurídico / Encarregado de dados (DPO)**

### Contexto — um conflito que precisa de decisão da SETES

O Despapelize hoje está configurado para **anonimizar** processos antigos: passado o
prazo definido (hoje, 5 anos após o arquivamento), nomes e CPFs são apagados, em
atendimento à LGPD.

Com documentos assinados surge um conflito **sem solução técnica**:

> A assinatura digital **contém, por dentro, o nome e o CPF de quem assinou**. Não é
> possível remover esse dado sem destruir a assinatura. Ou mantemos a assinatura
> válida com o dado pessoal dentro dela, ou apagamos o dado e a assinatura deixa de
> valer. **Não existe meio-termo.**

### 🔴 F1. Como a SETES resolve esse conflito?

- [ ] **Documentos assinados ficam fora da anonimização.** Eles são prova de um ato
      jurídico e a guarda se justifica por obrigação legal. O nome e o CPF do
      signatário permanecem. ← *sugestão nossa*
- [ ] **A anonimização prevalece.** Passado o prazo, o documento assinado é apagado
      por inteiro, assinatura e tudo.
- [ ] Precisamos avaliar com o jurídico / DPO antes de decidir.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** esta decisão precisa estar registrada e justificada, com
> nome de quem decidiu. É exatamente o tipo de questão que um fiscal da LGPD pergunta.

---

### 🟡 F2. Por quantos anos os documentos assinados devem ser **guardados**?

- [ ] 5 anos após o arquivamento do processo (igual à regra atual)
- [ ] 10 anos
- [ ] Outro prazo: ________
- [ ] Permanentemente
- [ ] Depende do tipo de processo — temos uma tabela de prazos. (Se tiver, envie-a.)

---

### 🟡 F3. Um documento assinado deve ser **impossível de apagar**, inclusive por um administrador do sistema?

É possível configurar o armazenamento para recusar qualquer exclusão até o prazo
terminar — nem a nossa equipe, nem a SETES conseguiriam apagar.

- [ ] **Sim, queremos essa proteção máxima.** Entendemos que é definitiva.
- [ ] **Queremos proteção, mas reversível** por um administrador, com registro.
      ← *sugestão nossa*
- [ ] **Não é necessário.**
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** a proteção máxima é **irreversível**. Uma vez ativada, o
> prazo não pode ser reduzido nem em caso de erro. É uma garantia forte e um
> compromisso igualmente forte.

---

### 🟡 F4. Se um funcionário sair da SETES, os documentos que ele assinou permanecem?

- [ ] Sim, permanecem como estão. ← *sugestão nossa*
- [ ] Precisamos avaliar.
- [ ] Concordo com a sugestão.

---

# BLOCO G — Quem vê as assinaturas
### 👤 Quem deveria responder: **Direção / Responsável pela operação**

### 🟡 G1. O **cidadão**, na consulta pública, deve ver que um documento foi assinado?

Hoje a consulta pública mostra dados do processo, **mas não o conteúdo dos
documentos**. A pergunta é se deve aparecer algo como *"Parecer técnico — assinado
por Maria Silva em 10/03/2027"*.

- [ ] **Não** — a consulta pública continua sem mencionar documentos ou assinaturas.
      ← *sugestão nossa*
- [ ] **Sim, só a indicação** de que existe assinatura, sem o nome de quem assinou.
- [ ] **Sim, com nome e data** do signatário.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** expor nome de funcionário num canal público é tratamento
> de dado pessoal e precisa de justificativa própria na LGPD. Hoje o sistema
> deliberadamente não faz isso.

---

### 🟡 G2. Quem precisa poder **conferir** se uma assinatura é válida?

Marque todos que se aplicam.

- [ ] Qualquer funcionário que tenha acesso ao processo ← *sugestão nossa*
- [ ] Só o Gestor e o Administrador
- [ ] O Auditor (o sistema já prevê que ele veja as assinaturas)
- [ ] O cidadão, pela consulta pública

---

### 🟡 G3. É útil poder conferir, no Despapelize, assinaturas de documentos **assinados fora** do sistema?

Exemplo: um fornecedor envia um contrato já assinado digitalmente; o funcionário
anexa ao processo e quer confirmar ali mesmo que a assinatura é legítima.

- [ ] **Sim, isso seria útil.** ← *sugestão nossa*
- [ ] Não, não precisamos.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** essa é a parte do projeto que **não custa nada**: não
> precisa de certificado, fornecedor nem contrato. Se for útil, podemos entregá-la
> primeiro, enquanto as decisões de compra ainda estão em andamento — a SETES ganha
> algo funcionando logo.

---

# BLOCO H — Implantação
### 👤 Quem deveria responder: **Direção**

### 🟡 H1. Há uma **data-limite** ou motivo externo pressionando essa entrega?

- [ ] Não, podemos planejar com calma.
- [ ] Sim. → Qual data e por quê? ______________________________________

---

### 🟡 H2. Prefere **começar com um grupo piloto** ou liberar para todos de uma vez?

- [ ] Piloto com uma unidade ou setor primeiro. ← *sugestão nossa*
- [ ] Para todos de uma vez.
- [ ] Concordo com a sugestão.

---

### 🟡 H3. Documentos **já existentes** no sistema precisam ser assinados retroativamente?

- [ ] **Não** — a assinatura vale para documentos novos, daqui para frente.
      ← *sugestão nossa*
- [ ] Sim, alguns documentos antigos precisam ser assinados.
- [ ] Concordo com a sugestão.

> **Por que perguntamos:** se precisar ser retroativo, cada documento antigo exigirá
> uma ação manual de alguém — é um esforço de operação, não de desenvolvimento.

---

### 🟡 H4. A SETES já tem alguma **política interna escrita** sobre assinatura eletrônica, uso de certificado ou documentos digitais?

- [ ] Sim. (Por favor, envie-nos uma cópia.)
- [ ] Não.
- [ ] Não sei.

> **Por que perguntamos:** se existir, o sistema deve seguir a política em vez de
> criarmos regras próprias. Se não existir e a SETES escolher a assinatura do
> próprio sistema, será necessário criar um termo — podemos ajudar a redigir.

---

# Resumo — quem responde o quê

| Bloco | Assunto | Quem deveria responder | Bloqueia o início? |
|---|---|---|---|
| **A** | Peso jurídico da assinatura | Jurídico / Direção | 🔴 **Sim** |
| **B** | O que e quem assina | Direção / Operação | 🔴 **Sim** (B1, B2, B7) |
| **C** | Celulares e aparelhos | RH / TI | 🔴 **Sim** (C1), se escolher ICP-Brasil |
| **D** | Custo e contratação | Financeiro / Compras | 🔴 **Sim** (D4), se escolher ICP-Brasil |
| **E** | Prova de data e hora | Jurídico | 🔴 **Sim** (E1) |
| **F** | Guarda, exclusão e LGPD | Jurídico / DPO | 🔴 **Sim** (F1) |
| **G** | Quem vê as assinaturas | Direção / Operação | 🟡 Não |
| **H** | Implantação | Direção | 🟡 Não |

## As 3 perguntas mais importantes

Se houver tempo para responder apenas três, que sejam estas:

1. **A1** — Os documentos assinados serão apresentados a alguém de fora da SETES?
2. **C1** — As pessoas que vão assinar têm celular com aplicativo?
3. **F1** — Documentos assinados ficam fora da anonimização da LGPD?

Essas três, isoladamente, já definem o tamanho do projeto.

## Uma observação final, com honestidade

Pela análise que fizemos, há uma possibilidade concreta de que a **assinatura do
próprio sistema** (Opção 1 do Bloco A) atenda plenamente à SETES — gratuita, sem
fornecedor, sem celular, aproveitando o registro de auditoria que já existe e
funciona. Isso depende inteiramente da resposta de A1 e A2.

Não estamos recomendando economizar por economizar. Estamos dizendo que **vale
responder A1 e A2 com calma, consultando o jurídico**, antes de autorizar a compra
de certificados — porque essa resposta pode mudar o custo do projeto em uma ordem de
grandeza, e a decisão é da SETES, não nossa.

---

*Documento preparado pela equipe de desenvolvimento do Despapelize.
Dúvidas sobre qualquer pergunta deste questionário podem ser enviadas antes da
resposta — nenhuma pergunta aqui exige conhecimento técnico para ser respondida.*
