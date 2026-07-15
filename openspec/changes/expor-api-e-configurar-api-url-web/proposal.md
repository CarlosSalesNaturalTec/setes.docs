## Why

O change `correcao-pipeline-deploy-wif` restaurou o pipeline e publicou `main` em produção, mas o smoke test (task 5.3) revelou que o frontend **não consegue falar com o backend**: o serviço `web` está no ar, mas o browser do usuário não alcança a `api` de nenhuma forma. Enquanto isso não for corrigido, nenhuma tela autenticada (login, setup, admin) funciona de fato em produção, mesmo com o código correto já publicado.

Duas causas independentes, ambas de infraestrutura/config de deploy (nenhuma de produto):

1. **`api` inacessível ao browser** — `infra/cloudrun.tf` declara `api.ingress = INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`, mas **nenhum load balancer interno foi provisionado** (e o `web` não tem VPC connector). A `api` só aceitaria tráfego de um LB interno que não existe.
2. **`web` buildado sem a URL da api** — `apps/web/lib/api.ts` lê `NEXT_PUBLIC_API_URL` em **build-time** (embutido no bundle JS servido ao browser), mas o `docker build` do `web` em `.github/workflows/deploy.yml` não passa esse build-arg, então o bundle cai no fallback `http://localhost:8000` — inalcançável a partir do navegador do usuário.

Arquitetura escolhida (decisão do usuário): **o browser chama a `api` diretamente**, alinhada ao design já existente — `lib/api.ts` é um cliente de browser com autenticação JWT própria (sliding window via `X-Renewed-Token`), rate limiting via `slowapi` e endpoints `/internal/*` protegidos por OIDC. Expor a `api` publicamente não remove nenhuma camada de segurança; apenas torna alcançável o que o front já espera consumir.

## What Changes

- **`infra/cloudrun.tf`**: `api.ingress` passa de `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` para `INGRESS_TRAFFIC_ALL`, e um novo `google_cloud_run_v2_service_iam_member` concede `roles/run.invoker` a `allUsers` na `api` (mesmo padrão do `web_public` já existente para o `web`) — sem essa segunda peça, o Cloud Run rejeita com `403` na camada de plataforma antes do request chegar ao container, independente do `ingress`. A `api` continua **não** `--allow-unauthenticated` no sentido de negócio: toda autorização real (JWT próprio, perfil/unidade) permanece na aplicação.
- **`.github/workflows/deploy.yml`**: o step de `docker build` do `web` passa a receber `--build-arg NEXT_PUBLIC_API_URL=<URL pública canônica da api>`.
- **`apps/web/Dockerfile`**: declara `ARG NEXT_PUBLIC_API_URL` e o promove a `ENV` no estágio `build`, para que `pnpm build` do Next.js embuta o valor no bundle.
- **Validação em produção**: smoke test do fluxo real do browser — `GET /setup/status` (via a origem pública da api) responde `200`, e a tela `/setup` no navegador carrega dados da api em vez de falhar contra `localhost`. Fecha o gap registrado na task 5.3 de `correcao-pipeline-deploy-wif`.

Fora de escopo: qualquer BFF/proxy no Next.js, VPC connector no `web`, ou load balancer interno (arquitetura alternativa descartada); qualquer mudança de comportamento de produto, schema de banco ou nova regra de negócio.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
- `plataforma-gcp`: adiciona o requisito de **alcançabilidade frontend→backend** — a `api` SHALL ser acessível pela origem do browser e o build do `web` SHALL embutir a URL da `api`. Hoje a capability especifica os dois serviços Cloud Run e seus health checks, mas não garante que o browser alcance a `api`; este change torna essa alcançabilidade uma propriedade especificada (com o cenário de "browser alcança a api" e o de "credencial ausente/ inválida é rejeitada pela própria api, não pela rede").

## Impact

- **Depende de**: `correcao-pipeline-deploy-wif` (arquivado/em fechamento) — que restaurou o WIF e publicou `main`; e de `bootstrap-infraestrutura` (arquivado), que criou `infra/cloudrun.tf` com o `ingress` interno.
- **Terraform**: `infra/cloudrun.tf` — atributo `ingress` de `google_cloud_run_v2_service.api` (mudança in-place, sem replace; não afeta a revisão de imagem, gerida pelo pipeline via `ignore_changes`). Nenhum outro recurso deve aparecer no `plan` — validar antes do `apply`.
- **CI/CD**: `.github/workflows/deploy.yml` (job `deploy-web`, step de build) e `apps/web/Dockerfile`. O `web` precisa de **rebuild** para o novo `NEXT_PUBLIC_API_URL` fazer efeito (é build-time, não runtime).
- **Frontend**: nenhuma mudança de código — `apps/web/lib/api.ts` já consome `NEXT_PUBLIC_API_URL`; só passa a recebê-lo de fato.
- **Banco de dados**: nenhuma tabela nova ou afetada.
- **Secret Manager / Cloud Storage**: nenhum segredo ou bucket novo — `NEXT_PUBLIC_API_URL` é a URL pública da api (não é segredo; `NEXT_PUBLIC_*` é exposto ao browser por definição).
- **Segurança**: a `api` passa a receber tráfego público, mas mantém toda a defesa de aplicação (JWT, `require_perfil`/`require_acesso_unidade`, `log_seguranca` de acesso negado, rate limiting `slowapi`, `/internal/*` OIDC-only). O Cloud SQL permanece sem IP público (`conectividade-e-seguranca`), inalterado.
- **LGPD**: não aplicável diretamente — mudança de infra/config de deploy, sem tratamento de dado pessoal novo. Desbloqueia o uso real das telas já avaliadas em `identidade-e-estrutura-organizacional`.
- **Risco de execução**: `terraform apply` sobre a `api` em produção é sensível; a mudança de `ingress` é in-place e reversível (basta reverter o atributo e reaplicar). Revisar o `plan` antes do `apply`.
