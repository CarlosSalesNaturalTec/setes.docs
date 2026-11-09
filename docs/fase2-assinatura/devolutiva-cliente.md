# Despapelize — Fase 2: Assinatura de Documentos

> **✅ RESPONDIDA** — respostas registradas em 2026-11-09 em `respostas-cliente.md`,
> seção "Devolutiva"; PDF preenchido em `devolutiva-respondida.pdf`. Perguntas 1, 2,
> 3, 4a e 4c respondidas; 4b (tabela F2), 5 (DPO), 6 e 7 sem resposta.

## Devolutiva do questionário

**Para:** Ana Morais — Diretora de Serviços Compartilhados
**De:** equipe de desenvolvimento do Despapelize
**Data:** 21/10/2026
**Assunto:** o que suas respostas decidiram, 4 perguntas que faltam, e uma conversa
sobre o prazo de 11/2026

---

Ana, obrigado pelas respostas — elas vieram completas e com observações que nos
pouparam várias idas e vindas. Das 8 perguntas que marcamos como bloqueantes, 6
estão resolvidas e já viraram decisão de projeto.

Este documento tem três partes:

1. **O que já está decidido** — não precisa de ação sua, é só para conferência.
2. **Quatro perguntas** que faltam para começar.
3. **Uma conversa honesta sobre 11/2026.**

---

## Parte 1 — O que suas respostas já decidiram

### O caminho: Certificado Digital ICP-Brasil

Duas respostas suas levaram a isso, cada uma sozinha já seria suficiente:

- **A1** — os documentos saem da instituição com frequência.
- **A3** — há atos da instituição que vão a registro público.

Então a assinatura do próprio sistema (a opção gratuita) **não atende**. O projeto
vai pelo certificado pago. Essa era a resposta mais cara das duas possíveis — mas
três outras respostas suas tornaram o impacto muito menor do que o normal:

| Sua resposta | Por que ajuda |
|---|---|
| **Até 5 pessoas assinam** (B4) | o custo dos certificados é pequeno |
| **Todas têm celular** (C1) | isto costuma inviabilizar o projeto. Não é o caso aqui |
| **Já têm e-CNPJ com a Soluti** (D1) | o fornecedor já conhece vocês; metade do caminho da contratação já existe |

E o **Sr. Ademilton liberar o início da contratação "desde já" (D4)** destravou
justamente o item mais demorado de todo o projeto.

### Decisões de produto que já podemos registrar

Estas saíram diretamente das suas respostas e **não precisamos mais perguntar**:

- Só os documentos **gerados pelo próprio sistema** serão assináveis (B1).
- Assinar é obrigatório para pessoal, compras, contratos e pagamentos (B2).
- **Mais de uma pessoa** pode assinar o mesmo documento (B3) — entra desde o começo.
- A assinatura é sempre **de uma pessoa**, nunca da instituição (B5).
- Só se assina enquanto o processo **estiver com você** (B6).
- Documento assinado **pode ser removido pelo Administrador**, com registro (B7).
- Documentos assinados **ficam de fora** do apagamento automático da LGPD (F1).
- A **consulta pública não muda** — cidadão não vê assinaturas (G1).
- **Qualquer funcionário** com acesso ao processo pode conferir uma assinatura (G2).
- Nada será assinado **retroativamente** (H3).
- Começamos com um **piloto** em uma unidade (H2).

### Uma observação técnica, para registro

Você marcou que o **modelo misto** interessa (A4) — assinatura simples no dia a dia e
certificado pago só para os documentos pesados. Ele existe para economizar
certificados quando muita gente assina.

Como na SETES **são até 5 pessoas**, o modelo misto não economizaria nenhum
certificado — e dobraria o trabalho de construção, porque seriam dois sistemas de
assinatura convivendo. **Nossa sugestão é abrir mão dele** e usar um padrão único.

Isso só muda se você souber de um crescimento à frente. É a **pergunta 4** adiante.

---

## Parte 2 — Quatro perguntas que faltam

São curtas. Três delas são de uma linha.

### Pergunta 1 — Um nome 🔴

A pergunta **A5** ("quem aprova formalmente esta decisão jurídica") voltou com o
campo **Nome em branco**. No campo Cargo ficou escrito "Diretoria Executiva ou o
Jurídico".

Precisamos de **um nome e um cargo**, não os dois como alternativa.

**Por que insistimos:** essa definição fica registrada na documentação do sistema
como decisão formal da SETES. Sem um responsável identificado, ela fica registrada
como suposição nossa — e é exatamente o tipo de registro que alguém procura anos
depois, quando uma assinatura é questionada.

> **Nome: ______________________  Cargo: ______________________**

Vale a mesma observação para o **Bloco F (LGPD)**: foi respondido por você, mas é
decisão do controlador sobre dados pessoais. Se a SETES tem um Encarregado de Dados
(DPO), o ideal é que ele **confirme a resposta F1** — ou que fique registrado que
essa decisão é da sua diretoria.

### Pergunta 2 — Os documentos de registro público entram no Despapelize? 🔴

Na **A2** você respondeu que não conhece lei que obrigue o certificado pago. Na
**A3**, logo em seguida, você listou atas, regulamentos, políticas e estatutos que
vão a registro.

Não é contradição sua — é que **registro público é justamente o caso em que a lei
exige o certificado pago**, sem alternativa. Você mesma anotou a saída: *"esses
documentos não necessariamente precisam tramitar pelo Despapelize."*

Precisamos transformar esse "não necessariamente" em uma decisão:

- ☐ **Não** — esses documentos ficam fora do Despapelize; são tratados por fora.
- ☐ **Sim** — eles vão tramitar no Despapelize e serão assinados lá.

**Por que perguntamos:** se for "sim", o certificado pago deixa de ser preferência e
passa a ser obrigação legal para essa classe — e isso muda o que podemos ou não
flexibilizar mais adiante.

### Pergunta 3 — O carimbo de data e hora: sim ou não? 🔴

Duas respostas suas se contradizem, e precisamos de uma delas:

- Na **D5** você escreveu: *"preferimos evitar qualquer custo por uso."*
- Na **E1** você concordou com nossa sugestão — que era **"sim, vale o custo por
  assinatura"**.

Nossa leitura é que a D5 foi respondida imaginando um volume que não existe aqui.
Com 5 pessoas assinando só os documentos pesados, estamos falando de **algumas
centenas de carimbos por ano** — um custo pequeno, não um custo recorrente relevante.

**O que se perde ao dizer não:** anos à frente, ao abrir um documento antigo, o
sistema não conseguirá dizer *"esta assinatura era válida na data em que foi
feita"*. Teríamos que **retirar essa tela do projeto** — preferimos não exibir do
que exibir sem base. Lembrando que o certificado de uma pessoa vence a cada 1 a 3
anos, e os documentos ficam guardados por muito mais tempo que isso.

- ☐ **Sim, queremos o carimbo** (vale o custo pequeno por assinatura)
- ☐ **Não** — e aceitamos que a tela de "válido na data da assinatura" saia do projeto

### Pergunta 4 — Três confirmações rápidas

**4a. As "até 5 pessoas" (B4) é o número de hoje ou já contando crescimento?**
Se houver previsão de crescer bastante, reavaliamos a sugestão sobre o modelo misto.

- ☐ É estável, não deve crescer muito
- ☐ Deve crescer → para quantas pessoas, aproximadamente? ________

**4b. A tabela de prazos de guarda (F2).** Você mencionou que a SETES tem uma, mas
ela não veio anexa. **Pode nos enviar?** É ela que define por quanto tempo o sistema
vai proteger cada documento assinado contra exclusão.

**4c. O nome da instituição.** Nosso questionário dizia "SETES"; suas respostas
dizem "ISETES". Qual é o correto? Pergunta pequena, mas vai aparecer em contrato
com o fornecedor e em texto na tela.

---

## Parte 3 — Sobre o prazo de 11/2026

Precisamos ser diretos com você: **o projeto completo não fica pronto em novembro.**

Você anotou na H1 que *"não é motivo externo, mas urge otimizarmos os processos, ter
mais segurança jurídica e rastreabilidade"*. Entendemos a urgência, e é por
levá-la a sério que preferimos dizer isso agora, e não em novembro.

### Por que não fecha

Quando se escolhe o certificado ICP-Brasil, entram etapas que não são de
programação — e que acontecem **em sequência**, uma esperando a outra:

1. A SETES contrata o fornecedor e emite uma credencial da instituição. Essa emissão
   envolve documentos da empresa e validação do fornecedor, e leva **semanas**.
2. Só depois disso nosso sistema consegue conversar com o fornecedor.
3. Além disso, o produto precisa ser construído e testado com um certificado real.

Mesmo com tudo correndo bem e começando a contratação hoje, novembro não cabe. Não é
falta de equipe — é prazo de terceiro.

### O que propomos: entregar em duas etapas

Há uma parte do projeto que **não depende de nada disso** — nem de contrato, nem de
certificado, nem de custo. É justamente a que você marcou como útil na **G3**:

> **Etapa 1 — Conferência de assinaturas (até 11/2026)**
> O Despapelize passa a **conferir assinaturas de documentos assinados fora do
> sistema**. Um fornecedor manda um contrato já assinado, o funcionário anexa ao
> processo e confere ali mesmo se a assinatura é legítima, de quem é, e se o
> documento foi alterado depois.
>
> Custo zero. Nenhuma dependência da contratação. E entrega valor real ainda neste
> prazo.

> **Etapa 2 — Assinar dentro do sistema (depois da contratação)**
> O restante do projeto, começando assim que a credencial da instituição estiver
> emitida.

Há um ganho técnico escondido aí, que vale mencionar: conferir uma assinatura é a
parte **mais difícil** do projeto inteiro. Fazendo ela primeiro, a SETES descobre se
está tudo certo **antes** de gastar com certificados — e não depois.

### O que você pode fazer esta semana para encurtar a Etapa 2

**Autorizar o início da contratação com a Soluti.** O Sr. Ademilton já indicou que
pode começar (D4). Como é o item mais demorado e nada depende dele para começar,
cada semana de antecipação aqui é uma semana a menos no projeto todo.

Vamos preparar as perguntas técnicas para a Soluti e enviar em paralelo, para que a
conversa comercial e a técnica andem juntas.

---

## Resumo — o que precisamos de volta

| | O que | Com quem |
|---|---|---|
| 1 | Nome e cargo de quem aprova a decisão jurídica (A5) | Direção Executiva / Jurídico |
| 2 | Documentos de registro público entram no Despapelize? | Jurídico |
| 3 | Carimbo de data e hora: sim ou não | Jurídico + Financeiro |
| 4a | "Até 5 pessoas" é estável? | Direção |
| 4b | A tabela de prazos de guarda | Arquivo / Jurídico |
| 4c | SETES ou ISETES? | Direção |
| 5 | Confirmação do DPO sobre a resposta F1 (LGPD) | DPO |
| 6 | Aval para iniciar a contratação com a Soluti | Presidência |
| 7 | De acordo com a entrega em duas etapas? | Direção |

As de número **1, 2 e 3 bloqueiam o início**. As demais podem vir depois, sem parar
o trabalho.

---

*Qualquer uma dessas perguntas pode ser conversada por telefone, se for mais rápido
que escrever. Nenhuma delas exige conhecimento técnico para ser respondida.*
