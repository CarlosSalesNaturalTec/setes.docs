## 1. Terraform — corrigir configuração do WIF

- [x] 1.1 Atualizar `infra/terraform.tfvars` (`github_repository = "CarlosSalesNaturalTec/setes.docs"`) — aceite: valor reflete o nome atual do repositório (`git remote -v`)
- [x] 1.2 Rodar `terraform plan` e revisar o diff — aceite: diff restrito a `google_iam_workload_identity_pool_provider.github` (replace, por causa do `attribute_condition`) e `google_service_account_iam_member.deploy_wif`; qualquer outro recurso no diff interrompe a task para investigação — **nota**: o plan também trouxe `google_cloud_run_v2_service.{api,web}` (drift pré-existente de `scaling`/metadata `client=gcloud`, causado por deploys manuais anteriores fora do Terraform, não relacionado ao WIF). Investigado e aprovado pelo usuário para aplicar junto (correção alinhada ao `min_instance_count=0` já declarado no HCL)
- [x] 1.3 Rodar `terraform apply` — aceite: apply conclui sem erro, provider WIF recriado com a nova `attribute_condition` — `Apply complete! Resources: 1 added, 3 changed, 1 destroyed.`

## 2. Levantamento pré-deploy

- [x] 2.1 Checar `southamerica-east1-docker.pkg.dev/setes-docs/setes-images/{api,web}` (`gcloud artifacts docker images list`) por imagens já buildadas a partir do SHA atual de `main` — aceite: decide se o build da seção 3/4 pode reaproveitar uma imagem existente ou precisa ser feito do zero. **Resultado**: HEAD atual = `c6ab0941b8274ffeb81d3f600fe23de78ccbb696`; nenhuma imagem com essa tag existe (api tem só `3d41242`/`b8c1a23`/`2621662`, todos do bootstrap 2026-07-10; web só tem `3d41242`). Build do zero é necessário.

## 3. Redeploy manual — api

- [x] 3.1 `docker build`/`push` da `api` a partir do HEAD de `main`, tag = SHA do commit (mesma convenção do `deploy.yml`) — aceite: imagem publicada no Artifact Registry
- [x] 3.2 Rodar a migration (`gcloud run jobs deploy migrate` + `execute --wait`, mesma sequência do `deploy.yml`) **antes** do deploy do serviço — aceite: job `migrate` completa com sucesso (`alembic upgrade head` sem erro)
- [x] 3.3 `gcloud run deploy api` com a imagem de 3.1 — aceite: nova revisão `Ready`, sem erro de startup probe (`/health`)

## 4. Redeploy manual — web

- [x] 4.1 `docker build`/`push` do `web` a partir do HEAD de `main`, tag = SHA do commit — aceite: imagem publicada no Artifact Registry
- [x] 4.2 `gcloud run deploy web` com a imagem de 4.1 — aceite: nova revisão `Ready`, sem erro de startup probe (`/api/health`)

## 5. Validação

- [x] 5.1 `gcloud run services describe api` e `describe web` — aceite: tag da imagem em ambos os serviços corresponde ao SHA do HEAD de `main` no momento do deploy
- [ ] 5.2 Confirmar a correção do WIF pelo caminho normal do CI: abrir um PR trivial que toque `apps/api/**` ou `apps/web/**` (ex.: comentário/no-op) e mergear em `main` — aceite: `deploy-api`/`deploy-web` completam com `success` no GitHub Actions (autenticação WIF funcionando, não só o deploy manual das seções 3/4)
- [ ] 5.3 Smoke test em produção: `GET /login` (esperado `200`, não `404`), `GET /setup/status` (esperado `200` com corpo válido) — aceite: rotas do change `identidade-e-estrutura-organizacional` acessíveis publicamente
- [ ] 5.4 Atualizar `infra/README.md` com uma nota curta sobre o incidente e a correção (rastreabilidade para futura auditoria de IAM, seguindo o padrão já usado na seção "Auditoria manual")

## 6. Fechamento

- [ ] 6.1 Rodar `openspec verify` (ou `/opsx:verify`) comparando proposal/design/tasks com o que foi feito antes de arquivar o change
