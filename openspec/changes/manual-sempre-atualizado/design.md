## Context

Ver `proposal.md` — Why. O estado atual, verificado no repositório:

```
openspec/config.yaml   rules.tasks
  ├── teste automatizado (histórico/dados pessoais)     "não é opcional"
  ├── teste E2E Playwright (login/tramitação/docs/CP)   "não é opcional"
  ├── pnpm gen:types (rota ou schema do FastAPI)        "o CI falha"
  └── ⟵ NADA sobre documentação de usuário

CLAUDE.md
  └── ⟵ nenhuma menção a docs/manual/, mkdocs.yml ou publicar-manual.yml

.github/workflows/
  ├── ci.yml               PR + main · jobs api / web / types-drift
  ├── deploy.yml           push main · path-filtered
  └── publicar-manual.yml  push main · docs/manual/**, mkdocs.yml,
                           requirements-docs.txt · mkdocs build --strict
```

Três restrições do ambiente moldam este design.

**1. As três obrigatoriedades que já existem em `rules.tasks` têm reforço fora do
processo.** Teste automatizado e E2E são executados pelo CI; `gen:types` tem job de
drift dedicado que quebra o build. A regra no `config.yaml` orienta quem escreve o
change, mas não é a única linha de defesa. Uma regra de documentação nova nasceria
**sem nenhum reforço** — é a diferença que este design precisa endereçar.

**2. Atualidade de manual não é verificável por máquina.** Nenhuma ferramenta
decide se a página `servidor/tramitar.md` ainda descreve a tela de tramitação. Isso
separa dois problemas que costumam ser confundidos:

```
manual QUEBRADO   → link morto, página fora do nav, arquivo órfão
                  → verificável: mkdocs build --strict

manual DEFASADO   → texto correto sintaticamente, descreve tela que mudou
                  → NÃO verificável por máquina · só por quem faz o change
```

**3. Existe uma lacuna temporal no reforço que hoje existe.** `mkdocs build --strict`
roda **apenas** em `publicar-manual.yml`, disparado por `push` na `main`. O
`ci.yml` não constrói documentação. Um PR que quebre um link do manual passa por
todo o CI, é aprovado, é mergeado — e **só então** falha, na publicação, já com
`main` contendo o defeito. O portão existe, mas está depois da porta.

O change `manual-mkdocs` estabeleceu o princípio que este design segue: preferir
**garantia estrutural** a **regra de processo** sempre que a escolha exista (D1
daquele design, sobre o `docs_dir`). Aqui a escolha existe só parcialmente — e o
design precisa ser explícito sobre onde ela existe e onde não.

## Goals / Non-Goals

**Goals:**

- Ligar mudança de produto a atualização de manual no mesmo lugar onde as demais
  obrigatoriedades do projeto já vivem, com a mesma força ("não é opcional").
- Tornar `docs/manual/` **descobrível** por quem lê `CLAUDE.md` — hoje não é.
- Antecipar a detecção de manual quebrado para **antes** do merge, fechando a
  lacuna temporal descrita no Context.
- Enunciar a regra com gatilho operacional, para que ela não vire ruído em change
  que não tem efeito visível ao usuário.

**Non-Goals:**

- **Nenhuma alteração de código de aplicação.** Nenhum endpoint, componente,
  contrato, schema ou tipo é tocado.
- **Nenhuma auditoria de defasagem já existente** nas 30 páginas do manual. A regra
  vale daqui para frente; varredura retroativa é escopo próprio (registrado no
  final da proposta).
- **Nenhuma tentativa de verificar automaticamente se o manual está atualizado.**
  É indecidível por máquina (ver Context 2); qualquer coisa que se parecesse com
  isso seria teatro de conformidade.
- **Nenhuma alteração no `publicar-manual.yml`.** Ele já satisfaz a exigência de
  publicar somente após merge em `main`.
- **Nenhum screenshot no manual.** O `manual-mkdocs` os excluiu deliberadamente
  (Non-Goals) porque envelhecem a cada mudança de UI — reintroduzi-los agravaria
  exatamente o problema que este change combate.

## Decisions

### D1 — A regra vive em `rules.tasks`, não em `rules.proposal` nem em `rules.design`

A obrigação entra em `openspec/config.yaml` sob `rules.tasks`, ao lado das regras
de teste automatizado, E2E e `gen:types`.

*Por quê:* `rules.tasks` é o único dos três que produz **item verificável na lista
de tarefas** do change. Uma regra em `rules.proposal` produziria um parágrafo que
alguém escreve e ninguém confere; em `rules.tasks`, ela produz uma linha com
critério de aceite que fica visível como pendente até ser marcada. É também onde as
outras três obrigatoriedades foram colocadas — e a consistência importa: quem lê o
`config.yaml` encontra as quatro exigências no mesmo bloco, não espalhadas.

*Alternativa considerada:* hook do Claude Code (`settings.json`) que bloqueia commit
tocando `apps/web/app/**` sem tocar `docs/manual/**`. **Rejeitada** — produz falso
positivo em toda refatoração, correção de bug sem efeito visível e ajuste de teste,
que são a maioria dos commits de frontend. Uma regra que dispara errado na maior
parte das vezes é desativada em uma semana.

### D2 — O gatilho é "mudança perceptível pelo usuário final", enunciado por exclusão

A regra não diz "toda change de frontend". Ela enuncia o gatilho e, logo em
seguida, o que **não** o aciona:

```
DISPARA                              NÃO DISPARA
─────────────────────────────────    ─────────────────────────────────
tela nova ou removida                refatoração sem efeito visível
passo a passo alterado               correção de bug que restaura o
campo/botão/menu alterado              comportamento já documentado
texto exibido ao usuário             migration/schema interno
regra de negócio que muda o que      infraestrutura, CI, Terraform
  o usuário pode fazer               mudança de teste
perfil ganha ou perde acesso         performance sem mudança de UI
```

*Por quê:* uma regra sem limite declarado é aplicada por excesso até perder
credibilidade, ou por defeito até não valer nada. O caso decisivo é a **correção de
bug**: consertar um comportamento para que ele volte a corresponder ao manual **não**
exige atualizar o manual — o manual já estava certo. Sem essa distinção explícita, a
regra sugeriria o contrário.

*Consequência aceita:* o gatilho exige julgamento, e julgamento erra. Erra-se para o
lado de atualizar o manual — é mais barato revisar um parágrafo desnecessário do que
descobrir uma instrução errada por reclamação de usuário.

### D3 — `mkdocs build --strict` passa a rodar também em PR, como job do `ci.yml`

Um job novo no `.github/workflows/ci.yml`, path-filtered por `docs/manual/**`,
`mkdocs.yml` e `requirements-docs.txt` — o mesmo padrão de filtragem dos jobs `api`,
`web` e `types-drift` já existentes —, executando `mkdocs build --strict` **sem
publicar**.

```
ANTES                                DEPOIS
PR  →  ci.yml (api, web, types)      PR  →  ci.yml (api, web, types, manual)
       ✅ passa mesmo com link morto        ❌ link morto barra o PR
merge →  publicar-manual.yml                merge →  publicar-manual.yml
       ❌ falha, main já quebrada                   ✅ publica
```

*Por quê:* é a única parte deste change que admite garantia estrutural em vez de
regra de processo, e o projeto tem preferência declarada por isso (D1 de
`manual-mkdocs`). O custo é baixo — `pip install -r requirements-docs.txt` +
`mkdocs build`, sem serviço de banco, sem credencial, sem permissão de escrita.

*Isto amenda a proposta.* `proposal.md` afirmava "Nenhuma automação nova de CI",
raciocinando corretamente que o item 4.2 (publicar só após `main`) já estava
satisfeito. A afirmação confundia **publicação** com **validação**: publicar segue
acontecendo apenas após merge em `main`, e este job não publica nada. A proposta foi
corrigida para refletir a decisão.

*O que este job NÃO faz:* não verifica se o manual está **atualizado** (ver Context
2). Ele detecta manual **quebrado**. Confundir os dois daria falsa segurança — e é
justamente por isso que D1 e D3 coexistem em vez de um substituir o outro.

*Alternativa considerada:* mover `publicar-manual.yml` para rodar em PR com
publicação condicional. **Rejeitada** — misturaria permissões de publicação
(`pages: write`, `id-token: write`) num workflow disparado por PR, ampliando
superfície sem ganho. Validar e publicar são responsabilidades separadas.

### D4 — `CLAUDE.md` documenta o manual na seção de fluxo de trabalho, com o alerta do `docs_dir` replicado

A seção nova cobre quatro pontos: onde o manual vive, como é publicado, quando é
publicado, e a advertência sobre o `docs_dir`.

*Por quê replicar o alerta do `docs_dir`* se ele já está comentado no `mkdocs.yml`:
o risco mapeado como "o maior" no design de `manual-mkdocs` é alguém "simplificar" o
`docs_dir` para `docs/` e publicar PRD, URLs de produção e configuração de e-mail
num site público. A defesa escolhida lá foi pôr a explicação no arquivo que a pessoa
vai editar. `CLAUDE.md` é o arquivo que um agente lê **antes** de editar qualquer
coisa — replicar o alerta aumenta a chance de ele ser lido antes, não depois.

*Consequência aceita:* duplicação de texto entre `CLAUDE.md` e `mkdocs.yml`, que
pode divergir. Aceita porque o custo de divergência aqui é baixo (as duas cópias
dizem "não aponte para `docs/`") e o custo da falha que ela previne é alto
(publicação de documento interno em site público).

### D5 — A regra referencia `mkdocs build --strict` local como aceite da tarefa

A tarefa que a regra gera tem por critério de aceite a execução de
`mkdocs build --strict` localmente, não apenas "o manual foi atualizado".

*Por quê:* o fatiamento do manual em 30 páginas transformou âncoras internas em
links entre arquivos. Adicionar ou renomear uma página quebra links em outras com
facilidade, e `--strict` é o que converte isso em erro em vez de aviso silencioso.
Com D3, o CI pega o mesmo defeito — mas pegá-lo antes do push é mais barato que
pegá-lo depois.

## Risks / Trade-offs

- **[O maior] A regra de D1/D2 é ignorada na prática, porque nada a força.**
  Diferentemente de teste e `gen:types`, ninguém quebra o build por não atualizar o
  manual — e o efeito de ignorá-la só aparece meses depois, para um usuário. → Não
  há mitigação completa; é limite reconhecido, não resolvido. Mitigação parcial: a
  regra em `rules.tasks` produz item **visível como pendente** na lista de tarefas
  do change, e a menção em `CLAUDE.md` (D4) faz o manual existir para quem lê as
  instruções do projeto — hoje ele é invisível ali. O que **não** se faz é fingir
  que D3 resolve isto: D3 detecta manual quebrado, não manual defasado.
- **A regra vira ruído e é contornada por reflexo.** Se disparar em change de
  infraestrutura ou refatoração, o hábito vira marcar a tarefa como não aplicável
  sem ler. → D2 enuncia o gatilho por exclusão, e a lista do "NÃO DISPARA" cobre
  justamente os casos de maior volume.
- **O job de D3 quebra por causa de dependência transitiva do MkDocs, não por
  defeito no manual.** → `requirements-docs.txt` já fixa versões com `==` (D4 de
  `manual-mkdocs`), precisamente por isso. O job herda essa proteção sem trabalho
  adicional.
- **O job de D3 adiciona tempo a PRs que não tocam documentação.** → Path filter no
  mesmo padrão dos jobs existentes: PR que não toca `docs/manual/**`, `mkdocs.yml`
  ou `requirements-docs.txt` não executa o job.
- **A duplicação do alerta do `docs_dir` (D4) diverge com o tempo.** → Aceito
  explicitamente em D4; ambas as cópias afirmam a mesma coisa e o custo da falha
  prevenida é desproporcionalmente maior.

## Migration Plan

Não há migration de banco, de contrato nem de aplicação. Nenhum serviço em produção
é afetado — nenhum código executável do produto é tocado.

**Ordem:** editar `openspec/config.yaml` (D1, D2) → editar `CLAUDE.md` (D4) →
adicionar o job ao `ci.yml` (D3) → validar que o job roda em PR que toca
`docs/manual/**` e não roda em PR que não toca → merge.

**Verificação de que D3 funciona:** introduzir deliberadamente um link quebrado numa
página do manual em branch de teste e confirmar que o job falha; desfazer. Sem isso,
a única evidência é o job passando — que também é o resultado de um job que não
testa nada.

**Rollback:** reverter o merge. Como nada de aplicação muda, não há estado a
restaurar; o `publicar-manual.yml` segue funcionando em qualquer das direções.

**Aplicar antes dos changes de UI:** `marca-visual-despapelize` e
`responsividade-mobile` alteram telas descritas no manual. Se este change for
aplicado depois deles, a regra nasce já com duas exceções.

## Open Questions

- **Nenhuma bloqueante.** As decisões de escopo (regra em `rules.tasks`, gatilho por
  exclusão, validação em PR, seção no `CLAUDE.md`) estão resolvidas em D1–D5.
- **Fora do escopo, para decisão futura:** se a varredura de defasagem retroativa
  das 30 páginas será feita, e quando. O manual foi escrito no mesmo período de
  `renomear-sistema-despapelize` e antes de `ajustes-ui-admin`, o que torna
  plausível — não confirmado — que partes já descrevam telas anteriores. Confirmar
  isso é trabalho de auditoria, não deste change.

<!-- Regras do projeto não aplicáveis a este change, declaradas para que a ausência
não seja lida como omissão: não há fluxo de 3+ etapas atravessando front/back/job,
logo nenhum diagrama de sequência é exigido; não há rotina automática nova (Cloud
Scheduler / Cloud Run Jobs) a documentar quanto a gatilho, janela e idempotência;
não há endpoint público novo, logo não há rate limiting nem ausência de autenticação
a declarar; não há migration Alembic. -->
