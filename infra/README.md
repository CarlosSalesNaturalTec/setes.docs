# infra/ — Terraform do SETES.DOCS

Provisiona toda a topologia GCP do bootstrap em `southamerica-east1` (residência de dados no Brasil).

## Pré-requisitos

- `gcloud auth application-default login` (ou uma identidade com os papéis necessários).
- Papéis do executor: `roles/owner` **não** é usado pelas SAs criadas, mas o operador que roda o `apply` precisa de permissão para criar SAs, IAM, org policies (`roles/orgpolicy.policyAdmin`), redes, Cloud SQL etc.

## Bootstrap do state (uma vez, fora do Terraform)

O backend GCS precisa existir antes do `init`:

```bash
gcloud storage buckets create gs://setes-docs-tfstate \
  --project=<PROJECT_ID> --location=southamerica-east1 \
  --uniform-bucket-level-access
gcloud storage buckets update gs://setes-docs-tfstate --versioning
```

## Uso

```bash
cp backend.hcl.example backend.hcl        # ajuste o bucket
cp terraform.tfvars.example terraform.tfvars  # ajuste project_id, github_repository, etc.

terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```

## Ordem de dependências (resumo)

APIs → org policies → rede + PSA → Cloud SQL → Secret Manager → IAM → Artifact Registry
→ Cloud Tasks → Cloud Run (api/web) → Jobs + Scheduler → WIF.

O Terraform resolve a ordem pelos `depends_on`/referências. A imagem dos serviços/jobs
começa como placeholder público e é substituída pelo pipeline (`ignore_changes` no image).

## Teto de conexões (task 6.4)

`api_max_instances × api_pool_size < db_max_connections`
Padrão: `10 × 5 = 50 < 100`. O app respeita `pool_size=5, max_overflow=0` (ver `apps/api/app/db/session.py`).

## Notas de verificação (residência / segurança)

- ~~`constraints/gcp.resourceLocations`~~ / ~~`constraints/iam.disableServiceAccountKeyCreation`~~ — **não aplicáveis no MVP**: exigem `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta GCP; `setes-docs` não tem Organização por trás. Ver `org_policies.tf` e `openspec/changes/bootstrap-infraestrutura/design.md` (D7).
- Secret Manager com replicação user-managed fixada na região.
- Cloud SQL sem IPv4 público (`ipv4_enabled = false`).
- Bucket com `public_access_prevention = enforced` e uniform access.

### Auditoria manual (task 11.2, 2026-07-10)

Sem as org policies automáticas, a residência/governança foi auditada manualmente contra o estado real do projeto `setes-docs`: nenhuma das 6 service accounts (`sa-web/api/jobs/scheduler/tasks-invoker/deploy`) tem papel primitivo ou chave `USER_MANAGED`; segredos, bucket e Cloud SQL confirmados sem acesso público e replicados/criados só em `southamerica-east1`. Achado: a service account padrão do Compute Engine (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`, criada automaticamente pelo GCP, não usada por este projeto) tinha `roles/editor` — removido. Reexecutar esta checagem manual a cada mudança relevante de IAM, já que não há enforcement automático de plataforma.
