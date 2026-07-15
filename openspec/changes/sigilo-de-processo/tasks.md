> **Nota sobre testes:** este change exige teste automatizado por **tocar histórico de tramitação** (eventos de sigilo) e **visibilidade por unidade/perfil** (permissão + acesso negado) — regra `tasks` do `config.yaml`. **Não** exige E2E Playwright: a regra de E2E cobre login/despacho/assinatura/consulta pública, e sigilo não é nenhum desses (a consulta pública que consome o sigilo trará seu próprio E2E no Épico 7). O frontend é coberto por teste de componente (Vitest/RTL).

## 1. Schema — migration Alembic `0005_sigilo_processo`

- [ ] 1.1 Em `models.py`: adicionar `MARCAR_SIGILO = "marcar_sigilo"` e `REMOVER_SIGILO = "remover_sigilo"` ao enum `TipoEventoTramitacao`, e a coluna `sigiloso: Mapped[bool]` (`server_default` false, `nullable=False`) em `Processo` — aceite: `import app.db.models` sem erro
- [ ] 1.2 Criar migration `0005_sigilo_processo` (`down_revision="0004_arquivamento_automatico"`, revision ≤ 32 chars) com `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'marcar_sigilo'` e `ADD VALUE 'remover_sigilo'` — aceite: `alembic upgrade head` roda limpo a partir de `0004` (valores adicionados, não usados na mesma migration)
- [ ] 1.3 Na mesma migration: `ADD COLUMN processo.sigiloso boolean NOT NULL DEFAULT false` — aceite: `\d processo` mostra a coluna; `SELECT sigiloso FROM processo` retorna `false` para linhas pré-existentes
- [ ] 1.4 Escrever `downgrade()` (drop coluna `processo.sigiloso`; documentar que os valores de enum permanecem órfãos, inócuos, como em `0004`) e testar ciclo `alembic downgrade -1` + `upgrade head` — aceite: ciclo up/down/up roda sem erro

## 2. Serviço de sigilo (US 2.6 Cen.1/1b/2)

- [ ] 2.1 Implementar `app/services/sigilo.py` — `marcar(db, *, processo, responsavel) -> Processo` e `remover(db, *, processo, responsavel) -> Processo`: se já no estado-alvo, no-op sem novo evento (D4); caso contrário, seta `processo.sigiloso`, insere `Tramitacao(tipo_evento=marcar_sigilo|remover_sigilo, responsavel_id=responsavel.id, unidades NULL, status_resultante=processo.status)` e persiste — aceite: marcar processo não-sigiloso vira `sigiloso=true` + 1 evento; marcar já-sigiloso não cria novo evento
- [ ] 2.2 Teste automatizado do serviço: marca/remove alteram `sigiloso` e geram exatamente 1 evento por mudança efetiva; no-op não duplica evento; o evento registra responsável, `unidades NULL` e `status_resultante` = status atual; o status do processo **não muda** com o sigilo — **obrigatório (toca histórico de tramitação imutável)**

## 3. Endpoints de sigilo (US 2.6 Cen.1/1b/2/3, acesso negado)

- [ ] 3.1 Adicionar `POST /processos/{id}/sigilo` (marcar) e `DELETE /processos/{id}/sigilo` (remover) em `routers/processos.py`, ambos com `get_current_user` + `_exigir_acesso_ao_processo` **antes** de agir, retornando `ProcessoResponse` — aceite: Servidor/Gestor da unidade atual e Administrador conseguem marcar/remover; resposta reflete `sigiloso` atualizado
- [ ] 3.2 Adicionar `sigiloso: bool` a `ProcessoResponse` e `CardProcessoResponse` (`schemas/processo.py`), preenchido nos respectivos `.de(...)` a partir de `processo.sigiloso` — aceite: detalhe e cards do Kanban trazem o campo
- [ ] 3.3 Teste automatizado de permissão e acesso negado: Servidor de outra unidade recebe 403 "Acesso negado…" e grava `log_seguranca`; Servidor/Gestor da unidade atual e Administrador (em qualquer unidade) têm sucesso; processo sigiloso continua aparecendo no Kanban da própria unidade com `sigiloso=true` (US 2.6 Cen.3) — **obrigatório (regra de visibilidade por unidade/perfil, com cenário de acesso negado)**

## 4. Frontend (Next.js — `apps/web`)

- [ ] 4.1 Indicador visual "Sigiloso" (ícone de cadeado/tarja) no card do Kanban (`app/processos`) quando `card.sigiloso` — aceite: card sigiloso exibe o indicador; card comum não (US 2.6 Cen.3)
- [ ] 4.2 Na tela de detalhe (`app/processos/[id]`): indicador de sigilo quando aplicável e ações "Marcar como Sigiloso" / "Remover Sigilo" (visíveis conforme o estado atual), consumindo `lib/api.ts` tipado (`POST`/`DELETE /processos/{id}/sigilo`) — aceite: marcar/remover atualiza o indicador e a lista de ações sem recarregar a página
- [ ] 4.3 Teste de componente (Vitest + RTL) do detalhe e do card: render do indicador quando `sigiloso`, presença da ação correta conforme o estado — aceite: `pnpm --filter @setes/web test` verde

## 5. Contrato de tipos e verificação final

- [ ] 5.1 Regenerar o contrato front↔back: `pnpm gen:types` e commitar `packages/api-types` (novo campo `sigiloso`, novos endpoints) — aceite: `pnpm gen:types:check` passa (snapshot não defasado)
- [ ] 5.2 Rodar as suítes locais antes do PR: `uv run ruff check .` e `uv run pytest` (API, Postgres real); `pnpm --filter @setes/web typecheck && pnpm --filter @setes/web test` (web) — aceite: todas verdes
