## 1. Migration / Schema

- [ ] 1.1 Adicionar valor `acesso_auditoria` à enum `TipoEventoLog` em `db/models.py`.
  *Aceite:* a enum expõe `ACESSO_AUDITORIA = "acesso_auditoria"`; nenhum outro valor alterado.
- [ ] 1.2 Criar migration Alembic que emite `ALTER TYPE ... ADD VALUE 'acesso_auditoria'`
  isolado e idempotente (checa existência antes de adicionar), fora de bloco transacional,
  seguindo o padrão das migrations de enum já existentes no repo.
  *Aceite:* `alembic upgrade head` aplica em banco limpo e em banco já com o change de
  auditoria; `alembic downgrade` documentado como no-op seguro (valor aditivo órfão).

## 2. Backend — Acesso de auditoria ao processo (US 9.1)

- [ ] 2.1 Ajustar `_exigir_acesso_ao_processo` em `routers/processos.py` para o ramo
  `usuario.pode_auditar` (D1): concede acesso independentemente da unidade.
  *Aceite:* auditor com `pode_auditar=true` lê processo de outra unidade e sigiloso.
- [ ] 2.2 Implementar a mensagem específica de rejeição para sigiloso-sem-permissão (D2):
  `"Acesso restrito — solicite autorização ao Administrador"`, distinta de
  `MSG_ACESSO_NEGADO_PROCESSO`, com registro `acesso_negado` em `log_seguranca`.
  *Aceite:* sigiloso fora do escopo sem permissão → 403 com a mensagem do PRD + log; processo
  comum fora do escopo → 403 com a mensagem genérica.
- [ ] 2.3 Registrar `acesso_auditoria` em `log_seguranca` apenas quando a permissão viabiliza
  o acesso (fora da unidade) — não quando o auditor já teria acesso pela unidade (D3).
  *Aceite:* INSERT imutável com usuário auditor, processo e data/hora; leitura na própria
  unidade não gera o evento.
- [ ] 2.4 Garantir que a leitura de documentos (`routers/documentos.py`) e de histórico
  (`/{id}/historico`) compartilha o mesmo seam ajustado, liberando o auditor.
  *Aceite:* auditor baixa/visualiza documentos e histórico de processo de outra unidade.
- [ ] 2.5 **(teste automatizado — obrigatório: toca `log_seguranca` e dado pessoal)** pytest
  cobrindo: auditor lê processo/histórico/documentos de outra unidade + sigiloso (200);
  não-auditor em sigiloso fora do escopo (403 + mensagem do PRD + `acesso_negado`);
  não-auditor em processo comum fora do escopo (403 mensagem genérica); registro
  `acesso_auditoria` presente só no acesso destravado e ausente na leitura da própria unidade.
  *Aceite:* testes verdes; asserts sobre a linha de `log_seguranca` em cada caso.

## 3. Backend — Relatório consolidado (US 9.2)

- [ ] 3.1 Criar `services/relatorio_auditoria.py` com as agregações (D4/D5): total de
  processos no período (por `criado_em`), tempo médio de tramitação (concluídos no período,
  dias corridos `concluido_em − criado_em`) e lista com status e unidade atual.
  *Aceite:* funções puras testáveis, parametrizadas por período/unidade(s)/tipo; tempo médio
  `None` quando não há concluídos.
- [ ] 3.2 Criar schemas Pydantic `RelatorioAuditoriaResponse`, item de lista e filtros.
  *Aceite:* status na lista é a enum `StatusProcesso` (máquina de estados), nunca string livre.
- [ ] 3.3 Criar `routers/auditoria.py` com `GET /auditoria/relatorio` guardado por dependência
  que exige `pode_auditar=true` (D6), com filtros período/unidade/tipo; montar em `main.py`.
  *Aceite:* auditor recebe consolidado; não-auditor recebe 403 + `acesso_negado`; filtros sem
  resultado retornam sinalização de vazio para a UI ("Nenhum dado encontrado...").
- [ ] 3.4 **(teste automatizado — obrigatório: toca dado pessoal e `log_seguranca`)** pytest do
  relatório: geração com filtros e totais/tempo médio corretos; estado vazio; tempo médio
  `None` com processos mas sem concluídos; 403 + `acesso_negado` para não-auditor.
  *Aceite:* testes verdes cobrindo os quatro casos.

## 4. Contrato frontend↔backend

- [ ] 4.1 Regenerar o snapshot do contrato: `pnpm gen:types`.
  *Aceite:* `pnpm gen:types:check` passa; `packages/api-types` inclui a rota de relatório e
  os novos schemas.

## 5. Frontend — Relatório de auditoria (US 9.2)

- [ ] 5.1 Criar rota autenticada `apps/web/app/auditoria/relatorios/page.tsx` com formulário
  de filtros (período/unidade/tipo), consumindo a rota via `lib/api.ts` tipado (sem `any`).
  *Aceite:* filtros disparam a busca e renderizam total, tempo médio e lista com status/unidade.
- [ ] 5.2 Implementar o estado vazio exibindo `"Nenhum dado encontrado para os filtros
  informados"` e o "—" para tempo médio ausente.
  *Aceite:* filtro sem resultado mostra a mensagem; concluídos ausentes mostram "—".
- [ ] 5.3 Restringir a rota/navegação a usuários com `pode_auditar` (gate em
  `auth-provider`/`protected-shell` ou navegação).
  *Aceite:* usuário sem permissão não vê o item de menu e é bloqueado ao acessar a URL direta.
- [ ] 5.4 **(teste unit/RTL)** vitest cobrindo render do relatório com dados, estado vazio e
  ocultação para usuário sem permissão.
  *Aceite:* testes verdes.

## 6. E2E Playwright — acesso de auditoria (fluxo de visibilidade crítico)

- [ ] 6.1 E2E do acesso de auditoria a processo sigiloso: auditor autorizado abre um processo
  sigiloso de outra unidade e vê o conteúdo completo; usuário sem permissão recebe a mensagem
  `"Acesso restrito — solicite autorização ao Administrador"`.
  *Aceite:* ambos os caminhos (concedido / negado) passam no Playwright.
- [ ] 6.2 E2E do relatório consolidado: auditor gera relatório com filtros e vê o consolidado;
  filtro sem resultado exibe a mensagem de vazio.
  *Aceite:* fluxo verde ponta a ponta (api+web contra Postgres local).

## 7. Verificação final

- [ ] 7.1 Rodar `openspec validate auditoria-e-relatorios` e os checks locais (`uv run pytest`,
  `ruff check .`, `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`,
  `pnpm gen:types:check`).
  *Aceite:* validação do change sem erros; suíte e checks verdes.
