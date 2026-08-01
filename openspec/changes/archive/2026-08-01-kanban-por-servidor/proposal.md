## Why

O quadro de processos hoje é **por unidade**: o Servidor vê tudo o que está na
sua unidade (ampliado à unidade de origem pelo change
`visibilidade-processos-origem`). Na avaliação da primeira entrega o cliente
recusou esse recorte (`docs/Ajustes SETES DOCS.pdf`): *"ao logar como servidor
não mais exibir no kanban os processos relacionados à UNIDADE inteira"*.

O quadro passa a ser **pessoal**: o Servidor vê exclusivamente os processos que
lhe dizem respeito — os que criou e os que passaram por ele. Mas "meus
processos" não é uma lista homogênea: alguns estão **parados comigo esperando
minha ação**, outros seguiram adiante e eu apenas **acompanho**. O cliente pediu
essa distinção explicitamente. O Gestor mantém a visão por unidades geridas.

O documento traz junto três filtros de busca no quadro (tipo, assunto parcial,
data) e cinco cards de contagem no dashboard.

Este é o **terceiro** dos seis changes dos ajustes pós-avaliação e depende
diretamente de `tramitacao-manual`, que cria o conceito de servidor responsável.

## What Changes

- **Escopo do quadro do Servidor deixa de ser a unidade** e passa a ser o
  conjunto pessoal: processos em que sou o **responsável atual**, os que **criei**
  e aqueles pelos quais **já passei** (detentor em algum evento do histórico).
- **Distinção entre ação e acompanhamento**: o card ganha o atributo
  `acao_requerida` (sou o responsável atual). Cards de ação recebem destaque
  sólido; cards de acompanhamento são apresentados de forma discreta, com o nome
  do servidor que detém o processo.
- **Arquivados saem do padrão**: o checkbox existente "Exibir concluídos e
  arquivados" é desdobrado — **Concluídos passam a ser exibidos por padrão**
  (o cliente os quer no quadro pessoal) e **Arquivados ficam ocultos** até que o
  checkbox **"Exibir Arquivados"** seja marcado.
- **Três filtros novos** no quadro, combináveis entre si e com o checkbox:
  por **tipo de processo**, por **assunto** (busca de texto parcial) e por
  **data** (período de criação).
- **Gestor mantém o escopo por unidades geridas**, inclusive para arquivados —
  sua visão não estreita para o indivíduo.
- **Dashboard ganha cinco cards de contagem**: Total (Abertos + Em Tramitação +
  Concluídos + Arquivados), Abertos, Em Tramitação, Concluídos e Arquivados.
- **Autorização permanece por unidade** — apenas a *visão* estreita. Um colega da
  mesma unidade continua podendo abrir o processo pela busca ou por URL direta.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: o quadro e o dashboard já existem; o que muda são
seus requisitos de escopo, filtro e apresentação. -->

### Modified Capabilities

- `quadro-kanban`: o escopo do Servidor passa de unidade para conjunto pessoal
  (responsável ∪ criador ∪ participante histórico); card ganha `acao_requerida`
  e o nome do detentor atual; o checkbox de finalizados é desdobrado em
  "Exibir Arquivados"; três filtros novos (tipo, assunto parcial, data).
- `dashboard-kpis`: cinco cards de contagem por status, no topo do dashboard.

## Impact

- **Dependências**: requer `tramitacao-manual` (consome
  `processo.servidor_atual_id` e os campos de servidor em `tramitacao`) e os
  arquivados `ajustar-visualizacao-processos`, `visibilidade-processos-origem` e
  `dashboard-kpis-gestor`.
- **Tabelas PostgreSQL**: nenhuma tabela nova nem coluna nova. Apenas **índices**
  para sustentar o novo filtro de participação:
  `ix_tramitacao_servidor_destino` em `(servidor_destino_id, processo_id)` e
  `ix_tramitacao_servidor_origem` em `(servidor_origem_id, processo_id)`.
- **Migrations**: `0025_ix_tramitacao_servidores`.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket
  novo no Cloud Storage.
- **Backend** (`apps/api`): `services/processo_consulta.py` (`listar_kanban`,
  `buscar`, `atributos_contextuais` — escopo pessoal, `acao_requerida`, filtros),
  `services/dashboard.py` (contagens por status), `routers/processos.py` (query
  params dos filtros e de arquivados), `routers/dashboard.py`,
  `schemas/processo.py`, `schemas/dashboard.py`.
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados
  (`pnpm gen:types`; CI `gen:types:check`).
- **Frontend** (`apps/web`): `app/processos/page.tsx` (filtros, checkbox de
  arquivados, estilos de ação/acompanhamento), `lib/processo-ui.ts`,
  `app/dashboard/page.tsx` (cards de contagem).
- **LGPD**: nenhuma coleta nova de dado pessoal. O card passa a exibir o **nome
  do servidor** que detém o processo — dado pessoal de servidor já visível no
  histórico de tramitação para quem tem acesso ao processo, sem ampliação de
  escopo. O estreitamento do quadro **reduz** a exposição de dados pessoais de
  interessados, ao deixar de listar para o Servidor processos de colegas que ele
  não tocou. Por tocar visibilidade de dados pessoais, o change **exige** testes
  automatizados pytest, incluindo cenários de acesso negado.
- **PRD**: `docs/PRD.md` US 1.4, US 2.3 e US 2.8 atualizados — a regra de
  visibilidade por unidade no quadro deixa de valer para o Servidor.
