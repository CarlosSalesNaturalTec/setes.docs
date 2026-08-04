## Context

Ver `proposal.md` — Why. O que enquadra o design é o **alcance** da string
`SETES.DOCS`, não sua complexidade: 17 ocorrências em código, distribuídas por três
camadas com consequências bem diferentes.

```
apps/web  (6 arquivos)   → texto de tela. Sem efeito colateral.
apps/api  (4 arquivos)   → 5 assuntos de e-mail + 1 corpo  → chega ao usuário final
                         → FastAPI(title=…)               → muda o contrato OpenAPI
infra     (2 arquivos)   → apenas `description` de recurso. Sem efeito em plan/apply.
```

Dois fatos determinam quase todo o resto:

- **`FastAPI(title=…)` alimenta `info.title` do OpenAPI**, e `packages/api-types/openapi.json`
  é um snapshot commitado que o job `types-drift` do CI compara. Mudar o título sem
  regenerar reprova o CI — não é opcional nem adiável.
- **A spec `identidade-visual` fixa literalmente** `título "SETES.DOCS"` e o subtítulo
  `"SISTEMA ELETRÔNICO"`. Sem delta de spec, a implementação passa a contradizer a
  spec consolidada.

O shell já tem, no topo da sidebar, um elemento de subtítulo exatamente onde "SETES"
precisa entrar (`protected-shell.tsx:169` — `"Sistema Eletrônico"`, uppercase,
tracking-wide). A tela de Login não tem: lá o subtítulo é novo, entre o `<h1>` e o
`"Acesse sua conta"` existente.

## Goals / Non-Goals

**Goals:**

- Nome do produto e subtítulo de cliente consistentes em todas as superfícies de
  apresentação, sem nenhuma tela divergente.
- Contrato OpenAPI e `packages/api-types` em sincronia, com o CI verde.
- Delta de spec que impeça a implementação de contradizer `identidade-visual`.

**Non-Goals:**

- **Nenhuma internacionalização.** Não se introduz camada de i18n nem sistema de
  mensagens; as strings continuam literais no código, como hoje.
- **Nenhuma alteração de infraestrutura.** Nome do repositório, ID do projeto GCP,
  nomes de recursos Terraform e caminho do diretório permanecem `setes.docs`.
- **Nenhuma mudança de comportamento.** Autenticação, autorização, navegação, rotas e
  payloads permanecem idênticos.
- **Nenhum redesign.** Cores, tipografia, ícone da marca e layout não mudam — só o
  texto.

## Decisions

### D1 — Constante única para o nome do produto no frontend

O nome do produto e o subtítulo de cliente ficam em **uma constante exportada** de um
módulo de marca em `apps/web/lib/`, consumida pelas seis telas. Nenhuma tela repete a
string literal.

*Por quê:* a spec exige consistência entre superfícies (`Nome do produto consistente
entre as telas`). Com literais espalhados, a consistência depende de ninguém esquecer
uma tela — que é exatamente o defeito que estamos corrigindo agora. Com constante, um
rename futuro é um ponto só.

*Alternativa considerada:* variável de ambiente `NEXT_PUBLIC_APP_NAME`, permitindo
white-label por deploy. Rejeitada — não há segundo cliente, e a variável precisaria
ser propagada por Terraform, workflow de deploy e configuração de E2E para servir a um
requisito que ninguém pediu. Se o white-label surgir, a constante é o ponto natural de
extensão.

*Não vale para o `metadata.title` do `layout.tsx`:* ele é avaliado no módulo de
metadata do Next e pode consumir a mesma constante, mas é a única superfície que não é
JSX — atenção para não deixá-la para trás.

### D2 — Backend: constante para o prefixo de assunto de e-mail

Os cinco assuntos de e-mail seguem o padrão `"SETES.DOCS — <descrição>"`. O prefixo
vira **uma constante no backend**, e os assuntos passam a compô-la.

*Por quê:* mesma razão do D1, com um agravante — o assunto de e-mail é a superfície
mais visível ao usuário final e a menos coberta por teste. Um assunto esquecido só
aparece quando um usuário real recebe a mensagem em produção.

*Onde:* junto do módulo que já centraliza o envio, não num módulo de constantes novo.
O corpo do e-mail de boas-vindas (`usuarios.py:194`) também cita o nome e entra no
mesmo tratamento.

### D3 — Regeneração de tipos é passo obrigatório, não consequência

`pnpm gen:types` + commit de `packages/api-types` é **uma tarefa explícita** da lista,
imediatamente após a alteração de `main.py`, não um item de checklist final.

*Por quê:* é a única forma de o change reprovar o CI. O `types-drift` compara o
snapshot inteiro; ainda que `schema.ts` não mude (o `info.title` não gera tipo),
`openapi.json` muda e basta para o job falhar.

*Verificação:* `pnpm gen:types:check` localmente antes do push confirma a sincronia
sem depender do CI para descobrir.

### D4 — Sidebar: substituição, não acréscimo

Na sidebar, "SETES" **substitui** `"SISTEMA ELETRÔNICO"`; não convivem. No Login,
"SETES" é uma linha **nova**, e `"Acesse sua conta"` permanece.

*Por quê:* a sidebar tem um único slot de subtítulo, e empilhar dois subtítulos sob
um nome de produto num painel de 240px de largura degrada a hierarquia visual que a
capability `identidade-visual` estabelece. `"SISTEMA ELETRÔNICO"` era descrição
genérica; `"SETES"` é informação real (quem é o cliente) e ocupa melhor o mesmo
espaço. No Login há espaço vertical de sobra, e `"Acesse sua conta"` tem função
distinta — é chamada de ação, não identificação de marca.

*Consequência de spec:* o requisito de sidebar em `identidade-visual` cita
`"SISTEMA ELETRÔNICO"` no texto normativo. O delta o remove explicitamente, para que o
subtítulo antigo não sobreviva como requisito órfão.

### D5 — Documentação acompanha, histórico arquivado não

`docs/PRD.md`, `docs/manual-usuario.md`, `docs/primeiro-acesso-producao.md`,
`README.md` e `CLAUDE.md` são atualizados. **`openspec/changes/archive/**` e
`docs/history/**` não são tocados.**

*Por quê:* changes arquivados são registro histórico do que foi decidido *à época*.
Reescrevê-los retroativamente falsifica o registro e quebra a rastreabilidade das
citações `(Dx)` que o código faz. O mesmo vale para os rascunhos em `docs/history/`.
O nome antigo permanecer lá é correto, não é dívida.

*Exceção:* `openspec/specs/identidade-visual/spec.md` é spec consolidada **viva** —
mas é atualizada pelo `openspec archive` deste change a partir do delta, não editada à
mão.

## Risks / Trade-offs

- **Uma superfície esquecida** (ex.: `metadata.title`, que não é JSX e não aparece em
  varredura visual) → após a implementação, `grep -rn "SETES.DOCS"` limitado a `apps/`,
  `packages/` e `infra/` deve retornar **zero**. É a verificação de fechamento, e é
  barata.
- **Teste E2E ou Vitest afirmando o texto antigo quebra silenciosamente até o CI** →
  varrer `apps/web/e2e/` e os `*.test.tsx` por "SETES" antes de rodar a suíte;
  `01-setup-login.spec.ts` é o candidato mais provável.
- **Esquecer `pnpm gen:types`** → mitigado por D3 elevando a regeneração a tarefa
  própria, com `gen:types:check` local antes do push.
- **Trade-off aceito: nome do repositório e recursos GCP continuam `setes.docs`.**
  Fica uma divergência entre o nome do produto e a infraestrutura que o serve. É
  deliberado — renomear recurso Terraform implica destroy/create em produção, e o
  ganho é cosmético num artefato que só a equipe técnica vê.
- **E-mails já enviados mantêm o assunto antigo.** Usuários com histórico verão as duas
  marcas na caixa de entrada durante um tempo. Sem mitigação possível nem necessária.

## Migration Plan

Não há migration de banco, de dados nem de contrato de rota. O deploy é o do
repositório (`deploy.yml` em push para `main`), sem passo extra.

**Rollback:** reverter o merge. Como nenhum estado persistido muda — sem migration,
sem alteração de payload, sem novo campo — o rollback é imediato e sem efeito
colateral. E-mails enviados na janela entre deploy e rollback mantêm o assunto novo;
isso é inconsequente.

**Ordem sugerida:** `apps/api` (incluindo a regeneração de tipos) antes de `apps/web`,
para que o snapshot de tipos e o código do backend nunca fiquem dessincronizados numa
etapa intermediária. Dentro de um único merge `--no-ff`, porém, a ordem dos commits é
higiene de revisão, não requisito técnico.
