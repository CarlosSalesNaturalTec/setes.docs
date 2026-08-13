## Context

Motivação e diagnóstico do material de origem em `proposal.md — Why`; requisitos em
`specs/identidade-visual/spec.md`. O que segue é só o que molda as decisões.

**O que existe hoje.** O símbolo aparece em duas cópias com desenhos diferentes:

| Origem | Forma | Cor | Consumo |
| --- | --- | --- | --- |
| `apps/web/app/icon.svg` | folha de documento em traço branco, sobre quadrado navy | `#1e3a5f` fixo | favicon |
| `components/icons.tsx` → `IconMarca` | só a folha, sem recipiente | `currentColor` | chip do Login (48px) e da sidebar (32px) |

`IconMarca` é `stroke="currentColor"`, e é exatamente isso que hoje permite o mesmo
componente servir o chip branco do Login (traço navy) e o chip do topo da sidebar
(traço navy sobre chip branco, dentro do `bg-navy-900`). Nenhuma tela passa cor.

**O material de origem.** `docs/images/logo_despapelize.jpeg`, 438×740, JPEG sem
alfa: fundo azul "craquelado" chapado, árvore de copa cheia (dezenas de folhas
individuais), wordmark "Despapelize®" atravessando o meio, raízes de circuito
(traços terminados em nós circulares) abaixo. Composição **vertical e entrelaçada** —
o wordmark fica *entre* a copa e as raízes, não ao lado delas.

Duas consequências que decidem quase tudo abaixo:

1. **O símbolo isolado não se extrai por recorte.** Remover o wordmark deixa um vão
   entre copa e raízes que precisa ser recomposto — é redesenho, não crop.
2. **A copa não sobrevive a 32px.** Dezenas de folhas separadas por vãos de ~2px na
   arte original viram um borrão no chip da sidebar.

**Restrição herdada:** a capability `identidade-visual` já exige chip circular nos
dois locais, `IconMarca` como componente único e ausência de duplicação de SVG entre
Login e sidebar. O proposal preserva os três de propósito — este change troca o
desenho, não a arquitetura de consumo.

## Goals / Non-Goals

**Goals:**

- Um símbolo reconhecível como a marca Despapelize, legível de 16px (favicon) a 48px
  (Login), sem ativo por tamanho.
- Preservar a propriedade "um componente serve fundo claro e fundo escuro" que o
  `IconMarca` atual tem e que uma marca colorida perderia.
- Resolver, de forma verificada e não presumida, se o favicon declarado em
  `app/layout.tsx` está sendo servido.

**Non-Goals:**

- Aplicar a marca ao site MkDocs do manual. Fora do escopo deste proposal.
- Redesenhar Login ou sidebar. A estrutura das duas telas não muda — só o desenho
  dentro do chip.
- Reproduzir a arte do pôster (textura, gradiente, sombra). É peça gráfica.
- Registrar tipograficamente o wordmark como fonte da interface.

## Decisions

### D1 — Redesenho vetorial à mão, não autotrace

O símbolo é **redesenhado** em vetor tomando o JPEG como referência, não passado por
vetorizador automático.

Autotrace sobre JPEG com textura produz centenas de caminhos com ruído de compressão
nas bordas, arquivo de dezenas de KB e nós impossíveis de ajustar — e ainda assim não
resolveria o problema real, que é a recomposição descrita no Context (1) e a
simplificação da copa (2). Redesenhar custa mais uma vez e entrega um ativo com
geometria limpa, editável e de poucos KB.

**Fidelidade perseguida:** a *estrutura* da marca — copa arredondada de folhas, tronco
curto, raízes que terminam em nós de circuito. **Não** perseguida: a contagem exata de
folhas, a textura, o vão de espessura variável entre elementos. A copa é resolvida
como um agrupamento de folhas em número reduzido, com vãos que sobrevivem a 32px
(requisito "Símbolo legível no menor slot").

### D2 — Símbolo monocromático em `currentColor`

O símbolo é **monocromático** e herda a cor do contexto via `currentColor`, como o
`IconMarca` atual. Não há variante clara e variante escura em arquivos separados.

O material de origem já é essencialmente monocromático — um azul sobre fundo azul —
então a redução para uma cor não descarta informação de marca; descarta a variação
tonal do pôster. Em troca, preserva-se a propriedade que o requisito "Símbolo funciona
sobre fundo claro e sobre fundo escuro" exige e que uma marca de duas cores quebraria:
o mesmo componente serve os dois chips sem que nenhuma tela precise escolher variante.

Isso também mantém a **assinatura de `IconMarca` inalterada** (`{ className }`), e com
ela o requisito de componente único e sem duplicação — nenhuma tela passa a receber
prop de variante.

*Alternativa descartada:* ativos coloridos por fundo (`simbolo-claro.svg` /
`simbolo-escuro.svg`). Devolveria à tela a decisão de qual arquivo usar, que é
exatamente a porta pela qual as duas cópias divergentes de hoje entraram.

### D3 — Wordmark da marca horizontal em curvas

Na marca horizontal, "Despapelize" é desenhado a partir da forma tipográfica do
material de origem e convertido em **curvas** (`<path>`); nenhum `<text>` e nenhum
`font-family` sobrevive no ativo. Assim o desenho é idêntico em qualquer superfície e
nenhuma webfont entra no `package.json`.

O símbolo de marca registrada (®) presente no material **é preservado** na marca
horizontal — é a forma como o cliente apresenta a marca — e **ausente** no símbolo
isolado, onde não haveria legibilidade nem sentido.

### D4 — Dois arquivos, uma origem de verdade documentada

O símbolo continua existindo em dois lugares, porque os dois consumos são
incompatíveis: o favicon precisa ser **arquivo** (`app/icon.svg`, convenção do App
Router) e o chip precisa ser **componente** (`IconMarca`, para herdar `currentColor`
e `className`). Não há como o Next.js servir um e o React inlinar o outro a partir de
um único artefato sem introduzir passo de build.

A decisão é **assumir as duas cópias e amarrá-las**, não eliminá-las:

- `IconMarca` é a origem declarada do desenho; `app/icon.svg` carrega o mesmo
  `<path>`, com a cor resolvida para o favicon.
- Ambos levam comentário citando `(D4)` e apontando um para o outro, para que quem
  editar um saiba que o outro existe.
- O requisito de spec que importa — "sem duplicação de markup SVG **entre Login e
  sidebar**" — continua satisfeito: as duas telas consomem o componente.

*Alternativa descartada:* um script gerador (`gen:marca`) com drift check no CI, no
padrão de `packages/api-types`. Descartada por desproporção: são dois arquivos e um
`<path>`, com frequência de mudança de anos; um passo de build, um script e um job de
CI para vigiar isso custa mais do que o erro que evita. Se um dia a marca ganhar mais
formas e mais superfícies (manual, e-mail, apresentação), a conta inverte e essa
alternativa deve ser reaberta.

### D5 — Favicon: verificar antes de corrigir

O proposal levanta a suspeita de 404 no favicon. O mecanismo provável é outro, e a
implementação deve **medir antes de mexer**:

- `app/icon.svg` é **convenção de arquivo** do App Router: o Next.js serve o arquivo e
  injeta sozinho o `<link rel="icon">`. `apps/web/public/` estar vazio não implica
  404 — `/icon.svg` é rota gerada pela convenção, não arquivo estático de `public/`.
- Declarar `metadata.icons` **sobrepõe** as tags que a convenção geraria. O
  `icons: { icon: "/icon.svg" }` de `app/layout.tsx:9` provavelmente é redundante e
  funcional ao mesmo tempo: aponta para a URL que a própria convenção serve, perdendo
  apenas o parâmetro de cache-busting que o Next acrescentaria.

**Tarefa de verificação, com correção condicional:** subir o dev server, requisitar
`/icon.svg` e inspecionar o `<link rel="icon">` renderizado. Se responder 200, remover
a declaração redundante de `metadata.icons` e deixar a convenção agir sozinha. Se
responder 404, aí sim o ativo vai para `public/`. Não presumir nenhum dos dois.

### D6 — Marca horizontal mora com o símbolo, sem consumidor por ora

A marca horizontal vai para `apps/web/public/marca/` como SVG. Nenhuma tela a consome
neste change (requisito "Marca horizontal disponível para superfícies com largura" é
explícito quanto a isso), e é o primeiro conteúdo de `apps/web/public/`.

Colocá-la em `public/` e não em `components/` é deliberado: ela não precisa de
`currentColor` nem de `className`, e o próximo consumidor provável — uma superfície
fora do React — vai querer uma URL, não um componente.

### D7 — Verificação de legibilidade e contraste

Três verificações que não se fazem lendo o código, e que são critério de aceite das
tarefas correspondentes:

- **32px**: renderizar o chip da sidebar e confirmar que copa e raízes continuam
  distinguíveis (requisito "Símbolo legível no menor slot"). É a verificação que
  governa quanto a copa é simplificada em D1 — se falhar, simplifica-se mais.
- **16px**: o favicon na aba real do navegador, não a imagem ampliada.
- **Contraste ≥ 3:1** (WCAG 2.1 AA para elemento gráfico não textual) nos dois chips.
  Ambos são navy `#1e3a5f` sobre chip branco — ~11.4:1, folgado — mas o número é
  medido e registrado, não presumido.

## Risks / Trade-offs

- **Redesenho pode afastar-se do que o cliente reconhece como a marca dele** → D1 fixa
  o que é fidelidade obrigatória (estrutura) e o que é descartável (textura, contagem
  de folhas); a validação do ativo com o cliente fica registrada como tarefa antes da
  aplicação nas telas, não depois.
- **A copa simplificada a ponto de sobreviver a 32px pode ficar genérica a 48px** →
  as raízes de circuito, e não a copa, são o traço distintivo da marca; a
  simplificação preserva-as com prioridade. Verificação em D7 nos dois tamanhos.
- **Monocromático descarta a variação tonal do material** → aceito em D2 em troca da
  propriedade de funcionar nos dois fundos; a marca horizontal, que vive em
  superfícies maiores, pode receber cor num change futuro sem desfazer nada disto.
- **As duas cópias do `<path>` (D4) podem divergir** → risco assumido, mitigado por
  comentário cruzado; é o mesmo modo de falha que produziu a divergência atual, então
  a mitigação é fraca por construção. O gatilho para trocar de estratégia está
  declarado em D4.
- **`apps/web/public/` deixa de estar vazio** → diretório convencional do Next.js, sem
  efeito sobre rotas ou middleware.

## Migration Plan

Sem migration de banco, contrato ou dado — o change é de apresentação. Ordem que evita
estado intermediário quebrado:

1. Redesenhar o símbolo e validar legibilidade a 32px e 16px **antes** de tocar em
   qualquer tela — é o passo que pode exigir retrabalho de desenho.
2. `IconMarca` passa a renderizar o símbolo novo; Login e sidebar não mudam (consomem
   o componente). Testes existentes continuam valendo.
3. `app/icon.svg` recebe o mesmo desenho; verificação do favicon (D5) e correção
   condicional.
4. Marca horizontal em `public/marca/`.

**Rollback:** reverter o commit. Nenhum estado externo é criado — sem segredo, sem
bucket, sem recurso de infra, sem alteração de banco. O deploy anterior volta a servir
o ícone antigo sem passo adicional.

## Open Questions

- **Validação do ativo redesenhado com o cliente.** Deferível quanto ao planejamento —
  não muda specs, abordagem nem divisão de tarefas —, mas é bloqueante para o merge:
  está como tarefa explícita antes da aplicação nas telas. Se o cliente tiver o
  original vetorial da marca (AI/EPS/PDF/SVG), ele **substitui** o redesenho de D1 e
  o trabalho vira só a extração do símbolo e a simplificação para 32px — vale
  perguntar antes de desenhar.
