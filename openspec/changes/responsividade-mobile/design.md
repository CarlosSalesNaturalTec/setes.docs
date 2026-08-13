# Design — responsividade-mobile

## Context

Ver `proposal.md` — Why. O levantamento em código confirmou o diagnóstico e
acrescentou dois fatos que mudam o desenho:

**1. `app/processos/[id]/page.tsx` já é tabulada.** A dúvida deixada em aberto
na proposta ("se a densidade exigir reorganizar histórico e documentos em abas,
isso amplia o escopo") **está resolvida sem ampliar escopo**: a tela já separa
Detalhes / Documentos / Histórico em abas (`page.tsx:648-669`), e o histórico já
é uma `<ol>` de cards empilhados (`page.tsx:716-733`), não uma tabela. Nada
precisa ser reorganizado.

O que a inspeção revelou no lugar disso é um defeito concreto de viewport
estreito, do mesmo tipo das tabelas — **padrão certo existente, não aplicado**:

| Modal | Contêiner | Rolagem |
|---|---|---|
| `components/modal.tsx:34` | `items-start … overflow-y-auto p-4 sm:p-8` | ✅ |
| `processos/[id]/page.tsx:32` (conclusão) | `items-center … p-4` | ⚠ sem rolagem |
| `processos/[id]/page.tsx:202` (tramitação) | `items-center … p-4` | ⚠ sem rolagem |

O modal de tramitação em modo "Enviar" renderiza quatro campos (unidade, setor,
servidor, mensagem) mais cabeçalho e botões. Centrado verticalmente num contêiner
sem `overflow-y-auto`, num aparelho de 640 px de altura o excedente sai da área
visível **pelas duas pontas** e não há como rolar até o botão "Confirmar" — o
fluxo de tramitação fica inexecutável no celular. É o achado mais grave do
change, e não estava na proposta.

**2. A suíte E2E é serial e com estado compartilhado.** `playwright.config.ts`
fixa `fullyParallel: false`, `workers: 1`; `global-setup.ts` zera o banco **uma
vez** para a execução inteira; e os specs `01`–`16` constroem estado uns sobre os
outros (o `ADMIN_ROOT` criado em `01` é reaproveitado adiante — ver
`e2e/fixtures.ts`). Isso restringe fortemente como um segundo projeto Playwright
pode ser adicionado (D5).

Restrições que moldam tudo abaixo: sem alteração de backend, sem migration, sem
regeneração de tipos; `tailwind.config.ts` não customiza `screens`, portanto os
breakpoints são os defaults (`sm` 640, `md` 768, `lg` 1024).

## Goals / Non-Goals

**Goals:**

- Aplicar padrões **já presentes no repositório** às telas que não os receberam —
  o contêiner rolável de `admin/tipos-processo` e o modal rolável de
  `components/modal.tsx`. O change deve ser majoritariamente reaplicação, não
  invenção.
- Deixar o comportamento em tela estreita **verificável automaticamente**, para
  que a correção não regrida em silêncio como regrediu até aqui.

**Non-Goals:**

- Conversão de tabela em cards, redesenho de telas, novos breakpoints ou nova
  escala tipográfica.
- Corrigir divergências de identidade visual encontradas de passagem — por
  exemplo `app/consulta-publica/page.tsx:105`, que usa `bg-blue-600` em vez do
  token navy. É violação do requisito "Tokens de marca" da capability
  `identidade-visual`, mas é **assunto de marca, não de viewport**; misturá-la
  aqui contaminaria o diff. Registrada em Open Questions.
- Otimização de toque (área mínima de alvo, gestos) e performance em rede móvel.

## Decisions

### D1 — Rolagem horizontal vai no contêiner, e a identidade visual vai junto

As cinco tabelas quebradas carregam `rounded-card border border-navy-50 shadow-card`
**na própria `<table>`, junto com `overflow-hidden`**. O `overflow-hidden` está lá
para que o conteúdo respeite o canto arredondado — não é engano gratuito, é o que
faz o radius funcionar. Por isso a correção não pode ser "remover `overflow-hidden`":
isso resolveria o corte e quebraria o card.

A correção é adotar a forma de `admin/tipos-processo/page.tsx:148-149`, movendo a
identidade visual para fora e deixando a tabela nua:

```
<div className="… overflow-x-auto rounded-card border border-navy-50 bg-superficie-card shadow-card">
  <table className="w-full text-left text-sm">
```

O contêiner passa a ser o card (borda, radius, sombra, superfície) e o
`overflow-x-auto` recorta o excedente no mesmo raio. A `<table>` perde
`overflow-hidden`, `rounded-card`, `border` e `shadow-card`, e mantém apenas
largura e tipografia. A margem (`mt-3` / `mt-6`) acompanha o contêiner.

*Alternativa descartada:* `display: block` + `overflow-x-auto` na própria
`<table>`. Funciona, mas destrói a semântica de tabela para leitores de tela e
faz as colunas pararem de se alinhar entre `thead` e `tbody`.

### D2 — Sem largura mínima, `overflow-x-auto` não rola nada

Esta é a decisão que a proposta não podia ter: **envolver a tabela num contêiner
`overflow-x-auto` é necessário mas não suficiente**. Com `w-full`, a tabela mede
exatamente a largura do contêiner; não há excedente, logo não há rolagem — o
navegador simplesmente comprime as colunas e quebra o texto caractere a caractere.
O resultado seria ilegível de um jeito diferente, e o cenário "Tabela larga rola
dentro do próprio contêiner" da spec falharia.

A tabela precisa, portanto, de um piso de largura. Adota-se `min-w-[<N>px]` na
`<table>`, dimensionado por contagem de colunas (~120 px por coluna de dados,
com folga para a coluna de ações):

| Tela | Colunas | `min-w` |
|---|---|---|
| `admin/usuarios` | 6 (nome, e-mail, perfil, status, unidade, ações) | `min-w-[720px]` |
| `admin/unidades` (unidades) | conferir na implementação | dimensionar pela regra |
| `admin/unidades` (setores) | conferir na implementação | dimensionar pela regra |
| `admin/lgpd/solicitacoes` | conferir na implementação | dimensionar pela regra |
| `admin/documentos-removidos` | conferir na implementação | dimensionar pela regra |

A contagem de cada tabela é conferida na tarefa correspondente — o valor não é
crítico, o que é crítico é **existir** e ser maior que 360 px.

`admin/tipos-processo` (3 colunas) fica como está: não recebe `min-w`, porque em
360 px suas três colunas curtas ainda cabem. Ele é o modelo do padrão de
contêiner, não um alvo de correção.

*Alternativa considerada:* `whitespace-nowrap` nas células, deixando o conteúdo
ditar a largura. Descartada porque a coluna "Assunto"/"Justificativa" de algumas
telas comporta texto longo, e proibir quebra transformaria uma linha isolada numa
rolagem horizontal de vários milhares de pixels.

### D3 — Os modais de `processos/[id]` adotam o contêiner de `components/modal.tsx`

Os dois modais locais passam de `items-center … p-4` para
`items-start … overflow-y-auto p-4 sm:p-8`, idêntico a `components/modal.tsx:34`.
Com `items-start` o diálogo ancora no topo e o excedente cresce para baixo, dentro
de um contêiner que rola; os botões deixam de ser inalcançáveis.

Efeito colateral aceito: em desktop, um modal curto deixa de ficar centrado
verticalmente e passa a ficar ancorado no topo, com o respiro de `sm:p-8`. É
exatamente o que o modal de cadastro de usuário já faz hoje — a mudança **aumenta**
a consistência entre os modais do sistema em vez de introduzir uma exceção.

*Alternativa descartada:* manter `items-center` e acrescentar
`max-h-[90vh] overflow-y-auto` no diálogo interno. Também resolve, mas cria um
segundo padrão de modal no repositório para o mesmo problema que
`components/modal.tsx` já resolve de outro jeito.

*Não se adota* extrair os dois modais para o componente `Modal` compartilhado:
eles têm cabeçalho e rodapé próprios e o refactor extrapola um change de
apresentação.

### D4 — Colapso de duas colunas em coluna única

Duas listas de definição usam grade fixa de duas colunas:

- `consulta-publica/page.tsx:18` — `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`
- `processos/[id]/page.tsx:674` — `grid-cols-[auto_1fr]` →
  `grid-cols-1 sm:grid-cols-[auto_1fr]`

A barra de abas de `processos/[id]:648` (`flex gap-4 border-b`) recebe
`overflow-x-auto` por precaução: os três rótulos atuais cabem em 360 px, mas a
barra é um ponto de crescimento natural e o custo é uma classe.

### D5 — O projeto Playwright móvel roda **apenas** specs dedicadas

Restrição de D-Context 2: a suíte é serial, com banco zerado uma única vez e
estado encadeado entre specs. Se o projeto móvel herdasse o `testDir` inteiro,
os 16 specs rodariam **duas vezes** contra o mesmo banco — a segunda passada
falharia em toda asserção de criação ("usuário já existe"), e o tempo de CI
dobraria. Um segundo projeto só é viável se o conjunto de specs for disjunto.

Portanto:

```
projects: [
  { name: "chromium", use: { ...devices["Desktop Chrome"] },
    testIgnore: /.*\.mobile\.spec\.ts/ },
  { name: "mobile",   use: { ...devices["Pixel 5"] },
    testMatch: /.*\.mobile\.spec\.ts/ },
]
```

O `testIgnore` no projeto desktop é tão necessário quanto o `testMatch` no
móvel — sem ele, o desktop também executaria os specs móveis, em viewport
largo, onde não testam nada.

Ordenação e estado: o projeto `mobile` roda depois de `chromium`, sobre o banco
**já povoado** pelos specs `01`–`16` (o `globalSetup` não roda de novo entre
projetos). Os specs móveis, portanto:

- reaproveitam `ADMIN_ROOT` de `e2e/fixtures.ts` para autenticar, como os demais;
- criam seus próprios unidade, setor, servidor e processo, com **nomes e e-mails
  distintos** dos usados em `01`–`16`, para não colidir com o estado existente;
- usam `helpers/auth.ts` (`login`/`logout`), que já zera o rate limit de `/auth/*`
  antes de cada login — sem isso os logins adicionais estouram o limite de 10/min
  e a suíte falha por "Too Many Requests".

`Pixel 5` (393 × 851, `isMobile`, `hasTouch`) é o descritor escolhido: é um
aparelho representativo e o Playwright o executa sobre o mesmo Chromium já
instalado, sem novo download de browser no CI. As asserções de largura de 360 px
da spec são verificadas por `page.setViewportSize` dentro dos specs onde a
diferença importa.

*Alternativa descartada:* um arquivo de configuração Playwright separado para
móvel. Duplicaria `webServer`, `globalSetup` e as flags de dev, e exigiria uma
segunda subida de API + Next no CI.

### D6 — Cobertura E2E móvel: login, tramitação e consulta pública

A regra do projeto exige Playwright para login, tramitação, documentos e consulta
pública. Este change altera a **apresentação** de login (shell), tramitação
(modais — D3), tabelas administrativas (D1/D2) e consulta pública (D4) em tela
estreita, então os três primeiros fluxos que ele de fato toca ganham spec móvel:

| Spec | Cobre | Cenário da spec |
|---|---|---|
| `17-login-mobile.mobile.spec.ts` | login + gaveta de navegação + tabela rolável | "Página não rola horizontalmente", "Tabela larga rola dentro do próprio contêiner" |
| `18-tramitacao-mobile.mobile.spec.ts` | modal de tramitação alcançável e envio concluído | "Modal de tramitação mais alto que a tela é rolável", "Tramitação se completa a partir de um smartphone" |
| `19-consulta-publica-mobile.mobile.spec.ts` | consulta por número sem autenticação | "Consulta pública legível em smartphone sem login" |

Documentos não ganha spec móvel: a aba de documentos não é alterada por nenhuma
decisão deste design, e criar cobertura móvel para uma tela que o change não toca
é custo de manutenção sem contrapartida.

**Como se afirma "a página não rola horizontalmente"** — asserção mecânica, não
inspeção visual:

```
const overflow = await page.evaluate(
  () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
);
expect(overflow).toBeLessThanOrEqual(0);
```

E para a tabela, o inverso — o contêiner **deve** ter excedente rolável:
`scrollWidth > clientWidth` no contêiner, com `scrollLeft` assumindo valor
positivo após rolagem.

### D7 — Nenhuma alteração de backend, contrato ou dados

Confirmado pela inspeção: o change toca `apps/web/app/**`, `apps/web/e2e/**` e
`apps/web/playwright.config.ts`. Não há migration (nenhuma tabela PostgreSQL
afetada), não há segredo novo no Secret Manager, não há bucket novo, não há rota
ou schema FastAPI alterado — portanto **não há `pnpm gen:types`** e o job de
drift do CI não é afetado. Nenhum endpoint público é criado ou alterado: o rate
limiting de `/publico/*` permanece exatamente como está.

**LGPD:** nenhum dado pessoal novo é coletado, exibido, retido ou transmitido. As
telas afetadas exibem os mesmos campos aos mesmos perfis em qualquer largura — a
spec fixa isso como requisito ("Mesmos dados e ações em qualquer largura") e o
cenário de acesso negado em tela estreita garante que a adaptação não vira via de
exposição.

Não há diagrama de sequência: nenhum fluxo deste change atravessa front, back e
job assíncrono — é apresentação no cliente, ponta a ponta.

## Risks / Trade-offs

- **`min-w` fixo em pixels envelhece mal** → o valor é um piso de legibilidade,
  não uma medida de layout; se uma coluna for acrescentada a uma dessas tabelas
  no futuro, o `min-w` deve ser revisto junto. O comentário no código cita `(D2)`
  justamente para que quem mexer encontre o motivo.
- **Modal ancorado no topo é percebido como regressão visual em desktop** →
  é mudança deliberada (D3) e alinha com `components/modal.tsx`; se incomodar,
  a correção é uma decisão de marca posterior, não a volta do `items-center`,
  que reintroduz o defeito.
- **O projeto móvel depende do estado deixado pelos specs desktop** → acoplamento
  real (D5). Mitigação: os specs móveis criam o próprio estado com nomes
  distintos e não assumem nada além do `ADMIN_ROOT`, que é o mesmo contrato que
  `04`–`16` já usam. Se algum dia a suíte passar a rodar projetos em paralelo,
  esta premissa precisa ser revista.
- **Tempo de CI cresce** → três specs a mais, um deles com fluxo completo de
  tramitação. Contido: são três arquivos, não uma segunda passada da suíte (D5).
- **Vitest não protege contra regressão de layout** → os testes de componente não
  asseguram classes de layout, como a própria proposta observa; a proteção real é
  o projeto móvel do Playwright. Não se acrescentam asserções de `className` em
  Vitest, que testariam a implementação e não o comportamento.

## Migration Plan

Não aplicável — mudança de apresentação no cliente, sem migration, sem alteração
de dados e sem etapa de deploy própria. Rollback é a reversão do merge.

## Open Questions

- `app/consulta-publica/page.tsx:105` usa `bg-blue-600` em vez do token navy,
  violando o requisito "Tokens de marca disponíveis para toda a UI" da capability
  `identidade-visual`. Fora do escopo deste change (Non-Goals) — decidir se vira
  correção pontual em `marca-visual-despapelize` ou change próprio. Não afeta as
  specs, o desenho nem as tarefas abaixo.
