## Context

Depois de `correcao-pipeline-deploy-wif`, `main` está publicado em produção, mas o browser não alcança a `api`. Estado atual observado (inspeção de `infra/cloudrun.tf`, `.github/workflows/deploy.yml`, `apps/web/Dockerfile`, `apps/web/lib/api.ts`):

- **`infra/cloudrun.tf:32`** — `google_cloud_run_v2_service.api` tem `ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"`. Não há load balancer interno em nenhum `.tf` (`infra/network.tf` provisiona VPC/subnet para Direct VPC egress do Cloud SQL, não um LB de aplicação). O serviço `web` (`cloudrun.tf:163`) tem `ingress = "INGRESS_TRAFFIC_ALL"` e uma env var **server-side** `API_BASE_URL = google_cloud_run_v2_service.api.uri` (`cloudrun.tf:184`) — mas o `web` não tem `vpc_access`, então nem o SSR alcança a `api` interna. A `api` está, na prática, inalcançável de qualquer origem.
- **`apps/web/lib/api.ts:21`** — `const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";`. Como `NEXT_PUBLIC_*` é resolvido em **build-time** pelo Next.js e embutido no bundle servido ao browser, e o `docker build` do `web` (`deploy.yml:93`) roda `docker build -t "$IMAGE" -f apps/web/Dockerfile .` **sem** `--build-arg`, o bundle de produção contém `http://localhost:8000` — inalcançável a partir do navegador do usuário.
- **URL canônica da `api`** — `infra/cloudrun.tf:20` já fixa `oidc_audience = "https://api-2j5ojmtaiq-rj.a.run.app"` (URL determinística do Cloud Run por projeto/serviço/região). É essa a origem que o browser precisa alcançar.

A arquitetura pretendida (e já implementada no cliente) é **browser → `api` direto**: `apps/web/lib/api.ts` é um cliente de browser que persiste o Bearer token e captura o `X-Renewed-Token` (sliding window). O backend tem autenticação/autorização próprias, rate limiting (`slowapi`) e `/internal/*` OIDC-only. Ou seja, a `api` foi projetada para ser consumida diretamente pelo browser — falta apenas torná-la alcançável e informar sua URL ao build do front.

## Goals / Non-Goals

**Goals:**
- Tornar a `api` alcançável pela origem do browser (`ingress = INGRESS_TRAFFIC_ALL`), sem abrir mão de nenhuma defesa de aplicação.
- Fazer o build do `web` embutir a URL pública canônica da `api` em `NEXT_PUBLIC_API_URL`, para o cliente do browser resolver a `api` real em produção.
- Validar com evidência do fluxo real do browser (não só "revisão Ready") que o front passou a falar com o back.

**Non-Goals:**
- Introduzir BFF/proxy `/api/*` no Next.js, VPC connector no `web`, ou load balancer interno (arquitetura alternativa "browser → web → api interna", descartada por decisão do usuário).
- Mudar `apps/web/lib/api.ts` ou qualquer código de produto — o cliente já consome `NEXT_PUBLIC_API_URL`.
- Migrar a resolução da URL da `api` para runtime (ex.: config endpoint) — mantém-se build-time, como o Next.js espera para `NEXT_PUBLIC_*`.
- Alterar a env var server-side `API_BASE_URL` do serviço `web` (não usada pelo caminho browser→api; fora de escopo).

## Decisions

**D1 — `api.ingress = INGRESS_TRAFFIC_ALL` + IAM invoker público; segurança fica na aplicação.**
Trocar o `ingress` da `api` de `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` para `INGRESS_TRAFFIC_ALL` em `infra/cloudrun.tf`. **Correção identificada na implementação**: `ingress` sozinho controla só a alcançabilidade de rede — o Cloud Run v2 aplica, numa camada separada e sempre ativa, autorização IAM (`roles/run.invoker`) antes de qualquer request chegar ao container. Hoje a `api` só concede `run.invoker` a `sa-web` e `sa-tasks-invoker` (`infra/iam.tf:94-106`); um browser sem credencial GCP receberia `403` da própria plataforma Cloud Run, nunca alcançando o JWT da aplicação. Por isso o change também adiciona um `google_cloud_run_v2_service_iam_member` concedendo `roles/run.invoker` a `allUsers` na `api`, no mesmo padrão já usado para o `web` (`cloudrun.tf:205-210`, recurso `web_public`). Isso é o análogo do `--allow-unauthenticated` do `gcloud run deploy` — remove a exigência de token OIDC/IAM do Cloud Run, mas **não** remove nenhuma autorização de negócio: a autenticação/autorização real continua inteiramente no backend (sessão JWT HS256 + tabela `sessao`, `require_perfil`/`require_acesso_unidade`, `log_seguranca` de acesso negado, rate limiting `slowapi`, `/internal/*` verificando OIDC do Cloud Tasks — este último continua exigindo `run.invoker` de `sa-tasks-invoker`, inalterado). Alternativa considerada — manter a `api` interna e adicionar VPC connector + internal LB (ou proxy no Next.js) — descartada pelo usuário: mais superfície de infra para um MVP onde a `api` já se defende sozinha. Ambas as mudanças (`ingress` e IAM member) são **in-place**/aditivas (não forçam replace do serviço) e não tocam a imagem (protegida por `ignore_changes` em `cloudrun.tf:150`).

**D2 — `NEXT_PUBLIC_API_URL` como build-arg vindo de GitHub Actions Variable.**
`apps/web/Dockerfile` passa a declarar `ARG NEXT_PUBLIC_API_URL` e promovê-lo a `ENV NEXT_PUBLIC_API_URL` **antes** do `pnpm build` (estágio `build`), para o Next.js embutir o valor. O `deploy.yml` passa `--build-arg NEXT_PUBLIC_API_URL=${{ vars.NEXT_PUBLIC_API_URL }}` no `docker build` do `web`. A URL vem de uma **repository variable** do GitHub Actions (mesmo padrão de `vars.WIF_PROVIDER`, `vars.DEPLOY_SA_EMAIL`, `vars.GCP_PROJECT_ID` já usados no workflow), definida como a URL canônica `https://api-2j5ojmtaiq-rj.a.run.app`. Alternativa considerada — derivar a URL em tempo de CI via `gcloud run services describe api --format='value(status.url)'` — descartada: adiciona uma chamada gcloud e um ponto de falha, sendo que a URL é determinística e já está fixada como constante em `cloudrun.tf`. Documentar a criação da variable como task explícita (não versionável no repo).

**D3 — Rebuild obrigatório do `web`; `api` só precisa do apply.**
Como `NEXT_PUBLIC_API_URL` é build-time, o valor só passa a valer numa **nova imagem** do `web` — um simples redeploy da imagem atual não resolve. Sequência: (1) `terraform apply` do `ingress` da `api`; (2) rebuild+push+deploy do `web` com o novo build-arg. A `api` não precisa de rebuild (a mudança é só de ingress, no plano de infra). Para o `web`, seguir a mesma convenção do `deploy.yml` (tag = SHA). Validar preferencialmente pelo caminho normal do CI (um PR que toque `apps/web/**` dispara `deploy-web`), com redeploy manual como fallback — espelhando o que foi feito e aprovado em `correcao-pipeline-deploy-wif`.

**D4 — Validação pelo fluxo real do browser.**
O critério de aceite do gap (task 5.3 do change anterior) é o browser alcançar a `api`. Validar: (a) `GET https://api-2j5ojmtaiq-rj.a.run.app/setup/status` → `200` direto (ingress público funcionando); (b) inspecionar o bundle publicado do `web` (`_next/static/chunks/.../setup/page-*.js`) e confirmar que contém a URL da `api`, não `localhost:8000`; (c) abrir `/setup` no navegador e confirmar que a tela consome dados da `api` sem erro de rede. Sem esse passo (c), repete-se o erro do change anterior: "Ready" no Cloud Run não prova conectividade do browser.

## Risks / Trade-offs

- [Risco] Expor a `api` publicamente aumenta a superfície de ataque → Mitigação: nenhuma rota fica sem autenticação além das já públicas por design (`/health`, futura consulta pública); rate limiting `slowapi` já montado (`app/rate_limit.py`); `/internal/*` exige OIDC do Cloud Tasks e é rejeitado por origem pública sem token válido. O Cloud SQL permanece sem IP público (inalterado).
- [Risco] `NEXT_PUBLIC_API_URL` errado ou ausente na variable do CI → o bundle volta a apontar para `localhost` e o gap reaparece silenciosamente (revisão fica "Ready" mesmo assim) → Mitigação: a validação D4(b)/(c) inspeciona o bundle e o fluxo real; task dedicada para criar a variable antes do primeiro build.
- [Risco] A URL canônica `api-2j5ojmtaiq-rj.a.run.app` mudaria se o serviço `api` fosse recriado do zero → Mitigação: é o mesmo pressuposto já assumido por `oidc_audience` em `cloudrun.tf:20`; se o serviço for recriado, ambos os valores (audience e build-arg) precisam ser atualizados juntos — anotar junto ao local existente.
- [Trade-off] Manter a URL da `api` como GitHub variable (não no Terraform output automatizado) cria um acoplamento manual entre infra e CI. Aceito para o MVP: a URL é estável e já duplicada como constante no HCL.

## Migration Plan

1. `infra/cloudrun.tf`: `api.ingress = "INGRESS_TRAFFIC_ALL"` + novo `google_cloud_run_v2_service_iam_member` (`allUsers` → `roles/run.invoker` na `api`).
2. `terraform plan` — confirmar diff restrito a `google_cloud_run_v2_service.api` (atributo `ingress`, update in-place) e ao novo `google_cloud_run_v2_service_iam_member` (recurso novo, sem replace de nada existente); qualquer outro recurso pausa o apply para investigação.
3. `terraform apply`.
4. Criar/confirmar a repository variable `NEXT_PUBLIC_API_URL = https://api-2j5ojmtaiq-rj.a.run.app` no GitHub Actions.
5. `apps/web/Dockerfile`: `ARG`/`ENV NEXT_PUBLIC_API_URL` no estágio `build`. `.github/workflows/deploy.yml`: `--build-arg NEXT_PUBLIC_API_URL=${{ vars.NEXT_PUBLIC_API_URL }}` no build do `web`.
6. Publicar nova imagem do `web`: preferir o caminho do CI (PR tocando `apps/web/**` → `deploy-web`); fallback é build/push/deploy manual (tag = SHA de `main`), replicando o `deploy.yml`.
7. Smoke test (D4): `GET /setup/status` na origem da `api` → `200`; inspeção do bundle; `/setup` no browser consumindo a `api`.

**Rollback**: reverter `ingress` para `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` e reaplicar restaura o estado anterior (a `api` volta a inalcançável, mas os serviços seguem servindo); reverter o build-arg exige apenas rebuild do `web`. Nenhum dos passos é destrutivo (sem replace de serviço, sem migration de banco).

## Open Questions

- A repository variable `NEXT_PUBLIC_API_URL` já existe no GitHub (de alguma configuração anterior) ou precisa ser criada? — verificar em Settings → Secrets and variables → Actions → Variables antes do passo 5. (Não versionável; task de implementação deve confirmar o valor exato contra a URL real da `api`.)
