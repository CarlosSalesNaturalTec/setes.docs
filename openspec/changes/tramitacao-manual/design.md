## Context

A tramitação hoje é inteiramente derivada do roteiro. `services/processo.py`
depende de `roteiro_snapshot` (`proxima_etapa`, `etapa_anterior`, `is_ultima`,
`is_primeira`) e move o processo por `ordem_atual`:

```
despachar()  →  is_ultima(etapas, ordem_atual) ? concluir : ordem_atual += 1
devolver()   →  is_primeira(...) ? bloquear    : ordem_atual -= 1
```

O destino nunca é escolhido: é `etapas[ordem_atual ± 1].unidade_id`. A conclusão
é um ramo interno de `despachar()` que dispara um 409 pedindo confirmação.

Fatos que enquadram o design:

- O banco em avaliação **pode ser refeito** (decisão do cliente: dados são de
  teste). Isso elimina a necessidade de backfill sofisticado nas migrations —
  mas elas continuam escritas para aplicar sobre a base existente.
- `Tramitacao` já é INSERT-only com `status_resultante` NOT NULL, e já possui o
  padrão de **evento ortogonal ao status** (`services/sigilo.py`:
  `status_resultante=processo.status`). Reatribuir encaixa nesse padrão.
- O CHECK `ck_tramitacao_responsavel` (migration `0004`) garante
  `responsavel_id` obrigatório para todos os eventos exceto
  `arquivamento_automatico` — vale igualmente para os três tipos novos.
- `unidade_origem_id` do processo é imutável desde a criação e continua sendo a
  base da visibilidade por origem (`visibilidade-processos-origem`).

## Goals / Non-Goals

**Goals:**

- Destino explícito (unidade + setor + servidor) em toda movimentação.
- Três tipos de ação com semânticas distintas e não sobrepostas.
- Conclusão como ação própria.
- Histórico imutável enriquecido com setor, servidor e mensagem, mantendo-se
  INSERT-only.
- Notificação dirigida à pessoa responsável, não à unidade inteira.
- Remoção completa do roteiro, sem deixar código morto.

**Non-Goals:**

- **Nenhuma mudança na máquina de estados** (ver D4).
- **Nenhuma mudança em autorização.** O acesso continua por **unidade**:
  `tem_acesso_a_unidade`, `require_acesso_unidade`, `_exigir_acesso_ao_processo`
  e `_exigir_leitura_ao_processo` ficam intocados. Setor e servidor definem
  *roteamento e visão*, não fronteira de permissão.
- Nenhuma mudança no Kanban, dashboard ou filtros — é o change
  `kanban-por-servidor`.
- Nenhuma mudança em sigilo, documentos, consulta pública, LGPD ou arquivamento
  automático (que continua sendo a única via para `arquivado`).
- Sem tramitação em lote, sem delegação temporária, sem substituto de férias.

## Decisions

### D1 — `processo.servidor_atual_id` e `setor_atual_id` como responsável corrente

Duas colunas novas, ambas NOT NULL:

```
processo.setor_atual_id     FK → setor
processo.servidor_atual_id  FK → usuario
```

Na criação, `servidor_atual_id = criado_por_id` e `setor_atual_id =
criador.setor_id` — **o processo nasce atribuído ao criador** (decisão do
cliente), de modo que aparece no Kanban dele antes de qualquer tramitação.

Alternativa rejeitada: derivar o responsável atual do último evento de
`tramitacao`. Exigiria um `DISTINCT ON` em toda montagem de Kanban e em toda
checagem de ação; a coluna denormalizada é lida em todo request e escrita raramente.

### D2 — Três tipos de ação com regras de destino distintas

```
┌────────────┬────────────────────────────┬─────────────────┬──────────────────┐
│ Ação       │ Destino                    │ Status          │ Exige            │
├────────────┼────────────────────────────┼─────────────────┼──────────────────┤
│ Envio      │ unidade/setor/servidor     │ → em_tramitacao │ mensagem         │
│            │ livres; servidor ≠ atual   │                 │                  │
│ Devolução  │ resolvido automaticamente  │ → em_tramitacao │ motivo +         │
│            │ (remetente anterior)       │                 │ justificativa    │
│ Reatribuir │ MESMA unidade; setor livre │ INALTERADO      │ justificativa    │
│            │ nela; servidor ≠ atual     │ (ortogonal)     │                  │
└────────────┴────────────────────────────┴─────────────────┴──────────────────┘

   Unidade errada?  →  DEVOLUÇÃO        Setor/pessoa errados?  →  REATRIBUIR
```

A divisão dá significado próprio a cada tipo e torna mensurável a taxa de erro de
atribuição. Alternativa rejeitada: Reatribuir com destino livre — viraria um
Envio com rótulo diferente e se sobreporia à Devolução.

### D3 — Devolução resolve o destino sozinha

O destino é sempre "quem me enviou": o **último** evento de `tramitacao` do tipo
`envio` ou `reatribuicao` cujo `servidor_destino_id` é o servidor atual. A UI só
pede motivo e justificativa. Se não existir tal evento (processo nunca tramitou,
ainda com o criador), a devolução é bloqueada com 409 — não há para onde voltar.

Isso substitui a regra antiga "não é possível devolver na unidade de origem do
roteiro", que deixa de fazer sentido sem roteiro.

### D4 — Reatribuir é ortogonal ao status: a máquina de estados **não muda**

Reatribuir grava `status_resultante = processo.status` e **não chama**
`validar_transicao` — exatamente o padrão de `services/sigilo.py:26` e dos
eventos de documento. Consequência: `_TRANSICOES` em
`services/processo_estado.py` fica **idêntica**, porque as demais transições já
estão cobertas:

```
   ABERTO ──── Envio ────▶ EM_TRAMITACAO ──── Envio/Devolução ──┐
      │                          │           ▲                  │
      │                          │           └──────────────────┘
      │                     Concluir
   Concluir                      │
      │                          ▼
      └───────────────────▶ CONCLUÍDO ──(rotina automática)──▶ ARQUIVADO

   ⟲ Reatribuir — self-loop em ABERTO e EM_TRAMITACAO, não transiciona
```

Um processo `aberto` reatribuído continua `aberto`; `em_tramitacao` continua
`em_tramitacao`. **Zero alteração em `processo_estado.py`.**

### D5 — Quem pode executar cada ação

```
Envio       servidor_atual
Devolução   servidor_atual
Reatribuir  servidor_atual  ∪  remetente da última tramitação
                            ∪  gestor da unidade atual
Concluir    servidor_atual  ∪  gestor da unidade atual
```

Reatribuir tem o conjunto mais amplo (decisão do cliente) porque o erro pode ser
percebido por quem recebeu, por quem errou o destino, ou pela chefia. A
verificação é **em cima da autorização por unidade existente**, não em vez dela:
o usuário precisa primeiro passar por `_exigir_acesso_ao_processo` (unidade) e
só então pela regra de papel acima. Rejeição grava `log_seguranca`.

### D6 — `responsavel_id` ≠ `servidor_origem_id`

`responsavel_id` = **quem agiu**. `servidor_origem_id`/`servidor_destino_id` =
**quem deteve** o processo. Quando o **gestor** reatribui, ele é o responsável
mas nunca foi detentor — e por isso não entra no conjunto de participantes usado
pelo Kanban (change `kanban-por-servidor`):

```
participantes = { criado_por_id } ∪ { servidor_origem_id } ∪ { servidor_destino_id }
```

O gestor já enxerga o processo pelo escopo de unidade; incluí-lo como
participante o faria carregar o processo no Kanban pessoal para sempre.

### D7 — `despacho` renomeado para `envio` no enum

`TipoEventoTramitacao.DESPACHO` → `ENVIO`, e `REATRIBUICAO` adicionado. O
vocabulário da tela passa a ser "Envio" (pedido do cliente), e manter `despacho`
no enum criaria divergência entre código e interface. Como o banco será refeito,
a migration faz `ALTER TYPE ... RENAME VALUE` + `ADD VALUE` sem necessidade de
backfill de linhas.

`CONCLUSAO`, `ARQUIVAMENTO_AUTOMATICO`, `MARCAR_SIGILO`, `REMOVER_SIGILO`,
`REMOVER_DOCUMENTO` e `RESTAURAR_DOCUMENTO` permanecem inalterados.

### D8 — Notificação por pessoa, não por unidade

`services/notificacao.py::gerar_notificacoes` hoje faz fan-out para todos os
servidores da unidade de destino (`servidores_da_unidade`). Passa a receber um
**destinatário único** (`usuario_id`). Dois tipos novos em `TipoNotificacao`:

- `REATRIBUIDO_PARA_VOCE` — ao servidor que passou a deter o processo.
- `DESTINO_CORRIGIDO` — ao **remetente original** cuja atribuição foi corrigida
  (decisão do cliente: ele precisa saber que errou o destino). Emitida apenas
  quando o remetente original existe e não é o próprio autor da reatribuição.

`NOVO_PROCESSO` e `CONCLUIDO` permanecem, mas com destinatário único.

### D9 — Prazo não é afetado por Reatribuir

`prazo_dias` e `prazo_em` ficam intocados na reatribuição (decisão do cliente):
um erro interno de atribuição não reinicia o relógio do interessado. Envio e
Devolução também não alteram prazo — comportamento já vigente.

### D10 — Migrations `0022`, `0023`, `0024` (schema antes de endpoint)

- `0022_processo_setor_servidor_atual` — adiciona `processo.setor_atual_id` e
  `processo.servidor_atual_id`; backfill `servidor_atual_id = criado_por_id` e
  `setor_atual_id` = setor do criador; então `SET NOT NULL`.
  `down_revision = "0021_usuario_setor_e_campos"`.
- `0023_tramitacao_setor_servidor_mensagem` — adiciona as quatro FKs e
  `mensagem` em `tramitacao` (todas nullable — eventos ortogonais como sigilo não
  as preenchem); `ALTER TYPE tipo_evento_tramitacao RENAME VALUE 'despacho' TO
  'envio'` e `ADD VALUE 'reatribuicao'`; `ADD VALUE` nos dois tipos novos de
  `tipo_notificacao`. `down_revision = "0022_..."`.
- `0024_remover_roteiro` — remove `processo.roteiro_id` e `processo.ordem_atual`,
  depois `DROP TABLE roteiro_etapa` e `DROP TABLE roteiro` (nessa ordem, pela FK).
  `down_revision = "0023_..."`.

Três revisions em vez de uma para manter `downgrade` reversível por etapa e a
cadeia legível. `ADD VALUE` em enum não roda dentro de transação em Postgres
antigo — a migration usa `COMMIT` explícito antes, no padrão já usado por
`0014_lgpd_enums`.

### Fluxo principal — Reatribuição

```
Servidor B (recebeu errado)    web (/processos/{id})         api
     │  abre o processo              │                        │
     │  clica "Tramitar"             │                        │
     │  tipo = Reatribuir            │                        │
     │───────────────────────────────▶ GET /unidades/{u}/setores
     │  (unidade FIXA = atual)       │────────────────────────▶
     │  escolhe setor                │◀──────────────────────── setores da unidade
     │───────────────────────────────▶ GET /usuarios?setor_id=
     │  escolhe servidor C           │◀──────────────────────── servidores ativos
     │  escreve justificativa        │                        │
     │───────────────────────────────▶ POST /processos/{id}/reatribuir
     │                               │────────────────────────▶
     │                               │   D5: B é servidor_atual → autorizado
     │                               │   D2: unidade destino == unidade atual
     │                               │   D2: servidor C != servidor B
     │                               │   ── transação única ──────────────
     │                               │   INSERT tramitacao (reatribuicao,
     │                               │     servidor_origem=B, destino=C,
     │                               │     responsavel=B, justificativa,
     │                               │     status_resultante = status atual)  D4
     │                               │   UPDATE processo SET servidor_atual=C,
     │                               │     setor_atual=<novo>    (status e
     │                               │     prazo INALTERADOS)          D9
     │                               │   INSERT notificacao → C (reatribuido)  D8
     │                               │   INSERT notificacao → A (destino
     │                               │     corrigido; A = remetente original)  D8
     │                               │   ── commit ──────────────────────
     │                               │◀──────────────────────── 200
     │  "Processo reatribuído para   │                        │
     │   C. Prazo mantido."          │      (após commit: enfileira e-mails)
```

## Risks / Trade-offs

- [**Maior risco do plano**: `tests/helpers_processo.py` é usado por quase toda
  a suíte e exige roteiro] → a atualização do helper é a **primeira** tarefa de
  teste do change, feita antes das demais, para que a suíte volte a compilar em
  bloco em vez de arquivo a arquivo. Como a suíte não é paralelizável, uma
  quebra ampla é cara de diagnosticar.
- [Remover o roteiro elimina a garantia de que o processo percorre as etapas
  certas] → é exatamente o que o cliente pediu; o controle passa a ser humano.
  Mitigação de produto: o histórico registra todos os detentores, tornando
  auditável quem desviou o fluxo. Registrado como decisão do cliente, não como
  omissão.
- [Destino livre permite enviar processo para unidade sem relação com o assunto]
  → nenhuma validação de "destino plausível" é introduzida (não foi pedida e não
  há regra objetiva). A Devolução existe justamente para corrigir.
- [`servidor_atual_id` NOT NULL torna a desativação de usuário mais delicada] →
  a guarda existente (`contar_processos_sob_responsabilidade`, US 8.4) passa a
  contar por `servidor_atual_id`, ficando **mais** precisa do que a heurística
  atual de "último responsável". Ajuste incluído nas tarefas.
- [`ALTER TYPE ... RENAME VALUE` é irreversível de forma limpa no downgrade] → o
  downgrade renomeia de volta; o valor `reatribuicao` adicionado não pode ser
  removido de um enum Postgres, o que é aceito (downgrade deixa um valor órfão,
  sem linhas). Documentado na docstring da migration.
- [Notificação `DESTINO_CORRIGIDO` pode ser lida como exposição de erro do
  colega] → o texto é factual e sem juízo ("O processo X que você encaminhou foi
  reatribuído para <servidor>"), e só o remetente original recebe.
- [PRD Épico 2 descreve o modelo roteirizado em vários cenários] → a reescrita do
  PRD é tarefa explícita do change, não follow-up.
