## Why

A tela de Processos hoje oferece apenas o quadro Kanban, com colunas de fundo
cinza uniforme e cards enxutos (número, assunto, unidade e prazo). Uma versão
anterior do software já entregava uma visualização mais rica e reconhecida pelos
usuários — alternância entre **Kanban** e **Lista**, colunas com cores por
status, e cards com tipo de processo, unidade por extenso e data de criação.
Este change reconstitui aquela experiência sobre a máquina de estados e o
contrato atuais.

## What Changes

- **Alternância de visualização Kanban ↔ Lista** na tela de Processos, com toggle
  no cabeçalho. A Lista renderiza os mesmos processos como linhas empilhadas, com
  a *pill* de status alinhada à direita.
- **Colunas do Kanban coloridas por status**: Aberto (azul), Em Tramitação
  (âmbar), Concluído (verde), Arquivado (cinza) — hoje todas cinza.
- **Cards enriquecidos** (Kanban e Lista): passam a exibir **tipo do processo**
  (badge), **unidade atual por extenso** (nome completo, para todos os perfis, não
  só sigla no Gestor) e **"Criado em dd/mm/aaaa hh:mm"**. Indicador de sigilo
  permanece o cadeado 🔒 já existente (sem *pill* de nível).
- **Contador corrigido** no cabeçalho: `{n} processo(s)` refletindo o total real.
- **Filtro**: mantém-se **apenas o filtro por unidade** (Gestor, US 2.8). Sem
  barra de busca livre, sem filtros de Status/Nível, sem "Documentos" nem
  "Avançados".
- **Contrato do card** (`CardProcessoResponse`) ganha três campos aditivos:
  `tipo_processo_nome`, `unidade_atual_nome`, `criado_em`. Mudança **não-breaking**
  (campos adicionais); exige `pnpm gen:types` + commit de `packages/api-types`.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: a tela de Processos e o card já existem. -->

### Modified Capabilities
- `quadro-kanban`: o requisito do card passa a incluir tipo de processo, unidade
  por extenso e data de criação; introduz-se o **modo de visualização Lista** como
  alternativa ao Kanban; formaliza-se a **cor por coluna de status** e o
  **contador de processos**. Filtro segue restrito a unidade (Gestor).

## Impact

- **Backend** (`apps/api`): `app/schemas/processo.py` — `CardProcessoResponse` +
  `.de()` carregando `tipo_processo` e `unidade_atual` (relationships/join). Sem
  novas tabelas, migrations, segredos no Secret Manager ou buckets. Nenhum dado
  pessoal (CPF/CNPJ, nome de interessado) é adicionado ao card — tipo, unidade e
  data de criação não são dados pessoais, portanto **sem novo tratamento LGPD**.
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados via
  `pnpm gen:types` (CI `gen:types:check`).
- **Frontend** (`apps/web`): `app/processos/page.tsx` (toggle + Lista + colunas
  coloridas + cards + contador), `lib/processo-ui.ts` (cores por coluna, rótulos),
  `tailwind.config.ts` (tokens semânticos de cor por status). Teste de componente
  Vitest para o toggle Kanban/Lista e a renderização de colunas/badges.
- **Dependências**: requer `quadro-kanban` e `processos` já implementados
  (arquivados). Sem impacto na imutabilidade do histórico de tramitação.
