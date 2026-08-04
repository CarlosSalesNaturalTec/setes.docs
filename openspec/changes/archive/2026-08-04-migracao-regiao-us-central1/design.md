## Context

A região é uma variável única (`infra/variables.tf`, `var.region =
"southamerica-east1"`) referenciada por praticamente todo recurso regional:

```
artifact_registry.tf  cloudrun.tf      cloudsql.tf     cloudtasks.tf
iam.tf                jobs_scheduler.tf network.tf     providers.tf
secrets.tf            storage.tf
```

Mecanicamente, portanto, mudar de região é mudar uma variável. O que torna a
operação não trivial são três imutabilidades do GCP:

```
Cloud SQL         região é imutável         → instância precisa ser recriada
Cloud Storage     location é imutável       → bucket precisa ser recriado
Secret Manager    replicação user-managed   → segredo precisa ser recriado
                  não é alterável
```

Num cenário com dados reais, isso significaria *dump/restore*, cópia de objetos e
janela de indisponibilidade. **Não é o caso**: o cliente autorizou o descarte
integral dos dados, que são de teste, e o sistema ainda não está em produção de
fato — está em fase de avaliação.

Há também um conjunto de comentários e justificativas espalhados pela infra que
declaram residência nacional como **requisito de conformidade**, e não como
escolha:

```
variables.tf:14   "Região única ... (residência de dados no Brasil)"
storage.tf:6      "regional, dentro do Brasil"
secrets.tf:2      "replication.user_managed ... garante residência (D4/D7)"
org_policies.tf   política de restrição de localização
```

Esses textos deixam de ser verdadeiros e precisam ser revistos junto com a
variável — caso contrário o repositório passa a afirmar uma conformidade que não
pratica.

Por fim, `openspec/config.yaml` descreve o cliente como *"órgão da administração
pública (Bahia)"*, informação que o próprio cliente corrigiu. Essa descrição
alimenta o contexto de todo change futuro e precisa ser corrigida aqui.

## Goals / Non-Goals

**Goals:**

- Região única em `us-central1`, alcançando todos os recursos regionais.
- Ambiente reconstruído do zero, com schema recriado pelas migrations existentes.
- Comentários e specs de residência revistos para refletir a decisão real.
- Contexto do projeto corrigido em `openspec/config.yaml`.
- Base legal da transferência internacional documentada.
- Manual de instruções atualizado com os seis changes.

**Non-Goals:**

- **Nenhuma preservação de dados.** Não haverá *dump/restore*, cópia de bucket
  nem exportação — decisão explícita do cliente.
- **Nenhuma alteração de código de aplicação.** Backend, frontend e contrato de
  API ficam intocados.
- Nenhuma mudança nas garantias de segurança do bucket, no controle de acesso, na
  anonimização LGPD, na retenção ou na purga.
- Nenhuma arquitetura multi-região, réplica de leitura ou CDN.
- Nenhuma revisão dos parâmetros de custo do Cloud SQL — já tratados no change
  arquivado `reducao-custo-cloudsql`.

## Decisions

### D1 — Reconstrução, não migração

`terraform destroy` seguido de `terraform apply` com `region = "us-central1"`.
Nenhuma etapa de transferência de dados.

Isso é possível **apenas** porque o cliente autorizou o descarte integral. A
decisão e a autorização ficam registradas na documentação do change (D5) — não
como detalhe de implementação, mas como o fato que viabiliza toda a abordagem.

Alternativa rejeitada: migração com preservação (*dump* do Cloud SQL, Storage
Transfer Service entre buckets, recriação de segredos, janela de
indisponibilidade). Correta se houvesse dados a preservar; aqui seria trabalho e
risco sem finalidade.

### D2 — Ordem de execução para não deixar o ambiente inacessível

```
 1. confirmar por escrito a autorização de descarte (D5)
 2. afrouxar/remover a restrição de localização em org_policies.tf
 3. terraform destroy
 4. alterar var.region → us-central1  +  revisar comentários (D4)
 5. terraform apply   → rede, Cloud SQL, bucket, segredos, Artifact Registry
 6. repovoar os segredos (db-password, jwt-signing-key, sendgrid-api-key)
 7. publicar imagens no Artifact Registry da nova região
 8. Cloud Run Job efêmero → alembic upgrade head   (schema do zero)
 9. deploy dos serviços web e api
10. fluxo de inicialização → primeiro Administrador
11. validação ponta a ponta dos seis changes
```

O passo 2 vem antes do `destroy` porque a política de localização, se estiver
ativa, bloquearia a criação de recursos na região nova no passo 5. O passo 6 é
manual e deliberadamente não automatizado: valores de segredo não pertencem ao
repositório.

### D3 — Segredos recriados, nunca versionados

Os três segredos são recriados vazios pelo Terraform e populados manualmente
fora do repositório. `db-password` e `jwt-signing-key` são **regerados** (não
reaproveitados) — como o banco é novo e todas as sessões serão invalidadas de
qualquer forma, reaproveitar valores antigos só prolongaria a vida de um segredo
sem necessidade. `sendgrid-api-key` mantém o valor vigente, por ser credencial de
terceiro alheia à região.

### D4 — Revisão dos textos de residência, não apenas da variável

Cada ocorrência que afirma residência nacional como requisito é reescrita para
declarar a realidade nova: **região única escolhida por custo, com transferência
internacional documentada sob a LGPD**. Alcança `variables.tf`, `storage.tf`,
`secrets.tf`, `org_policies.tf` e as specs de `plataforma-gcp` e
`gestao-documental`.

Deixar os comentários antigos seria pior do que não ter comentário: o
repositório passaria a afirmar uma conformidade que não pratica, e um leitor
futuro tomaria a afirmação como restrição vigente.

### D5 — Base legal e autorização registradas antes da execução

A transferência internacional (LGPD, Art. 33) exige base legal do **controlador**
— o cliente, não o fornecedor. Antes do `destroy`, este change exige registrar em
documentação:

- a base legal adotada para a transferência internacional;
- quem autorizou a decisão pelo lado do cliente, e quando;
- a autorização explícita de descarte integral dos dados existentes.

Não é burocracia defensiva: é o insumo que sustenta a decisão caso ela seja
questionada depois, e o registro de que a escolha entre custo e residência foi do
cliente, feita com a informação de que São Paulo responde mais rápido para
usuários brasileiros.

A política de privacidade e o aviso de tratamento passam a informar o tratamento
no exterior.

### D6 — Correção do contexto em `openspec/config.yaml`

O campo `context` descreve o cliente como órgão da administração pública da
Bahia. O cliente informou tratar-se de **instituição privada**. A correção entra
neste change porque é aqui que a informação passa a ter consequência prática
(residência de dados). Mantém-se explícito que a **LGPD continua obrigatória** —
a natureza privada do controlador muda a análise de transferência internacional,
não a aplicabilidade da lei.

### Fluxo principal

```
   ANTES                                    DEPOIS
   southamerica-east1                       us-central1
   ┌──────────────────────┐                 ┌──────────────────────┐
   │ Cloud Run  web + api │                 │ Cloud Run  web + api │
   │ Cloud SQL  (dados de │  destroy        │ Cloud SQL  (vazio,   │
   │            teste)    │  ──────▶ ∅ ────▶│   schema por Alembic)│
   │ Bucket documentos    │   apply         │ Bucket documentos    │
   │ Secrets (3)          │                 │ Secrets (3, novos)   │
   │ Tasks/Scheduler/Jobs │                 │ Tasks/Scheduler/Jobs │
   │ Artifact Registry    │                 │ Artifact Registry    │
   └──────────────────────┘                 └──────────────────────┘
        dados descartados                    primeiro acesso refeito
        (autorizado — D1/D5)                 pelo fluxo de inicialização

   Inalterados: código de aplicação, contrato de API, migrations,
                garantias do bucket, controle de acesso, LGPD operacional
```

## Risks / Trade-offs

- [**Operação destrutiva e irreversível**] → mitigada por: ser o último change do
  plano, exigir autorização escrita antes da execução (D5), e incidir sobre
  ambiente que ainda não está em produção de fato. Ainda assim, é o change de
  maior consequência caso executado fora de ordem — por isso a ordem explícita
  do D2.
- [Latência maior para usuários brasileiros] → reconhecida pelo próprio cliente
  no documento de ajustes ("é mais rápido nas respostas, porém mais caro") e
  aceita em favor do custo. Decisão de negócio registrada, não omissão técnica.
- [Transferência internacional sem base legal documentada] → bloqueada por
  construção: o registro da base legal e da autorização é **pré-requisito** do
  `destroy` (D5), não tarefa posterior.
- [Comentários de residência sobrevivendo à mudança e afirmando conformidade
  inexistente] → revisão explícita de cada ocorrência (D4), com tarefa própria e
  critério de aceite verificável por busca.
- [Política de localização bloqueando a criação na região nova] → afrouxada antes
  do `destroy` (passo 2 do D2), não depois.
- [Segredos repovoados manualmente podem ser esquecidos, derrubando a aplicação]
  → passo explícito na ordem de execução, com validação ponta a ponta (passo 11)
  que só passa se os três estiverem corretos.
- [`openspec/config.yaml` desatualizado contaminaria todo change futuro com a
  premissa errada de órgão público] → corrigido neste change (D6), com a ressalva
  de que a LGPD permanece obrigatória.
- [Executar antes dos demais changes obrigaria reconstruir o ambiente duas vezes]
  → registrado na proposta como recomendação forte de ordem.
