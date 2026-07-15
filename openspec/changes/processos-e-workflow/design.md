## Context

`identidade-e-estrutura-organizacional` (arquivado) deixou o schema de identidade/estrutura e a migration head `0002_identidade_estrutura`, além das primitivas de autorização (`app/security/autorizacao.py`: `get_current_user → require_perfil → require_acesso_unidade`) e do padrão de log imutável (`log_seguranca`). Este change cria a primeira entidade de negócio movimentável (`processo`) e o primeiro histórico de tramitação de processo — o precedente de imutabilidade já existe em `log_seguranca`.

Restrições que moldam este design:
- Stack fixa: FastAPI + SQLAlchemy 2.x + Alembic, PostgreSQL, Next.js/App Router. PKs UUID geradas na aplicação (`default=uuid.uuid4`), enums via `SAEnum`, timestamps `timezone=True` com `server_default=func.now()` — mesmas convenções de `models.py`.
- Histórico de tramitação é **imutável** por regra do projeto (INSERT, nunca UPDATE/DELETE).
- Status é **máquina de estados explícita**, nunca campo de texto livre nem drag-and-drop (Kanban é só visualização no MVP).
- Roteiro já é **versionado**: `Roteiro` tem `vigente: bool` e `tipo_processo_id`; uma alteração de roteiro cria um novo `Roteiro` (novo `vigente=True`) e nunca muta `roteiro`/`roteiro_etapa` existentes. Este change consome esse versionamento, não o reescreve.
- Número do processo: `AAAA/NNNNNN`, sequencial de 6 dígitos reiniciado por ano, **expansível sem limite superior** (US 2.1 Cen.1).
- Escala do MVP: ~500 usuários ativos, 10.000 processos simultâneos, pico de 50–100 requisições concorrentes.
- Contrato front↔back é **gerado** — toda mudança de schema/rota exige `pnpm gen:types`.

## Goals / Non-Goals

**Goals:**
- Modelar `processo`, `processo_interessado`, `tramitacao` e `processo_contador_ano` numa única migration Alembic (`0003`), encadeada em `0002_identidade_estrutura`.
- Geração do número `AAAA/NNNNNN` atômica, livre de corrida e de duplicidade, com reinício anual e expansão de dígitos.
- Snapshot do roteiro na criação, reutilizando `Roteiro.vigente` sem copiar etapas.
- Máquina de estados explícita (Aberto → Em Tramitação → Concluído → [Arquivado reservado]) com transições validadas no serviço, cada uma emitindo evento imutável em `tramitacao`.
- Despacho e devolução determinísticos por posição no roteiro-snapshot.
- Consumir a primitiva de autorização existente para o filtro de Kanban/busca/detalhe por unidade (fecha US 1.4) e popular "Meu Perfil" (fecha US 1.5 Cen.1) e a contagem real de pendentes na desativação de unidade (US 8.1 Cen.3).

**Non-Goals:**
- **Sigilo de processo (US 2.6)** e **arquivamento automático (US 2.5, 1º Cloud Run Job)** — Change B. O enum de status já nasce com `arquivado`, mas nenhuma transição o alcança aqui; a coluna `sigiloso` **não** é criada neste change (entra no Change B).
- **Notificações (Épico 5)** — o despacho move o processo e registra o evento, mas **não** enfileira e-mail nem gera notificação interna de "novo processo recebido".
- **Documentos/anexos (Épico 3)** e **assinatura (Épico 4)** — "Meu Perfil" mantém a seção "documentos assinados" vazia.
- **Dashboard (Épico 6)** e **consulta pública (Épico 7)** — nenhum endpoint público nem rate limiting neste change (todas as rotas são autenticadas).
- **Parâmetros configuráveis (US 8.5)** — o prazo de alerta e afins não são consumidos aqui; o prazo do processo é dado de entrada por processo, não parâmetro global.

## Decisions

### D1 — Número do processo: contador por ano com upsert-incremento atômico
**Escolha:** tabela `processo_contador_ano` (`ano int PK`, `ultimo_sequencial int not null`). A alocação do número ocorre **na mesma transação** que insere o `processo`, por um único statement atômico:
```sql
INSERT INTO processo_contador_ano (ano, ultimo_sequencial) VALUES (:ano, 1)
ON CONFLICT (ano) DO UPDATE
  SET ultimo_sequencial = processo_contador_ano.ultimo_sequencial + 1
RETURNING ultimo_sequencial;
```
O número é formatado como `f"{ano}/{seq:06d}"` — o especificador `:06d` garante o piso de 6 dígitos e **expande naturalmente** para 7, 8+ dígitos sem limite (US 2.1 Cen.1).
**Por quê:** o `ON CONFLICT DO UPDATE ... RETURNING` toma lock de linha no Postgres e resolve alocação concorrente num só round-trip. Como o incremento vive na mesma transação do INSERT do processo, um rollback desfaz o incremento — sem "buracos" na numeração por transações abortadas.
**Expansão e alerta:** ao cruzar 1.000.000 (7 dígitos) e 10.000.000 (8 dígitos), registrar evento em log de sistema; ao atingir 10.000.000 num ano, emitir alerta administrativo (US 2.1 Cen.1). Registrado via `log_seguranca` com um `tipo_evento` novo (`expansao_numero_processo` / `alerta_capacidade`) — reaproveita o log imutável existente em vez de criar tabela.
**Alternativas consideradas:** sequence Postgres por ano (reset anual é manual e gaps em rollback são inerentes a sequences — rejeitado); `SELECT ... FOR UPDATE` + `UPDATE` (dois statements, mesma semântica, mais round-trips).

### D2 — Snapshot de roteiro: FK para o `Roteiro` vigente, sem cópia de etapas
**Escolha:** `processo.roteiro_id` FK → `roteiro.id`, resolvido na criação como o `Roteiro` com `tipo_processo_id = tipo` e `vigente = True`. Como `roteiro`/`roteiro_etapa` são imutáveis (nova versão = nova linha, a antiga vira `vigente=False` mas permanece), a FK é um snapshot permanente — processos em andamento seguem o roteiro vigente na criação mesmo após o tipo mudar (US 8.2 Cen.2). Nenhuma etapa é duplicada.
**Validação:** se o tipo não tem `Roteiro` vigente **ou** o roteiro vigente tem zero `roteiro_etapa`, a criação é rejeitada com a mensagem da US 2.1 Cen.3c.
**Por quê:** aproveita o versionamento que já existe; evita desnormalização e divergência entre "roteiro do processo" e "roteiro do tipo à época".

### D3 — Posição no roteiro: ordinal explícito em `processo.ordem_atual`
**Escolha:** `processo.ordem_atual int` guarda a `ordem` (de `roteiro_etapa`) da etapa em que o processo está. Despacho → `ordem_atual + 1`; devolução → `ordem_atual - 1`. A unidade destino/anterior é a `roteiro_etapa` do snapshot com aquela `ordem`.
**Por quê:** despacho e devolução tornam-se determinísticos e independem de a unidade aparecer mais de uma vez no roteiro; a devolução (US 2.2b) precisa da unidade **imediatamente anterior no roteiro**, que é `ordem_atual - 1` por definição — não "de onde veio por último". `ordem_atual == 0` (primeira etapa) ⇒ devolução bloqueada (US 2.2b Cen.2); `ordem_atual == última` ⇒ despacho vira conclusão (US 2.2 Cen.2/4).
**Coerência:** `processo.unidade_atual_id` é redundante com `roteiro_etapa[ordem_atual].unidade_id`, mas é mantido desnormalizado para o filtro de Kanban por unidade ser um índice simples (`WHERE unidade_atual_id = ...`) sem join ao roteiro. Os dois são atualizados juntos, na mesma transação da transição.

### D4 — Máquina de estados no serviço; `tramitacao` imutável
**Escolha:** enum `StatusProcesso` = [`aberto`, `em_tramitacao`, `concluido`, `arquivado`]. Transições válidas validadas em `services/processo.py`:
`aberto → em_tramitacao` (primeiro despacho), `em_tramitacao → em_tramitacao` (despacho/devolução intermediários), `{aberto|em_tramitacao} → concluido` (despacho na última etapa). `→ arquivado` **não é implementado** aqui. Qualquer transição fora dessa tabela levanta erro — não há endpoint que escreva `status` como texto livre.
Cada transição insere uma linha em `tramitacao` **na mesma transação**. `tramitacao` é **append-only**: o serviço só faz INSERT; não há rota nem método de update/delete. Endurecimento opcional (tarefa marcada como opcional): `REVOKE UPDATE, DELETE` na tabela para o role de aplicação, ou trigger `BEFORE UPDATE/DELETE ... RAISE`.
**Eventos:** `TipoEventoTramitacao` = [`despacho`, `devolucao`, `conclusao`]. A **criação não é evento de tramitação** — "Meu histórico" de um processo recém-criado mostra "Nenhuma movimentação registrada" + data de criação (US 2.4 Cen.2); a autoria da criação vive em `processo.criado_por_id`/`criado_em`.

### D5 — Prazo: `prazo_dias` (entrada) + `prazo_em` (data derivada fixada na criação)
**Escolha:** `prazo_dias int` (dias corridos informados) e `prazo_em date` = `date(criado_em) + prazo_dias`, calculado uma vez na criação. "Dias restantes" no card = `prazo_em - hoje`; vencido quando negativo (US 2.3 Cen.4). O prazo é do processo (fixo desde a criação), não reiniciado por unidade no MVP.
**Por quê:** materializar `prazo_em` torna a ordenação do Kanban por prazo e o destaque de vencidos um índice/ordenação simples, sem recomputar por render.

### D6 — Autorização por unidade: consumir a primitiva existente
**Escolha:** reutilizar `require_acesso_unidade` de `app/security/autorizacao.py`. Kanban/busca do Servidor filtram `processo.unidade_atual_id = current_user.unidade_id`; do Gestor, `unidade_atual_id IN (unidades de unidade_gestor)`; detalhe e ações (despachar/devolver) chamam `require_acesso_unidade(processo.unidade_atual_id)`. Toda rejeição — inclusive acesso direto por URL a processo de outra unidade — grava `log_seguranca` (`tipo_evento=acesso_negado`), fechando US 1.4 Cen.2 na prática.
**"Meu Perfil" (US 1.5 Cen.1):** a lista de atuação = processos onde `criado_por_id = user` **OU** existe `tramitacao.responsavel_id = user`, ordenada por data da ação — visível independentemente da unidade atual do processo (o histórico de atuação acompanha o usuário mesmo após transferência, US 1.4 Cen.3).
**Desativação de unidade (US 8.1 Cen.3):** a contagem antes fixada em zero passa a ser `COUNT(processo WHERE unidade_atual_id = unidade AND status IN ('aberto','em_tramitacao'))`.

### D7 — Validação de CPF/CNPJ: utilitário puro, sem dependência externa
**Escolha:** validador de dígito verificador em Python puro (`app/services/documento_fiscal.py`), aplicado no schema Pydantic do interessado quando `documento` é informado. CPF/CNPJ são **opcionais** (só nome é obrigatório); quando presentes, `tipo_documento` (`cpf`|`cnpj`) determina o algoritmo. Mensagens exatas da US 2.1 Cen.3/3b.
**Por quê:** regra estável e pequena; dependência externa não se justifica.

## Sequência — Despacho (US 2.2)

```
Servidor        Web (Next.js)         API (FastAPI)                 PostgreSQL
   │  clica "Despachar"  │                    │                          │
   ├────────────────────>│  POST /processos/{id}/despachar              │
   │                     ├───────────────────>│                          │
   │                     │        require_acesso_unidade(unidade_atual)  │
   │                     │                    │ (nega → log_seguranca)   │
   │                     │                    ├─ BEGIN ─────────────────>│
   │                     │                    │  lê processo + roteiro-snapshot (etapas)
   │                     │                    │  calcula próxima etapa (ordem_atual+1)
   │                     │   se última etapa: │                          │
   │                     │<── 409 "confirmar conclusão?" ────────────────┤
   │  confirma           │  POST .../despachar?confirmar=true            │
   │                     │                    │  UPDATE processo (status, unidade_atual, ordem_atual)
   │                     │                    │  INSERT tramitacao (evento imutável)
   │                     │                    ├─ COMMIT ────────────────>│
   │                     │<── 200 processo atualizado ───────────────────┤
   │<────────────────────┤  Kanban reflete no próximo refresh           │
```
Devolução (US 2.2b) segue o mesmo fluxo com `ordem_atual-1`, motivo obrigatório e bloqueio em `ordem_atual==0`. **Nenhuma** notificação/e-mail é disparada neste change (Épico 5).

## Migration Plan (schema antes de endpoint)

Migration Alembic `0003_processos_workflow` (`down_revision = "0002_identidade_estrutura"`; revision ≤ 32 chars). Cria, nesta ordem:

1. **Enums**: `statusprocesso`, `tipoeventotramitacao`, `tipodocumentointeressado` (`cpf`|`cnpj`), `tipoparticipacaointeressado` (`requerente`|`representado`|`terceiro`), `motivodevolucao` (`documentacao_insuficiente`|`correcao_dados`|`diligencia_complementar`). Novos valores em `tipoeventolog` para D1 (expansão/alerta de capacidade).
2. **`processo_contador_ano`** (`ano PK`, `ultimo_sequencial`).
3. **`processo`** (`id`, `numero` unique, `assunto`, `tipo_processo_id` FK, `roteiro_id` FK, `status`, `unidade_atual_id` FK, `unidade_origem_id` FK, `ordem_atual`, `prazo_dias`, `prazo_em`, `criado_por_id` FK, `criado_em`, `concluido_em` nullable).
4. **`processo_interessado`** (`id`, `processo_id` FK, `nome`, `documento` nullable, `tipo_documento` nullable, `tipo_participacao` nullable).
5. **`tramitacao`** (`id`, `processo_id` FK, `tipo_evento`, `unidade_origem_id` FK nullable, `unidade_destino_id` FK nullable, `responsavel_id` FK, `status_resultante`, `motivo` nullable, `justificativa` text nullable, `criado_em`).

**Índices:** `processo(numero)` unique; `processo(unidade_atual_id, status)` (Kanban por unidade + coluna); `processo(tipo_processo_id)`; `processo(criado_por_id)` ("Meu Perfil"); `tramitacao(processo_id, criado_em)` (linha do tempo); `tramitacao(responsavel_id)` ("Meu Perfil"); `processo_interessado(processo_id)`.

Só após a migration, a camada de API: router `processos` (criar, listar/Kanban, detalhe, histórico, despachar, devolver, buscar) montado em `main.py`, consumindo `autorizacao.py`. Regenerar `packages/api-types` (`pnpm gen:types`).

## Riscos / Trade-offs

- **Redundância `unidade_atual_id` × `ordem_atual`+roteiro:** aceita deliberadamente por performance de Kanban (D3); risco de divergência mitigado por atualização conjunta na mesma transação e por teste que verifica a coerência após cada transição.
- **Imutabilidade por convenção:** como em `log_seguranca`, a garantia primária é a ausência de caminhos de update/delete no código; o `REVOKE`/trigger é endurecimento opcional. Testado por teste que tenta e verifica que não há rota de edição de evento.
- **Numeração sem gaps só dentro de transações concluídas:** o upsert-incremento na mesma transação evita gaps por rollback; ainda assim, o requisito do PRD é unicidade e reinício anual, não ausência absoluta de gaps — atendido.
- **"Parado"/alertas de prazo:** não calculados aqui (Épico 5/6); `prazo_em` já deixa o dado pronto para esses épicos consumirem.
