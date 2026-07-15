## Why

O Épico 2 está quase completo: `processos-e-workflow` (arquivado) entregou criação, despacho, devolução, Kanban, histórico e busca; `arquivamento-automatico` (arquivado) entregou a transição `Concluído → Arquivado`. Falta **uma única história do Épico 2**: a **US 2.6 — Sigilo de processo**. Ela foi explicitamente adiada duas vezes — `processos-e-workflow` a empurrou para uma "Change B", e `arquivamento-automatico` a re-empurrou para um "change irmão B2" que nunca foi criado. Este change fecha essa dívida.

Além de completar o Épico 2, o sigilo é **pré-requisito rígido do Épico 7 (Consulta Pública)**: a consulta pública precisa esconder processos sigilosos (US 7.1 Cen.4, US 7.2) e, sem a marcação existir, o primeiro deploy da consulta pública vazaria qualquer processo. O sigilo cria o mecanismo; a **ocultação na consulta pública é do Épico 7**, fora deste change.

O change é deliberadamente enxuto: uma coluna booleana em `processo`, um par de ações (marcar/remover) que gravam evento imutável no histórico já existente, e um indicador visual interno. **Sem infra nova** — sem bucket, sem segredo, sem rate limiting, sem tocar a máquina de estados (sigilo é ortogonal ao status).

## What Changes

- **US 2.6 Cen.1 — Marcar como Sigiloso**: Servidor ou Gestor **da unidade atual do processo**, ou Administrador, aciona "Marcar como Sigiloso"; o processo passa a `sigiloso = true`, a ação é registrada como **evento imutável** no histórico de tramitação (`tramitacao`), e o processo **deixaria de aparecer na consulta pública** (a consulta pública em si é Épico 7 — aqui garante-se apenas a marcação e o evento).
- **US 2.6 Cen.1b — Administrador em qualquer unidade**: o Administrador marca/remove sigilo em processo de **qualquer** unidade, sem restrição de unidade, com registro no histórico. (O modelo de autorização por unidade já existente — `require_acesso_unidade`/`_exigir_acesso_ao_processo` — já concede: Servidor só a própria unidade, Gestor as geridas, Administrador todas.)
- **US 2.6 Cen.2 — Remover Sigilo**: usuário com a mesma permissão (Servidor/Gestor da unidade atual, ou Administrador) aciona "Remover Sigilo"; `sigiloso` volta a `false`, a remoção é registrada como evento imutável, e o processo voltaria a aparecer na consulta pública (Épico 7).
- **US 2.6 Cen.3 — Visibilidade interna**: um processo sigiloso continua aparecendo **normalmente** no Kanban da sua unidade e na tela de detalhe, com um **indicador visual "Sigiloso"** (ícone de cadeado/tarja) no card e no detalhe.
- **Cenário de acesso negado (invariante do projeto)**: tentativa de marcar/remover sigilo de processo de unidade fora do escopo do usuário retorna "acesso negado" e grava linha imutável em `log_seguranca` — reutiliza `_exigir_acesso_ao_processo` (US 1.4 Cen.2, já provado).

**Fora de escopo deste change:**
- **Épico 7 — Consulta Pública** (a ocultação efetiva do sigiloso na busca pública, o rate limiting, a não-exibição de CPF/CNPJ) → change futuro. Aqui só existe a marcação e sua visibilidade interna.
- **Assinatura, documentos, notificações, dashboard, auditoria, LGPD** → épicos seguintes.
- **Nenhuma alteração na máquina de estados** — sigilo é atributo ortogonal ao status; não há transição nova em `processo_estado.py`.

## Capabilities

### New Capabilities
- `sigilo-processo`: a marcação de sigilo do processo (atributo `sigiloso`), as ações de marcar/remover com seu modelo de permissão (Servidor/Gestor da unidade atual, Administrador em qualquer unidade) e o cenário de acesso negado, e a garantia de visibilidade interna do processo sigiloso. A capability é dona ponta-a-ponta do sigilo; a consulta pública (Épico 7) será uma **consumidora** desse atributo, não sua dona.

### Modified Capabilities
- `workflow-tramitacao`: o histórico imutável passa a admitir **dois novos tipos de evento** — `marcar_sigilo` e `remover_sigilo` — registrando cada mudança de sigilo (responsável, data/hora), sem alterar a máquina de estados nem o status do processo.
- `quadro-kanban`: o card do Kanban passa a expor o atributo `sigiloso` para renderização do indicador visual (US 2.6 Cen.3), sem alterar escopo, ordenação ou filtro.

## Impact

- **Dependência de change anterior:** requer `processos-e-workflow` arquivado — consome `processo` (adiciona coluna `sigiloso`), `tramitacao` (novos tipos de evento), o modelo de autorização por unidade (`_exigir_acesso_ao_processo`/`require_acesso_unidade`/`tem_acesso_a_unidade`) e `log_seguranca` (acesso negado). Transitivamente requer `arquivamento-automatico` (a migration encadeia em `0004`).
- **Tabelas PostgreSQL afetadas** (migration `0005_sigilo_processo`, encadeada em `0004_arquivamento_automatico`):
  - `processo` — **nova coluna** `sigiloso boolean NOT NULL DEFAULT false`. As linhas existentes ficam válidas pelo default (não-sigilosas).
  - `tramitacao` — **sem alteração de schema**; dois novos valores no enum `tipo_evento_tramitacao`: `marcar_sigilo` e `remover_sigilo`. Os eventos de sigilo têm `responsavel_id` = usuário humano que agiu (o CHECK `ck_tramitacao_responsavel` de `0004` continua satisfeito — só `arquivamento_automatico` dispensa responsável), `unidade_origem_id`/`unidade_destino_id` nulas e `status_resultante` = status atual do processo (sigilo não altera o status).
- **Máquina de estados:** **nenhuma alteração** — sigilo é atributo ortogonal ao status; `processo_estado.py` não muda.
- **Secret Manager:** nenhum segredo novo.
- **Cloud Storage:** nenhum bucket novo.
- **Rate limiting:** N/A — todos os endpoints deste change são autenticados; a consulta pública com `slowapi` é Épico 7.
- **LGPD:** este change **não introduz nem expõe dados pessoais novos**. O sigilo é justamente um mecanismo de **proteção** de visibilidade: marca processos que não devem aparecer na consulta pública (a ocultação efetiva é Épico 7). Nome/CPF/CNPJ de interessados permanecem inalterados e só acessíveis internamente por usuários autorizados por unidade. O histórico `tramitacao` ganha eventos com responsável funcional, sob a mesma política de retenção dos demais logs de auditoria.
- **Código:** migration `0005`; nova coluna `sigiloso` no modelo `Processo`; dois valores no enum `TipoEventoTramitacao`; novo serviço `services/sigilo.py` (marcar/remover, idempotente, com inserção do evento); dois endpoints em `routers/processos.py` (`POST`/`DELETE /processos/{id}/sigilo`) reutilizando `_exigir_acesso_ao_processo`; campo `sigiloso` em `ProcessoResponse` e `CardProcessoResponse`. Frontend: indicador de cadeado/tarja no card do Kanban e no detalhe, e ações "Marcar como Sigiloso"/"Remover Sigilo" na tela de detalhe. Regenerar `packages/api-types` (`pnpm gen:types`). Testes: unitário/integração da marcação, do evento imutável e do modelo de permissão/acesso negado (obrigatórios — tocam histórico de tramitação e visibilidade por unidade/perfil); teste de componente (Vitest/RTL) do indicador e das ações. **Sem E2E Playwright obrigatório** — a regra de E2E do `config.yaml` cobre login/despacho/assinatura/consulta pública; sigilo não é nenhum desses (a consulta pública que o consome virá com seu próprio E2E no Épico 7).
