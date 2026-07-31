## 1. Migration e schema (antes de endpoint/UI — design D10)

- [x] 1.1 Migration `0022_processo_setor_servidor_atual`: adicionar `processo.setor_atual_id` (FK→`setor`) e `processo.servidor_atual_id` (FK→`usuario`); backfill `servidor_atual_id = criado_por_id` e `setor_atual_id` = setor do criador; `SET NOT NULL` nas duas. `down_revision = "0021_usuario_setor_e_campos"`. Aceite: upgrade/downgrade limpos sobre base com processos existentes; `ruff check migrations/` verde.
- [x] 1.2 Migration `0023_tramitacao_setor_servidor_mensagem`: adicionar `setor_origem_id`, `setor_destino_id`, `servidor_origem_id`, `servidor_destino_id` (todas FK nullable) e `mensagem` text em `tramitacao`; `ALTER TYPE tipo_evento_tramitacao RENAME VALUE 'despacho' TO 'envio'` e `ADD VALUE 'reatribuicao'`; `ADD VALUE` de `reatribuido_para_voce` e `destino_corrigido` em `tipo_notificacao`. Usar `COMMIT` explícito antes dos `ADD VALUE`, no padrão de `0014_lgpd_enums`. Aceite: enum atualizado; docstring citando `Change tramitacao-manual (design.md D7, D8, D10)`.
- [x] 1.3 Migration `0024_remover_roteiro`: remover `processo.roteiro_id` e `processo.ordem_atual`; `DROP TABLE roteiro_etapa` e `DROP TABLE roteiro` nessa ordem. Aceite: upgrade limpo; docstring registrando que o downgrade recria as tabelas vazias e não restaura dados.
- [x] 1.4 `db/models.py`: novas colunas de `Processo` e `Tramitacao`, `TipoEventoTramitacao.ENVIO`/`REATRIBUICAO`, dois valores novos em `TipoNotificacao`; remover as classes `Roteiro` e `RoteiroEtapa`. Comentários citando `(D1)`, `(D6)`, `(D7)`. Aceite: modelos batem exatamente com as três migrations.
- [x] 1.5 `db/dev_reset.py`: remover `roteiro`/`roteiro_etapa` da ordem de truncamento. Aceite: `POST /internal/dev/reset` funciona sem referência a tabela inexistente.

## 2. Backend — remoção do roteiro

- [x] 2.1 Excluir `services/roteiros.py` e `services/roteiro_snapshot.py` e todas as importações. Aceite: nenhuma ocorrência de `roteiro` ou `ordem_atual` em `apps/api/app` (verificar por busca).
- [x] 2.2 `routers/tipos_processo.py` e `schemas/tipos_processo.py`: remover rotas e schemas de roteiro/etapas, preservando o CRUD de tipo de processo e o `prazo_anonimizacao_anos`. Aceite: OpenAPI sem rotas de roteiro; gestão de tipo intacta.
- [x] 2.3 Excluir `tests/test_roteiros.py`. Aceite: suíte sem referência a roteiro.

## 3. Backend — tramitação manual (design D1, D2, D3, D4, D5, D9)

- [x] 3.1 `services/processo.py::criar_processo`: remover a resolução de roteiro/snapshot; definir `servidor_atual_id = criador.id` e `setor_atual_id = criador.setor_id`; rejeitar criação por usuário sem setor (422). Aceite: processo nasce `aberto`, atribuído ao criador.
- [x] 3.2 `services/processo.py::enviar`: destino explícito (unidade, setor, servidor) validando setor∈unidade, servidor∈setor e `servidor_destino != servidor_atual` (422); transição para `em_tramitacao` via `validar_transicao`; INSERT de `tramitacao` com tipo `envio`, origem/destino de unidade, setor e servidor, `mensagem` e `responsavel_id`. Aceite: uma única transação; processo e evento coerentes.
- [x] 3.3 `services/processo.py::devolver`: resolver o destino automaticamente a partir do último evento `envio`/`reatribuicao` cujo `servidor_destino_id` é o servidor atual (D3); 409 quando não houver remetente anterior; motivo e justificativa obrigatórios. Aceite: a API não aceita destino informado pelo cliente na devolução.
- [x] 3.4 `services/processo.py::reatribuir`: unidade de destino SHALL ser a unidade atual (422 caso contrário), setor livre dentro dela, `servidor_destino != servidor_atual` (422), justificativa obrigatória; `status_resultante = processo.status` **sem** chamar `validar_transicao` (D4); prazo intocado (D9). Aceite: status e `prazo_em` idênticos antes e depois.
- [x] 3.5 `services/processo.py::concluir`: ação própria, `validar_transicao(status, CONCLUIDO)`, congelamento de `arquivar_em` a partir de `sistema_config` (comportamento já existente, apenas extraído do despacho). Aceite: concluir não depende de nenhuma noção de "última etapa".
- [x] 3.6 Guarda de papel por ação (D5): Envio/Devolução restritos ao `servidor_atual`; Reatribuir também ao remetente da última tramitação e ao gestor da unidade; Concluir também ao gestor. Aplicada **após** a autorização por unidade existente; rejeição grava `log_seguranca`. Aceite: nenhuma alteração em `security/autorizacao.py`.
- [x] 3.7 Confirmar que `services/processo_estado.py` permanece **byte-idêntico** (D4). Aceite: arquivo não aparece no diff do change.
- [x] 3.8 `services/processo_consulta.py::contar_processos_sob_responsabilidade`: passar a contar por `servidor_atual_id` em vez da heurística de "último responsável". Aceite: guarda de desativação de usuário (US 8.4) continua verde nos testes existentes.

## 4. Backend — notificações por pessoa (design D8)

- [x] 4.1 `services/notificacao.py`: `gerar_notificacoes` passa a receber destinatário único (`usuario_id`) em vez de fan-out por unidade; remover `servidores_da_unidade` se ficar sem uso. Aceite: uma notificação por evento, não N.
- [x] 4.2 Emitir `REATRIBUIDO_PARA_VOCE` ao servidor de destino e `DESTINO_CORRIGIDO` ao remetente original (omitida quando o remetente é o próprio autor da reatribuição ou não existe). Texto factual, sem juízo. Aceite: dois inserts na mesma transação do evento.
- [ ] 4.3 Testes pytest de notificação (obrigatórios — histórico de tramitação): destinatário único no envio; ambos os avisos na reatribuição; ausência de `DESTINO_CORRIGIDO` quando não há remetente original.

## 5. Backend — rotas e schemas

- [x] 5.1 `schemas/processo.py`: `EnviarRequest` (unidade/setor/servidor destino + mensagem), `DevolverRequest` (motivo + justificativa, **sem** destino), `ReatribuirRequest` (setor + servidor destino + justificativa), `ConcluirRequest`; `ProcessoResponse` e `EventoHistoricoResponse` com setor/servidor de origem e destino e mensagem. Aceite: OpenAPI reflete as três ações.
- [x] 5.2 `routers/processos.py`: `POST /processos/{id}/enviar`, `/devolver`, `/reatribuir`, `/concluir`, substituindo `/despachar`. Autorização por unidade preservada, guarda de papel do D5 aplicada em seguida. Aceite: rota `/despachar` não existe mais.
- [x] 5.3 Endpoints de apoio à cascata: `GET /unidades/{id}/setores` (já criado no change anterior) e `GET /usuarios?setor_id=` retornando apenas servidores **ativos** do setor. Aceite: listas alimentam os selects sem expor usuários inativos.
- [ ] 5.4 Testes pytest de tramitação (obrigatórios — histórico imutável + dados pessoais): envio com destino válido; envio para si mesmo rejeitado; devolução resolvendo o remetente correto; devolução sem remetente anterior bloqueada; reatribuição preservando status e prazo; reatribuição para outra unidade rejeitada; reatribuição para o mesmo servidor rejeitada; conclusão explícita a partir de `aberto` e de `em_tramitacao`; histórico com a sequência completa de detentores; **acesso negado** com log em: agir sobre processo de unidade fora do escopo, Envio/Devolução por quem não é o servidor atual, Reatribuir por servidor sem nenhum dos três papéis do D5.

## 6. Contrato

- [x] 6.1 `pnpm gen:types` e commit de `packages/api-types/{openapi.json,schema.ts}`. Aceite: `pnpm gen:types:check` verde.

## 7. Frontend

- [x] 7.1 `app/processos/[id]/page.tsx`: modal de Tramitação com select de tipo de ação (Envio / Devolução / Reatribuir) e campos condicionais — Envio: unidade→setor→servidor em cascata + mensagem; Devolução: destino exibido como leitura ("devolver para <servidor>") + motivo + justificativa; Reatribuir: unidade fixa (readonly) + setor→servidor + justificativa. Aceite: nenhum campo de destino editável na Devolução.
- [x] 7.2 `app/processos/[id]/page.tsx`: botão **Concluir** próprio, com confirmação; remoção do fluxo de confirmação embutido no despacho. Aceite: concluir não passa mais por 409 de confirmação de despacho.
- [x] 7.3 `app/processos/[id]/page.tsx`: histórico exibindo, por evento, o tipo de ação, servidor de origem e destino, setor e mensagem/justificativa. Aceite: reatribuições distinguíveis de envios na linha do tempo.
- [x] 7.4 `app/processos/novo/page.tsx` e `app/admin/tipos-processo/page.tsx`: remover toda a UI de roteiro/etapas. Aceite: nenhuma referência a roteiro no `apps/web`.
- [x] 7.5 `lib/api.ts` e `lib/processo-ui.ts`: métodos das quatro ações e rótulos dos novos tipos de evento. Aceite: sem `any` nos payloads.
- [ ] 7.6 Testes Vitest: cascata unidade→setor→servidor; bloqueio de envio para o próprio servidor atual; unidade readonly na reatribuição; campos condicionais por tipo de ação; render do histórico com os três tipos.

## 8. Testes E2E Playwright (obrigatório — altera despacho)

- [x] 8.1 **Primeiro**: atualizar `tests/helpers_processo.py` (pytest) para criar processos sem roteiro, com setor e servidor atuais. Aceite: a suíte pytest volta a coletar sem erros de importação antes de qualquer outra tarefa de teste deste change.
- [ ] 8.2 Reescrever `e2e/05-processos-despacho.spec.ts`: Servidor A cria processo (aparece no Kanban de A) → envia para Servidor B de outra unidade → B devolve com motivo → A reenvia → B **reatribui** para C do mesmo setor → C conclui. Verificar em cada passo o histórico e a notificação do destinatário, incluindo o aviso de destino corrigido para A. Aceite: `pnpm test:e2e` verde.
- [ ] 8.3 Ajustar `e2e/04-unidades-tipos-processo.spec.ts` (sem roteiro), `e2e/13-admin-readonly-processos.spec.ts` e `e2e/14-visibilidade-processos-origem.spec.ts` às novas ações. Aceite: suíte E2E completa verde.

## 9. Documentação mestre

- [x] 9.1 `docs/PRD.md` Épico 2: reescrever US 2.1 (criação sem roteiro, atribuída ao criador), US 2.2 (Envio), US 2.2b (Devolução com destino automático), nova US de Reatribuição, US 2.4 (histórico com setor/servidor) e a conclusão como ação própria. Aceite: PRD sem nenhuma menção a roteiro automático.
- [x] 9.2 Renomear a capability consolidada `openspec/specs/tipos-processo-e-roteiros/` para `openspec/specs/tipos-processo/` na sincronização das specs. Aceite: nome da capability coerente com seu conteúdo.
- [x] 9.3 `docs/manual-usuario.md`: seção de tramitação reescrita com os três tipos de ação e a conclusão explícita. Aceite: descrições coerentes com a UI final.
