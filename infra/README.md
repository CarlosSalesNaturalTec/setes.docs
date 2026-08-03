# infra/ — Terraform do SETES.DOCS

Provisiona toda a topologia GCP em região única (`var.region`, atualmente `us-central1`) —
escolha de custo, não de residência; a transferência internacional de dados está
documentada em `docs/lgpd-transferencia-internacional-us-central1.md` (change
`migracao-regiao-us-central1`, D4).

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

## Notas de verificação (segurança)

- ~~`constraints/gcp.resourceLocations`~~ / ~~`constraints/iam.disableServiceAccountKeyCreation`~~ — **não aplicáveis no MVP**: exigem `roles/orgpolicy.policyAdmin`, vinculável só em Organização/Pasta GCP; `setes-docs` não tem Organização por trás. Ver `org_policies.tf` e `openspec/changes/bootstrap-infraestrutura/design.md` (D7).
- Secret Manager com replicação user-managed fixada na região.
- Cloud SQL sem IPv4 público (`ipv4_enabled = false`).
- Bucket com `public_access_prevention = enforced` e uniform access.

### Auditoria manual (task 11.2, 2026-07-10)

Sem as org policies automáticas, a residência/governança foi auditada manualmente contra o estado real do projeto `setes-docs`: nenhuma das 6 service accounts (`sa-web/api/jobs/scheduler/tasks-invoker/deploy`) tem papel primitivo ou chave `USER_MANAGED`; segredos, bucket e Cloud SQL confirmados sem acesso público e replicados/criados só em `southamerica-east1`. Achado: a service account padrão do Compute Engine (`PROJECT_NUMBER-compute@developer.gserviceaccount.com`, criada automaticamente pelo GCP, não usada por este projeto) tinha `roles/editor` — removido. Reexecutar esta checagem manual a cada mudança relevante de IAM, já que não há enforcement automático de plataforma.

### Incidente WIF — repositório renomeado (change `correcao-pipeline-deploy-wif`, 2026-07-14)

O pipeline de deploy (`.github/workflows/deploy.yml`) ficou quebrado desde a renomeação do repositório GitHub de `CarlosSalesNaturalTec/processos_gestor` para `CarlosSalesNaturalTec/setes.docs`: `infra/terraform.tfvars` (`github_repository`) não foi atualizado, então a `attribute_condition` do WIF provider (`google_iam_workload_identity_pool_provider.github` em `wif.tf`) continuou apontando para o nome antigo e a autenticação (`google-github-actions/auth@v2`) falhava com `unauthorized_client`. Efeito: o change `identidade-e-estrutura-organizacional` (arquivado, código em `main` desde o PR#11) nunca chegou a produção — `api`/`web` seguiam nas imagens do bootstrap. Correção: `github_repository` atualizado para o nome atual em `terraform.tfvars` (gitignored, não versionado) e reaplicado via `terraform apply`; validado tanto por redeploy manual quanto por um `deploy-api` real via CI (PR#14). Decisão deliberada: não generalizar para `assertion.repository_id` (estável a renomeações) — o repositório não deve ser renomeado de novo.

Nota para auditoria futura: `terraform plan` desta correção também revelou drift pré-existente em `google_cloud_run_v2_service.{api,web}` (`scaling`/metadata `client=gcloud`), causado por deploys manuais anteriores fora do Terraform — aplicado junto por já estar alinhado ao `min_instance_count=0` declarado no HCL.

**Gap não resolvido neste change**: o smoke test pós-deploy mostrou que o `web` carrega as páginas (`/login`, `/setup` → 200), mas o browser do usuário não consegue de fato chamar a API — `NEXT_PUBLIC_API_URL` não é configurado em build-time (bundle cai no fallback `http://localhost:8000`) e `api` tem `ingress = INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` sem nenhum load balancer interno provisionado. Anterior a este change, não bloqueou o fechamento — rastrear em change separado.

### Exposição da api ao browser (change `expor-api-e-configurar-api-url-web`, 2026-07-14/15)

Fecha o gap acima. Antes: `api.ingress = INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` (sem LB interno provisionado — `api` inalcançável de qualquer origem) e o build do `web` não recebia `NEXT_PUBLIC_API_URL` (bundle caía no fallback `http://localhost:8000`). Depois: `api.ingress = INGRESS_TRAFFIC_ALL` + `google_cloud_run_v2_service_iam_member.api_public` (`roles/run.invoker` a `allUsers`, mesmo padrão do `web_public` — sem essa peça o Cloud Run rejeita com `403` na camada de plataforma antes do IAM/ingress importarem); `apps/web/Dockerfile` promove `ARG NEXT_PUBLIC_API_URL` a `ENV` antes do `pnpm build`, e `deploy.yml` passa `--build-arg NEXT_PUBLIC_API_URL=${{ vars.NEXT_PUBLIC_API_URL }}` (repository variable) só no build do `web`. A `api` ficou pública na rede, mas **nenhuma autorização de negócio foi removida**: sessão JWT, `require_perfil`/`require_acesso_unidade`, rate limiting `slowapi` e `log_seguranca` de acesso negado continuam só na aplicação — confirmado por `curl` sem `Authorization` retornando `401` em rotas autenticadas.

Gap adicional descoberto durante a validação (não previsto no proposal/design originais): ingress público + IAM `allUsers` não bastam — o CORS middleware da aplicação (`app/config.py:75`, default só `localhost:3000`) rejeitava a origem de produção do `web` com `400 Disallowed CORS origin`. Corrigido com `env CORS_ALLOWED_ORIGINS = local.web_url` no serviço `api` (`local.web_url` fixo, mesmo padrão de `local.oidc_audience` — referenciar `google_cloud_run_v2_service.web.uri` diretamente criaria dependência circular Terraform, já que `web` referencia `api.uri` em `API_BASE_URL`). Se `api` **ou** `web` forem recriados do zero, os três valores fixos (`oidc_audience`, `web_url`, e a URL usada em `NEXT_PUBLIC_API_URL`/`api_public`) precisam ser atualizados juntos.

### Migração de região para `us-central1` (change `migracao-regiao-us-central1`, 2026-08-02/03)

`terraform destroy` do ambiente `southamerica-east1` seguido de `terraform apply` em `us-central1` (D1/D2 do design do change) — ambiente reconstruído do zero, dados de teste descartados conforme autorização registrada em `docs/lgpd-transferencia-internacional-us-central1.md`. Duas pegadinhas na execução real:

- **VPC/peering/range PSA reaproveitados, não recriados**: são recursos globais (não regionais); o `terraform destroy` da conexão de peering (`google_service_networking_connection.psa`) ficou preso por mais de 40 minutos num atraso de propagação do GCP ("Producer services... are still using this connection", mesmo sem nenhuma instância Cloud SQL viva). Decisão: manter `google_compute_network.vpc`, `google_compute_global_address.psa_range` e a conexão PSA como estavam — nenhum dos dois guarda dado de processo, e nada na autorização do cliente ou nas imutabilidades do GCP (região do Cloud SQL, localização do bucket, replicação do secret) exige destruí-los.
- **WIF pool/provider em soft-delete**: o `google_iam_workload_identity_pool.github` e seu `google_iam_workload_identity_pool_provider.github`, uma vez destruídos, ficam em soft-delete por 30 dias (erro `409 Requested entity already exists` ao tentar recriar com o mesmo ID) — resolvido com `gcloud iam workload-identity-pools [providers] undelete` seguido de `terraform import` de cada um.
- Igual ao incidente da seção anterior: `local.oidc_audience` e `local.web_url` (`cloudrun.tf`) precisaram ser atualizados de `-rj` (southamerica-east1) para `-uc` (us-central1) após a recriação de `api`/`web`. As variáveis do repositório GitHub `NEXT_PUBLIC_API_URL` e `CLOUDSQL_PRIVATE_IP` também estavam desatualizadas e foram corrigidas via `gh variable set` — `WIF_PROVIDER` não muda (ID global, reaproveitado via undelete).
- **Gap real descoberto no `deploy.yml`, não específico desta migração**: `job-manutencao-diaria` e `job-anonimizacao-lgpd` (`jobs_scheduler.tf`, `image = local.placeholder_image` com `ignore_changes` — "substituída pelo pipeline") **nunca são atualizados pelo pipeline**. `deploy.yml` só publica imagem real para `api`, `web` e o job efêmero `migrate` — os dois jobs agendados continuam com a imagem placeholder (`hello`, que não roda `python -m app.jobs.entrypoint*`) até alguém rodar `gcloud run jobs update --image` manualmente, como foi feito aqui após o `apply`. **Consequência**: qualquer alteração futura no código de `apps/api/app/jobs/` também não chega a esses jobs via CI — é um bug latente, não introduzido por este change, só exposto porque o ambiente foi reconstruído do zero. Recomenda-se abrir um change dedicado para adicionar `gcloud run jobs update job-manutencao-diaria/job-anonimizacao-lgpd --image "$IMAGE"` ao `deploy-api` do `deploy.yml`.
