## Why

O Dashboard do Gestor (US 6.1) hoje entrega apenas KPIs numéricos e listas —
falta uma visão consolidada da **distribuição da carga de trabalho** (quantos
processos ativos por unidade, por tipo e por usuário responsável), que o Gestor
precisa para enxergar concentração e desbalanceamento entre suas unidades. Em
paralelo, a marca do produto aparece como a letra "S" em um chip circular no
Login e na navegação, divergindo do ícone institucional já usado no favicon
(`apps/web/app/icon.svg`); unificar essa marca elimina a inconsistência visual.

## What Changes

**Frente A — Gráficos de distribuição no Dashboard (nova US 6.2, Épico 6)**
- Novo endpoint `GET /dashboard/distribuicoes` (Gestor), com o mesmo filtro
  `unidade_id` opcional dos KPIs, retornando três agregações de **processos
  ativos** (Aberto + Em Tramitação) no escopo do Gestor:
  - **por Unidade** (agrupado por `unidade_atual_id` → nome da unidade)
  - **por Tipo** (agrupado por `tipo_processo_id` → nome do tipo)
  - **por Usuário/autor** (agrupado por `criado_por_id` → nome do usuário)
- Escopo restrito às unidades geridas do Gestor; `unidade_id` fora do escopo →
  **403 + `log_seguranca` (`acesso_negado`)**, reusando `resolver_escopo_gestor`.
- Processos **sigilosos entram na contagem** para o Gestor (sem filtro extra —
  mesmo comportamento dos KPIs atuais).
- Front: `/dashboard` renderiza três gráficos de barras horizontais **abaixo**
  dos KPIs (não substitui a US 6.1), com estado vazio "Nenhum dado disponível
  para o período".

**Frente B — Marca institucional (modifica `identidade-visual`)**
- Substituir a letra "S" pelo **ícone do favicon**, **mantendo o chip circular**,
  no Login (`app/login/page.tsx`) e na sidebar (`components/protected-shell.tsx`).
- Extrair o SVG para um componente reutilizável `IconMarca`
  (`components/icons.tsx`) usado nos dois chips (sem duplicar markup).

## Capabilities

### New Capabilities
- `dashboard-distribuicoes`: gráficos de distribuição de processos ativos do
  Gestor por unidade, por tipo e por usuário/autor, no escopo das unidades
  geridas, com filtro por unidade e cenário de acesso negado explícito (US 6.2).

### Modified Capabilities
- `identidade-visual`: a marca no chip do Login e da sidebar passa a exibir o
  ícone institucional do favicon em vez da letra "S" (chip circular preservado).

## Impact

- **Backend** (`apps/api`):
  - `app/services/dashboard.py`: novas agregações `distribuicao_por_unidade`,
    `distribuicao_por_tipo`, `distribuicao_por_usuario` sobre a base de ativos
    (`_query_ativos` / `resolver_escopo_gestor`) — sem duplicar cálculo.
  - `app/schemas/dashboard.py`: `DistribuicaoItem` + `DistribuicoesResponse`.
  - `app/routers/dashboard.py`: rota `GET /dashboard/distribuicoes`
    (perfil Gestor, `unidade_id` opcional, `EscopoNegado`→403+log).
- **Contrato**: `pnpm gen:types` + commit de `packages/api-types`
  (`openapi.json` + `schema.ts`).
- **Frontend** (`apps/web`): nova dependência **`recharts`**; `app/dashboard/
  page.tsx` faz 2ª chamada (`api.obterDashboardDistribuicoes`) e renderiza os
  três `BarChart`; `components/icons.tsx` ganha `IconMarca`; edição de
  `app/login/page.tsx` e `components/protected-shell.tsx`.
- **Banco de dados**: nenhuma tabela nova ou migration — só leitura agregada de
  `processo` (FKs já existentes: `unidade_atual_id`, `tipo_processo_id`,
  `criado_por_id`). Sem novo segredo no Secret Manager nem bucket no Storage.
- **LGPD**: o gráfico "por Usuário" exibe **nome de servidor** (dado pessoal).
  Tratamento: apenas leitura agregada, restrita ao escopo das unidades geridas
  do Gestor autenticado; nenhuma nova coleta, retenção ou persistência de dado
  pessoal — os nomes já existem em `usuario`. Exige **teste automatizado**,
  incluindo o cenário de acesso negado (unidade fora do escopo).
- **Dependência**: requer `dashboard-kpis` (US 6.1) e `controle-acesso-por-
  unidade` já em vigor (reusa escopo do Gestor e `log_seguranca`).
