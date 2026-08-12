## Why

O manual do usuário em `docs/manual/` tem 30 páginas descrevendo passo a passo as
telas do sistema. Ele foi criado pelo change `manual-mkdocs` (arquivado em
2026-08-04) e o próprio design daquele change registrou o risco que agora se
materializa:

> **"O manual envelhece a cada mudança de UI."** → Nada neste change impede isso; é
> custo permanente de manter documentação.
> — `openspec/changes/archive/2026-08-04-manual-mkdocs/design.md`, Risks / Trade-offs

Hoje **não existe nenhum mecanismo** que ligue uma mudança de produto à atualização
do manual:

- `openspec/config.yaml` tem regras obrigatórias em `rules.tasks` para teste
  automatizado, teste E2E Playwright e `pnpm gen:types` — **nenhuma para
  documentação de usuário**.
- `CLAUDE.md` não menciona `docs/manual/`, `mkdocs.yml` nem o workflow de
  publicação em lugar algum. Quem lê o arquivo de instruções do projeto **não fica
  sabendo que o manual existe**.

A consequência é previsível: as changes que descrevem telas — como as duas
propostas em paralelo, `marca-visual-despapelize` e `responsividade-mobile` — não
terão nenhum lembrete de que há um manual descrevendo essas mesmas telas. O manual
diverge silenciosamente, e a divergência só é descoberta por um usuário final
seguindo uma instrução que não corresponde mais ao que está na tela.

O ponto deste change é fechar essa lacuna **no mesmo lugar onde as outras
obrigatoriedades do projeto já vivem** — não criar processo novo, mas estender o
que já funciona.

## What Changes

- **`openspec/config.yaml` ganha regra em `rules.tasks`**: toda change que altere
  uma tela, um fluxo de usuário final ou o texto exibido ao usuário **deve incluir
  tarefa correspondente de atualizar `docs/manual/**`** — no mesmo padrão
  vinculante ("não é opcional") já usado pelas regras de teste automatizado, E2E e
  `gen:types`.
- **A regra é explícita sobre quando *não* se aplica**, para não virar ruído: change
  puramente de backend sem efeito visível ao usuário, de infraestrutura, de
  migration interna ou de refatoração não dispara atualização de manual. O gatilho é
  **mudança perceptível pelo usuário final**, não mudança de código.
- **`CLAUDE.md` ganha seção sobre a documentação do usuário**, cobrindo o que hoje
  está ausente: que o manual vive em `docs/manual/`, que é publicado como site
  MkDocs no GitHub Pages, que a publicação ocorre **apenas após merge em `main`**
  (o workflow dispara em `push` na `main` com path filter — comportamento já
  vigente, apenas não documentado), e o alerta de que **`docs_dir` aponta para
  `docs/manual/` por controle de segurança** (D1 de `manual-mkdocs`), nunca para
  `docs/`.
- **A validação local é registrada**: `mkdocs build --strict` é o portão que
  transforma link quebrado e página fora do `nav` em erro. Quem atualiza o manual
  deve rodá-lo antes de abrir PR — hoje isso só existe dentro do workflow.
- **`mkdocs build --strict` passa a rodar também em PR**, como job novo do
  `.github/workflows/ci.yml`, path-filtered no mesmo padrão dos jobs `api`, `web` e
  `types-drift` — **sem publicar nada**. Hoje o `--strict` só roda em
  `publicar-manual.yml`, disparado por `push` na `main`: um PR que quebre um link do
  manual passa por todo o CI, é mergeado, e **só então** falha na publicação, com a
  `main` já contendo o defeito. O portão existe, mas está depois da porta.
- **O `publicar-manual.yml` não é alterado.** Ele já satisfaz o item 4.2 —
  publicação continua ocorrendo exclusivamente após merge em `main`. O job novo
  **valida**; ele não publica. São responsabilidades separadas, e o job de PR não
  recebe as permissões de publicação (`pages: write`, `id-token: write`).
- **O que a automação não faz**: `--strict` detecta manual **quebrado** (link morto,
  página fora do `nav`), não manual **defasado**. Se um texto ainda descreve
  corretamente uma tela que mudou é indecidível por máquina — por isso a regra de
  autoria acima e a verificação de CI coexistem, em vez de uma substituir a outra.

## Capabilities

### New Capabilities

<!-- Nenhuma. Nenhum comportamento do sistema muda: este change altera as regras do
processo de trabalho (openspec/config.yaml) e o arquivo de instruções do projeto
(CLAUDE.md). Nenhum código de aplicação é tocado. O change declara skip_specs: true. -->

### Modified Capabilities

<!-- Nenhuma. Nenhuma capability em openspec/specs/ é alterada — as regras vivem em
openspec/config.yaml, que não é uma spec de capability. -->

## Impact

- **Dependências**: **requer `manual-mkdocs` arquivado** (já está, desde
  2026-08-04) — a regra só faz sentido com o manual e o pipeline existindo.
  Convém aplicar este change **antes** de `marca-visual-despapelize` e
  `responsividade-mobile`, para que a regra já os alcance: ambos alteram telas
  descritas no manual.
- **Tabelas PostgreSQL**: **nenhuma**.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: **nenhum**.
- **Backend / Frontend**: **nenhuma alteração de código de aplicação**. Nenhum
  endpoint, componente, contrato ou tipo é tocado.
- **Contrato**: **nenhuma regeneração de tipos**.
- **Arquivos alterados**: `openspec/config.yaml` (`rules.tasks`), `CLAUDE.md`
  (seção nova) e `.github/workflows/ci.yml` (job de validação do manual).
- **CI/CD**: um **job novo** em `ci.yml` executando `mkdocs build --strict` em PRs
  que toquem `docs/manual/**`, `mkdocs.yml` ou `requirements-docs.txt` — sem
  publicar e sem permissões de publicação. `.github/workflows/publicar-manual.yml`
  **permanece inalterado**: continua sendo o único caminho de publicação, disparado
  apenas por `push` na `main`, preservando o item 4.2.
- **LGPD**: **não aplicável**.
- **PRD**: nenhuma alteração. `docs/PRD.md` continua sendo o documento mestre de
  requisitos; o manual descreve o uso do sistema e é derivado dele.

> **Limite deliberado deste change**: ele institui a regra daqui para frente. Ele
> **não** audita as 30 páginas do manual em busca de defasagem já existente frente
> a changes arquivados. Se essa varredura for desejada — o manual foi escrito antes
> de `ajustes-ui-admin` e no mesmo período de `renomear-sistema-despapelize` —, ela
> é escopo próprio, com custo próprio, e deve ser uma change separada.
