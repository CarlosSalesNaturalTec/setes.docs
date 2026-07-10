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

- `constraints/gcp.resourceLocations = in:southamerica-east1-locations` bloqueia recursos fora da região.
- `constraints/iam.disableServiceAccountKeyCreation` bloqueia chaves JSON de SA.
- Secret Manager com replicação user-managed fixada na região.
- Cloud SQL sem IPv4 público (`ipv4_enabled = false`).
- Bucket com `public_access_prevention = enforced` e uniform access.
