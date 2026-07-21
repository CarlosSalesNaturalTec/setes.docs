## Context

A tela de Processos (`apps/web/app/processos/page.tsx`) hoje renderiza somente o
Kanban, com colunas de fundo cinza uniforme e cards enxutos servidos por
`CardProcessoResponse` (número, assunto, `unidade_atual_id`, prazo, dias
restantes, `sigiloso`). Os nomes de unidade só são resolvidos para o Gestor, e
apenas como sigla. A versão anterior do software exibia mais informação por card
(tipo de processo, unidade por extenso, data de criação) e oferecia alternância
Kanban/Lista com colunas coloridas por status.

Restrições vigentes do projeto:
- O front **não escreve tipos de API à mão**: `apps/api` é a fonte da verdade e
  `pnpm gen:types` regenera `packages/api-types` (CI `gen:types:check`). Qualquer
  campo novo no card exige regenerar e commitar o contrato.
- A máquina de estados (`aberto → em_tramitacao → concluido → arquivado`) é
  explícita; cor por coluna é atributo de UI, não altera estado.
- Tokens de tema em `tailwind.config.ts` hoje cobrem só `navy` e `superficie`.

## Goals / Non-Goals

**Goals:**
- Reconstituir a experiência da versão anterior: toggle Kanban/Lista, colunas
  coloridas, cards com tipo, unidade por extenso e data de criação, contador
  correto.
- Enriquecer o contrato do card de forma **aditiva** (não-breaking), mantendo a
  camada tipada `api.ts` sem `any`.
- Reaproveitar a máquina de estados, a ordenação por prazo e o escopo de
  visibilidade por unidade/perfil já existentes.

**Non-Goals:**
- Barra de busca livre, filtros de Status/Nível, botões "Documentos" e
  "Avançados" da versão antiga (fora de escopo — só o filtro por unidade permanece).
- *Pill* colorida de nível (Público/Restrito): mantém-se o cadeado 🔒 atual.
- Drag-and-drop no Kanban (segue read-only, transições só por ações explícitas).
- Qualquer mudança no endpoint `/processos/busca` ou paginação.

## Decisions

### D1 — Enriquecer `CardProcessoResponse` com 3 campos aditivos
Adicionar `tipo_processo_nome: str`, `unidade_atual_nome: str` e
`criado_em: datetime` ao schema e ao builder `.de()` em
`apps/api/app/schemas/processo.py`. O builder passa a depender de
`processo.tipo_processo` e `processo.unidade_atual` (nome por extenso), então a
consulta `listar_kanban`/`buscar` em `processo_consulta` deve carregar essas
relações com `joinedload`/`selectinload` para evitar N+1.

- **Por que aditivo e não um novo schema?** Mantém uma única forma de card para
  Kanban, Lista e busca; consumidores atuais não quebram; `KanbanResponse` não
  muda de envelope.
- **Alternativa descartada:** resolver os nomes no front via `listarUnidades` +
  `listarTiposProcesso`. Rejeitada: multiplica chamadas, só funciona para perfis
  com acesso a essas listagens (Gestor), e o nome da unidade por extenso passa a
  ser necessário para **todos** os perfis.

### D2 — Toggle Kanban/Lista como estado de UI (client-side), sem nova rota
O modo de visualização é `useState<"kanban" | "lista">("kanban")` na página, com
persistência opcional em `localStorage`. Ambos os modos consomem a **mesma**
resposta de `listarKanban` já carregada — a Lista é só outra projeção do mesmo
array de cards.

- **Por que não duas rotas/telas?** Os dados e o escopo de visibilidade são
  idênticos; separar em rotas duplicaria carregamento e lógica de autorização.
- **Consequência:** o requisito de "acesso negado" do Kanban consolidado vale
  automaticamente para a Lista, pois nenhuma das visões amplia o conjunto de
  cards retornado pelo backend.

### D3 — Cores por status como tokens semânticos em Tailwind
Estender `tailwind.config.ts` com tokens por status (ex.: `status.aberto`,
`status.tramitacao`, `status.concluido`, `status.arquivado`) e centralizar o
mapeamento status→classe em `lib/processo-ui.ts` (junto de `COLUNAS_KANBAN`), em
vez de espalhar `bg-amber-100`/`bg-green-100` pelos componentes. A mesma tabela
alimenta o cabeçalho da coluna no Kanban e a *pill* de status na Lista.

- **Por que tokens semânticos?** Um único ponto de verdade para a paleta de
  status; consistência entre Kanban e Lista; troca de cor sem caçar literais.
- **Alternativa descartada:** cores literais inline por componente — divergem com
  o tempo e dificultam manter Kanban e Lista alinhados.

### D4 — Contador derivado do total real
O cabeçalho passa a exibir `{total} processo(s)` usando `resp.total` de
`KanbanResponse` (já retornado pelo backend), corrigindo o "5 de 0 processo(s)"
da versão antiga.

## Risks / Trade-offs

- **[Contrato desatualizado quebra o CI]** → após D1, rodar `pnpm gen:types` e
  commitar `packages/api-types/{openapi.json,schema.ts}` no mesmo change; o job
  `types-drift` falha caso contrário.
- **[N+1 ao carregar tipo/unidade por card]** → usar eager loading
  (`joinedload`) na consulta do Kanban/busca; validar contagem de queries no
  teste de backend.
- **[Cores de status podem colidir com destaque de vencido]** → o destaque de
  vencido (barra vermelha 4px + negrito) é atributo do **card**, ortogonal à cor
  da **coluna/pill de status**; manter camadas separadas para não ofuscar o alerta
  de prazo.
- **[Contraste/acessibilidade das cores de status]** → escolher tons com
  contraste suficiente (texto legível sobre o fundo do cabeçalho e da *pill*),
  seguindo `identidade-visual`.

## Migration Plan

1. Backend: adicionar campos ao schema + `.de()` e eager loading na consulta;
   atualizar/estender teste de `listar_kanban` para cobrir os novos campos.
2. `pnpm gen:types` + commit de `packages/api-types`.
3. Frontend: tokens em `tailwind.config.ts`; mapeamento de cores + rótulos em
   `lib/processo-ui.ts`; toggle, Lista, colunas coloridas, cards e contador em
   `app/processos/page.tsx`; teste Vitest do toggle e da renderização.
4. Deploy padrão (Cloud Run); rollback = reverter o merge — mudança puramente
   aditiva no contrato e de apresentação no front, sem migration de banco.

## Open Questions

- Persistir o modo de visualização escolhido (localStorage) entre sessões, ou
  sempre abrir em Kanban? (Assumido: default Kanban, persistência opcional — não
  bloqueia a implementação.)
