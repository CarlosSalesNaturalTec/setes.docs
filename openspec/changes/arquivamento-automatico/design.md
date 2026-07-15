## Context

`processos-e-workflow` (arquivado) deixou a máquina de estados com `arquivado` no enum mas **sem a transição** `Concluído → Arquivado` (reservada explicitamente). `bootstrap-infraestrutura` (arquivado) deixou o Cloud Run Job `job-manutencao-diaria` (cron diário 03:00 America/Bahia, `sa-jobs` com Direct VPC egress), um entrypoint placeholder (`app/jobs/entrypoint.py`) e o **contrato de idempotência já provado em memória** (`app/jobs/manutencao_diaria.py` + `tests/test_idempotencia.py`: seleção por estado, execução repetida sem duplicar, retomada após dias parado). Este change dá pernas de banco a esse contrato.

Restrições que moldam este design:
- Convenções de `models.py`: PKs UUID app-side, enums via `SAEnum` (`native_enum`, `values_callable`), timestamps `timezone=True`. `sistema_config` é singleton `id=1`.
- Precedente de congelamento: `prazo_em` (date) já é congelado na criação (Change A). O prazo de arquivamento segue o mesmo padrão.
- Histórico `tramitacao` é imutável (INSERT-only) — vale para o evento de arquivamento.
- O job roda fora de contexto de request; abre sessão via `get_session_factory()` (pool 5, `max_overflow=0`).
- Escala: ~10.000 processos; a rotina roda 1×/dia.

## Goals / Non-Goals

**Goals:**
- Implementar a transição `Concluído → Arquivado` como rotina diária idempotente e retomável, com evento imutável por processo (US 2.5 Cen.1/3/4).
- Congelar `arquivar_em` na conclusão, garantindo não-retroatividade de mudanças de prazo (US 2.5 Cen.2).
- Tornar o prazo de arquivamento configurável pelo Administrador (fatia mínima da US 8.5).
- Substituir o entrypoint placeholder pelo passo de arquivamento real, preservando o contrato de idempotência já provado.

**Non-Goals:**
- Sigilo de processo (US 2.6) — change irmão B2.
- Demais parâmetros da US 8.5 e a tela de "Configurações do Sistema" completa.
- Demais passos do `job-manutencao-diaria` (alerta de prazo US 5.2, purga de anexos US 8.7, expurgo de notificações US 5.1) e o job trimestral de anonimização (US 10.3).

## Decisions

### D1 — `arquivar_em`: instante absoluto congelado na conclusão
**Escolha:** nova coluna `processo.arquivar_em timestamptz NULL` (NULL enquanto não concluído). Na ação de conclusão (`services/processo.py`, ramo da última etapa), grava-se `arquivar_em = concluido_em + prazo_arquivamento_dias` (dias corridos), lendo o prazo vigente de `sistema_config`. A rotina seleciona por `status = 'concluido' AND arquivar_em <= :agora`.
**Por quê absoluto e não "dias no processo":** congelar o instante final (não o número de dias) torna a seleção do job um único predicado indexável e elimina recomputação; e é exatamente o que o contrato in-memory já modela (`arquivar_a_partir_de: datetime`). Espelha `prazo_em` do Change A.
**Não-retroatividade (Cen.2):** como `arquivar_em` é fixado na conclusão, alterar `prazo_arquivamento_dias` depois não toca processos já concluídos — só afeta conclusões futuras. Sem congelamento, a coluna seria derivável e o Cen.2 inobservável (ver proposal).
**Índice:** `(status, arquivar_em)` para a varredura do job.

### D2 — `prazo_arquivamento_dias` em `sistema_config` + endpoint Admin-only
**Escolha:** coluna `sistema_config.prazo_arquivamento_dias int NOT NULL DEFAULT 30` (singleton id=1). Novo router `sistema_config` com `GET /sistema-config` e `PUT /sistema-config` (ou `PATCH`), ambos `require_perfil(ADMINISTRADOR)`. A escrita valida inteiro positivo (`>= 1`); valor inválido → 422 "O valor deve ser um número inteiro positivo" (US 8.5 Cen.3). A leitura do prazo na conclusão (D1) é `SELECT prazo_arquivamento_dias FROM sistema_config WHERE id=1`.
**Por quê no `sistema_config` existente:** o singleton já é o lar de configuração do sistema; adicionar coluna com `server_default=30` mantém a linha id=1 já semeada válida sem backfill.
**Escopo:** só este parâmetro (fatia mínima US 8.5). Regras vivem na capability `arquivamento-automatico` (ver proposal).

### D3 — Evento de arquivamento sem responsável humano: `responsavel_id` nullable + CHECK
**Problema:** `tramitacao.responsavel_id` é hoje `NOT NULL` (FK `usuario`). O arquivamento é ação de sistema — não há usuário.
**Escolha:** tornar `tramitacao.responsavel_id` **nullable** e adicionar CHECK `responsavel_id IS NOT NULL OR tipo_evento = 'arquivamento_automatico'`. O evento de arquivamento tem `responsavel_id = NULL`, `unidade_origem_id = NULL`, `unidade_destino_id = NULL`, `status_resultante = 'arquivado'`, `tipo_evento = 'arquivamento_automatico'` — o próprio tipo de evento identifica a autoria de sistema.
**Por quê nullable + CHECK e não usuário-sentinela:** um `usuario` "SISTEMA" fictício não tem perfil válido (o enum é servidor/gestor/administrador), poluiria listagens de usuário e "Meu Perfil", e exigiria excluí-lo em toda query. NULL + evento autodescritivo é honesto (não há responsável) e o CHECK preserva a garantia para os eventos humanos (despacho/devolução/conclusão continuam obrigando `responsavel_id`).
**Refinamento da proposta:** o Impact do proposal dizia "tramitacao — sem alteração de schema"; este design refina para **um ALTER (nullable) + CHECK**, além do novo valor de enum. É a única correção de schema face ao proposal.

### D4 — Lógica de arquivamento como serviço sobre `Session`; contrato in-memory preservado
**Escolha:** novo `app/services/arquivamento.py` com `arquivar_vencidos(db: Session, *, agora: datetime) -> int` que executa a seleção por estado (D1) e, para cada processo, transiciona e insere o evento. O `app/jobs/entrypoint.py` deixa de ser placeholder: abre sessão via `get_session_factory()`, chama `arquivar_vencidos`, loga o total e retorna 0. O contrato in-memory `app/jobs/manutencao_diaria.py` e `tests/test_idempotencia.py` são **preservados como guard de lógica pura** (rápido, sem banco) — documentam a propriedade; o novo teste DB-backed prova a fiação real.
**Por quê preservar o in-memory:** já prova a propriedade essencial de forma determinística e barata; apagá-lo perderia um guard válido. Os dois níveis (pura + integração) se complementam.

### D5 — Idempotência e commit por processo (retomável a meio caminho)
**Escolha:** a rotina captura **um único instante** `agora = now()` no início da execução (injetável para teste, como o `agora` do contrato in-memory) e o usa em toda a varredura. Para cada processo selecionado: `validar_transicao(concluido → arquivado)`, seta `status=arquivado`, insere `Tramitacao(arquivamento_automatico)`, e **faz commit por processo** (ou por lote pequeno). 
**Por quê commit por processo:** uma falha a meio caminho deixa os já arquivados persistidos; a próxima execução, por selecionar por estado atual, retoma só os restantes (US 2.5 Cen.4) sem reprocessar os já arquivados (a transição é o guard — Cen.3). All-or-nothing num único commit desperdiçaria progresso numa falha tardia.
**Guard de transição:** um processo já `arquivado` não satisfaz `status='concluido'`, então nunca reentra — idempotência por design, exatamente como `test_idempotencia.py` prova.

## Sequência — Rotina diária de arquivamento (US 2.5)

```
Cloud Scheduler        Cloud Run Job              services/arquivamento         PostgreSQL
   │ cron 03:00 (sa-scheduler)  │                          │                         │
   ├──── RunJob (OIDC) ────────▶│ entrypoint.run()         │                         │
   │                            ├─ get_session_factory()() │                         │
   │                            ├─ agora = now(utc) ───────▶ arquivar_vencidos(agora)│
   │                            │                          ├─ SELECT ... WHERE       │
   │                            │                          │   status='concluido'    │
   │                            │                          │   AND arquivar_em<=agora├────▶│
   │                            │                          │◀── [processos vencidos]─┤
   │                            │                          │  para cada processo:    │
   │                            │                          │   status=arquivado      │
   │                            │                          │   INSERT tramitacao     │
   │                            │                          │   (arquivamento_auto.)  │
   │                            │                          │   COMMIT (por processo)─┼────▶│
   │                            │◀── total arquivado ──────┤                         │
   │                            ├─ log.info(total)         │                         │
   │◀─── exit 0 ────────────────┤                          │                         │
```
Sem superfície HTTP pública; a única autorização é o OIDC do Scheduler sobre a `sa-jobs` (spec `rotinas-agendadas`). **Nenhuma** notificação/e-mail é disparada por este passo (alerta de prazo é US 5.2, fora de escopo).

## Migration Plan (schema antes de endpoint/serviço)

Migration Alembic `0004_arquivamento_automatico` (`down_revision = "0003_processos_workflow"`; revision ≤ 32 chars). Aplica, nesta ordem:

1. **Enum**: `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'arquivamento_automatico'`. Em PG16 roda dentro da transação da migration desde que o valor não seja *usado* na mesma migration (só é adicionado aqui) — atende. (Se o runner reclamar, isolar em passo com autocommit.)
2. **`processo`**: `ADD COLUMN arquivar_em timestamptz NULL`; índice `ix_processo_status_arquivar_em (status, arquivar_em)`.
3. **`sistema_config`**: `ADD COLUMN prazo_arquivamento_dias int NOT NULL DEFAULT 30` (a linha singleton id=1 já existente fica válida pelo default).
4. **`tramitacao`**: `ALTER COLUMN responsavel_id DROP NOT NULL`; `ADD CONSTRAINT ck_tramitacao_responsavel CHECK (responsavel_id IS NOT NULL OR tipo_evento = 'arquivamento_automatico')`.
5. `downgrade()` reverte na ordem inversa (drop CHECK, restaura NOT NULL — exige que não haja linhas de arquivamento; documentar; drop coluna sistema_config, drop índice+coluna processo). O valor de enum adicionado não é removível trivialmente em PG — `downgrade` documenta a limitação (deixar o valor órfão é inócuo).

Só após a migration: congelamento em `services/processo.py` (conclusão lê `sistema_config`), `services/arquivamento.py`, entrypoint real, router `sistema_config` (GET/PUT admin-only). Regenerar `packages/api-types` (`pnpm gen:types`) pela mudança de contrato do endpoint.

## Riscos / Trade-offs

- **`ALTER TYPE ADD VALUE` em migration:** documentado acima; caminho de contingência (autocommit isolado) se o ambiente PG reclamar.
- **`responsavel_id` nullable enfraquece a garantia por coluna:** mitigado pelo CHECK que só permite NULL no evento de arquivamento; os fluxos humanos continuam obrigados.
- **Commit por processo × custo:** a 10k processos/dia, o volume diário arquivável é pequeno (só os que venceram naquele dia); commit por processo é aceitável e maximiza retomabilidade. Se algum dia o lote for grande (ex.: 1ª execução após acúmulo), pode-se commitar em chunks — não necessário no MVP.
- **Relógio único por execução (`agora`):** evita janela em que processos "vencem" no meio da varredura; e torna o teste determinístico (injeção de `agora`), alinhado ao contrato in-memory.
- **Leitura de `sistema_config` na conclusão:** adiciona um SELECT à ação de despacho-conclusão; custo desprezível (singleton, 1 linha).
