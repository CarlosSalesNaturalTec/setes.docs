## Context

O SETES.DOCS parte do zero: nenhum recurso GCP provisionado, nenhum monorepo estruturado. Este change estabelece a topologia de infraestrutura base sobre a qual todos os changes de negócio serão construídos.

Restrições que moldam o design:
- **Cliente é órgão público brasileiro (Bahia).** Residência de dados em território nacional e latência para Salvador/BA são requisitos, não preferências. LGPD (Lei 13.709/2018) é obrigatória.
- **Escala do MVP é pequena.** Até 500 usuários ativos (concorrência real estimada em ~50–100 requisições simultâneas em pico) e ~10.000 processos ativos — este segundo número é **volume de dados**, não carga. O gargalo previsível não é CPU/RAM, e sim **conexões ao banco** sob escala horizontal do Cloud Run.
- **Um único ambiente de produção, um único projeto GCP.** Sem staging no MVP.
- **Backend FastAPI sem worker dedicado.** Qualquer processamento assíncrono precisa reaproveitar o próprio serviço `api`.
- **Assinatura ICP-Brasil (Épico 4) está fora do MVP** (condicionada a Discovery Técnico, movida para Fase 2).

Stakeholders: equipe de desenvolvimento (monorepo TS+Python), operação/compliance do órgão (residência e auditoria), e os changes futuros que consomem esta base.

## Goals / Non-Goals

**Goals:**
- Provisionar toda a topologia GCP em `southamerica-east1`, com residência de dados garantida por convenção de módulo (org policy de região não aplicável no MVP — ver D7).
- Estabelecer os dois serviços Cloud Run (web/api), o Cloud SQL privado, o bucket de documentos, os 3 segredos e as duas rotinas agendadas.
- Definir o modelo de IAM de menor privilégio (6 service accounts); trava de "sem chaves de SA" via org policy não aplicável no MVP (ver D7).
- Estabelecer o pipeline CI/CD (GitHub Actions + WIF) e a estrutura de monorepo com contrato OpenAPI→TS.
- Deixar registrado o **contrato de idempotência** que as rotinas de negócio (US 2.5, US 10.3) deverão honrar.

**Non-Goals:**
- Nenhuma tabela/schema de negócio (virão em changes futuros via Alembic).
- Nenhuma lógica de negócio das rotinas — apenas a infraestrutura e o contrato.
- Assinatura digital ICP-Brasil (Fase 2).
- Ambiente de staging/homologação.
- Observabilidade avançada, WAF, CDN — fora do escopo do bootstrap.

## Decisions

### D1 — Hospedagem: Cloud Run para os dois serviços
**Escolha:** dois serviços Cloud Run independentes (`web` Next.js/App Router, `api` FastAPI). API com `min-instances=0` no MVP (`concurrency=80`); web com `min-instances=0–1`.
**Por quê:** Next.js com App Router exige runtime servidor (Server Components/SSR), então Firebase Hosting sozinho não serve. Cloud Run dá scale-to-zero, pay-per-use e container próprio por serviço.
**Alternativas consideradas:** App Engine (modelo mais antigo, scale-to-zero pior, menos controle de container — sem ganho); Firebase Hosting para o front (só estático/CDN, ainda cairia em Functions por baixo para o runtime — adiciona camada sem eliminar o problema).

### D2 — Conectividade com Cloud SQL: IP privado + Direct VPC egress
**Escolha:** Cloud SQL for PostgreSQL sem IP público; a `api` e os jobs conectam via IP privado usando **Direct VPC egress** do Cloud Run.
**Por quê:** postura adequada a órgão público — o tráfego de dados nunca sai para a internet pública. Direct VPC egress é o mecanismo atual e dispensa o Serverless VPC Connector (menos custo fixo e menos infraestrutura para gerenciar).
**Alternativas consideradas:** IP privado + Serverless VPC Connector (igual em segurança, mas connector é instância extra com custo — mantido apenas como fallback caso Direct egress apresente limitação); IP público + Cloud SQL Auth Proxy (mais simples de começar, mas expõe a instância — inadequado para o perfil do cliente).

### D3 — Cloud Storage: bucket único, prefixo por processo
**Escolha:** um bucket, uniform bucket-level access, objetos sob `processos/{processo_id}/{documento_id}`.
**Por quê:** o processo tramita entre unidades — a unidade é volátil por design, o `processo_id` é a chave estável. Prefixo por unidade quebraria a cada despacho. Bucket por tenant/unidade não é o modelo adequado do Cloud Storage; prefixos são a prática padrão.
**Soft-delete de 30 dias (US 8.7):** a fonte da verdade é o **banco** (`documento.status = 'removido'`, `removido_em`). A lifecycle rule do Cloud Storage deleta por *idade do objeto desde a criação*, e não "30 dias desde a remoção" — logo, não expressa a semântica do PRD. A **purga física** é feita pelo job diário, consultando `removido_em < now() - 30d` e deletando o objeto (idempotente). Versionamento + soft-delete nativo do bucket servem apenas como rede de segurança contra exclusão acidental de infraestrutura.
**Alternativas consideradas:** lifecycle-by-age como regra de negócio (rejeitada — semântica incorreta); bucket por unidade (rejeitada — chave instável).

### D4 — Secret Manager: 3 segredos, injeção por variável de ambiente
**Escolha:** `db-password`, `jwt-signing-key`, `sendgrid-api-key`, cada um com replicação gerenciada pelo usuário fixada em `southamerica-east1`, injetados no Cloud Run como variáveis de ambiente apontando para `latest`.
**Por quê:** env var é a forma mais simples e suficiente para o MVP. Replicação fixada garante que o segredo não sai do Brasil (o padrão "automatic" replica globalmente).
**JWT HS256 vs RS256:** como a mesma `api` assina e valida o token, `HS256` com um único segredo é suficiente e mais simples. `RS256` (chave privada/ pública separadas) só compensaria se outro serviço precisasse validar sem compartilhar segredo — não é o caso no MVP.
**Alternativas consideradas:** montagem como volume de arquivo (permite rotação sem redeploy — registrado como upgrade futuro, não adotado no MVP); replicação automática (rejeitada por residência de dados).

### D5 — Rotinas: Cloud Scheduler → Cloud Run Jobs, idempotência por design
**Escolha:** Cloud Scheduler dispara Cloud Run Jobs (target nativo). Dois jobs: `job-manutencao-diaria` e `job-anonimizacao-lgpd`.
**Por quê Cloud Run Jobs e não endpoint HTTP na `api`:** o job roda até terminar sem limite de timeout de request; usa a `sa-jobs` isolada (sem ingress público, com permissão de DELETE no bucket que a `api` não precisa ter); e não compete com o processamento de requisições dos usuários.
**Gatilho / janela / retomada:**
- `job-manutencao-diaria` — cron diário em horário de baixa (ex.: 03:00 America/Bahia). Passos idempotentes e independentes: arquivamento (US 2.5), alerta de prazo por e-mail (US 5.2 Cen.2), purga de documentos soft-deleted > 30d (US 8.7), expurgo de notificações lidas > 30d (US 5.1 Cen.4). A falha de um passo não corrompe os demais.
- `job-anonimizacao-lgpd` — cron trimestral (US 10.3).

**Contrato de idempotência (chave do design):** a rotina **não processa "os vencidos de ontem"; processa "tudo que está vencido agora"**. A seleção é uma função do estado atual do banco:

```
SELECT * FROM processo
WHERE status = 'Concluído'
  AND concluido_em + prazo_arquivamento_vigente <= now();
-- prazo_vigente é congelado no processo no momento da conclusão (US 2.5 Cen.2)
```

Rodar 1× ou 10×, ou retomar após 3 dias de indisponibilidade, produz o mesmo resultado — os itens vencidos durante a queda são capturados na próxima execução (US 2.5 Cen.4). A transição de estado `Concluído → Arquivado` é o *guard*: um item já arquivado não reentra na query, então nenhum evento de histórico é duplicado. A mesma lógica vale para a anonimização ("arquivados há mais que o prazo legal E ainda não anonimizados").
**Alternativas consideradas:** rastrear quais dias já rodaram e reprocessar o delta (rejeitada — frágil, exige estado extra, não sobrevive a execução perdida); endpoint HTTP na `api` (rejeitada — timeout, privilégio e contenção de recurso).

### D6 — E-mail assíncrono: Cloud Tasks (Pub/Sub descartado)
**Escolha:** Cloud Tasks, fila `emails`, `maxAttempts=1`, com limite de despacho por segundo. As tarefas invocam um endpoint interno OIDC-only do próprio serviço `api`.
**Por quê:** o requisito US 5.2 Cenário 3 é explícito — **"o sistema NÃO realiza novas tentativas automáticas de envio para o mesmo evento"**. Pub/Sub é construído para redelivery com backoff (o oposto). Cloud Tasks entrega a tarefa por HTTP ao **próprio** serviço FastAPI (sem worker novo), permite `maxAttempts=1`, dedupe por task name, agendamento por tarefa e rate limit por fila (protege o provedor SaaS). A superfície operacional é menor que tópico+subscription+DLQ, e o volume de e-mail do MVP é baixíssimo.
**Comportamento em falha:** o endpoint tenta enviar ao provedor; em qualquer falha, **loga em "Logs do Sistema" e retorna 2xx (ACK)**, para que a fila não redespache. A notificação interna (sininho) é gravada no banco de forma síncrona, independente do e-mail.
**Provedor SaaS:** SendGrid ou Mailgun (decisão de provedor específico pode ser fechada na implementação; ambos oferecem webhook de bounce que alimenta o log de falha da US 5.2 Cen.3). Segredo: `sendgrid-api-key`.
**Alternativas consideradas:** Pub/Sub + subscriber em Cloud Run (rejeitada — retry automático conflita com a US 5.2 Cen.3, e exige worker/serviço adicional).

### D7 — Região: southamerica-east1 (verificada)
**Escolha:** região única `southamerica-east1` (Osasco/SP).
**Verificação (2026-07):** disponibilidade confirmada na documentação oficial por serviço para Cloud Run + Jobs, Cloud SQL, Cloud Storage, Secret Manager (replicação user-managed regional), Cloud Tasks e Cloud Scheduler — **sem exceções**. Cloud Build e Artifact Registry também disponíveis.
**Travas de residência (não bastam escolher a região):**
1. ~~Org policy `constraints/gcp.resourceLocations = in:southamerica-east1-locations` no projeto~~ — **não aplicável no MVP**: exige `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta GCP; `setes-docs` é um projeto standalone (conta pessoal, sem Organização). Confirmado via `terraform apply` e `gcloud org-policies set-policy` (403 `orgpolicy.policies.create` — o papel não pôde nem ser concedido no projeto). Trava vira convenção de módulo: todo recurso no Terraform já é fixado em `var.region` (`southamerica-east1`); revisão de PR é a proteção contra desvio, não enforcement automático. Revisitar se o projeto migrar para dentro de uma Organização GCP.
2. Secret Manager com replicação **user-managed** fixada em `southamerica-east1` (o padrão "automatic" replica globalmente) — esta trava não depende de org policy e segue ativa.
**Por quê:** residência de dados exigida para órgão público + menor latência para Salvador/BA.

### D8 — CI/CD: GitHub Actions + Workload Identity Federation
**Escolha:** GitHub Actions roda lint+test (pytest, Vitest), autentica no GCP via **Workload Identity Federation** (sem chave de SA), builda a imagem, publica no **Artifact Registry** e faz `gcloud run deploy`. Path filters do monorepo constroem `web`/`api` apenas quando o respectivo diretório muda.
**Por quê:** mantém o pipeline onde os desenvolvedores já trabalham (branches `feature/*`, `develop`, `main`); WIF elimina chaves JSON de longa duração (postura de segurança valorizada por gov); menos peças móveis que Cloud Deploy.
**Alternativas consideradas:** Cloud Build (nativo, mas duplica a lógica de teste fora do repo); GitHub Actions + Cloud Deploy (promoção dev→prod com aprovação — valioso quando houver governança formal de release; adiado, pois há só um ambiente no MVP).
**Combina com:** a intenção original era reforçar com a org policy `iam.disableServiceAccountKeyCreation`, mas ela não é aplicável no MVP (mesmo motivo de D7 — sem Organização GCP). WIF segue como a única barreira real contra chave JSON de SA: nenhum workflow usa/gera chave, mas nada no GCP bloqueia automaticamente a criação manual de uma.

### D9 — Monorepo: híbrido TS/Python + infra/
**Escolha:**
```
processos_gestor/
├─ apps/
│  ├─ web/               # Next.js — Dockerfile próprio
│  └─ api/               # FastAPI — pyproject.toml (uv), Dockerfile próprio
├─ packages/
│  └─ api-types/         # openapi-typescript (gerado), consumido só pelo web
├─ infra/                # Terraform (backend de state em bucket GCS versionado)
├─ .github/workflows/
├─ pnpm-workspace.yaml   # workspace TS: web + packages/*
└─ package.json
```
**Por quê:** é um monorepo poliglota. O workspace pnpm cobre só o lado TS (`web` + `api-types`); o `apps/api` (Python) é gerenciado por `uv` de forma independente — não force uma ferramenta única sobre os dois. O `infra/` com Terraform nasce aqui porque este change é, essencialmente, provisionamento (state em bucket GCS com versionamento).
**Contrato OpenAPI→TS:** `apps/api` (FastAPI) emite `openapi.json` → `openapi-typescript` gera `packages/api-types` → `apps/web` importa. Script `pnpm gen:types` + geração no CI, com **drift check** (CI falha se o snapshot commitado estiver defasado) para garantir que front e back não divergem. Snapshot commitado dá DX local sem precisar subir a API.
**Alternativas consideradas:** Nx/Turbo cobrindo Python também (rejeitado — overhead sem ganho para dois apps poliglotas).

### D10 — IAM: 6 service accounts, menor privilégio no nível do recurso
**Escolha:**
```
sa-web            → run.invoker em api (chamada SSR OIDC). Nada mais.
sa-api            → cloudsql.client
                    secretmanager.secretAccessor  (POR segredo: db, jwt, sendgrid)
                    storage.objectUser            (POR bucket)
                    cloudtasks.enqueuer           (fila emails)
sa-jobs           → cloudsql.client
                    secretmanager.secretAccessor  (db, sendgrid)
                    storage.objectAdmin           (bucket — precisa DELETE p/ purga)
                    (sem ingress; não recebe internet)
sa-scheduler      → permissão de execução NOS jobs (só isso)
sa-tasks-invoker  → run.invoker em api (OIDC p/ endpoint /internal/tasks/*)
sa-deploy (WIF)   → artifactregistry.writer, run.admin, iam.serviceAccountUser
```
**Princípios:** `secretAccessor` no recurso-segredo (não no projeto); `storage.*` no bucket (não no projeto); `sa-jobs` separada da `sa-api` porque o job precisa de DELETE no bucket e a superfície pública não deve tê-lo; nenhum papel primitivo (Owner/Editor).
**Alternativas consideradas:** uma única SA para tudo (rejeitada — viola menor privilégio); SAs separadas por job (`sa-job-arquivamento` vs `sa-job-anonimizacao`) — refino futuro se a auditoria exigir; no MVP, uma `sa-jobs` é suficiente.

## Diagrama de sequência — envio assíncrono de e-mail (Épico 5)

Fluxo que atravessa back + fila + provedor externo (exigido pela regra de design para fluxos assíncronos):

```
Servidor/    Serviço API      Cloud Tasks     Endpoint interno    Provedor      Logs do
Evento       (FastAPI)        (fila emails)   /internal/tasks     SaaS (email)  Sistema
  │              │                 │                │                 │             │
  │ evento       │                 │                │                 │             │
  │ (despacho)   │                 │                │                 │             │
  │─────────────▶│                 │                │                 │             │
  │              │ grava           │                │                 │             │
  │              │ notificação     │                │                 │             │
  │              │ interna (sino)  │                │                 │             │
  │              │ [síncrono, DB]  │                │                 │             │
  │              │                 │                │                 │             │
  │              │ enqueue task    │                │                 │             │
  │              │────────────────▶│                │                 │             │
  │              │                 │ POST + OIDC    │                 │             │
  │              │                 │ (sa-tasks-     │                 │             │
  │              │                 │  invoker)      │                 │             │
  │              │                 │───────────────▶│                 │             │
  │              │                 │                │ envia e-mail    │             │
  │              │                 │                │────────────────▶│             │
  │              │                 │                │                 │             │
  │              │                 │        ┌───────┴─── sucesso ─────┤             │
  │              │                 │        │       │  200 OK (ACK)   │             │
  │              │                 │◀───────┘       │                 │             │
  │              │                 │                │                 │             │
  │              │                 │        ┌── falha de entrega ─────┤             │
  │              │                 │        │       │ registra falha  │             │
  │              │                 │        │       │────────────────────────────▶ │
  │              │                 │        │       │ 200 OK (ACK, sem retry —      │
  │              │                 │◀───────┘       │ maxAttempts=1, US 5.2 Cen.3)  │
```

Ponto-chave: mesmo em falha de entrega, o endpoint responde 200 (ACK) após logar, para que a fila **não** redespache — honrando "sem novas tentativas automáticas". A notificação interna do sininho é independente do e-mail.

## Migrations (Alembic) — separado do design de API

Este change **não** cria tabelas de negócio. Ele apenas:
- Provisiona a instância Cloud SQL vazia e o usuário/role de aplicação.
- Estabelece a baseline do Alembic (`alembic init`, configuração de conexão via IP privado, migration inicial vazia ou apenas com extensões necessárias, ex.: `pgcrypto`/`uuid-ossp` se adotadas).
As tabelas (`processo`, `unidade`, `tramitacao`, `documento`, etc.) e suas FKs vêm nos changes de negócio subsequentes, com schema descrito antes dos endpoints.

## Risks / Trade-offs

- **[Esgotamento de conexões ao Cloud SQL]** Cloud Run escala horizontalmente; `nº_instâncias × pool_size` pode exceder `max_connections`. → Mitigação: pool pequeno por instância (ex.: `pool_size=5, max_overflow=0`), `max-instances` limitado (ex.: 10), e PgBouncer como sidecar se apertar. Com 500 usuários não se chega ao teto, mas o teto é documentado e monitorado.
- **[Sem ambiente de staging]** Um único projeto de produção significa que testes de integração não têm um espelho seguro. → Mitigação: testes de integração em CI contra recursos efêmeros/descartáveis (ex.: Postgres em container no runner), Playwright em fluxos críticos, e deploy com revisão gradual do Cloud Run (traffic splitting) para validar antes de 100%.
- **[env var de segredo resolvida no deploy]** Rotação de segredo exige nova revisão do serviço. → Mitigação aceita no MVP; upgrade para montagem como volume documentado em D4.
- **[maxAttempts=1 e falha transitória do provedor]** Uma indisponibilidade momentânea do SaaS descarta o e-mail (sem retry), por decisão de produto (US 5.2 Cen.3). → Mitigação: a falha fica registrada em "Logs do Sistema" e a notificação interna do sininho não é afetada; reenvio, se necessário, é ação manual do Administrador.
- **[Cold start com min-instances=0]** No MVP a `api` roda com `min-instances=0` para custo zero em ocioso; a primeira requisição após período ocioso paga o cold start do Cloud Run. → Trade-off aceito: volume de tráfego do MVP não justifica manter instância aquecida; revisitar `min-instances=1` se a latência da primeira requisição incomodar em produção.
- **[Org policies de governança não aplicáveis no MVP]** `gcp.resourceLocations` e `iam.disableServiceAccountKeyCreation` exigem `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta GCP; `setes-docs` não tem Organização por trás (conta pessoal). Sem elas, região e chaves de SA dependem de convenção/revisão, não de enforcement automático da plataforma. → Mitigação: controles diretos que não dependem de org policy seguem ativos (Cloud SQL sem IP público, bucket sem acesso público, replicação de segredo fixada na região, nenhum módulo Terraform referencia outra região); revisitar se o projeto migrar para dentro de uma Organização GCP.

## Open Questions

- ~~Provedor de e-mail definitivo~~ — **Resolvido:** SendGrid (conta free, single sender `naturalbahia@gmail.com`, `docs/emailConfig.md`). **Achado da validação (task 11.1):** esse remetente não é confiável para destinatários Gmail/Google Workspace — o Gmail aplica DMARC `p=reject` em `@gmail.com` enviado por infraestrutura de terceiros (SendGrid), causando descarte silencioso ("Delivered" no SendGrid, mas nunca chega) ou rate-limit (421, "isn't aligned with SPF/DKIM"). Funcionou para um destinatário `.gov.br`. Antes do change de negócio que implementa o envio real (US 5.2) depender de entrega para Gmail/Outlook, configurar Domain Authentication no SendGrid (SPF/DKIM/DMARC) com um domínio próprio do órgão — não dá pra resolver isso mantendo o remetente como um Gmail pessoal.
- Extensões PostgreSQL a habilitar na baseline (ex.: `pgcrypto` para o identificador anonimizado irreversível da US 10.3) — confirmar na primeira migration de negócio.
- ~~Estratégia de state do Terraform~~ — **Resolvido:** bucket dedicado no mesmo projeto (`gs://setes-docs-tfstate`, versionado, mesma região).
