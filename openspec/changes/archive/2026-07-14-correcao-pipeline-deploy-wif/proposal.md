## Why

O pipeline de deploy (`.github/workflows/deploy.yml`) está quebrado desde 2026-07-14: a autenticação via Workload Identity Federation falha com `unauthorized_client` / "rejected by the attribute condition" porque o repositório GitHub foi renomeado de `CarlosSalesNaturalTec/processos_gestor` para `CarlosSalesNaturalTec/setes.docs`, mas `infra/terraform.tfvars` (`github_repository`) — e por consequência a `attribute_condition` do WIF provider e a IAM binding da `sa-deploy` em `infra/wif.tf` — continuam apontando para o nome antigo. Na prática, isso significa que o change `identidade-e-estrutura-organizacional`, arquivado como concluído, nunca chegou a produção: os serviços Cloud Run `web` e `api` ainda rodam as imagens do bootstrap (commits `3d41242` e `2621662`, respectivamente), confirmado via `gcloud run services describe` e smoke test (`GET /login` → 404 em produção). Precisa ser corrigido antes que qualquer change futuro possa ser considerado "em produção" de fato.

## What Changes

- Atualizar `infra/terraform.tfvars` (`github_repository`) para o nome atual do repositório (`CarlosSalesNaturalTec/setes.docs`).
- `terraform apply` para propagar a correção à `attribute_condition` do WIF provider (`google_iam_workload_identity_pool_provider.github`) e à IAM binding da `sa-deploy` (`google_service_account_iam_member.deploy_wif`) em `infra/wif.tf`.
- Redisparar o deploy da `api` e do `web` a partir do estado atual de `main` (sem novas features de produto) para publicar o código já mergeado do change `identidade-e-estrutura-organizacional`.
- Validar em produção, via smoke test pós-deploy, que as rotas desse change estão acessíveis (`/setup`, `/login`, etc.) e que `gcloud run services describe` mostra as imagens com o SHA correspondente ao HEAD de `main`.

Fora de escopo: qualquer generalização do mecanismo de WIF (ex.: usar `repository_id` em vez do nome do repositório) — descartada porque o repositório não será renomeado novamente.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
(nenhuma — o requisito de WIF em `plataforma-gcp` ("Deploy autenticado via Workload Identity Federation") não muda; este change corrige um valor de configuração que o deixou fora de conformidade com o requisito já especificado, não altera o requisito em si)

## Impact

- **Depende de**: `bootstrap-infraestrutura` (arquivado) — change que criou `infra/wif.tf` e `infra/terraform.tfvars`.
- **Desbloqueia**: a publicação em produção do change `identidade-e-estrutura-organizacional` (já arquivado, código já em `main`, aguardando deploy).
- **Terraform**: `infra/terraform.tfvars` (variável `github_repository`); reaplicação de `infra/wif.tf` (atualiza `google_iam_workload_identity_pool_provider.github.attribute_condition` e `google_service_account_iam_member.deploy_wif`). Nenhum outro recurso deve ser afetado — validar via `terraform plan` antes do `apply`.
- **Banco de dados**: nenhuma tabela nova ou afetada.
- **Secret Manager / Cloud Storage**: nenhum segredo ou bucket novo.
- **CI/CD**: `.github/workflows/deploy.yml` não muda — a causa é infraestrutura, não o workflow; a execução do pipeline após o `apply` valida a correção.
- **LGPD**: não aplicável diretamente — mudança de infraestrutura de deploy, sem tratamento de dado pessoal. Desbloqueia, porém, a publicação de um change que trata dados pessoais (`identidade-e-estrutura-organizacional`), cujo tratamento LGPD já foi avaliado nesse change anterior.
- **Risco de execução**: `terraform apply` em produção é uma ação sensível sobre infraestrutura já provisionada — revisar o `plan` antes de aplicar; a mudança é estritamente escopada ao WIF provider e à IAM binding correspondente.
