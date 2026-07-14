## Context

`bootstrap-infraestrutura` (arquivado) deixou o Cloud SQL privado, o baseline Alembic (`0001_baseline`, só extensões — nenhuma tabela de negócio), o segredo `jwt-signing-key` (D4, HS256, já lido em `Settings.jwt_signing_key`), a fila Cloud Tasks `emails` e o endpoint receptor `POST /internal/tasks/email` (OIDC-only, `maxAttempts=1`, contrato "loga e sempre dá ACK"). Este change é o primeiro a criar tabela de negócio e o primeiro a *emitir* tarefas para essa fila — o bootstrap só implementou o lado receptor.

Restrições que moldam este design:
- Stack fixa: FastAPI + SQLAlchemy 2.x + Alembic, PostgreSQL, Next.js/App Router.
- JWT é assinado com o único segredo HS256 já provisionado — não há troca de algoritmo neste change.
- Histórico de tramitação é imutável por regra do projeto (INSERT, nunca UPDATE) — vale também para os logs de segurança introduzidos aqui.
- Escala do MVP: ~500 usuários ativos, pico de 50–100 requisições concorrentes (herda do dimensionamento de `bootstrap-infraestrutura`).
- `processo` e `documento` (Épico 2/3) ainda não existem — algumas regras deste change (contagem de processos em andamento, filtro de Kanban) precisam de uma interface estável que os changes futuros implementam de verdade.

## Goals / Non-Goals

**Goals:**
- Modelar o schema completo de identidade e estrutura organizacional (`usuario`, `unidade`, `unidade_gestor`, `tipo_processo`, `roteiro`, `roteiro_etapa`) e seu suporte (`token_autenticacao`, `senha_historico`, `log_seguranca`, `sistema_config`) numa única migration Alembic coerente.
- Definir o modelo de sessão (JWT + registro server-side) que sustenta expiração por inatividade, logout imediato e múltiplas sessões concorrentes independentes (US 1.8, 1.9).
- Definir o mecanismo de tokens de uso único (primeiro acesso, recuperação de senha) e sua integração com a fila de e-mail existente.
- Definir as primitivas de autorização por perfil/unidade reutilizáveis pelos épicos seguintes.
- Definir o versionamento de roteiro de tramitação (US 8.2 Cen.2: processos em andamento mantêm o roteiro vigente na criação).
- Definir a inicialização atômica do sistema (US 8.0), livre de condição de corrida.

**Non-Goals:**
- Parâmetros operacionais configuráveis (US 8.5) — valores usados aqui são constantes hardcoded (timeout 30min, bloqueio 3 tentativas/30min, link 1º acesso 48h, link recuperação 2h, histórico 6 senhas).
- Permissão de Auditor (US 8.3), desativação de usuário (US 8.4), restauração de documento (US 8.7).
- Filtro real do Kanban por unidade e listagem de processos/documentos em "Meu Perfil" — dependem de `processo`/`documento`, que não existem até o change de Épico 2/3. Este change entrega a primitiva de autorização que esses endpoints futuros vão consumir.
- Rate limiting distribuído entre instâncias (fora de escopo — ver D6).

## Decisions

### D1 — Sessão: JWT + registro server-side (`sessao`)
**Escolha:** cada login gera um JWT HS256 (claims: `sub`=usuario_id, `jti`=uuid, `exp`) **e** uma linha em `sessao` (usuario_id, jti, criada_em, ultima_atividade, revogada_em nullable, ip, user_agent). Toda rota autenticada, além de validar assinatura/`exp` do JWT, consulta `sessao` por `jti`: se `revogada_em` estiver preenchido ou `ultima_atividade` estiver a mais de 30 min, rejeita com 401 "Sessão expirada por inatividade". Em requisição válida, atualiza `ultima_atividade = now()` e reemite um JWT com `exp = now() + 30min` (sliding window) — o frontend troca o token silenciosamente a cada resposta.
**Por quê:** JWT puro stateless não sustenta *inatividade* (só expiração absoluta) nem revogação imediata (logout, reset de senha por Admin). Um registro server-side leve resolve os três: inatividade (compara `ultima_atividade`), logout (`revogada_em = now()`), sessões concorrentes independentes (uma linha por dispositivo/login, US 1.9).
**Custo aceito:** 1 leitura+1 escrita em `sessao` por requisição autenticada — aceitável na escala do MVP (ver Riscos).
**Alternativas consideradas:** JWT stateless puro com `exp` curto e refresh token separado (mais comum, mas não resolve logout imediato sem uma blocklist — que é, na prática, o mesmo registro server-side proposto aqui, só que redescoberto); Redis para sessão (mais rápido, mas introduz um novo componente de infra fora do escopo de `bootstrap-infraestrutura` — Postgres já está lá e o volume não justifica).

### D2 — Hash de senha: bcrypt
**Escolha:** `passlib[bcrypt]`, custo 12, armazenado em `usuario.senha_hash` e nas linhas de `senha_historico`.
**Por quê:** padrão maduro no ecossistema Python/FastAPI, custo ajustável, sem dependência de biblioteca nativa problemática em container (ao contrário de argon2 em algumas imagens slim).
**Alternativas consideradas:** argon2 (mais moderno, mas exige libargon2 no container — complexidade extra sem necessidade a esta escala).

### D3 — Tokens de uso único (primeiro acesso / recuperação de senha)
**Escolha:** tabela `token_autenticacao` (usuario_id FK, tipo enum [`primeiro_acesso`, `recuperacao_senha`], token_hash, expira_em, usado_em nullable). O token enviado por e-mail é um valor aleatório opaco (secrets.token_urlsafe); só o **hash** (sha256) é persistido — o valor puro nunca é armazenado, só existe no link do e-mail. TTL por tipo: 48h (primeiro acesso), 2h (recuperação). Ao ser usado com sucesso, `usado_em = now()`; tentativa de reuso é rejeitada (US 1.6 Cen.3).
**Por quê:** mesmo padrão de segurança de um password hash — se o banco vazar, os tokens ainda ativos não são utilizáveis diretamente.
**Alternativas consideradas:** JWT de uso único assinado com `jwt-signing-key` (elimina a tabela, mas não permite invalidar um token ainda não expirado — ex.: gerar novo link de primeiro acesso não invalidaria o anterior sem uma blocklist, reintroduzindo o mesmo problema do D1).

### D4 — Autorização por perfil e unidade
**Escolha:** dependências FastAPI compostas: `get_current_user` (valida sessão via D1) → `require_perfil(*perfis)` (verifica `usuario.perfil`) → `require_acesso_unidade(unidade_id)` (Servidor: só a própria `unidade_id`; Gestor: `unidade_id` ∈ unidades de `unidade_gestor`; Administrador: qualquer unidade). Centralizadas em `app/security/autorizacao.py`, para que os endpoints do Épico 2 (Kanban, US 1.4) reutilizem a mesma função em vez de duplicar a regra.
**Escopo neste change:** aplica-se a `gestao-usuarios`, `unidades-administrativas` e `tipos-processo-e-roteiros` (ex.: Gestor só cadastra em unidade que gere — US 1.2 Cen.2). A função fica pronta para o Épico 2 consumir; não há endpoint de processo aqui para exercê-la de ponta a ponta.
**Cenário de acesso negado:** toda rejeição de `require_perfil`/`require_acesso_unidade` grava uma linha em `log_seguranca` (tipo_evento=`acesso_negado`, contexto com rota e unidade solicitada) — cobre a regra do config.yaml de cenário de acesso negado explícito.
**Alternativas consideradas:** políticas declarativas tipo Casbin/OPA (poder excessivo para 3 perfis e uma regra de escopo por unidade — complexidade não paga neste MVP).

### D5 — Bloqueio de conta por tentativas de login
**Escolha:** contadores no próprio `usuario` (`tentativas_login_falhas int default 0`, `bloqueado_ate timestamp nullable`). Senha incorreta incrementa o contador; ao atingir 3, seta `bloqueado_ate = now() + 30min` e enfileira e-mail de alerta. Login com senha correta durante bloqueio não decrementa nem reinicia o contador (US 1.3 Cen.2b). Reset de senha bem-sucedido (recuperação ou reset por Admin) zera `tentativas_login_falhas` e `bloqueado_ate` atomicamente na mesma transação que atualiza `senha_hash`.
**Por quê:** dado de baixa cardinalidade e alta frequência de leitura/escrita — vive melhor como coluna do próprio `usuario` do que em tabela separada (evita join extra em todo login).
**Alternativas consideradas:** tabela `tentativa_login` (histórico completo por tentativa) — mantida fora de escopo; se auditoria detalhada de tentativas for exigida depois, `log_seguranca` (tipo_evento=`login_falha`) já cobre o registro, sem precisar de tabela dedicada.

### D6 — Rate limiting nos endpoints não autenticados
**Escolha:** `slowapi` (token bucket em memória do processo) nas rotas `/auth/login`, `/auth/recuperar-senha` e `/auth/primeiro-acesso`: 10 requisições/minuto por IP. Complementar ao bloqueio por conta (D5), que é a defesa primária e é compartilhada entre instâncias (vive no Postgres).
**Por quê:** essas rotas não exigem Bearer token (só o link/credenciais), então são superfície de enumeração/brute-force distribuído entre contas — mesma categoria de risco que a regra do config.yaml associa a endpoints públicos, mesmo não sendo consulta pública.
**Limitação assumida:** contador em memória não é compartilhado entre instâncias Cloud Run (cada réplica tem seu próprio balde) — múltiplas instâncias multiplicam o limite efetivo. Aceito como camada complementar, não como controle único (ver Riscos).
**Alternativas consideradas:** rate limit no Postgres/Redis compartilhado (mais correto, mas novo componente de estado compartilhado só para isso — desproporcional ao MVP).

### D7 — Inicialização do sistema sem condição de corrida
**Escolha:** tabela singleton `sistema_config` (id fixo = 1, `inicializado boolean default false`, seed na própria migration). O endpoint de setup executa `UPDATE sistema_config SET inicializado = true WHERE id = 1 AND inicializado = false RETURNING id` dentro da mesma transação que cria o Administrador root e a primeira `unidade`; se `UPDATE` não retornar linha, aborta com 409 "Sistema já inicializado" (US 8.0 Cen.2) sem criar nada.
**Por quê:** o `UPDATE ... WHERE ... RETURNING` é atômico no nível de linha do Postgres — resolve a corrida de duas requisições de setup simultâneas sem lock explícito.
**Extensão futura:** `sistema_config` é o lugar natural para os parâmetros da US 8.5 (fora de escopo aqui, mas a tabela já nasce pronta para novas colunas).

### D8 — Roteiro de tramitação versionado
**Escolha:** `roteiro` tem `tipo_processo_id` FK e `vigente boolean`; um índice único parcial garante no máximo um `vigente=true` por `tipo_processo_id`. Editar o roteiro de um tipo de processo **cria uma nova linha** em `roteiro` (nova versão, `vigente=true`) e marca a anterior `vigente=false` — nunca faz UPDATE nas `roteiro_etapa` de uma versão existente. `roteiro_etapa` (roteiro_id FK, unidade_id FK, ordem) descreve a sequência daquela versão.
**Por quê:** US 8.2 Cen.2 exige que processos em andamento mantenham o roteiro vigente na criação. Quando o Épico 2 criar `processo`, ele vai gravar `processo.roteiro_id` apontando para a versão vigente no momento — imutável dali em diante, mesmo que o Administrador edite o roteiro depois.
**Acesso centralizado:** toda leitura de roteiro vigente passa por `obter_roteiro_vigente(tipo_processo_id)` (única função, um lugar) — nunca query direta espalhada pelo código, para não esquecer o filtro `vigente=true`.
**Alternativas consideradas:** um único `roteiro` por `tipo_processo` com histórico de alterações em tabela de auditoria separada (mais complexo para o mesmo resultado); FK direta `tipo_processo.roteiro_vigente_id` (rejeitada — cria dependência circular de criação entre `tipo_processo` e `roteiro`; a query com `vigente=true` evita o ciclo).

### D9 — Seam para "processos em andamento" (US 8.1 Cen.3) até o Épico 2 existir
**Escolha:** função `contar_processos_em_andamento(unidade_id) -> int` isolada em `app/services/unidades.py`, retornando `0` fixo nesta implementação, com docstring explícita `# TODO(épico-2): substituir por contagem real de processo.status quando a tabela existir`. A desativação de unidade (US 8.1 Cen.3/4) chama essa função — o comportamento observável hoje é "sempre permite desativar", o que é o resultado correto enquanto não existe nenhum processo no sistema.
**Por quê:** documenta o contrato futuro em vez de simplesmente omitir a validação — o change de Épico 2 só precisa trocar o corpo da função, não o call site.
**Risco aceito:** ver Riscos/Trade-offs.

### D10 — Envio de e-mail: novo cliente de enqueue (lado que faltava no bootstrap)
**Escolha:** `app/email/queue.py` com `enqueue_email(EmailMessage, event_id)`, usando `google-cloud-tasks` para criar uma Cloud Task na fila `emails` (provisionada no bootstrap) apontando para `POST /internal/tasks/email` com OIDC (`sa-tasks-invoker`, já existente). `event_id` vira o nome da task (`projects/.../queues/emails/tasks/{event_id}`) — dedup nativo do Cloud Tasks, reaproveitando o padrão de idempotência já estabelecido no bootstrap. `event_id` para este change: `primeiro-acesso:{token_id}`, `recuperacao-senha:{token_id}`, `cadastro-confirmacao:{usuario_id}:{timestamp}`.
**Por quê:** o bootstrap só implementou o lado receptor (`process_email_task`); nenhum código ainda enfileira nada. Este é o primeiro consumidor real da fila.
**Alternativas consideradas:** chamar `send_email` diretamente do request HTTP síncrono (rejeitado — acopla a latência do provedor SaaS ao tempo de resposta do cadastro/login, e reintroduz o problema de retry que a fila já resolve).

### D11 — Log de segurança: tabela append-only
**Escolha:** `log_seguranca` (usuario_id FK nullable — nullable porque tentativa de acesso pode ocorrer antes de identificar o usuário, ex.: e-mail não cadastrado; tipo_evento enum [`acesso_negado`, `login_bloqueado`, `reset_senha_admin`, `login_falha`]; contexto jsonb; criado_em). Só INSERT, nunca UPDATE/DELETE — mesma regra de imutabilidade do histórico de tramitação, aplicada aqui a eventos de segurança.
**Por quê:** cobre US 1.4 Cen.2 (log de acesso indevido) e US 1.10 Cen.1 (log de auditoria do reset por Admin) com uma única tabela, em vez de duas.

## Diagrama de sequência — cadastro de usuário + primeiro acesso (US 1.1/1.2 → 1.6)

Atravessa front, back e a fila assíncrona de e-mail (D10):

```
Admin/Gestor    API (FastAPI)        Postgres         Cloud Tasks      /internal/tasks/email   SendGrid
     │                │                   │                 │                  │                  │
     │ POST /usuarios │                   │                 │                  │                  │
     │───────────────▶│                   │                 │                  │                  │
     │                │ valida perfil/    │                 │                  │                  │
     │                │ unidade (D4)      │                 │                  │                  │
     │                │──────────────────▶│                 │                  │                  │
     │                │ INSERT usuario    │                 │                  │                  │
     │                │ (status=pendente) │                 │                  │                  │
     │                │──────────────────▶│                 │                  │                  │
     │                │ INSERT            │                 │                  │                  │
     │                │ token_autenticacao│                 │                  │                  │
     │                │ (tipo=1o_acesso,  │                 │                  │                  │
     │                │  hash, exp=+48h)  │                 │                  │                  │
     │                │──────────────────▶│                 │                  │                  │
     │                │ enqueue_email     │                 │                  │                  │
     │                │ (event_id=        │                 │                  │                  │
     │                │  "primeiro-       │                 │                  │                  │
     │                │  acesso:{id}")    │                 │                  │                  │
     │                │──────────────────────────────────────▶                 │                  │
     │ 201 Created     │                   │                 │ POST + OIDC      │                  │
     │◀───────────────│                   │                 │ (sa-tasks-invoker)                  │
     │                │                   │                 │─────────────────▶│                  │
     │                │                   │                 │                  │ valida OIDC       │
     │                │                   │                 │                  │ POST /v3/mail/send│
     │                │                   │                 │                  │─────────────────▶│
     │                │                   │                 │                  │◀─ ─ ─ ─ ─ ─ ─ ─ ─│
     │                │                   │                 │                  │ loga + 200 (ACK) │
     │                │                   │                 │◀─────────────────│                  │
```

Login com bloqueio por tentativas (US 1.3 Cen.2/2b/4) e recuperação de senha seguem o mesmo formato: o primeiro é síncrono (Front → API → Postgres, sem fila); o segundo reaproveita exatamente o diagrama acima trocando `tipo=recuperacao_senha`, TTL 2h e `event_id="recuperacao-senha:{token_id}"`.

## Migration Plan

Uma única revisão Alembic, `0002_identidade_estrutura_organizacional` (`down_revision = "0001_baseline"`):

1. Enums: `perfil_usuario` (servidor, gestor, administrador), `status_usuario` (pendente_primeiro_acesso, ativo, inativo), `tipo_token_autenticacao` (primeiro_acesso, recuperacao_senha), `tipo_evento_log` (acesso_negado, login_bloqueado, reset_senha_admin, login_falha).
2. `unidade` — sem `gestor_responsavel_id` ainda (evita ciclo de criação com `usuario`).
3. `usuario` — com `unidade_id` FK → `unidade` (nullable só para Administrador, que pode não ter lotação fixa).
4. `ALTER TABLE unidade ADD COLUMN gestor_responsavel_id FK → usuario` (nullable).
5. `unidade_gestor` (gestor_id FK → usuario, unidade_id FK → unidade, PK composta).
6. `tipo_processo`, `roteiro` (com índice único parcial `WHERE vigente`), `roteiro_etapa`.
7. `token_autenticacao`, `senha_historico`, `log_seguranca`.
8. `sessao` (usuario_id FK → usuario, jti, criada_em, ultima_atividade, revogada_em nullable, ip, user_agent) — suporta D1.
9. `sistema_config` + seed `INSERT (id=1, inicializado=false)`.
10. Índices: `usuario.email` (unique), `sessao.jti` (unique), `sessao.usuario_id`, `token_autenticacao.token_hash` (unique), `roteiro_etapa (roteiro_id, ordem)` (unique).

**Rollback:** downgrade dropa todas as tabelas/enums na ordem inversa. Seguro — é a primeira migration de negócio, nenhum dado de produção pré-existe além do próprio deploy de setup.
**Deploy:** migration roda antes do rollout da nova revisão do serviço `api` no Cloud Run (sem downtime — cria tabelas novas, não altera nenhuma existente).

## Risks / Trade-offs

- **[Risco] D1 adiciona 1 leitura+1 escrita em `sessao` por requisição autenticada, sob Cloud Run com `min-instances=0`** → Mitigação: índice único em `jti`; volume do MVP (50–100 req/s pico) é baixo o suficiente para o pool de conexões já dimensionado no bootstrap absorver sem contenção.
- **[Risco] D6 (rate limit em memória) não é compartilhado entre réplicas Cloud Run** → Mitigação: é camada complementar; a defesa primária contra brute-force é o bloqueio por conta (D5), que vive no Postgres e é compartilhado por definição.
- **[Risco] D9 (stub de contagem de processos) permite desativar qualquer unidade sem checagem real até o Épico 2** → Mitigação: comportamento correto hoje (não existe nenhum processo no sistema); `TODO` explícito no código e nesta seção do design tornam o seam visível na revisão do change de Épico 2.
- **[Risco] D8 (roteiro versionado por convenção de query, não FK)** exige que todo acesso passe por `obter_roteiro_vigente` → Mitigação: função única centralizada; revisão de código deve rejeitar qualquer query direta a `roteiro`/`roteiro_etapa` fora dela.
- **[Trade-off] bcrypt custo 12 (D2)** é mais lento que alternativas leves → aceito porque login não é hot path de alto QPS nesta escala, e custo baixo demais enfraquece a defesa contra ataque offline em caso de vazamento do hash.

## Open Questions

- Formato do corpo do e-mail (texto simples vs. HTML) para primeiro acesso/recuperação — o bootstrap's `EmailMessage.body` é texto simples; mantido assim neste change por suficiência, sem bloquear a entrega.
- `usuario.unidade_id` para perfil Gestor: assumido como a lotação formal do Gestor, independente das unidades que ele gerencia via `unidade_gestor` (US 8.6b) — o PRD não é explícito sobre se essas duas noções coincidem. Confirmar na revisão de specs; não bloqueia o design porque o schema suporta ambos os casos (coincidentes ou não).
- Limite exato do rate limiting (D6) — 10 req/min/IP é um default razoável, não especificado no PRD; ajustável sem migration.
