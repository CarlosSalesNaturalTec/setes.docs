## Context

Ver `proposal.md` — Why. Três fatos do ambiente moldam este design mais do que
qualquer preferência de ferramenta.

**1. O MkDocs constrói tudo que está no `docs_dir`.** Não apenas o que está no `nav`.
Ficar fora do `nav` produz um aviso de build (`INFO - The following pages exist in
the docs directory, but are not included in the "nav" configuration`) e nada mais — a
página é gerada e servida por URL direta. Excluir de verdade exige plugin
(`mkdocs-exclude`) ou não colocar o arquivo lá.

**2. GitHub Pages é público.** Um site do Pages servido a partir de repositório
privado continua acessível sem autenticação, exceto em planos Enterprise com Pages
privado. O repositório é `CarlosSalesNaturalTec/setes.docs`.

**3. `docs/` hoje é uma pasta mista.** Junto do manual convivem:

```
docs/
├── manual-usuario.md               ← ÚNICO arquivo destinado ao usuário final
├── PRD.md                          ← 111 KB de especificação interna
├── primeiro-acesso-producao.md     ← URLs de produção, procedimento de bootstrap
├── emailConfig.md                  ← identificação de conta do provedor de e-mail
├── decisao-regiao-us-central1.md   ← decisão interna de arquitetura
├── lgpd-transferencia-…md          ← análise interna de conformidade
├── Ajustes SETES DOCS.pdf          ← documento do cliente
└── history/  (29 arquivos)         ← demanda original, rascunhos de PRD, reviews
```

Combinados, os três fatos significam que `docs_dir: docs` publicaria toda essa coluna
da direita num site público. Essa é a restrição central do design, não um detalhe de
configuração.

O manual em si tem ~780 linhas com hierarquia limpa — `##` por público, `###` por
tarefa — que já corresponde quase 1:1 à navegação desejada.

## Goals / Non-Goals

**Goals:**

- Site navegável por perfil, com busca, publicado em endereço estável.
- Fonte única para o manual: sem cópia paralela que possa divergir.
- Impossibilidade **estrutural** de publicar documento interno — não uma regra que
  alguém precise lembrar de seguir.
- Documentar os três mecanismos automáticos a partir do comportamento real do código.

**Non-Goals:**

- **Nenhuma alteração de código de aplicação.** Nenhum endpoint, componente, contrato
  ou tipo é tocado.
- **Nenhuma documentação de API** (`mkdocstrings`, Swagger embutido). O público é o
  usuário final; o contrato OpenAPI já é servido pelo próprio FastAPI.
- **Nenhum domínio customizado.** O endereço padrão `*.github.io` basta; domínio
  próprio é decisão de produto à parte.
- **Nenhuma versionagem de documentação** (`mike`). Existe uma versão do produto.
- **Nenhuma tradução.** Português brasileiro apenas.
- **Nenhuma captura de tela nesta iteração.** Screenshots envelhecem com cada mudança
  de UI e este change segue dois changes que alteram telas; entram depois, se pedidas.

## Decisions

### D1 — `docs_dir` restrito a `docs/manual/`, e não `docs/` com denylist

O `docs_dir` do MkDocs aponta para `docs/manual/`. Os documentos internos permanecem
em `docs/`, fora do diretório de build.

```
docs/
├── manual/          ◄── docs_dir — SÓ isto existe para o MkDocs
│   └── …
├── PRD.md           ─┐
├── emailConfig.md    │  invisíveis ao build: não estão sob o docs_dir
├── history/         ─┘
```

*Por quê:* é a diferença entre uma garantia estrutural e uma regra de processo. Com
denylist (`mkdocs-exclude`), a segurança do site passa a depender de toda pessoa que
adicionar um documento interno a `docs/` lembrar de atualizar o `mkdocs.yml`. O modo
de falha é silencioso — ninguém percebe que um arquivo novo foi publicado até alguém
encontrá-lo. Com `docs_dir` restrito, adicionar um documento interno a `docs/`
simplesmente não o publica, sem que ninguém precise saber que essa regra existe.

Dado o conteúdo concreto de `docs/` (credencial de provedor de e-mail, URLs de
produção, demanda comercial do cliente), o modo de falha silencioso é inaceitável.

*Alternativa considerada:* mover os internos para `internal/` e deixar `docs/` só com
o manual. Rejeitada — mexe em mais caminhos, quebra links existentes no PRD, no
`CLAUDE.md` e em changes arquivados, e obtém a mesma garantia por mais trabalho.

*Consequência aceita:* links relativos do manual para documentos internos (se houver)
quebram no site. São links que **devem** quebrar — apontariam para conteúdo não
publicado.

### D2 — Fatiamento por público, espelhando a estrutura atual

`docs/manual-usuario.md` é dividido em uma página por seção `##` existente, e as
seções longas por perfil são subdivididas por `###`:

```
docs/manual/
├── index.md                 ← apresentação + os três perfis + como usar o manual
├── comum/                   ← §1-8 (primeiro acesso … sair)
├── servidor/                ← Kanban, criar, tramitar, concluir, documentos, sigilo
├── gestor/                  ← KPIs, quadro consolidado, cadastro de usuários
├── administrador/           ← usuários, unidades, setores, tipos, modelos, LGPD…
├── cidadao/                 ← consulta pública, solicitação LGPD
├── como-funciona/           ← ⟵ NOVO: arquivamento, consulta pública, LGPD
└── glossario.md
```

*Por quê:* a organização por perfil é a do manual atual e a que o próprio produto usa
(o perfil determina o que a pessoa vê). Reorganizar por funcionalidade obrigaria cada
usuário a filtrar mentalmente o que não se aplica a ele.

*O `nav` é declarado explicitamente* no `mkdocs.yml`, não inferido do sistema de
arquivos — controla a ordem, que é pedagógica (comum → seu perfil → glossário) e não
alfabética.

### D3 — Seção "Como funciona" separada das instruções de tarefa

Arquivamento, consulta pública e LGPD ganham seção própria em vez de virarem
parágrafos dentro das páginas de perfil.

*Por quê:* os três compartilham uma característica que os distingue de tudo o mais no
manual — **acontecem sem que ninguém os acione**. Não há "como fazer", só "o que
esperar". Enfiá-los sob um perfil sugeriria que aquele perfil os controla, que é
justamente a confusão a evitar: nenhum usuário arquiva um processo, e nenhum
administrador decide quando a anonimização automática roda.

*Conteúdo derivado do código, não do PRD:* o PRD descreve o que foi especificado; o
manual deve descrever o que o sistema faz. Nos três casos foram lidos os serviços e
jobs correspondentes. Divergência encontrada entre código e spec é **defeito a
reportar**, não algo que o manual resolva escolhendo um dos dois.

*Os três pontos que a seção precisa deixar explícitos:*

| Mecanismo | O que o usuário mais erra |
|---|---|
| Arquivamento | Achar que arquivar apaga. Não apaga — oculta do quadro por padrão. |
| Consulta pública | Achar que sigiloso "aparece protegido". Não aparece de forma alguma. |
| LGPD | Achar que anonimizar apaga o processo. O processo permanece íntegro e auditável. |

### D4 — Dependências em `requirements-docs.txt` na raiz, fora do `uv` da API

*Por quê:* MkDocs não é dependência da aplicação. Colocá-lo no `pyproject.toml` de
`apps/api` — mesmo como extra — o arrastaria para a resolução de dependências da API e
potencialmente para a imagem de contêiner. O CI da API roda `uv sync --extra dev` e não
deve baixar tema de documentação.

*Versões fixadas* (`==`), não faixas: build de documentação que quebra sozinho quando
uma dependência transitiva publica versão nova é ruído puro — não há bug de segurança a
correr atrás num gerador de site estático.

### D5 — Publicação por GitHub Actions com path filter, sem `gh-pages`

Workflow disparado por push em `main`, filtrado por `docs/manual/**`,
`mkdocs.yml` e `requirements-docs.txt`, publicando via as ações oficiais de Pages
(`upload-pages-artifact` / `deploy-pages`) com `GITHUB_TOKEN`.

*Por quê o path filter:* é o padrão já estabelecido em `.github/workflows/ci.yml` e
`deploy.yml`, ambos filtrados por app. Um commit que só toca `apps/api` não deve
disparar build de documentação.

*Por quê não `mkdocs gh-deploy`:* ele empurra o site construído para uma branch
`gh-pages`, versionando artefato de build no repositório e exigindo permissão de
escrita em branch. As ações oficiais publicam como artefato, sem branch extra e sem
commit de conteúdo gerado.

*Permissões mínimas* no workflow: `pages: write` e `id-token: write`, nada além.

*Pré-requisito não automatizável:* habilitar Pages com origem "GitHub Actions" nas
configurações do repositório. É clique na interface do GitHub — o workflow falha até
que seja feito, com erro explícito.

### D6 — Remoção de `docs/manual-usuario.md` no mesmo commit do fatiamento

O arquivo original é removido junto com a criação de `docs/manual/`, não depois.

*Por quê:* duas fontes coexistindo, ainda que por um único merge, é o começo da
divergência que a proposta quer evitar. Como o conteúdo é movido e não reescrito, o
Git registra a operação como movimentação e o histórico do texto é preservado.

*Referências a atualizar:* `CLAUDE.md`, `README.md` e o PRD, se apontarem para o
caminho antigo. Changes arquivados que o citem **não** são editados — são registro
histórico (mesmo princípio do D5 de `renomear-sistema-despapelize`).

## Risks / Trade-offs

- **[O maior] Alguém, mais tarde, "simplifica" o `docs_dir` para `docs/`** e publica
  os internos. → O `mkdocs.yml` carrega comentário explicando por que o `docs_dir` é
  restrito, com o inventário do que está em `docs/`. A defesa é a explicação estar no
  arquivo que a pessoa vai editar, não num documento que ela não vai ler.
- **O manual documenta comportamento que o código não tem** (ou o contrário). → As
  três seções novas são escritas com o serviço correspondente aberto ao lado, e as
  afirmações verificáveis são conferidas contra `services/arquivamento.py`,
  `services/consulta_publica.py`, `services/lgpd.py` e
  `services/anonimizacao_lgpd.py`. Divergência encontrada vira relato, não texto
  conciliador.
- **O manual envelhece a cada mudança de UI.** → Nada neste change impede isso; é
  custo permanente de manter documentação. Mitigação parcial: sem screenshots (ver
  Non-Goals), o texto sobrevive a mudanças visuais que não alterem os passos.
- **Dependência de ordem:** escrito antes de `renomear-sistema-despapelize` e
  `ajustes-ui-admin`, o manual nasce descrevendo o nome e as telas antigos. → A
  proposta declara os dois como pré-requisito; a primeira tarefa da lista é confirmar
  que ambos estão concluídos.
- **Trade-off aceito: o site é público e o produto é interno.** O manual descreve
  fluxos de um sistema que exige login; nada nele é segredo operacional, mas ele revela
  que a instituição usa o produto e como seus processos funcionam. Alternativa seria
  Pages privado (exige Enterprise) ou servir a documentação atrás do próprio login do
  sistema (muito mais trabalho). Aceito porque o conteúdo é manual de uso, não
  configuração — e porque a consulta pública do próprio sistema já é aberta.
- **`docs/emailConfig.md` continua versionado com identificação de conta.** O
  `docs_dir` restrito impede a publicação no site, mas o arquivo permanece no
  repositório e no histórico do Git. → Fora do escopo deste change; registrado na
  proposta como decisão de segurança à parte.

## Migration Plan

Não há migration de banco, de contrato nem de aplicação. Nenhum serviço em produção é
afetado — o site é estático e independente do Cloud Run.

**Ordem:** habilitar Pages no repositório → adicionar `mkdocs.yml`,
`requirements-docs.txt` e o workflow → fatiar o manual e remover o original → validar
`mkdocs build --strict` localmente → merge.

**`--strict` é o portão:** ele transforma em erro os avisos de link quebrado e de
página fora do `nav`. Como o fatiamento converte âncoras internas (`#primeiro-acesso`)
em links entre páginas, é onde os links quebrados aparecem — e é a verificação de que
o `docs_dir` não recolheu nada inesperado.

**Rollback:** reverter o merge restaura `docs/manual-usuario.md`. O site publicado
permanece no ar com a última versão até a próxima publicação; se for preciso tirá-lo
do ar, desabilita-se Pages nas configurações do repositório. Nenhum estado de
aplicação é afetado em nenhuma das direções.
