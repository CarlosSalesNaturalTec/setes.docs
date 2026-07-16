## Context

O change anterior `administracao-usuario-auditoria` entregou a flag `usuario.pode_auditar`
(booleana, ortogonal ao perfil) e os eventos de concessão/revogação em `log_seguranca`,
mas deixou o **consumo** para o Épico 9. Hoje a leitura de processo (`routers/processos.py`)
é guardada por `_exigir_acesso_ao_processo`, que delega a `tem_acesso_a_unidade` — ou seja,
mesmo um usuário com `pode_auditar = true` continua restrito à própria unidade. Não há
nenhuma rota de relatório consolidado; as agregações de KPIs existem em
`services/dashboard.py`, porém parametrizadas por **unidades geridas** de um Gestor e por
uma **janela fixa de 12 meses** para tempo médio.

Este change implementa US 9.1 (leitura irrestrita mediante `pode_auditar`) e US 9.2
(relatório consolidado em tela). Restrições herdadas: histórico imutável (INSERT de
evento, nunca UPDATE), status como máquina de estados explícita, toda regra de visibilidade
com caminho de "acesso negado" registrado em `log_seguranca`.

## Goals / Non-Goals

**Goals:**
- Conceder leitura irrestrita de qualquer processo (inclusive sigiloso) a usuários com
  `pode_auditar`, como caminho de autorização paralelo à visibilidade por unidade.
- Distinguir a rejeição de sigiloso-sem-permissão (mensagem própria do PRD) da rejeição
  genérica de unidade.
- Registrar em `log_seguranca` (`acesso_auditoria`) todo acesso que **só** a permissão de
  auditoria viabiliza — trilha rastreável de quem auditou o quê.
- Entregar relatório consolidado (total, tempo médio de tramitação, lista com status/unidade
  atual) filtrável por período/unidade/tipo, exibido em tela, reaproveitando a lógica de
  agregação do dashboard.

**Non-Goals:**
- Exportação do relatório em PDF/CSV (o PRD define como versão futura — US 9.2 Cen.1).
- Qualquer alteração no mecanismo de concessão/revogação da permissão (já entregue).
- Épico 10 (LGPD / anonimização) e Épico 4 (assinatura) — apenas expõe assinaturas já
  existentes onde houver.
- Novas tabelas ou colunas (a flag já existe).

## Decisions

### D1 — `pode_auditar` como bypass no seam de acesso ao processo, não novo perfil
`_exigir_acesso_ao_processo` (em `routers/processos.py`) passa a liberar o acesso quando
`usuario.pode_auditar` for verdadeiro, **antes** de aplicar a checagem de unidade. Mantém-se
o perfil intacto (a flag é ortogonal). Alternativa considerada: criar um perfil `AUDITOR` na
enum `PerfilUsuario` — **rejeitada**, porque o change anterior modelou a auditoria
deliberadamente como flag ortogonal (um Gestor pode também ser auditor), e um perfil novo
quebraria essa ortogonalidade e exigiria migração de dados.

### D2 — Mensagem de rejeição específica só para sigiloso-sem-permissão
A regra de decisão no seam de leitura fica:

```
se usuario.pode_auditar:                      → concede + registra acesso_auditoria (se fora da unidade)
senão se tem_acesso_a_unidade(processo):      → concede (visibilidade normal, sem log)
senão se processo.sigiloso:                   → 403 "Acesso restrito — solicite autorização
                                                 ao Administrador" + log acesso_negado
senão:                                         → 403 MSG_ACESSO_NEGADO_PROCESSO (genérica de
                                                 unidade, já existente) + log acesso_negado
```

Assim a mensagem do PRD (US 9.1 Cen.2) só aparece quando há de fato sigilo em jogo; processo
comum fora da unidade continua com a mensagem genérica. Alternativa: usar a mensagem
específica para toda rejeição — **rejeitada** por vazar semântica de sigilo e divergir do PRD.

### D3 — Registrar `acesso_auditoria` apenas quando a permissão é o que viabiliza o acesso
Novo valor `acesso_auditoria` na enum `TipoEventoLog`. O evento é inserido **somente** no
ramo `pode_auditar` do seam **e** quando o usuário **não** teria acesso pela regra de unidade
(evita ruído quando o auditor lê processo da própria unidade, ao qual já teria acesso). Isso
mantém o log como trilha do que a auditoria *destravou*, não um duplo-registro de toda
leitura. O registro é INSERT imutável, coerente com a invariante de histórico.

### D4 — Relatório reaproveita a *lógica* de agregação do dashboard, não as funções tal como estão
As funções de `services/dashboard.py` são parametrizadas por `unidades: list[UUID]` (bom: o
relatório passa **todas** as unidades, ou o subconjunto do filtro) — mas duas divergências
impedem reuso direto:
- `total_ativos` conta só `Aberto`+`Em Tramitação`; o relatório quer **total de processos no
  período** (todos os status criados na janela de filtro).
- `tempo_medio_tramitacao_dias` usa janela **fixa de 12 meses**; o relatório usa o **período
  informado** nos filtros.

Decisão: criar `services/relatorio_auditoria.py` que **reusa o padrão de cálculo** (média de
`concluido_em − criado_em` em dias corridos; contagem por `unidade_atual_id`/status) mas com a
janela e o recorte de status próprios do relatório. Alternativa: generalizar as funções do
dashboard para aceitar janela e conjunto de status — **adiada**, para não arriscar regressão
nos KPIs do Épico 6 já entregues; pode virar refactor futuro.

### D5 — Semântica dos filtros do relatório
- **período** → filtra por `processo.criado_em` dentro do intervalo (total "no período").
- **unidade** → filtra por `unidade_atual_id` (coerente com "unidade atual" da lista do PRD);
  vazio = todas as unidades.
- **tipo** → filtra por `tipo_processo_id`; vazio = todos.
Estado vazio (nenhum processo) → mensagem `"Nenhum dado encontrado para os filtros
informados"` (US 9.2 Cen.2), distinta de tempo médio `None` (sem concluídos, mas com
processos), que exibe "—".

### D6 — Autorização da rota de relatório por `pode_auditar`, não por perfil
Nova rota em `routers/auditoria.py` (montada em `main.py`) guardada por uma dependência que
exige `pode_auditar = true`; rejeição registra `acesso_negado`. Reusa `get_current_user`; não
usa `require_perfil` (a permissão é ortogonal ao perfil).

## Sequência — leitura de processo por Auditor (US 9.1)

```
Auditor(web)        API /processos/{id}        autorizacao/seam        log_seguranca(DB)
    |                       |                          |                      |
    |-- GET (Bearer) ------>|                          |                      |
    |                       |-- get_current_user ----->|                      |
    |                       |   (pode_auditar=true)    |                      |
    |                       |-- _exigir_acesso_ao_processo ---------->|       |
    |                       |     pode_auditar? sim; fora da unidade? sim     |
    |                       |                          |-- INSERT acesso_auditoria -->|
    |                       |<-- concede ------------- |                      |
    |<-- 200 processo ------|                          |                      |
    |    completo           |                          |                      |
   (se pode_auditar=false e processo.sigiloso: 403 "Acesso restrito…" + INSERT acesso_negado)
```

## Migrations Alembic (schema antes de endpoint)

- **Migration única:** `ALTER TYPE tipoeventolog ADD VALUE 'acesso_auditoria'` (adição de
  valor de enum, **não retroativa**, sem backfill). Segue o precedente das migrations de enum
  do change de auditoria (`permissao_auditoria_concedida` etc.). Nenhuma alteração estrutural
  de tabela, nenhuma coluna nova, nenhum índice novo obrigatório (a leitura por
  `unidade_atual_id`/`tipo_processo_id`/`criado_em` usa colunas já existentes).
- **Nota operacional:** `ADD VALUE` não roda dentro de bloco transacional em algumas versões
  do Postgres/Alembic — a migration deve emitir o `ALTER TYPE` isolado (padrão já usado nas
  migrations de enum anteriores deste repo).

## API (depois do schema)

- `routers/processos.py` — ajuste em `_exigir_acesso_ao_processo` conforme D1/D2/D3; afeta
  `GET /processos/{id}`, `/{id}/historico` e a leitura de documentos (`routers/documentos.py`)
  que compartilham a checagem de acesso ao processo.
- `routers/auditoria.py` (novo) — `GET /auditoria/relatorio?inicio&fim&unidade_id&tipo_id`,
  Auditor-only (D6), retornando total, tempo médio e lista (status atual + unidade atual).
- `services/relatorio_auditoria.py` (novo) — agregações do relatório (D4/D5).
- `schemas/` — `RelatorioAuditoriaResponse`, item de lista e filtros.
- **Contrato:** rotas/schemas novos → `pnpm gen:types` (CI `types-drift` falha se defasado).

## Frontend

- Nova rota autenticada (ex.: `apps/web/app/auditoria/relatorios/page.tsx`) com formulário de
  filtros (período/unidade/tipo), render do consolidado em tela e estado vazio. Visível apenas
  a usuários com `pode_auditar` (gate no `auth-provider`/navegação). A leitura de processo já
  existente passa a funcionar para o Auditor sem alteração de tela (o backend é quem destrava).

## Risks / Trade-offs

- **[Divergência de agregação vs. dashboard]** relatório e KPIs podem exibir números
  diferentes para "tempo médio" por usarem janelas distintas (período do filtro vs. 12 meses
  fixos). → Mitigação: rotular claramente na UI o período do relatório; documentar que são
  métricas de recortes diferentes, por design (D4).
- **[Custo de log de auditoria]** acesso intenso de um auditor pode gerar muitos INSERTs em
  `log_seguranca`. → Mitigação: registrar só o acesso destravado pela permissão (D3), não toda
  leitura; volume esperado é baixo (perfil de fiscalização, não operação diária).
- **[`ADD VALUE` não transacional]** falha no meio da migration de enum. → Mitigação: emitir o
  `ALTER TYPE` isolado e idempotente (checar existência do valor antes de adicionar), seguindo
  o padrão das migrations de enum já no repo; retomada = re-rodar `alembic upgrade head`.
- **[Auditor vê dado pessoal]** o relatório e o detalhe expõem CPF/CNPJ/nome de interessado.
  → Mitigação: é base legal legítima de fiscalização (distinta da consulta pública, que
  oculta); acesso restrito a `pode_auditar` e todo acesso destravado é registrado.

## Migration Plan

1. Rodar a migration de enum (`acesso_auditoria`) no Cloud Run Job de migrations **antes** de
   trocar o serviço (fluxo de deploy já existente).
2. Deploy da API com o seam ajustado e a rota de relatório.
3. `pnpm gen:types` commitado; deploy do web com a nova rota.
4. **Rollback:** o valor de enum é aditivo e inócuo se não usado; reverter API/web para a
   versão anterior não exige desfazer a migration (o valor extra fica órfão, sem impacto).

## Open Questions

- O relatório deve permitir filtrar por **unidade por onde o processo passou** (via
  `tramitacao`), além de unidade atual? O PRD só menciona "unidade atual" na lista — assumido
  filtro por `unidade_atual_id` (D5); revisitar se surgir necessidade de fiscalização por
  trânsito histórico.
- "Tempo médio de tramitação" no relatório considera apenas processos **concluídos** no
  período (como o dashboard) ou também os em andamento (parcial até agora)? Assumido: só
  concluídos, alinhado ao dashboard e ao significado de "tramitação" (criação→conclusão).
