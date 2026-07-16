## Context

O Épico 5 liga os eventos de processo já existentes a dois canais: notificação interna
(sino) e e-mail. A fundação está pronta: `services/processo.py::despachar` já registra os
eventos `DESPACHO`/`CONCLUSAO` em `Tramitacao` dentro de uma transação; `processo.prazo_em`
existe; a fila Cloud Tasks `emails` e `enqueue_email` (com dedup nativo por *task name*
derivado de `event_id`) já operam para e-mails de autenticação; e `jobs/entrypoint.py` já
declara, em comentário, que "alerta de prazo" e "expurgo de notificações" são passos a
acretar ao job diário. Este design descreve como encaixar as duas capabilities novas
(`notificacoes-internas`, `alertas-email-processo`) e o delta de `rotinas-agendadas` sobre
essa base, sem introduzir infraestrutura nova.

## Goals / Non-Goals

**Goals:**
- Gerar notificação interna e e-mail nos eventos de despacho e conclusão, e alerta de prazo
  pela rotina diária, cumprindo US 5.1–5.4.
- Manter a notificação interna como fonte confiável e independente do e-mail (US 5.2 Cen.3:
  falha de e-mail não afeta o sino).
- Idempotência total das rotinas diárias (prazo e expurgo), reaproveitando o contrato de
  `rotinas-agendadas`.
- Parâmetro "dias de antecedência para alerta de prazo" configurável em runtime pelo Admin.

**Non-Goals:**
- Tempo real / websockets / push do navegador — o sino atualiza por polling (US não exige
  push).
- Preferências de notificação por usuário, notificação de devolução, digest de e-mail.
- Dashboard de KPIs (Épico 6) e canal/gestão LGPD (Épico 10) — changes futuros.

## Decisions

### D1 — Notificação gravada na transação do evento; e-mail enfileirado após o commit
A notificação interna é um INSERT na mesma transação que grava a `Tramitacao` de
despacho/conclusão — nasce atômica com o histórico. O enfileiramento de e-mail no Cloud
Tasks é uma chamada externa e **não** participa da transação do banco; é feito **após o
commit**, em modo best-effort, com `event_id` determinístico (dedup nativo). Assim, uma
falha ao enfileirar o e-mail nunca desfaz a notificação interna (satisfaz US 5.2 Cen.3), e
uma reexecução não duplica e-mail.

*Alternativa descartada:* publicar um evento de domínio e reagir de forma assíncrona
(outbox/worker). Rejeitada por overengineering para o MVP — os gatilhos já vivem in-process
em `despachar`, e a fila Cloud Tasks já é o mecanismo assíncrono.

```
Servidor (unid. A)        API (despachar)                 Cloud Tasks / e-mail
     |  POST /processos/{id}/despachar |                          |
     |------------------------------->|                          |
     |            BEGIN tx             |                          |
     |     INSERT Tramitacao(DESPACHO) |                          |
     |     INSERT Notificacao x N      |  (1 por servidor da unid. destino B)
     |            COMMIT               |                          |
     |            (após commit) enqueue_email x N ---------------->|  (event_id determinístico)
     |<-------------------------------|                          |
     |          200 OK                 |                          |
                                        \--- entrega assíncrona; falha => log + ACK (maxAttempts=1)
```

### D2 — Fan-out por linha: uma `Notificacao` por (destinatário, evento)
No momento da geração, resolve-se a lista de servidores da unidade alvo e grava-se **uma
linha por servidor**, com `lida_em` nullable por linha. O contador do sino é
`COUNT(*) WHERE usuario_id = me AND lida_em IS NULL`.

*Alternativa descartada:* uma `Notificacao` compartilhada + tabela `notificacao_leitura` por
usuário. Rejeitada: o volume (servidores por unidade) é baixo, e o fan-out por linha
simplifica leitura/expurgo/consulta sem joins. Trade-off aceito em D-Risk.

### D3 — Idempotência do alerta de prazo por guard de existência
A rotina de prazo seleciona `status IN ('Aberto','Em Tramitação') AND prazo_em <= hoje +
dias_antecedencia`. Para cada processo/servidor, só gera `alerta_prazo` se **não existir**
notificação `alerta_prazo` para aquele `(processo_id, usuario_id)` com o **mesmo `prazo_em`
vigente** (coluna `prazo_referencia` na notificação de alerta). O e-mail usa
`event_id = f"prazo:{processo_id}:{prazo_em}:{usuario_id}"` — dedup nativo do Cloud Tasks.
Reexecutar no mesmo dia, ou retomar após dias parados, não duplica (satisfaz o contrato de
`rotinas-agendadas`). Se o processo for despachado (muda `prazo_em`), um novo ciclo de alerta
passa a ser válido — comportamento desejado.

### D4 — Parâmetro em `sistema_config`, editado pelo router de configuração existente
Nova coluna `dias_antecedencia_alerta_prazo INT NOT NULL DEFAULT 2` no singleton
`sistema_config` (id=1). Edição pelo fluxo de configuração existente
(`routers/sistema_config.py`), protegido por `require_perfil(ADMINISTRADOR)` — reusa o padrão
de acesso negado já testado. A rotina de prazo lê o valor a cada execução (sem cache).

### D5 — Dois passos idempotentes acrescentados ao job diário
`jobs/entrypoint.py::run()` ganha, após arquivamento e purga de documentos, duas chamadas:
`verificar_prazos(session, agora)` (D3) e `expurgar_notificacoes_lidas(session, agora)`
(remove `WHERE lida_em IS NOT NULL AND lida_em < agora - 30d`; não-lidas são preservadas por
construção do WHERE). Ambos os serviços novos vivem em `services/` e são testáveis isolados,
espelhando `arquivar_vencidos`/`purgar_documentos_vencidos`.

```
Cloud Scheduler (diário) --> Cloud Run Job entrypoint.run()
   1. arquivar_vencidos                 (já existe)
   2. purgar_documentos_vencidos        (já existe)
   3. verificar_prazos:                 SELECT ativos com prazo_em na janela (dias_antecedencia)
        para cada (processo, servidor da unid. atual) sem alerta p/ prazo_em vigente:
            INSERT Notificacao(alerta_prazo)  ; enqueue_email("Prazo próximo")
   4. expurgar_notificacoes_lidas:       DELETE WHERE lida_em < agora - 30d
```

### D6 — Endpoints de notificação e contrato de tipos
Novo `routers/notificacoes.py`: `GET /notificacoes` (lista as próprias, aplicando a regra de
retenção de 30d para lidas), `GET /notificacoes/contador` (não lidas), `POST
/notificacoes/{id}/ler`, `POST /notificacoes/marcar-todas-lidas`. Toda operação escopa por
`usuario_id = current_user` — marcar/ler notificação de outro retorna acesso negado (padrão
`autorizacao`). Novas rotas/schemas exigem `pnpm gen:types` (CI falha via `gen:types:check`).

## Migrations (schema antes de endpoint)

1. **`create_notificacao`** — cria tabela `notificacao`:
   `id UUID PK` (gerado na app), `usuario_id UUID FK usuario`, `processo_id UUID FK processo`,
   `unidade_id UUID FK unidade`, `tipo` enum (`novo_processo`|`concluido`|`alerta_prazo`),
   `prazo_referencia DATE NULL` (só para `alerta_prazo`, base do guard de idempotência D3),
   `titulo`/`assunto`/payload mínimo para render, `lida_em TIMESTAMPTZ NULL`,
   `criado_em TIMESTAMPTZ NOT NULL`. Índices: `(usuario_id, lida_em)` para contador/lista;
   `(processo_id, usuario_id, tipo, prazo_referencia)` para o guard de prazo; `(lida_em)`
   para o expurgo.
2. **`add_dias_antecedencia_alerta_prazo`** — adiciona coluna em `sistema_config` com
   `DEFAULT 2` e backfill (a linha singleton id=1 recebe 2).

Ambas as migrations vêm antes dos endpoints/serviços correspondentes.

## Risks / Trade-offs

- **[Fan-out por linha multiplica registros por servidores da unidade]** → volume baixo no
  MVP (≤ 500 usuários, poucos servidores/unidade); índices em `(usuario_id, lida_em)` e o
  expurgo diário controlam o crescimento. Migração para modelo compartilhado fica em aberto
  se o volume crescer.
- **[E-mail enfileirado fora da transação (D1) pode enfileirar sem commit em caso de crash
  entre commit e enqueue]** → dedup por `event_id` torna o reenfileiramento seguro; a
  notificação interna (a fonte confiável) já está persistida. Perder um e-mail é aceitável
  (US 5.2 Cen.3 já prevê best-effort sem retry).
- **[Fan-out de e-mail em despacho para unidade grande gera N enqueues síncronos]** → é I/O
  para o Cloud Tasks (rápido); se necessário, agrupar/pós-processar fica em aberto. Fora do
  alvo de performance do MVP.
- **[Alerta de prazo depende de `prazo_em` estar corretamente definido na criação]** → já é
  o caso (`services/processo.py` define `prazo_em` na criação); a rotina apenas lê.

## Migration Plan

1. Aplicar as duas migrations Alembic (o job de deploy roda migrations no Cloud Run Job
   efêmero antes de trocar o serviço).
2. Deploy da API com router de notificações, geração nos serviços de despacho/conclusão e os
   dois passos novos no job diário.
3. `pnpm gen:types` e deploy do web com o componente de sino.
4. **Rollback:** as migrations são aditivas (nova tabela + nova coluna com default) — reverter
   o código não exige derrubar schema; a tabela `notificacao` pode ser mantida vazia sem
   efeito. Sem estado destrutivo.

## Open Questions

- **Corpo/campos exatos persistidos na `Notificacao`** — persistir snapshot mínimo (número,
  assunto, unidade origem/prazo) vs. resolver por join no render. Proposta: snapshot mínimo,
  para o histórico não mudar se o processo mudar depois. Decidir na implementação.
- **Atualização do sino no web** — polling em intervalo fixo vs. revalidação on-focus.
  Proposta: revalidar ao focar a aba + refetch ao abrir o painel; sem timer agressivo.
- **Gestor/Administrador recebem notificação?** As US 5.1/5.3/5.4 falam de "servidores da
  unidade". Proposta: destinatários = usuários vinculados à unidade alvo com perfil Servidor;
  Gestor acompanha pelo Kanban consolidado (Épico 2). Confirmar com o PRD na implementação.
