## Context

Ver `proposal.md` — Why. O estado verificado no repositório, em 2026-10-21:

```
openspec/config.yaml:30-38   "Não proponha changes de assinatura sem decisão
                              explícita de retomada do épico"          ← PROIBIÇÃO
CLAUDE.md:39-48              "está FORA DE ESCOPO"                     ← PROIBIÇÃO
docs/PRD.md:560-568          "movido para a Fase 2 / nada implementado"
docs/PRD.md:569              premissa "diretamente pelo navegador"     ← FALSA
docs/PRD.md:575,582,589      US 4.1 Cen.1 / Cen.3 / Cen.5              ← IMPOSSÍVEIS
docs/PRD.md:604              US 4.2 Cen.3                              ← CONDICIONAL

docs/fase2-assinatura/respostas-cliente.md   ← 33 respostas, 2026-10-13
docs/fase2-assinatura/estudo-tecnico.md      ← §1 e §4 sustentam o Portão 2
```

Três restrições moldam este design.

**1. A proibição é a única coisa que protege o projeto de uma implementação
precoce.** Removê-la sem substituto deixaria o caminho livre para
`assinatura-qualificada-psc` ser proposta amanhã — antes de a SETES ter contratado o
fornecedor, antes de a tabela de prazos (F2) chegar, antes de o conflito D5 × E1 ser
resolvido. A proibição existe por um motivo que ainda vale **em parte**.

**2. Três pendências do cliente não bloqueiam as mesmas coisas.** Tratá-las como um
bloco único ("falta resposta → nada anda") custaria semanas de calendário por nada:

```
A5 sem nome ──────────▶ bloqueia ESTE change (grava decisão sem dono)
                        não bloqueia pensar, revisar, nem a fatia de verificação

escopo do registro ───▶ bloqueia assinatura-qualificada-psc
público (A2 × A3)       não bloqueia a verificação nem a retomada

D5 × E1 (carimbo) ────▶ bloqueia assinatura-carimbo-tempo e US 4.2 Cen.3
                        não bloqueia mais nada

procurement (D4) ─────▶ bloqueia assinatura-qualificada-psc
                        não bloqueia assinatura-verificacao-fundacao
```

A fatia `assinatura-verificacao-fundacao` não é bloqueada por **nenhuma** delas. Com
H1 = 11/2026 na mesa, essa distinção vale calendário real.

**3. O PRD é documento mestre e tem leitores humanos com memória.** Apagar a
premissa falsa produziria um documento que parece sempre ter estado certo, e
destruiria o registro de que houve um Discovery, uma conclusão e uma decisão. O
próprio PRD já resolveu isso antes, em `PRD.md:27`, com tachado + nota explicativa.

---

## Decisões

### D1 — A proibição vira condicional com pendências nomeadas, não é removida

`config.yaml` e `CLAUDE.md` deixam de dizer "não proponha changes de assinatura" e
passam a dizer **o que foi decidido** e **o que continua bloqueando o quê**.

```
ANTES                              DEPOIS
┌────────────────────────┐         ┌──────────────────────────────────────┐
│ assinatura:            │         │ assinatura: RETOMADA 2026-10-13      │
│   FORA DE ESCOPO       │         │   caminho: QUALIFICADO (ICP-Brasil)  │
│   não proponha changes │   ──▶   │   liberado: verificacao-fundacao     │
│   (absoluto)           │         │   bloqueado: qualificada-psc         │
└────────────────────────┘         │     ⛔ procurement D4                │
                                   │     ⛔ escopo registro público       │
  porta trancada                   │   bloqueado: carimbo-tempo           │
                                   │     ⛔ conflito D5 × E1              │
                                   └──────────────────────────────────────┘
                                     porta com porteiro e lista
```

**Por quê:** a alternativa — remover a proibição e confiar que o próximo agente leia
o `README.md` do dossiê — falha exatamente no caso em que mais importa: um agente com
contexto parcial, lendo só `config.yaml`, concluindo "o épico foi retomado, posso
propor". O guard-rail precisa sobreviver à retomada.

**Consequência:** cada pendência resolvida exige uma edição pontual no `config.yaml`
retirando aquela linha. É manutenção recorrente, e é deliberada: o custo de atualizar
uma lista é menor que o de uma change proposta cedo demais.

### D2 — A premissa falsa é tachada e substituída, nunca apagada

A Premissa de Produto do Épico 4 (`PRD.md:569`) recebe o tratamento já usado em
`PRD.md:27`: o texto original preservado em `~~tachado~~`, seguido da premissa
corrigida e da nota de origem.

```
~~assinar ... diretamente pelo navegador, sem instalar software~~
    ↓
PREMISSA SUPERADA — Discovery Técnico, 2026-07-27. Nenhum navegador expõe
token/smart card; a limitação é permanente (estudo-tecnico.md §1).
    ↓
PREMISSA VIGENTE — certificado ICP-Brasil EM NUVEM, autorizado pelo
aplicativo do PSC no celular do signatário. A chave privada nunca chega
ao servidor do Despapelize.
```

O "Plano de contingência" do mesmo parágrafo descreve o que fazer *caso* o Discovery
encontre restrições. Ele encontrou. O plano é marcado como **acionado em 2026-07-27
e encerrado em 2026-10-13** — deixa de ser plano e vira histórico.

**Por quê:** um leitor que encontre o PRD em 2028 precisa entender por que o produto
não é o que a primeira versão prometia. Apagar a premissa transforma uma decisão
documentada em lacuna inexplicável.

### D3 — Os três critérios impossíveis são reescritos para o fluxo real, não deletados

Deletar reduziria o escopo sem substituto e deixaria buracos (certificado inválido,
falha de autorização e ausência de certificado continuam sendo casos reais que a
interface precisa tratar). Os textos abaixo são **normativos** — quem aplicar o
change copia daqui.

**US 4.1 Cenário 1** — `PRD.md:573-576`:

> * *Cenário 1: Assinatura com certificado em nuvem válido*
>   * **Dado** que um processo sob minha responsabilidade possui documento gerado
>     pelo sistema pendente de assinatura, e eu possuo certificado ICP-Brasil em
>     nuvem (e-CPF) válido e vinculado ao meu CPF junto ao provedor contratado
>   * **Quando** seleciono o documento, aciono "Assinar" e **autorizo a operação no
>     aplicativo do provedor, no meu celular**
>   * **Então** o sistema aplica a assinatura ao documento, registra data/hora,
>     vincula ao meu usuário, e o documento passa a constar como assinado no
>     processo e na seção "Documentos Assinados" do meu perfil
>   * **E** o sistema **em nenhum momento solicita, recebe, transporta ou armazena
>     PIN, senha ou biometria do certificado** — a autorização ocorre integralmente
>     entre o signatário e o provedor (DOC-ICP-17.01)

**US 4.1 Cenário 3** — `PRD.md:581-584`, substitui "PIN incorreto":

> * *Cenário 3: Autorização não concedida pelo provedor*
>   * **Dado** que acionei "Assinar" e o sistema solicitou a autorização ao provedor
>   * **Quando** a autorização não é concedida — por recusa, expiração do prazo de
>     resposta, ou bloqueio aplicado **pelo próprio provedor**
>   * **Então** o sistema exibe "Não foi possível obter a autorização de assinatura.
>     Verifique o aplicativo do seu provedor de certificado e tente novamente.", a
>     operação não é concluída, e o evento é registrado em `log_seguranca`
>   * **E** o sistema **não afirma o motivo da recusa nem aplica bloqueio próprio por
>     tentativas** — a causa é conhecida apenas pelo provedor, e qualquer mensagem
>     mais específica seria suposição

**US 4.1 Cenário 5** — `PRD.md:589-592`, substitui "token/smart card não conectado":

> * *Cenário 5: Nenhum certificado vinculado ao usuário*
>   * **Dado** que aciono "Assinar" em um documento
>   * **Quando** não existe certificado em nuvem vinculado ao meu CPF junto ao
>     provedor contratado
>   * **Então** o sistema exibe "Nenhum certificado digital encontrado para o seu
>     CPF. Procure a área responsável para regularizar seu certificado." e a
>     operação não é iniciada
>   * **E** a mensagem **não menciona token, smart card, driver ou instalação de
>     software** — nada disso existe neste fluxo

**Cenários 2 e 4 ficam como estão.** Cen.2 (certificado expirado ou revogado) é
válido nos dois fluxos. Cen.4 (coassinatura) é confirmado por **B3** = "comum na
SETES" e entra no plano como change própria.

### D4 — US 4.2 Cen.3 não é tocado; é marcado como condicional

O cenário promete exibir *"certificado expirado em [data], mas válido na data da
assinatura"*. Essa afirmação só é sustentável com carimbo de tempo de terceiro — e a
decisão sobre carimbo está em **contradição aberta**: D5 ("evitar qualquer custo por
uso") × E1 ("concordo" com a sugestão de que vale o custo por assinatura).

Recebe uma nota de condicionalidade e **nada mais**:

> **Nota (change retomada-epico-assinatura, 2026-10-21):** este cenário depende de
> carimbo de tempo de Autoridade Certificadora do Tempo. A decisão está pendente —
> as respostas D5 e E1 de 2026-10-13 se contradizem. Se a SETES decidir contra o
> carimbo, **este cenário sai do escopo**: sem carimbo independente não há como
> comprovar a validade na data, e exibir a afirmação seria promessa sem lastro.

**Por quê:** reescrever agora exigiria escolher um dos lados de uma decisão de
negócio que pertence ao cliente. Deletar agora destruiria o critério caso a decisão
venha a favor. A nota preserva as duas saídas e registra quem precisa decidir.

### D5 — Recortes de escopo entram como nota datada junto ao critério afetado

Padrão `**Nota (change ...)**`, já usado em `PRD.md:177-178`, acrescido da resposta
de origem:

| Recorte | Onde a nota entra | Origem |
|---|---|---|
| Só documentos gerados por `ModeloDocumento`, em PDF | US 4.1, cabeçalho | **B1** |
| Sem assinatura institucional (e-CNPJ) | US 4.1, cabeçalho | **B5** |
| Só assina enquanto o processo estiver com o servidor | US 4.1 Cen.1 | **B6** |
| Consulta pública sem documentos nem assinaturas | Épico 4, status | **G1** |
| Sem assinatura retroativa | Épico 4, status | **H3** |

**Por quê não editar os critérios diretamente:** a rastreabilidade é o produto. Daqui
a um ano, "por que não assinamos DOCX?" precisa ter resposta de uma linha — "B1,
2026-10-13" — e não virar arqueologia de histórico do git.

### D6 — `assinatura-avancada` não é planejada; o abandono do modelo misto fica registrado

**A4** aceitou o modelo misto. **B4** disse "até 5 pessoas". O modelo misto existe
para evitar comprar certificado para muita gente; com 5 pessoas não economiza
nenhum, e custaria um caminho paralelo completo: segundo fator no ato de assinar,
Termo de Aceite no primeiro-acesso, `DocumentoAssinatura.nivel` ramificando em toda
verificação, e duas semânticas de validade na interface.

Registrado no `config.yaml` como recomendação pendente de confirmação, **não** como
decisão. A confirmação é a pendência 9 de `respostas-cliente.md`.

**Por quê isto é decisão de design e não de produto:** o cliente aceitou o misto, e
nós recomendamos abrir mão. Essa divergência precisa estar escrita com a
justificativa, não resolvida no silêncio.

### D7 — Change sem capability em `openspec/specs/`

Nenhum comportamento de sistema muda. O change altera regras de processo e documento
mestre. Precedente direto no repositório: `2026-08-12-manual-sempre-atualizado`
alterou `config.yaml` + `CLAUDE.md` e não criou `specs/`.

A capability `assinatura-documentos` nascerá na primeira change de implementação
(`assinatura-verificacao-fundacao`), onde haverá comportamento a especificar.

---

## Atualização 2026-11-09 — efeitos da devolutiva respondida

A devolutiva voltou com A5 nomeado e com **duas das pendências que este design
supunha abertas já resolvidas**. Nenhuma decisão muda de natureza; três mudam de
conteúdo.

```
A5          ✅ Ademilton Leal Coutinho — Diretor Presidente → condição de apply OK
A2 × A3     ✅ registro público FORA do Despapelize        → D1 perde um bloqueio; D5 ganha um recorte
D5 × E1     ✅ carimbo de tempo SIM                         → D4 invertida; D1 perde um bloqueio
B4          ~10 pessoas (era "até 5")                      → D6 reavaliada e mantida
F2, F1/DPO  ⚠️ sem resposta                                → continuam bloqueando qualificada-psc
```

- **D1** — a lista de bloqueios do `config.yaml` fica: `assinatura-verificacao-fundacao`
  liberada; `assinatura-qualificada-psc` bloqueada por procurement (D4/Soluti), tabela
  F2, ratificação de F1, plano para quem não tiver certificado (D2) e política interna
  (H4); `assinatura-carimbo-tempo` com decisão tomada, dependente de
  `assinatura-qualificada-psc` e da contratação da ACT. O escopo de registro público
  e o conflito D5 × E1 **saem da lista**.
- **D4 — substituída.** A nota de condicionalidade não é mais verdadeira: o cliente
  decidiu. US 4.2 Cen.3 continua **intacto** (o texto era o certo) e recebe, em vez da
  nota condicional, uma nota de **confirmação** citando E1 e a devolutiva, Pergunta 3,
  com o alvo técnico (PAdES AD-RT, `estudo-tecnico.md` §4). O texto condicional
  original de D4 fica preservado acima como histórico de raciocínio.
- **D5** — um sexto recorte: documentos que vão a registro público (atas, estatutos,
  regulamentos, políticas) são tratados **fora** do Despapelize (A3 + devolutiva,
  Pergunta 2). Entra no bloco de status do Épico 4. Consequência registrada junto: o
  caminho qualificado passa a se fundar **só em A1** — continua determinado, mas como
  escolha, não como obrigação legal.
- **D6** — B4 ≈ 10. A recomendação é mantida pela mesma razão (o custo do caminho
  paralelo de código não escala com o número de signatários; e por D2 a economia de
  certificados nem seria da SETES). Continua **recomendação**, não decisão.

## Ordem de aplicação e por que ela importa

Os três arquivos precisam mudar **na mesma change** — é o que o `README.md` do
dossiê exige — mas a ordem dentro da aplicação não é indiferente:

```
1. docs/PRD.md          ← primeiro: o documento mestre passa a ser verdadeiro
       ▼
2. openspec/config.yaml ← depois: as regras passam a apontar para um PRD correto
       ▼
3. CLAUDE.md            ← por último: espelha 1 e 2 para quem lê o repositório
```

Se `config.yaml` liberasse antes de o PRD estar corrigido, existiria uma janela —
ainda que de minutos, ainda que só na árvore de trabalho — em que a proibição caiu e
os critérios impossíveis continuam valendo. É exatamente o cenário que o Portão 2
existe para evitar.

## Riscos e trade-offs

| Risco | Mitigação |
|---|---|
| **A lista de pendências do `config.yaml` envelhece** e vira ruído que ninguém atualiza | Cada change de assinatura subsequente tem tarefa explícita de retirar sua própria linha ao ser arquivada. A lista é curta (4 itens) por construção |
| **Retomar o épico cria pressão para implementar** antes do procurement | O `config.yaml` nomeia o bloqueio por change, não por épico: `verificacao-fundacao` liberada, `qualificada-psc` bloqueada. A pressão encontra uma porta aberta que é a certa |
| **Os critérios reescritos em D3 assumem o fluxo de nuvem** e podem não encaixar no que a Soluti oferece | O estudo (§9.2, §9.8) registra que o modelo de autorização varia por provedor. Os textos de D3 evitam prescrever redirect ou código — descrevem "autorizo no aplicativo", que vale nos dois desenhos |
| **F1 (LGPD) sem ratificação do DPO** fica registrada no PRD como decisão do cliente | O change registra a resposta **e a ausência de ratificação** no mesmo lugar (tarefa 1.2). Não se grava F1 como decisão fechada |
| **H1 = 11/2026 não é alcançável** e o cliente ainda não sabe | Fora do escopo deste change. É o assunto da `docs/fase2-assinatura/devolutiva-cliente.md`, Parte 3 |
