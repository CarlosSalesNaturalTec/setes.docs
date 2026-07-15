## Why

O change `processos-e-workflow` (arquivado) entregou a máquina de estados do processo `Aberto → Em Tramitação → Concluído → Arquivado`, mas deixou **a transição `Concluído → Arquivado` deliberadamente não implementada** — o estado `arquivado` existe no enum e nenhuma ação o alcança. Este change fecha essa lacuna: implementa a rotina automática que move processos concluídos para arquivado após o prazo configurado (US 2.5).

Além disso, honra uma promessa registrada no primeiro change do projeto: `bootstrap-infraestrutura` (arquivado) provisionou o Cloud Run Job `job-manutencao-diaria` (cron diário 03:00 America/Bahia) com um **entrypoint placeholder** (`app/jobs/entrypoint.py`: "nenhum passo de negócio implementado ainda") e um **contrato de idempotência já provado em memória** (`app/jobs/manutencao_diaria.py` + `tests/test_idempotencia.py`). A infra e o contrato existem; falta a lógica de banco. Este change é o primeiro passo de negócio real desse job.

Este é o **change B1** derivado do explore do Épico 2: arquivamento (US 2.5) é backend/job, hermético (zero dependência do Épico 7), e completa estruturas já existentes. O sigilo de processo (US 2.6) é um change irmão independente (B2), fora do escopo aqui.

## What Changes

- **US 2.5 — Arquivamento automático de processos concluídos**: a rotina diária seleciona processos `Concluído` cujo prazo de arquivamento já expirou e os transiciona para `Arquivado`, registrando um evento imutável no histórico de cada um (Cen.1, Cen.3). A seleção é **função do estado atual** (`status = 'concluido' AND arquivar_em <= now()`), de modo que reexecução e retomada após indisponibilidade não duplicam efeito (Cen.4) — o contrato de idempotência já provado em `test_idempotencia.py` passa a operar sobre o banco real.
- **Congelamento do prazo na conclusão (US 2.5 Cen.2)**: no momento em que um processo é concluído (`services/processo.py`, ação de despacho na última etapa), o sistema **congela** `arquivar_em = concluido_em + prazo_arquivamento_vigente` como um instante absoluto no próprio processo — espelho do `prazo_em` já congelado na criação. Alterações posteriores do prazo global **não afetam** processos já concluídos (não-retroatividade exigida pelo Cen.2).
- **US 8.5 (fatia mínima) — parâmetro de prazo de arquivamento configurável**: `sistema_config` (hoje singleton com apenas `id` + `inicializado`) ganha `prazo_arquivamento_dias` (padrão 30), e um endpoint Admin-only de leitura/escrita valida-o como inteiro positivo. **Escopo mínimo deliberado**: apenas este parâmetro entra agora — os outros 9 parâmetros operacionais do US 8.5 e a tela de configurações completa ficam para um change futuro. Justificativa: sem um valor mutável, o congelamento (Cen.2) seria cerimônia inobservável; congelar só se justifica se o valor pode mudar.
- **Entrypoint real do job diário**: `app/jobs/entrypoint.py` deixa de ser placeholder e passa a abrir sessão de banco (IP privado, `sa-jobs`) e executar o passo de arquivamento sobre o estado atual. O contrato in-memory de `app/jobs/manutencao_diaria.py` é preservado como guard de lógica pura (ou promovido a serviço real — decisão de `design.md`). Os demais passos previstos para o job (alerta de prazo US 5.2, purga de anexos US 8.7, expurgo de notificações US 5.1) **permanecem fora de escopo** — o job é projetado para acretar passos, e estes pertencem aos Épicos 3/5.

**Fora de escopo deste change:**
- **US 2.6 — Sigilo de processo** → change irmão B2.
- **Demais parâmetros do US 8.5** e a tela de "Configurações do Sistema" completa → change futuro.
- **Demais passos do job diário** (US 5.2 alerta de prazo, US 8.7 purga de anexos, US 5.1 expurgo de notificações) → Épicos 3/5.
- **Rotina trimestral de anonimização LGPD** (`job-anonimizacao-lgpd`, US 10.3) → Épico 10.

## Capabilities

### New Capabilities
- `arquivamento-automatico`: rotina diária que transiciona processos `Concluído → Arquivado` após o prazo configurado, de forma idempotente e retomável, com evento imutável de histórico por processo (US 2.5).

### Modified Capabilities
- `workflow-tramitacao`: a máquina de estados passa a **admitir a transição `Concluído → Arquivado`** (antes reservada e inalcançável); adiciona o evento `arquivamento_automatico` ao histórico imutável; e o congelamento de `arquivar_em` na conclusão passa a fazer parte da ação de conclusão (US 2.5 Cen.2).
- `inicializacao-sistema`: `sistema_config` deixa de ser um singleton apenas com `inicializado` e passa a carregar o primeiro parâmetro operacional configurável (`prazo_arquivamento_dias`), com endpoint Admin-only de leitura/escrita (fatia mínima da US 8.5).

## Impact

- **Dependência de change anterior:** requer `processos-e-workflow` arquivado — consome `processo` (adiciona coluna), `tramitacao` (novo tipo de evento), a máquina de estados de `processo_estado.py` (adiciona transição) e a ação de conclusão de `services/processo.py` (ponto do congelamento). Transitivamente requer `bootstrap-infraestrutura` (o Cloud Run Job `job-manutencao-diaria`, a `sa-jobs` e o contrato de idempotência de `manutencao_diaria.py`/`test_idempotencia.py`).
- **Tabelas PostgreSQL afetadas** (migration `0004`, encadeada em `0003_processos_workflow`):
  - `processo` — **nova coluna** `arquivar_em timestamptz NULL` (congelada na conclusão; NULL enquanto não concluído). Índice `(status, arquivar_em)` para a seleção do job.
  - `sistema_config` — **nova coluna** `prazo_arquivamento_dias int NOT NULL DEFAULT 30` (singleton id=1).
  - `tramitacao` — **sem alteração de schema**; novo valor `arquivamento_automatico` no enum `tipo_evento_tramitacao`. O evento de arquivamento tem `responsavel_id` = identidade do sistema/job (ver design — não há usuário humano), `unidade_origem/destino` nulas, `status_resultante = arquivado`.
- **Máquina de estados:** adiciona `concluido → arquivado` a `_TRANSICOES` em `processo_estado.py`. É a **única** transição nova; nenhuma outra muda.
- **Idempotência / retomada (US 2.5 Cen.4):** garantida por design — a seleção `WHERE status='concluido' AND arquivar_em <= now()` é função do estado atual; um processo já `arquivado` não reentra no predicado (a transição é o guard). O contrato já está provado em `test_idempotencia.py` (execução repetida, retomada após dias parado, seleção por estado); este change o faz operar sobre o banco real, preservando a propriedade.
- **Secret Manager:** nenhum segredo novo — o job já lê `db-password` e `sendgrid-api-key` (ver `infra/jobs_scheduler.tf`).
- **Cloud Storage:** nenhum bucket novo — arquivamento não move nem apaga documentos (a purga de anexos é US 8.7, fora de escopo).
- **Infra:** nenhuma mudança de Terraform — o job, o cron (03:00 diário) e a `sa-jobs` já estão provisionados; muda apenas a imagem do container (via pipeline) que passa a conter o entrypoint real. Rate limiting: N/A (o job não tem superfície HTTP pública; roda sob OIDC do Scheduler).
- **LGPD:** este change não introduz nem expõe dados pessoais novos. O arquivamento apenas transiciona status e registra evento; nome/CPF/CNPJ de interessados permanecem inalterados (a anonimização de arquivados é US 10.3, Épico 10, fora de escopo). O histórico `tramitacao` ganha um evento de sistema sem dado pessoal de terceiro.
- **Código:** migration `0004`; congelamento de `arquivar_em` na conclusão (`services/processo.py`); novo serviço de arquivamento operando sobre `Session` real; entrypoint real do job (`app/jobs/entrypoint.py`); nova coluna + endpoint Admin-only de `sistema_config` (`routers/`, `schemas/`, `services/`). Testes: unitário/integração da seleção e transição idempotente contra Postgres real (obrigatório — toca histórico de tramitação e transição de estado); teste do congelamento não-retroativo (US 2.5 Cen.2). **Sem E2E Playwright** — a rotina não tem fluxo de usuário; é exercitada por invocação direta do job/serviço contra o banco (regra de E2E do `config.yaml` aplica-se a login/despacho/assinatura/consulta pública, não a jobs). Regenerar `packages/api-types` pela mudança no endpoint de `sistema_config`.
