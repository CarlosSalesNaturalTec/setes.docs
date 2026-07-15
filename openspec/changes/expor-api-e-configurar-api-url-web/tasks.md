## 1. Expor a api (Terraform)

- [ ] 1.1 Alterar `infra/cloudrun.tf`: `google_cloud_run_v2_service.api.ingress` de `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` para `INGRESS_TRAFFIC_ALL` — aceite: diff do arquivo restrito a esse atributo (D1)
- [ ] 1.2 `terraform plan` e revisar o diff — aceite: diff restrito a `google_cloud_run_v2_service.api` (update in-place do `ingress`, sem replace, sem tocar `template[0].containers[0].image`); qualquer outro recurso no diff interrompe a task para investigação (drift), como em `correcao-pipeline-deploy-wif` task 1.2
- [ ] 1.3 `terraform apply` — aceite: apply conclui sem erro; `gcloud run services describe api --format='value(spec.template.metadata...)'` ou o console mostram ingress = `all`
- [ ] 1.4 Confirmar alcançabilidade pública da api sem tocar o front: `curl -i https://api-2j5ojmtaiq-rj.a.run.app/health` → `200` e `GET /setup/status` → `200` — aceite: a origem da api responde da internet pública (antes: inalcançável)

## 2. Configurar NEXT_PUBLIC_API_URL no build do web

- [ ] 2.1 Verificar/criar a repository variable `NEXT_PUBLIC_API_URL` em GitHub → Settings → Secrets and variables → Actions → Variables, valor = URL pública canônica da api (`https://api-2j5ojmtaiq-rj.a.run.app`, conferida contra `gcloud run services describe api --format='value(status.url)'`) — aceite: variable existe com o valor correto (resolve a Open Question do design)
- [ ] 2.2 `apps/web/Dockerfile`: declarar `ARG NEXT_PUBLIC_API_URL` e promovê-lo a `ENV NEXT_PUBLIC_API_URL` no estágio `build`, antes do `RUN pnpm build` — aceite: build local `docker build --build-arg NEXT_PUBLIC_API_URL=https://exemplo ...` embute o valor no bundle (D2)
- [ ] 2.3 `.github/workflows/deploy.yml` (job `deploy-web`, step "Build & push web"): adicionar `--build-arg NEXT_PUBLIC_API_URL=${{ vars.NEXT_PUBLIC_API_URL }}` ao `docker build` — aceite: workflow válido (`yaml` bem formado), build-arg presente só no build do `web` (não no da `api`)

## 3. Publicar e validar em produção

- [ ] 3.1 Publicar nova imagem do `web` com o build-arg: preferir o caminho do CI (PR trivial tocando `apps/web/**` → dispara `deploy-web` via WIF) — aceite: `deploy-web` `success` no GitHub Actions, nova revisão do `web` `Ready`; fallback documentado: build/push/deploy manual (tag = SHA de `main`) replicando o `deploy.yml`
- [ ] 3.2 Inspecionar o bundle publicado do `web` (`_next/static/chunks/app/setup/page-*.js` ou equivalente) — aceite: contém a URL pública da api, e **não** `http://localhost:8000` (fecha a regressão silenciosa apontada no Risco de D2)
- [ ] 3.3 Smoke test E2E do fluxo real do browser (Playwright, pois este change altera a alcançabilidade do login/setup — fluxo crítico): abrir `/setup` (e `/login`) apontando para a produção, confirmar que a tela consome dados da api sem erro de rede/CORS e que uma chamada autenticada retorna `200` — aceite: fluxo de setup/login carrega dados reais da api, não falha contra `localhost` (critério D4c; fecha o gap da task 5.3 de `correcao-pipeline-deploy-wif`)
- [ ] 3.4 Confirmar o caminho de rejeição na api pública: `curl -i https://api-2j5ojmtaiq-rj.a.run.app/<rota-autenticada>` sem `Authorization` → `401`/`403` — aceite: a exposição pública não concede acesso sem sessão válida (cenário "acesso negado" da spec)

## 4. Documentação e fechamento

- [ ] 4.1 Atualizar `infra/README.md` com nota curta sobre a mudança de ingress da api e a dependência do build-arg `NEXT_PUBLIC_API_URL` (rastreabilidade; mesmo padrão da nota do incidente WIF) — aceite: nota descreve o antes/depois e por que a api ficou pública (defesa na aplicação)
- [ ] 4.2 Rodar `/opsx:verify expor-api-e-configurar-api-url-web` comparando proposal/design/specs/tasks com o implementado antes de arquivar — aceite: sem divergência crítica; specs de `plataforma-gcp` refletidas na implementação
