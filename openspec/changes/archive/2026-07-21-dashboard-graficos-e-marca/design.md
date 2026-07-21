## Context

O Dashboard do Gestor (US 6.1, capability `dashboard-kpis`) já expõe KPIs por
meio de `GET /dashboard/kpis` e dois drill-downs, todos calculados em
`app/services/dashboard.py` sobre a base de **processos ativos no escopo do
Gestor** — `resolver_escopo_gestor(db, gestor, unidade_id)` resolve as unidades
geridas (e valida `unidade_id`, levantando `EscopoNegado`), e `_query_ativos`
filtra Aberto + Em Tramitação. Toda rejeição de escopo grava `log_seguranca`.

Esta mudança acrescenta três agregações sobre **exatamente essa mesma base** e um
gráfico para cada, além de unificar a marca (favicon) no Login e na sidebar. O
contrato front-back é gerado do OpenAPI (`pnpm gen:types`), então qualquer rota
nova exige regenerar `packages/api-types`. O front hoje não tem biblioteca de
gráficos; o dashboard é feito de `<div>` + Tailwind.

## Goals / Non-Goals

**Goals:**
- Três distribuições de processos **ativos** do Gestor (por unidade, por tipo, por
  usuário/autor) reusando a base e o escopo já validados dos KPIs.
- Mesmo contrato de filtro (`unidade_id` opcional) e mesma semântica de acesso
  negado (403 + `log_seguranca`) dos KPIs.
- Marca institucional (favicon) no chip circular do Login e da sidebar, a partir
  de um único componente reutilizável.

**Non-Goals:**
- Não alterar os KPIs da US 6.1 nem seus drill-downs (as distribuições convivem,
  não substituem).
- Não introduzir novo agrupamento de tempo/série temporal — são contagens
  instantâneas de ativos.
- Não excluir processos sigilosos da contagem do Gestor (decisão de produto).
- Não redesenhar a identidade visual além da troca do glifo da marca.
- Nenhuma migration / mudança de esquema no banco.

## Decisions

### D1 — Reusar a base de ativos e o escopo do Gestor, sem recalcular
As três agregações partem de `resolver_escopo_gestor` + `_query_ativos` já
existentes, adicionando apenas `GROUP BY` sobre `unidade_atual_id`,
`tipo_processo_id` e `criado_por_id`. Assim a contagem das barras nunca diverge
dos KPIs (mesma fonte da verdade). *Alternativa descartada:* novas queries
independentes — duplicariam a definição de "ativo" e o filtro de escopo, com risco
de divergência.

### D2 — Endpoint único `GET /dashboard/distribuicoes`
Um só endpoint retorna as três listas em um `DistribuicoesResponse`, espelhando o
formato de `GET /dashboard/kpis` (perfil Gestor, `unidade_id` opcional,
`EscopoNegado`→403+`log_seguranca`). *Alternativa descartada:* três endpoints
separados — mais chamadas no front e três vezes a mesma resolução de escopo.
*Alternativa descartada:* estender `DashboardKpisResponse` — poluiria o contrato
da US 6.1 e misturaria duas histórias.

Formato:
```
DistribuicaoItem      = { rotulo: str, quantidade: int }
DistribuicoesResponse = {
  por_unidade: DistribuicaoItem[],   # rotulo = nome da unidade
  por_tipo:    DistribuicaoItem[],   # rotulo = nome do tipo_processo
  por_usuario: DistribuicaoItem[],   # rotulo = nome do usuario (criado_por)
}
```
Cada lista ordenada por `quantidade` desc. Sem processos ativos → listas vazias;
o estado vazio ("Nenhum dado disponível para o período") é decidido no front por
lista vazia, coerente com os KPIs.

### D3 — Agregação por chave no banco, resolução de nome em seguida
O `GROUP BY` roda por FK (`unidade_atual_id` / `tipo_processo_id` /
`criado_por_id`) com `func.count`; os nomes (`Unidade.nome`, `TipoProcesso.nome`,
`Usuario.nome`) são resolvidos por join ou lookup, no mesmo padrão de
`produtividade_por_unidade`. Como `unidade_atual_id` é NOT NULL na versão atual,
**não há bucket "Sem unidade"**.

### D4 — `recharts` para os gráficos
Barras horizontais com eixo, gridlines e rótulos de categoria (como na imagem de
referência) via `recharts` — componível, tipado, responsivo com
`ResponsiveContainer`. *Alternativa descartada:* SVG à mão — mais código para
eixos/labels/responsividade sem ganho. O componente de gráfico fica isolado em
`app/dashboard` e recebe `DistribuicaoItem[]`; o `/dashboard` faz uma 2ª chamada
`api.obterDashboardDistribuicoes` além da de KPIs. Cores das barras seguem os
tokens de marca (navy + paleta categórica já usada na UI).

### D5 — Marca única via `IconMarca`
O SVG do favicon (`app/icon.svg`) é extraído para `IconMarca` em
`components/icons.tsx` (onde já vivem os ícones do menu). Login e
`protected-shell` passam a renderizar `<IconMarca/>` dentro do chip circular
existente (`rounded-full`), removendo o literal "S". *Alternativa descartada:*
`next/image` do próprio `icon.svg` — pesado para um glifo inline e sem controle de
`currentColor`. Um único componente evita duplicar o markup entre as duas telas.

## Risks / Trade-offs

- **Cardinalidade alta em "por Usuário"/"por Tipo"** (muitas barras) → o gráfico
  pode ficar longo. *Mitigação:* ordenar por quantidade desc; se necessário,
  limitar visualmente aos N maiores no front (decisão de UI, não do contrato).
- **Nome de servidor exposto (LGPD)** no gráfico "por Usuário" → *Mitigação:*
  leitura agregada estritamente no escopo das unidades geridas do Gestor
  autenticado; sem nova coleta/persistência; teste de acesso negado obrigatório.
- **Drift de contrato** se esquecer `pnpm gen:types` → o CI (`gen:types:check`)
  falha; a task de regenerar `packages/api-types` é explícita.
- **Nova dependência de bundle (`recharts`)** no `apps/web` → aceitável dado o
  ganho; isolada ao dashboard (import só na página que usa).
- **Contraste da marca** — o favicon já tem fundo navy próprio; dentro do chip
  branco do Login e do chip da sidebar convém checar o contorno. *Mitigação:*
  validar visualmente nos dois fundos ao aplicar.

## Migration Plan

Sem migration de banco. Deploy segue o fluxo normal (back primeiro para o novo
endpoint, `pnpm gen:types` commitado, depois front). Rollback = reverter o commit;
nenhum estado persistente é criado. A marca é puramente de apresentação e pode ser
revertida isoladamente das mudanças de dashboard.

## Open Questions

- Limitar "por Usuário"/"por Tipo" aos N maiores grupos no front? (default: exibir
  todos, ordenados desc — decidir só se a lista ficar longa na prática).
