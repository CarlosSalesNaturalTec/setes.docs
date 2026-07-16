## 1. Schema e migrations (Alembic — antes dos endpoints)

- [x] 1.1 Adicionar coluna `pode_auditar: Mapped[bool]` (`BOOLEAN NOT NULL DEFAULT false`) ao modelo `Usuario` em `apps/api/app/db/models.py`. Critério: modelo reflete a coluna; sem backfill necessário.
- [x] 1.2 Adicionar os valores `PERMISSAO_AUDITORIA_CONCEDIDA`, `PERMISSAO_AUDITORIA_REVOGADA` e `USUARIO_DESATIVADO` ao enum `TipoEventoLog`. Critério: enum Python inclui os três novos valores.
- [x] 1.3 Criar migration Alembic: `ALTER TABLE usuario ADD COLUMN pode_auditar ...` + `ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS ...` para os três eventos, seguindo o padrão de migration de enum já existente no repo (`ADD VALUE` fora de transação). Critério: `uv run alembic upgrade head` aplica em Postgres limpo; `downgrade` dropa a coluna.

## 2. Serviço de contagem de responsabilidade (US 8.4, guarda)

- [x] 2.1 Implementar `contar_processos_sob_responsabilidade(db, usuario) -> int` em `apps/api/app/services/processo_consulta.py` (ou serviço próximo), aplicando a regra D2: processos `ABERTO`/`EM_TRAMITACAO` cujo último responsável de tramitação é o usuário, ou que ele criou e ainda sem tramitação. Critério: função pura, testável isoladamente.
- [x] 2.2 Teste automatizado (pytest, Postgres real) de `contar_processos_sob_responsabilidade`: cobre último-responsável em andamento (conta), criador sem tramitação (conta), processo concluído/arquivado (não conta), responsável antigo que já despachou (não conta). **Obrigatório** — toca histórico de tramitação.

## 3. Permissão de auditoria — API (US 8.3)

- [x] 3.1 Adicionar `pode_auditar: bool` ao `UsuarioResponse` (schema + `UsuarioResponse.de`). Critério: resposta de usuário expõe a flag.
- [x] 3.2 `POST /usuarios/{usuario_id}/permissao-auditoria` (Admin-only via `require_perfil`): concede, idempotente, grava `permissao_auditoria_concedida` só em transição real. Critério: 404 se alvo inexistente; 200 e flag `true`.
- [x] 3.3 `DELETE /usuarios/{usuario_id}/permissao-auditoria` (Admin-only): revoga, idempotente, grava `permissao_auditoria_revogada` só em transição real. Critério: 200 e flag `false`; perfil do alvo inalterado.
- [x] 3.4 Testes automatizados (pytest) da concessão/revogação: sucesso + registro em `log_seguranca`; idempotência sem log duplicado; perfil inalterado; acesso negado para Servidor/Gestor/auditor-não-admin com registro `acesso_negado`. **Obrigatório** — toca `log_seguranca`.

## 4. Desativação de usuário — API (US 8.4)

- [x] 4.1 `POST /usuarios/{usuario_id}/desativar` (Admin-only): aplica a guarda de 2.1; bloqueia com "Este usuário possui X processo(s) em andamento. Reatribua os processos antes de desativar." (422); em sucesso, `status → INATIVO` e grava `usuario_desativado`; idempotente ("Usuário já está inativo", sem log). Critério: 404 se inexistente; mensagens exatas do PRD.
- [x] 4.2 Testes automatizados (pytest) da desativação: sucesso sem pendências + log; bloqueio com contagem correta na mensagem; concluído/arquivado não bloqueia; idempotência; acesso negado para não-Admin com registro. **Obrigatório** — toca `log_seguranca` e histórico.

## 5. Contrato frontend↔backend

- [x] 5.1 Regenerar o snapshot do contrato: `pnpm gen:types` (novas rotas + `pode_auditar`). Critério: `pnpm gen:types:check` passa (sem drift no CI).

## 6. Frontend (Next.js — admin/usuarios)

- [x] 6.1 Em `apps/web/app/admin/usuarios/page.tsx`, adicionar ações Admin-only "Conceder/Revogar Permissão de Auditoria" (refletindo `pode_auditar`) chamando as rotas via `lib/api.ts`. Critério: toggle reflete o estado retornado; sem `any` no payload.
- [x] 6.2 Adicionar ação "Desativar Usuário" com exibição da mensagem de guarda de processos pendentes retornada pela API. Critério: sucesso atualiza status para Inativo; bloqueio exibe a mensagem com a contagem.
- [x] 6.3 Teste de componente (Vitest + RTL) das ações de auditoria e desativação: renderização condicional por perfil, chamada das rotas e exibição da mensagem de guarda.

## 7. Teste E2E (Playwright) — desativação encerra o acesso

- [x] 7.1 Cenário E2E: Admin desativa um Servidor sem pendências → o Servidor não consegue mais fazer login (usuário inativo rejeitado). **Obrigatório** — o fluxo altera o acesso de login (US 8.4 Cen.1).

## 8. Fechamento

- [x] 8.1 Rodar suíte completa local (`uv run pytest`, `uv run ruff check .`, `pnpm --filter @setes/web typecheck && test`, `pnpm gen:types:check`, E2E) e corrigir pendências. Critério: tudo verde antes do PR.
