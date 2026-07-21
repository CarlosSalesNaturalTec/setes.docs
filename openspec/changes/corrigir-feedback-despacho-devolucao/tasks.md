## 1. Correção do fluxo no cliente

- [ ] 1.1 Em `apps/web/app/processos/[id]/page.tsx`, capturar o `unidade_atual_id` anterior (a partir do `processo` em estado) antes de chamar `api.despacharProcesso`/`api.devolverProcesso`, e usar a `ProcessoResponse` retornada. **Aceite**: a resposta da ação é lida; nenhuma chamada a `carregar()` no caminho de sucesso que muda de unidade.
- [ ] 1.2 Implementar a inferência de saída de escopo: se `resposta.unidade_atual_id !== unidadeAnterior`, exibir confirmação de sucesso nomeando a unidade de destino (via `nomeUnidade`) e navegar para `/processos` com `useRouter().push`; **sem** re-buscar o detalhe. **Aceite**: despacho que move o processo para outra unidade não dispara `GET /processos/{id}` e não exibe "Acesso negado — você não tem permissão para visualizar este processo".
- [ ] 1.3 Implementar o caminho "permanece no escopo": se `resposta.unidade_atual_id === unidadeAnterior` (ex.: conclusão na própria unidade, status `concluido`), `setProcesso(resposta)` e recarregar apenas o histórico (`api.historicoProcesso(id)`), sem navegar. **Aceite**: conclusão na própria unidade mantém a tela de detalhes com status "Concluído" atualizado.
- [ ] 1.4 Aplicar a mesma correção a `devolver()` (US 2.2b): mesmo padrão de comparação de unidade, confirmação de sucesso nomeando a unidade de destino e navegação ao Kanban. **Aceite**: devolução que retorna o processo à unidade anterior mostra sucesso e leva ao Kanban, sem erro de acesso.
- [ ] 1.5 Preservar o tratamento do modal de conclusão (409) e dos erros reais: o `catch` que trata `ApiError.status === 409` (`promptConclusao`) e o `catch` de erro genérico permanecem; a lógica de sucesso/navegação roda apenas após o `await` da ação retornar 2xx. **Aceite**: cancelar a conclusão não navega nem mostra sucesso; um 403 real da própria ação exibe erro e permanece na tela.
- [ ] 1.6 Garantir que a confirmação de sucesso sobreviva à navegação para o Kanban (query param lido por `apps/web/app/processos/page.tsx`, store de UI, ou equivalente). **Aceite**: ao chegar ao Kanban após despacho, o usuário vê a confirmação de sucesso com a unidade de destino.

## 2. Testes de componente (Vitest + RTL)

- [ ] 2.1 Em `apps/web/app/processos/[id]/page.test.tsx`, adicionar teste: despacho cuja resposta muda `unidade_atual_id` → confirmação de sucesso exibida, `router.push('/processos')` chamado, `GET /processos/{id}` NÃO chamado após a ação, e a mensagem "Acesso negado — você não tem permissão para visualizar este processo" nunca aparece. **Aceite**: teste falha contra o código atual (regressão coberta) e passa com a correção.
- [ ] 2.2 Adicionar teste: conclusão na própria unidade (resposta com mesma `unidade_atual_id`, status `concluido`) → permanece na tela, status atualizado, histórico recarregado, sem navegação. **Aceite**: teste verde.
- [ ] 2.3 Adicionar teste para `devolver()`: resposta com `unidade_atual_id` alterado → sucesso + navegação; sem falso erro de acesso. **Aceite**: teste verde.
- [ ] 2.4 Adicionar teste de guarda: falha real da ação (mock rejeitando com 403) → mensagem de erro exibida, sem `router.push`, sem confirmação de sucesso; e 409 na última etapa → modal de conclusão exibido. **Aceite**: teste verde.

## 3. Teste E2E (Playwright) — fluxo crítico de despacho

- [ ] 3.1 Em `apps/web/e2e/05-processos-despacho.spec.ts`, estender/adicionar cenário: Servidor da unidade de origem despacha um processo para a próxima unidade do roteiro e observa confirmação de sucesso + Kanban sem o processo, **sem** a mensagem de acesso negado. **Aceite**: E2E passa contra api+web reais (Postgres local), reproduzindo o cenário do PRD US 2.2 Cen.1 do ponto de vista do cliente.
- [ ] 3.2 Adicionar cobertura E2E do caminho de conclusão na própria unidade (permanece na tela com status "Concluído") para garantir que a heurística não navega indevidamente. **Aceite**: E2E verde.

## 4. Verificação e fechamento

- [ ] 4.1 Rodar `pnpm --filter @setes/web typecheck` e `pnpm --filter @setes/web test`; rodar `cd apps/web && pnpm test:e2e` para o fluxo de despacho. **Aceite**: typecheck, unit e E2E verdes.
- [ ] 4.2 Confirmar que o backend, o contrato OpenAPI e `packages/api-types` **não** foram tocados (sem `pnpm gen:types`). **Aceite**: `git diff` sem alterações fora de `apps/web` e `openspec/`.
- [ ] 4.3 Validação manual pós-deploy no ambiente GCP com o processo 2026/000007 (ou equivalente): despachar e confirmar ausência da mensagem de acesso negado, presença da confirmação de sucesso e do processo na unidade de destino. **Aceite**: comportamento observado conforme a spec `workflow-tramitacao`.
