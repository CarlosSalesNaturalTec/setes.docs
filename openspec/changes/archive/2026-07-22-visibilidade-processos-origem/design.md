## Context

A visibilidade da tela de Processos deriva hoje exclusivamente de
`Processo.unidade_atual_id` (`services/processo_consulta.py::unidades_visiveis`
+ `listar_kanban`/`buscar`). O detalhe do processo é liberado por
`_exigir_leitura_ao_processo` (unidade atual OU `pode_auditar`); a escrita por
`_exigir_acesso_ao_processo` (unidade atual, estrita). Despachado o processo,
a unidade de origem perde Kanban e detalhe — resta o "Meu Perfil" (metadados).

Fatos que simplificam o design:

- `Processo.unidade_origem_id` **já existe** como coluna (FK para `unidade`),
  preenchida na criação — não há migration de dado.
- O backend já bloqueia toda escrita fora da unidade atual; o "read-only" é
  garantido por construção, o trabalho é liberar leitura e ajustar UI.
- O front já tem um modo read-only de tela (Administrador,
  `13-admin-readonly-processos`) para reutilizar.
- O card já foi enriquecido por change anterior com campos aditivos + regeneração
  de tipos (`ajustar-visualizacao-processos`) — mesmo procedimento aqui.

## Goals / Non-Goals

**Goals:**

- Kanban/Lista com escopo `unidade_atual ∪ unidade_origem`, read-only fora da
  unidade atual, sem sigilosos fora da unidade atual.
- Busca interna (US 2.7) com o **mesmo** escopo — Kanban, Lista e busca nunca
  divergem sobre o que é visível.
- Leitura do detalhe/histórico liberada para o escopo da unidade de origem
  (exceto sigiloso), mantendo negação + `log_seguranca` nos demais casos.
- Destaque de devolução calculado do histórico imutável (sem estado novo).
- Checkbox "Exibir concluídos e arquivados" (default desmarcado, todos os
  perfis).
- Revisão do PRD US 1.4 Cen.1.

**Non-Goals:**

- Nenhuma mudança em consulta pública, notificações (Épico 5 já cobre aviso de
  devolução), permissão de auditoria, regras de sigilo ou máquina de estados.
- Nenhum estado de "visto/não visto" para o destaque de devolução.
- Nenhuma mudança na escrita (despacho/devolução/sigilo/documentos seguem
  estritos à unidade atual).
- Sem paginação nova na tela (mantém página única de até 50 como hoje).

## Decisions

### D1 — Escopo por `unidade_origem_id`, com sigilo restrito à unidade atual

`listar_kanban` e `buscar` passam a filtrar:

```
(unidade_atual_id IN escopo)
OR (unidade_origem_id IN escopo AND sigiloso = false)
```

`unidades_visiveis` permanece intocada (é reutilizada por outros consumidores).
A exclusão de sigilosos fica **dentro do ramo de origem**: o sigiloso na própria
unidade atual continua aparecendo com 🔒, como hoje. Alternativa rejeitada:
derivar a origem da primeira etapa do roteiro ou da primeira tramitação — a
coluna denormalizada já existe e é imutável após a criação.

### D2 — `somente_leitura` calculado no backend, por usuário

`CardProcessoResponse` ganha `somente_leitura: bool` =
`unidade_atual_id ∉ escopo(usuario)` (para Administrador, `False` — a UI dele
já é read-only por perfil). Calcular no backend evita que o front precise
conhecer a lista de unidades geridas do Gestor. O **detalhe** não ganha campo
novo: o front decide o modo leitura comparando `processo.unidade_atual_id` com
a unidade do Servidor (Gestor/Admin já não têm controles de ação — são
exclusivos do perfil Servidor).

### D3 — `devolvido` derivado do último evento do histórico

`devolvido: bool` no card = o **último** evento de `tramitacao` do processo é
`DEVOLUCAO` **e** `unidade_atual_id ∈ escopo(usuario)`. Sem coluna nova, sem
UPDATE — o destaque "apaga" sozinho quando o próximo despacho insere novo
evento (histórico imutável preservado). Implementação: uma única consulta em
lote para a página de cards (`DISTINCT ON (processo_id) … ORDER BY processo_id,
criado_em DESC` sobre os ids da página), não N+1.

### D4 — Filtro de concluídos/arquivados no servidor (`incluir_finalizados`)

`GET /processos/kanban` ganha query param `incluir_finalizados: bool = false`.
Com `false`, a query exclui `status IN (concluido, arquivado)`. Alternativa
rejeitada (filtrar só no front): com o escopo ampliado, concluídos/arquivados
acumulam sem limite e passariam a consumir a página de 50 cards e a distorcer o
contador — filtrando no servidor, `total` e `mensagem_vazio` permanecem
corretos. O checkbox do front controla o param e persiste em `localStorage`
(`setes:processos:exibir-finalizados`), mesmo padrão da chave do modo
Kanban/Lista. Default `false` alinhado ao checkbox desmarcado. A busca (US 2.7)
não ganha o param — busca é pontual e continua retornando qualquer status.

### D5 — Leitura do detalhe pela unidade de origem

`_exigir_leitura_ao_processo` ganha um ramo: se
`tem_acesso_a_unidade(unidade_origem_id)` **e** o processo não é sigiloso,
libera leitura (detalhe, histórico, listagem/download de documentos seguem a
mesma primitiva de leitura). Ordem das checagens preservada: `pode_auditar`
primeiro (com log `acesso_auditoria`), depois unidade atual, depois origem;
sigiloso fora da unidade atual continua caindo em "Acesso restrito — solicite
autorização ao Administrador" com `acesso_negado` no log. A escrita
(`_exigir_acesso_ao_processo`) não muda.

### D6 — Apresentação: cinza para read-only, âmbar para devolvido

- Card/linha com `somente_leitura`: fundo acinzentado + opacidade reduzida
  (`bg-gray-100/opacity-75`) — o card segue clicável para o detalhe.
- Card/linha com `devolvido`: badge "↩ Devolvido" + borda esquerda âmbar de
  4px. Se também vencido, a borda vermelha de vencido prevalece (prazo é mais
  urgente) e o badge âmbar permanece.
- Os dois estados são mutuamente exclusivos por construção (`devolvido` exige
  processo na unidade; `somente_leitura` exige fora dela).

### D7 — Migration: índice em `unidade_origem_id`

Única migration Alembic do change (schema antes de endpoint): índice
`ix_processo_unidade_origem_id` em `processo.unidade_origem_id`, que passa a
ser filtro de toda montagem de Kanban. Sem mudança de dado.

### Fluxo principal

```
Servidor COFIN                web (/processos)             api
     │  abre a tela                │                        │
     │─────────────────────────────▶ GET /processos/kanban  │
     │                             │  ?incluir_finalizados=false
     │                             │────────────────────────▶
     │                             │   escopo: atual ∪ origem (sem sigiloso fora)
     │                             │   + devolvido/somente_leitura por card
     │                             │◀────────────────────────
     │  vê card acinzentado        │                        │
     │  (processo na AJUR)         │                        │
     │  clica no card              │                        │
     │─────────────────────────────▶ GET /processos/{id}    │
     │                             │────────────────────────▶
     │                             │   _exigir_leitura: origem ok, não sigiloso
     │                             │◀────────────────────────
     │  detalhe em modo leitura    │  (sem Despachar/Devolver/sigilo/anexos)
```

## Risks / Trade-offs

- [Processo marcado sigiloso na unidade de destino "some" do acompanhamento da
  origem sem aviso] → comportamento decidido em produto (sigilo prevalece);
  o evento de sigilo fica registrado no histórico, visível quando/se o sigilo
  for removido. Cenário explícito na spec.
- [Escopo ampliado aumenta o volume de cards da página única de 50] → o default
  `incluir_finalizados=false` corta a cauda longa (concluídos/arquivados);
  processos ativos simultâneos por unidade são poucos no órgão. Paginação real
  fica como evolução futura se necessário.
- [`somente_leitura` por usuário torna o card dependente do contexto da
  requisição] → já é o caso do próprio conjunto de cards (escopo por usuário);
  campo documentado como contextual no schema.
- [Front antigo (cache) sem o checkbox chamaria o endpoint sem o param e
  perderia concluídos/arquivados] → janela curta de deploy conjunto no
  monorepo; comportamento degradado é apenas visual e igual ao novo default.
- [PRD US 1.4 Cen.1 fica desatualizado se só a spec mudar] → a revisão do PRD é
  tarefa explícita do change, não follow-up.
