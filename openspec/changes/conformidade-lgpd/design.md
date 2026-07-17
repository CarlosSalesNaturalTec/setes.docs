## Context

O Épico 10 fecha o MVP não-condicional. A base já existe: `processo` (com
`StatusProcesso.ARQUIVADO` e `arquivado_em` congelado pela rotina de arquivamento),
`processo_interessado` (dado pessoal do titular — nome obrigatório, CPF/CNPJ opcional),
`tipo_processo`, `sistema_config` (padrão de parâmetro operacional runtime) e a
infraestrutura de `rotinas-agendadas`: o Cloud Run Job `job-anonimizacao-lgpd` já está
provisionado com Cloud Scheduler trimestral (`0 4 1 1,4,7,10 *`, America/Bahia) e
`sa-jobs` (sem ingress, IAM já restrito), mas roda o mesmo `command` placeholder do job
diário (`python -m app.jobs.entrypoint`) — nenhuma lógica de negócio.

Dois gatilhos distintos precisam do **mesmo efeito irreversível** (anonimizar um
interessado): um clique do Administrador (US 10.2, sob demanda, qualquer processo citado
numa solicitação) e uma rotina trimestral (US 10.3, só processos `Arquivado` com prazo
legal vencido). Isso pede um serviço único, dois chamadores.

## Goals / Non-Goals

**Goals:**
- Canal público de solicitação LGPD (US 10.1), com protocolo, validação e confirmação
  por e-mail.
- Fila administrativa (US 10.2) com atender/rejeitar, Admin-only.
- Serviço único de anonimização irreversível de interessado, compartilhado entre
  atendimento manual e rotina automática.
- Rotina trimestral real no job já provisionado (US 10.3), com prazo configurável por
  tipo de processo, seguindo o contrato de idempotência de `rotinas-agendadas`.

**Non-Goals:**
- Exportação do relatório de solicitações LGPD (não pedido pelo PRD — só listagem em tela).
- Autenticação do solicitante ou verificação criptográfica de identidade — a validação de
  titularidade é manual, feita pelo Administrador ao analisar o documento anexado (mesmo
  padrão de "confiança no operador humano" da US 8.7 para restauração de documento).
- Reversão de anonimização — por definição do PRD, é irreversível; não há "desfazer".
- Alterar o schedule, a service account ou qualquer outra peça de infra de
  `rotinas-agendadas` além do `command` do job `job-anonimizacao-lgpd`.

## Decisions

### D1 — Serviço único `anonimizar_interessados` com dois chamadores
`services/lgpd.py` expõe `anonimizar_interessados(db, processo, *, agora) -> int`:
sobrescreve, para cada `processo_interessado` do processo ainda não anonimizado
(`anonimizado_em IS NULL`), `nome = "Titular Anonimizado"` e `documento` (quando presente)
por um identificador anonimizado gerado (hash truncado não reversível — não o CPF
mascarado, que ainda seria correlacionável), e marca `anonimizado_em = agora`. Registra
**um único** evento `interessado_anonimizado` em `log_seguranca` por processo (não por
interessado), com `contexto = {"processo_id": ..., "origem": "manual"|"automatico",
"solicitacao_lgpd_id": <id ou null>}`.

Dois chamadores:
- **Manual** (`routers/lgpd.py`, ação "Atender Solicitação"): chama direto, Admin-only,
  qualquer `processo` (independente de status — o titular pode pedir a qualquer momento,
  PRD não restringe a `Arquivado`), `origem="manual"`.
- **Automático** (`app/jobs/entrypoint_lgpd.py` → `services/anonimizacao_lgpd.py`): seleciona
  os processos elegíveis (D3) e chama o mesmo serviço por processo, `origem="automatico"`,
  `solicitacao_lgpd_id=None`.

*Por que um serviço único:* evita duas implementações do mesmo efeito irreversível
divergindo com o tempo (ex.: uma zera CPF, a outra não) — o requisito de negócio
("substituir CPF/CNPJ por identificador anonimizado irreversível, nome por 'Titular
Anonimizado'") é idêntico nas duas USs (10.2 Cen.2 e 10.3 Cen.1).

### D2 — Guard de idempotência: coluna `anonimizado_em`, não string-matching
Alternativa descartada: inferir "já anonimizado" comparando `nome == "Titular
Anonimizado"` — frágil (um interessado legítimo poderia se chamar assim; string mágica
espalhada por múltiplos pontos de leitura) e não dá timestamp para auditoria. A coluna
`processo_interessado.anonimizado_em TIMESTAMPTZ NULL` é o guard explícito: a seleção da
rotina automática (D3) e o `WHERE anonimizado_em IS NULL` dentro do próprio serviço
tornam re-execuções sem efeito adicional — mesmo contrato de idempotência de
`rotinas-agendadas` ("seleção é função do estado atual").

### D3 — Seleção da rotina automática: por processo, não por interessado
Query em `services/anonimizacao_lgpd.py`:

```sql
SELECT p.* FROM processo p
JOIN tipo_processo tp ON tp.id = p.tipo_processo_id
WHERE p.status = 'Arquivado'
  AND p.arquivado_em + (tp.prazo_anonimizacao_anos || ' years')::interval <= :agora
  AND EXISTS (
    SELECT 1 FROM processo_interessado pi
    WHERE pi.processo_id = p.id AND pi.anonimizado_em IS NULL
  )
```

Para cada processo selecionado, chama `anonimizar_interessados` (que por sua vez filtra
os interessados ainda não anonimizados daquele processo). Um processo com todos os
interessados já anonimizados não satisfaz o `EXISTS` e não é reselecionado — guard de
transição igual ao de `arquivar_vencidos` (mesmo padrão do módulo `arquivamento.py`).

*Por que por processo, e não uma query direta em `processo_interessado`:* o prazo é
parametrizado por **tipo de processo**, então a junção com `tipo_processo` e o filtro por
`arquivado_em` só fazem sentido no nível do processo; iterar por processo também mantém o
registro em `log_seguranca` (D1) agrupado por processo, coerente com o histórico de
tramitação existente.

### D4 — Novo entrypoint próprio para `job-anonimizacao-lgpd`
Hoje `infra/jobs_scheduler.tf` aponta os dois jobs (`job-manutencao-diaria` e
`job-anonimizacao-lgpd`) para o mesmo `command: ["python", "-m", "app.jobs.entrypoint"]`
— puro placeholder, como o comentário no arquivo já registra. Este change cria
`app/jobs/entrypoint_lgpd.py` (mesmo padrão de `entrypoint.py`: abre sessão, chama o
serviço, loga total processado, fecha sessão) e altera **só** a entrada `job-anonimizacao-lgpd.command`
em `jobs_scheduler.tf` para `["python", "-m", "app.jobs.entrypoint_lgpd"]`. Nenhuma outra
linha do Terraform muda — schedule, `sa-jobs`, VPC egress e IAM já estão corretos e fora
de escopo.

### D5 — Protocolo sequencial por ano, reaproveitando o padrão de `numero_processo`
`solicitacao_lgpd.protocolo` segue o mesmo padrão de concorrência-segura já usado pelo
número de processo (`ProcessoContadorAno` + `services/numero_processo.py`): nova tabela
`solicitacao_lgpd_contador_ano` (`ano PK`, `ultimo_sequencial`), upsert atômico na mesma
transação da criação da solicitação. Formato: `LGPD/AAAA/NNNNNN` (6 dígitos, reinicia por
ano) — mesma convenção visual do número de processo, mas prefixado para não colidir
visualmente com ele.

*Por que não reaproveitar `ProcessoContadorAno` diretamente:* é uma sequência
semanticamente diferente (protocolo de solicitação ≠ número de processo); compartilhar a
tabela acopla dois contadores que devem evoluir independentemente (ex.: se um dia o
formato do protocolo LGPD mudar, não deve afetar a numeração de processo).

### D6 — Upload do documento de identificação: bucket dedicado, sem soft-delete
O documento de identificação (RG/CNH com foto) anexado ao formulário público é dado
pessoal sensível de identidade civil, **não** um anexo de processo — não deve conviver no
bucket `documentos` (retenção de 30 dias + restauração administrativa da US 8.7, pensada
para anexos de processo, não para prova de identidade de solicitante externo). Novo
bucket `${project_id}-lgpd-solicitacoes`, mesmo padrão de uniform bucket-level access do
bucket de documentos, acessível apenas por `sa-api` (upload) e `sa-jobs` não precisa
acessá-lo (a rotina automática não lê esse documento). Sem soft-delete/restauração — não
há requisito do PRD para isso; o arquivo fica vinculado à `solicitacao_lgpd` enquanto o
registro existir.

Validações reaproveitam o padrão já estabelecido em `services/documento.py`: formatos
aceitos (PDF, JPG, PNG — mais restrito que os anexos de processo, que também aceitam
DOC/DOCX), rejeição de arquivo vazio (0 byte). Tamanho máximo: mesmo teto de 20 MB por
consistência com o restante do sistema (PRD não especifica um valor diferente para este
formulário).

### D7 — Endpoint público sob rate limiting existente
`POST /publico/lgpd/solicitacoes` entra no mesmo router `consulta_publica`-adjacente,
reaproveitando `slowapi` já montado. Usa o mesmo limite `RATE_LIMIT_CONSULTA_PUBLICA`
(60/min/IP) definido em `app/rate_limit.py` — não é a mesma operação da consulta pública,
mas é o mesmo perfil de risco (endpoint público sem autenticação, potencial alvo de
scraping/spam), e o PRD não define um limite dedicado para este formulário.

### D8 — Rejeição de solicitação exige justificativa (US 10.2 Cen.3)
`POST /lgpd/solicitacoes/{id}/rejeitar` exige `justificativa: str` não vazia no corpo —
mesma validação de campo obrigatório já usada em `US 2.2b` (devolução de processo, motivo
obrigatório). Estado da solicitação só transiciona de `pendente`/`em_analise` para
`atendida`/`rejeitada` — transição final, sem caminho de volta (mesma semântica de
máquina de estados explícita que rege `processo.status`, ainda que este não seja o status
do processo em si).

## Sequence — Atendimento de solicitação (US 10.2, atravessa front, back e e-mail)

```
Cidadão          Frontend (público)      API (FastAPI)              DB              E-mail (fila)
  |                     |                      |                     |                   |
  |--preenche form----->|                      |                     |                   |
  |                     |--POST /publico/lgpd/solicitacoes---------->|                     |
  |                     |                      |--valida processo--->|                   |
  |                     |                      |--gera protocolo---->|                   |
  |                     |                      |--INSERT solicitacao->|                   |
  |                     |                      |--enfileira e-mail confirmação----------->|
  |                     |<--protocolo----------|                     |                   |
  |<--"Protocolo: XXXX"-|                      |                     |                   |

Administrador       Admin UI                API (FastAPI)              DB           E-mail (fila)
  |                     |                      |                     |                   |
  |--abre fila LGPD----->|--GET /lgpd/solicitacoes------------------>|                     |
  |                     |<--lista--------------|<--SELECT-----------|                   |
  |--Atender------------>|--POST .../atender-->|                     |                   |
  |                     |                      |--anonimizar_interessados(processo)------>|
  |                     |                      |--UPDATE processo_interessado------------>|
  |                     |                      |--INSERT log_seguranca------------------->|
  |                     |                      |--UPDATE solicitacao (atendida)---------->|
  |                     |                      |--enfileira e-mail conclusão-------------->|
  |                     |<--200----------------|                     |                   |
```

## Migration Plan

**Alembic (schema antes de endpoint, ordem de aplicação):**
1. `CREATE TABLE solicitacao_lgpd_contador_ano (ano INTEGER PRIMARY KEY, ultimo_sequencial INTEGER NOT NULL);`
2. `CREATE TYPE tipo_solicitacao_lgpd AS ENUM ('exclusao', 'anonimizacao');`
   `CREATE TYPE status_solicitacao_lgpd AS ENUM ('pendente', 'em_analise', 'atendida', 'rejeitada');`
3. `CREATE TABLE solicitacao_lgpd (...)` — `protocolo UNIQUE`, `processo_id FK processo.id`,
   `nome_solicitante`, `cpf_solicitante`, `email_solicitante`, `tipo tipo_solicitacao_lgpd`,
   `status status_solicitacao_lgpd DEFAULT 'pendente'`, `documento_identificacao_chave`
   (chave no bucket dedicado), `justificativa_rejeicao NULL`, `criado_em`,
   `atendido_em NULL`, `atendido_por_id FK usuario.id NULL`.
4. `ALTER TABLE tipo_processo ADD COLUMN prazo_anonimizacao_anos INTEGER NOT NULL DEFAULT 5;`
   — sem backfill retroativo de comportamento (aplica-se só a partir de agora, mesma regra
   não retroativa de `sistema_config`).
5. `ALTER TABLE processo_interessado ADD COLUMN anonimizado_em TIMESTAMPTZ NULL;` — default
   NULL cobre todas as linhas existentes (nada é anonimizado retroativamente pela
   migration em si; só pela execução seguinte da rotina/atendimento).
6. `ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'interessado_anonimizado';` (fora de
   transação implícita — seguir o padrão de migration de enum já usado no repo).

**Infra (Terraform, aplicado antes do deploy do novo entrypoint):**
1. `infra/storage.tf` — novo `google_storage_bucket.lgpd_solicitacoes`.
2. `infra/iam.tf` — `sa-api` ganha `storage.objectUser` no novo bucket (mesmo padrão do
   bucket de documentos); `sa-jobs` **não** recebe acesso (não precisa ler o documento).
3. `infra/jobs_scheduler.tf` — troca o `command` de `job-anonimizacao-lgpd` para
   `["python", "-m", "app.jobs.entrypoint_lgpd"]`. Schedule, service account e VPC egress
   inalterados.

*Rollback:* todas as mudanças de schema são aditivas (novas tabelas/colunas/valores de
enum) — reversível via `alembic downgrade` dropando tabelas/colunas novas; valores de enum
Postgres não são removíveis sem recriar o tipo (aceitável ficarem órfãos, mesmo padrão já
aceito em changes anteriores). Reverter o `command` do job para o entrypoint antigo é uma
troca de uma linha no Terraform, sem impacto em dado.

## Risks / Trade-offs

- **[Verificação de titularidade é só manual/documental]** → aceito como Non-Goal; é o
  mesmo nível de confiança operacional já usado em outras USs administrativas do
  sistema (ex.: restauração de documento). Mitigação: o documento de identificação fica
  disponível para o Administrador conferir antes de "Atender".
- **[`ALTER TYPE ... ADD VALUE` fora de transação]** → seguir o padrão de migration de
  enum já validado nos changes anteriores (`administracao-usuario-auditoria`, `sigilo-de-processo`).
- **[Bucket novo aumenta a superfície de infraestrutura]** → justificado por D6: dado de
  identidade civil de terceiro não deve compartilhar retenção/acesso com anexos de
  processo; escopo e IAM ficam mínimos (só `sa-api` grava, ninguém mais lê).
- **[Rotina trimestral tem janela de verificação longa entre execuções]** → aceitável por
  design (US 10.3 é sobre conformidade de retenção de longo prazo, não tempo real); o
  contrato de idempotência de `rotinas-agendadas` já garante que uma falha de execução
  não perde processos vencidos — eles permanecem elegíveis até a próxima execução.

## Open Questions

- Nenhuma bloqueante. Formato do protocolo (`LGPD/AAAA/NNNNNN`) e prazo padrão de
  anonimização (5 anos) são convenções assumidas por analogia ao padrão já usado no
  projeto (número de processo, `sistema_config`) — ajustáveis sem impacto arquitetural
  caso o cliente peça outro valor/formato.
