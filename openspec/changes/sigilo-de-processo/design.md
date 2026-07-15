## Context

`processos-e-workflow` (arquivado) deixou `processo`, `tramitacao` (histórico imutável INSERT-only), o modelo de autorização por unidade (`_exigir_acesso_ao_processo` em `routers/processos.py`, que já grava `log_seguranca` no acesso negado — US 1.4 Cen.2) e os schemas `ProcessoResponse`/`CardProcessoResponse`. `arquivamento-automatico` (arquivado) deixou a migration mais recente `0004_arquivamento_automatico`, o valor de enum `arquivamento_automatico` e o CHECK `ck_tramitacao_responsavel` (responsável obrigatório exceto para o evento de arquivamento). Este change acrescenta o sigilo sobre essa base, sem infra nova.

Restrições que moldam este design:
- Convenções de `models.py`: PKs UUID app-side, enums via `SAEnum` (`native_enum`, `values_callable`), timestamps `timezone=True`.
- Histórico `tramitacao` é **imutável (INSERT-only)** — vale para os eventos de sigilo.
- Sigilo é **ortogonal ao status**: não é uma transição da máquina de estados; `processo_estado.py` não é tocado.
- O modelo de permissão da US 2.6 (Servidor/Gestor da unidade atual, Administrador em qualquer unidade) **coincide exatamente** com `tem_acesso_a_unidade`/`_exigir_acesso_ao_processo` já existente — não há regra de autorização nova a inventar.
- Escala: ~10.000 processos; marcar/remover sigilo é ação pontual de usuário (não em lote).

## Goals / Non-Goals

**Goals:**
- Adicionar o atributo `sigiloso` ao processo e as ações de marcar/remover com o modelo de permissão da US 2.6 (Cen.1, 1b, 2).
- Registrar cada marcação/remoção como evento imutável no histórico de tramitação.
- Expor o `sigiloso` na API para o indicador visual interno (US 2.6 Cen.3), no card do Kanban e no detalhe.
- Reutilizar o cenário de acesso negado por unidade já provado, gravando `log_seguranca`.

**Non-Goals:**
- Ocultação do sigiloso na consulta pública, rate limiting, não-exibição de CPF/CNPJ (Épico 7).
- Qualquer alteração na máquina de estados ou no status do processo.
- Auditoria/relatórios consolidados sobre sigilo (Épico 9).

## Decisions

### D1 — `sigiloso` como coluna booleana em `processo`, default `false`
**Escolha:** nova coluna `processo.sigiloso boolean NOT NULL DEFAULT false`. Todo processo nasce não-sigiloso; a marcação é uma ação explícita posterior. As linhas já existentes ficam válidas pelo `server_default` (sem backfill), espelhando como `0004` adicionou `arquivar_em`/`prazo_arquivamento_dias`.
**Por quê booleano e não estado:** sigilo é um atributo de **visibilidade**, ortogonal à máquina de estados (`Aberto/Em Tramitação/Concluído/Arquivado`). Modelá-lo como status poluiria o enum e a tabela de transições. Um processo pode ser sigiloso em qualquer status.
**Índice:** **não** neste change. O predicado que se beneficiaria de índice (`WHERE NOT sigiloso`) é da consulta pública (Épico 7), que criará seu próprio índice quando o padrão de acesso público existir. Aqui o `sigiloso` só é lido junto do próprio processo já carregado por id.

### D2 — Dois novos tipos de evento no histórico: `marcar_sigilo` e `remover_sigilo`
**Escolha:** adicionar `MARCAR_SIGILO = "marcar_sigilo"` e `REMOVER_SIGILO = "remover_sigilo"` ao enum `TipoEventoTramitacao`. Cada mudança de sigilo insere um `Tramitacao` com: `tipo_evento` correspondente, `responsavel_id` = usuário humano que agiu, `unidade_origem_id`/`unidade_destino_id` = `NULL` (sigilo não move o processo), `status_resultante` = **status atual do processo** (inalterado), `criado_em` = agora.
**Por quê no histórico de `tramitacao` e não em log separado:** a US 2.6 (Cen.1/1b/2) exige explicitamente que a ação seja "registrada no **histórico de tramitação**". Reusar `tramitacao` mantém a linha do tempo do processo completa e honra o invariante de histórico imutável já estabelecido.
**CHECK preservado:** o `ck_tramitacao_responsavel` de `0004` (`responsavel_id IS NOT NULL OR tipo_evento = 'arquivamento_automatico'`) continua satisfeito — eventos de sigilo têm sempre `responsavel_id` humano. Nenhuma alteração de constraint.
**`status_resultante` de um evento que não muda status:** registrar o status atual é honesto (a linha do tempo mostra "em que status estava quando o sigilo mudou") e satisfaz o `NOT NULL` da coluna sem exceção especial.

### D3 — Endpoints `POST` e `DELETE /processos/{id}/sigilo`, reutilizando `_exigir_acesso_ao_processo`
**Escolha:** dois endpoints em `routers/processos.py`:
- `POST /processos/{id}/sigilo` → marca (`sigiloso = true`).
- `DELETE /processos/{id}/sigilo` → remove (`sigiloso = false`).

Ambos dependem de `get_current_user` (não `_require_servidor` — pois Gestor e Administrador também agem) e chamam `_exigir_acesso_ao_processo(db, usuario=..., processo=..., request=...)` **antes** de agir. Essa função já implementa exatamente o modelo da US 2.6: `tem_acesso_a_unidade` é `true` para Servidor/Gestor da unidade atual e para Administrador em qualquer unidade; em qualquer outro caso levanta 403 e grava `log_seguranca` (US 2.6 acesso negado, reaproveitando US 1.4 Cen.2).
**Por quê POST/DELETE e não um PUT com corpo `{sigiloso: bool}`:** as duas ações do PRD ("Marcar como Sigiloso" / "Remover Sigilo") são naturalmente um `POST` (cria a condição) e um `DELETE` (remove a condição) sobre o sub-recurso `/sigilo`; dispensa corpo e torna cada intenção explícita e idempotente por método.

### D4 — Idempotência: marcar já-sigiloso (ou remover já-não-sigiloso) é no-op sem evento duplicado
**Escolha:** o serviço lê o estado atual; se já está no estado-alvo, **retorna o processo sem inserir novo evento** (no-op idempotente, 200). Só quando há mudança efetiva de `false→true` (ou `true→false`) é que grava o evento no histórico.
**Por quê:** evita poluir o histórico imutável com eventos redundantes ("marcou sigilo" duas vezes seguidas sem mudança real). Mantém a linha do tempo fiel às mudanças de estado de visibilidade. O retorno 200 idempotente é mais amigável ao frontend (o botão pode ser acionado sem medo de erro) do que um 409.

### D5 — `sigiloso` exposto em `ProcessoResponse` e `CardProcessoResponse`
**Escolha:** adicionar `sigiloso: bool` a ambos os schemas (detalhe e card do Kanban), preenchido a partir de `processo.sigiloso` nos respectivos `.de(...)`. O frontend renderiza o indicador (cadeado/tarja) quando `sigiloso` é `true`, no card do Kanban (US 2.6 Cen.3) e na tela de detalhe.
**Contrato:** mudança aditiva no OpenAPI → regenerar `packages/api-types` (`pnpm gen:types`); `gen:types:check` do CI falha se o snapshot ficar defasado.

## Migration Plan (schema antes de endpoint/serviço)

Migration Alembic `0005_sigilo_processo` (`down_revision = "0004_arquivamento_automatico"`; revision ≤ 32 chars). Aplica, nesta ordem:

1. **Enum**: `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'marcar_sigilo'` e `ADD VALUE 'remover_sigilo'`. Em PG16 rodam dentro da transação da migration desde que os valores não sejam *usados* na mesma migration (só são adicionados aqui) — atende. (Se o runner reclamar, isolar em passo com autocommit, como documentado em `0004`.)
2. **`processo`**: `ADD COLUMN sigiloso boolean NOT NULL DEFAULT false`. A linha existente de cada processo fica válida (não-sigilosa) pelo default.
3. `downgrade()` reverte na ordem inversa: `DROP COLUMN processo.sigiloso`. Os valores de enum adicionados **não** são removíveis trivialmente em PG — o `downgrade` documenta que permanecem órfãos (inócuo), mesmo padrão de `0004`.

Só após a migration: coluna `sigiloso` no modelo `Processo` e os dois valores no enum `TipoEventoTramitacao` (`models.py`); `services/sigilo.py` (`marcar`/`remover`, idempotentes, inserindo o evento); os dois endpoints em `routers/processos.py`; campo `sigiloso` nos schemas. Regenerar `packages/api-types`.

## Riscos / Trade-offs

- **`ALTER TYPE ADD VALUE` em migration:** já enfrentado e documentado em `0004`; caminho de contingência (autocommit isolado) se o ambiente PG reclamar.
- **Ausência de índice em `sigiloso`:** deliberada — o consumidor que precisa de varredura por `sigiloso` é a consulta pública (Épico 7), que definirá o índice junto do seu padrão de acesso. Aqui o campo só é lido no processo já carregado por id; índice agora seria especulativo.
- **`status_resultante` em evento que não muda status:** registrar o status atual é a escolha honesta e evita uma exceção de schema; a leitura da linha do tempo deixa claro que o evento é de sigilo (pelo `tipo_evento`), não de mudança de status.
- **Reuso de `_exigir_acesso_ao_processo`:** o modelo de permissão da US 2.6 coincide com o já existente — reusar evita divergência de regra de autorização e herda o cenário de acesso negado já testado. O risco seria se a US 2.6 exigisse permissão *diferente* da visibilidade por unidade; ela não exige (Cen.1/1b/2 mapeiam 1:1 em `tem_acesso_a_unidade`).
- **Idempotência sem evento duplicado (D4):** um cliente que espere um evento por clique não o verá em cliques redundantes; é o comportamento desejado (histórico reflete mudanças reais), documentado no spec.
