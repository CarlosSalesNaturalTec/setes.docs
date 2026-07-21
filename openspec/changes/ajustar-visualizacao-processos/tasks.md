## 1. Backend — enriquecer contrato do card (D1)

- [ ] 1.1 Adicionar `tipo_processo_nome: str`, `unidade_atual_nome: str` e `criado_em: datetime` a `CardProcessoResponse` em `apps/api/app/schemas/processo.py`
- [ ] 1.2 Atualizar `CardProcessoResponse.de()` para preencher os três campos a partir de `processo.tipo_processo.nome`, `processo.unidade_atual.nome` e `processo.criado_em`
- [ ] 1.3 Garantir eager loading de `tipo_processo` e `unidade_atual` nas consultas de `listar_kanban` e `buscar` (`app/services/processo_consulta.py`) para evitar N+1
- [ ] 1.4 Atualizar/estender os testes de `listar_kanban`/`buscar` para cobrir os novos campos do card e validar ausência de N+1

## 2. Contrato de tipos (gen:types)

- [ ] 2.1 Rodar `pnpm gen:types` na raiz
- [ ] 2.2 Commitar `packages/api-types/openapi.json` e `packages/api-types/schema.ts` atualizados
- [ ] 2.3 Confirmar `pnpm gen:types:check` verde (sem drift)

## 3. Frontend — tokens e utilitários de UI (D3)

- [ ] 3.1 Adicionar tokens semânticos de cor por status em `apps/web/tailwind.config.ts` (`status.aberto` azul, `status.tramitacao` âmbar, `status.concluido` verde, `status.arquivado` cinza)
- [ ] 3.2 Centralizar o mapeamento status→classe (cabeçalho de coluna e pill) em `apps/web/lib/processo-ui.ts`, junto de `COLUNAS_KANBAN`
- [ ] 3.3 Adicionar helper de formatação de data de criação ("Criado em dd/mm/aaaa hh:mm") em `lib/processo-ui.ts`

## 4. Frontend — cards e Kanban colorido

- [ ] 4.1 Atualizar `CardProcesso` em `app/processos/page.tsx` para exibir tipo (badge), unidade por extenso, data de criação e manter o indicador 🔒 para sigilosos
- [ ] 4.2 Aplicar cor por coluna nos cabeçalhos do Kanban usando os tokens de `processo-ui.ts`, preservando ordenação por prazo e destaque de vencidos
- [ ] 4.3 Corrigir o contador do cabeçalho para `{total} processo(s)` usando `resp.total`

## 5. Frontend — visualização em Lista (D2)

- [ ] 5.1 Adicionar estado de modo de visualização (`"kanban" | "lista"`, default Kanban, persistência opcional em localStorage) e o controle de toggle no cabeçalho
- [ ] 5.2 Implementar o render de Lista (linhas empilhadas: número, tipo, assunto, unidade por extenso, data de criação, 🔒 quando sigiloso, pill de status à direita) reutilizando a mesma resposta de `listarKanban`
- [ ] 5.3 Garantir que Lista e Kanban compartilham o mesmo escopo de visibilidade (nenhuma amplia o conjunto de cards) e as mensagens de vazio corretas

## 6. Testes e verificação

- [ ] 6.1 Teste de componente Vitest para o toggle Kanban↔Lista e a renderização de colunas coloridas/badges/contador em `app/processos/page.test.tsx`
- [ ] 6.2 Rodar `pnpm --filter @setes/web typecheck` e `pnpm --filter @setes/web test`
- [ ] 6.3 Rodar `uv run ruff check .` e `uv run pytest` em `apps/api`
