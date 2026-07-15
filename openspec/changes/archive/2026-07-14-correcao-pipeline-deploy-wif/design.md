## Context

O pipeline `.github/workflows/deploy.yml` autentica no GCP via Workload Identity Federation (WIF), configurada em `infra/wif.tf` (`google_iam_workload_identity_pool_provider.github`) com `attribute_condition = "assertion.repository == '${var.github_repository}'"`. `var.github_repository` é definido em `infra/terraform.tfvars` como `CarlosSalesNaturalTec/processos_gestor`. O repositório GitHub foi renomeado para `CarlosSalesNaturalTec/setes.docs` (confirmado via `git remote -v` e via `repository: CarlosSalesNaturalTec/setes.docs` nos logs do `actions/checkout` dos runs falhos), mas essa mudança nunca foi propagada à configuração Terraform.

Efeito observado (run `29357473621`, PR#11, 2026-07-14): `google-github-actions/auth failed ... "unauthorized_client", "error_description":"The given credential is rejected by the attribute condition."` — os jobs `deploy-api` e `deploy-web` falham no passo de autenticação, antes de qualquer build/push/deploy. Os merges seguintes (PR#12, PR#13) não tocaram `apps/api/**`/`apps/web/**`, então o path-filter do workflow pulou (`skipped`) os jobs de deploy, mascarando o problema como "pipeline verde".

Confirmado via `gcloud run services describe` que a produção está travada nas imagens do bootstrap:
- `web`: revisão `web-00002-mgg`, imagem tag `3d41242...` (PR#1, 2026-07-10)
- `api`: revisão `api-00011-66c`, imagem tag `2621662...` (PR#7, 2026-07-10)

O código do change `identidade-e-estrutura-organizacional` (arquivado, 100% das tasks concluídas) está em `main` desde o merge do PR#11, mas nunca foi publicado.

## Goals / Non-Goals

**Goals:**
- Restaurar a autenticação WIF do pipeline de deploy, alinhando `github_repository` ao nome real do repositório.
- Publicar em produção o estado atual de `main` (que já inclui `identidade-e-estrutura-organizacional`), sem introduzir nenhuma mudança de produto neste change.
- Confirmar, com evidência concreta (não apenas "pipeline verde"), que a produção passou a refletir o código de `main`.

**Non-Goals:**
- Generalizar o mecanismo de WIF para tolerar renomeações futuras do repositório (ex.: usar `assertion.repository_id` em vez de `assertion.repository`) — descartado explicitamente: o repositório não será renomeado novamente.
- Qualquer mudança de comportamento de produto, schema de banco, ou capability nova/modificada.
- Automatizar detecção de drift entre `terraform.tfvars` e o repositório real — fora de escopo pelo mesmo motivo acima.

## Decisions

**D1 — Corrigir por valor fixo, não por mecanismo dinâmico.**
Atualizar `infra/terraform.tfvars`: `github_repository = "CarlosSalesNaturalTec/setes.docs"`. Alternativa considerada — trocar `attribute_mapping`/`attribute_condition` para usar `assertion.repository_id` (estável a renomeações) — descartada por decisão do usuário: escopo mínimo, sem generalização desnecessária para um evento que não vai se repetir.

**D2 — `terraform plan` antes de `apply`, escopo de revisão restrito.**
A mudança em `terraform.tfvars` afeta apenas dois recursos: `google_iam_workload_identity_pool_provider.github` (recriação do provider, pois `attribute_condition` força replace) e `google_service_account_iam_member.deploy_wif` (a member string referencia `var.github_repository` via `attribute.repository/${var.github_repository}`, então também é afetada). O `plan` deve ser inspecionado para confirmar que **somente** esses dois recursos aparecem no diff — qualquer diff adicional é sinal de drift não relacionado e deve pausar o apply.

**D3 — Redeploy sem novo commit de produto.**
Depois do `apply`, disparar manualmente `gcloud run deploy api`/`gcloud run deploy web` com a imagem já existente no Artifact Registry correspondente ao HEAD de `main` (se existir) ou, mais simples e alinhado ao pipeline normal, criar um commit vazio/trivial em `main` (ex. `git commit --allow-empty`) para reacionar `deploy.yml` — mas como o path-filter só builda `api`/`web` quando esses diretórios mudam, um commit vazio não dispara `deploy-api`/`deploy-web`. Decisão: usar `gcloud run deploy` manual com build a partir do HEAD atual (equivalente ao que o workflow faria), garantindo que a imagem publicada corresponda exatamente ao SHA de `main` no momento do apply. A tarefa de implementação deve gerar a imagem (`docker build`/`push`) e rodar a migration (`alembic upgrade head`) na mesma sequência que `deploy.yml` usa, para não pular o passo de migration antes do deploy da `api`.

## Risks / Trade-offs

- [Risco] `attribute_condition` força recriação do WIF provider (`google_iam_workload_identity_pool_provider`) → há uma janela entre destroy e create em que o pipeline de deploy não consegue autenticar. Mitigação: aplicar fora de horário de deploys concorrentes; validar com um run manual do workflow logo após o `apply`.
- [Risco] Redeploy manual (fora do workflow) pode divergir do processo padrão (ex.: esquecer a migration antes do deploy da `api`, como o workflow faz). Mitigação: replicar exatamente a sequência de `deploy.yml` (build → push → migrate → deploy) nas tasks, na ordem correta.
- [Trade-off] Não generalizar para `repository_id` significa que uma futura renomeação do repositório vai quebrar o pipeline do mesmo jeito. Aceito conscientemente pelo usuário — não é um risco deste change, é uma decisão de escopo.

## Migration Plan

1. Atualizar `infra/terraform.tfvars` (`github_repository`).
2. `terraform plan` — confirmar que o diff é restrito a `google_iam_workload_identity_pool_provider.github` e `google_service_account_iam_member.deploy_wif`.
3. `terraform apply`.
4. Validar autenticação: disparar o workflow `Deploy` manualmente (`gh workflow run` ou um PR trivial que toque `apps/api/**`/`apps/web/**`) e confirmar que `deploy-api`/`deploy-web` completam com sucesso.
5. Se o passo 4 não builda automaticamente (por causa do path-filter), publicar manualmente via `gcloud run deploy` a partir do HEAD de `main`, replicando a sequência build → push → migrate (api) → deploy do `deploy.yml`.
6. Smoke test pós-deploy: `gcloud run services describe api/web` (confirmar SHA da imagem = HEAD de `main`) + `GET /login` em produção (esperado: 200, não 404) + `GET /setup/status`.

**Rollback**: se o `apply` do passo 3 quebrar o WIF de forma inesperada (ex.: diff maior que o previsto no passo 2), reverter `terraform.tfvars` para o valor anterior e reaplicar — o estado anterior (ainda que quebrado para deploy) é conhecido e não afeta os serviços `api`/`web` já em execução (Cloud Run não depende de WIF para servir tráfego, só o pipeline de CI depende).

## Open Questions

- Existe alguma imagem já buildada no Artifact Registry correspondente ao HEAD atual de `main` (de alguma tentativa anterior), ou o build precisa ser feito do zero na task de deploy manual? — verificar em `southamerica-east1-docker.pkg.dev/setes-docs/setes-images/{api,web}` antes de decidir a task exata.
