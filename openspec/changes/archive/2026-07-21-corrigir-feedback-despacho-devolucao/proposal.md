## Why

Em produção, ao despachar (ou devolver) um processo, o Servidor vê a mensagem
**"Acesso negado — você não tem permissão para visualizar este processo"** e o
processo some do Kanban da sua unidade — como se a ação tivesse **falhado**. Na
verdade o despacho/devolução foi **concluído com sucesso**: o processo mudou de
`unidade_atual_id` e legitimamente saiu do escopo do Servidor de origem. A falsa
mensagem de erro vem de uma releitura indevida do processo logo após a ação
(`GET /processos/{id}` → 403), engolida como erro de carregamento no front. O
resultado é perda de confiança do usuário numa das ações mais frequentes do
sistema (RNF de usabilidade: despachar em ≤ 2 cliques). Ocorrido com o processo
2026/000007 no ambiente GCP.

## What Changes

- **Correção de UX front-only** em `apps/web/app/processos/[id]/page.tsx`: após
  `despachar()` e `devolver()`, o front passa a usar a `ProcessoResponse`
  retornada pela própria ação em vez de re-buscar o processo com `carregar()`.
- **Inferência de saída de escopo por mudança de unidade**: compara o
  `unidade_atual_id` que estava em tela (antes da ação) com o retornado pela
  resposta. Se **mudou**, o processo saiu do escopo do Servidor → exibe
  confirmação de sucesso nomeando a unidade de destino e navega para o Kanban
  (`/processos`), **sem** re-buscar o detalhe (que hoje causa o 403 espúrio).
- **Permanência em tela quando o processo continua no escopo**: se o
  `unidade_atual_id` **não mudou** (ex.: conclusão na própria unidade — status
  `concluido` — ou roteiro de unidade única), atualiza o processo em tela com a
  resposta e recarrega apenas o histórico, como hoje.
- **Cobre despacho (US 2.2) e devolução (US 2.2b)**, que hoje têm exatamente o
  mesmo defeito (ambos chamam `carregar()` após a ação bem-sucedida).
- **Nenhuma mudança na autorização por processo**: a autorização por unidade
  (`_exigir_leitura_ao_processo`, `require_acesso_unidade`) está correta conforme
  a spec — negar leitura de um processo fora do escopo é o comportamento previsto
  (US 1.4 Cen.2).
- **Ajuste pontual de autorização em `GET /unidades`** (descoberto durante a
  implementação, ver `design.md`): o catálogo de unidades (nome/sigla/ativo, dado
  não sensível) era restrito a Administrador/Gestor/auditor, o que fazia
  `nomeUnidade()` no front cair para o UUID bruto quando um Servidor comum tentava
  resolver o nome de uma unidade — inclusive hoje, no campo "Unidade atual" e no
  histórico, não só na confirmação de sucesso desta correção. `GET /unidades`
  passa a exigir apenas autenticação (`get_current_user`); cadastro, edição,
  desativação e reativação de unidade continuam restritos ao Administrador. O
  contrato OpenAPI (rota, schema de resposta) não muda — não é necessário
  `pnpm gen:types`.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `workflow-tramitacao`: adiciona requisito de **feedback ao Servidor após
  despacho/devolução bem-sucedidos** — a ação que remove o processo do escopo da
  unidade SHALL ser comunicada como sucesso (com a unidade de destino), nunca
  como erro de acesso. Refina os cenários de despacho (US 2.2) e devolução
  (US 2.2b) com o pós-ação observável no cliente.
- `unidades-administrativas`: adiciona requisito de **leitura do catálogo de
  unidades por qualquer usuário autenticado** (`GET /unidades`) — descoberto
  durante a implementação (design.md, Decisão 4): a restrição anterior
  (Administrador/Gestor/auditor) impedia o Servidor de resolver nomes de
  unidade no front. Gestão (cadastro/edição/desativação/reativação) continua
  Administrador-only.

## Impact

- **Código afetado**: frontend —
  `apps/web/app/processos/[id]/page.tsx` (funções `despachar` e `devolver`;
  estado de confirmação de sucesso e navegação via `useRouter`) e
  `apps/web/app/processos/page.tsx` (Kanban lê a confirmação de sucesso via
  query string). Teste de componente correspondente em
  `apps/web/app/processos/[id]/page.test.tsx` e `apps/web/app/processos/page.test.tsx`,
  e o fluxo E2E `apps/web/e2e/05-processos-despacho.spec.ts`. Backend —
  `apps/api/app/routers/unidades.py` (`GET /unidades` passa a exigir apenas
  autenticação, ver Decisão 4 do `design.md`) e
  `apps/api/tests/test_listagens_frontend.py`.
- **Backend / API / contrato OpenAPI**: rota e schema de `GET /unidades`
  inalterados (só a política de autorização muda); demais rotas inalteradas.
  Sem `pnpm gen:types`.
- **Banco de dados**: nenhuma tabela nova ou alterada; nenhuma migration.
- **Secret Manager / Cloud Storage**: sem novos segredos ou buckets.
- **LGPD**: sem novo tratamento de dados pessoais — a mudança é de fluxo de UI e
  não coleta, retém nem expõe CPF/CNPJ ou nome de interessado além do que já é
  exibido no detalhe do processo.
- **Dependências**: nenhuma nova; usa `next/navigation` (`useRouter`), já em uso.
- **Change anterior**: assume `processos-e-workflow` (arquivado) — os endpoints
  de despacho/devolução e a autorização por unidade já existem.
