## 1. Código — corrigir o audience do token OIDC

- [x] 1.1 `app/email/queue.py`: adicionar campo `oidc_audience` a `EnqueueConfig` e preenchê-lo em `config_from_settings` com `settings.oidc_audience` — aceite: `EnqueueConfig` carrega o audience base; sem hardcode de URL
- [x] 1.2 `app/email/queue.py`: passar `"audience": config.oidc_audience` no `oidc_token` da task em `enqueue_email` — aceite: a task criada assina o token com a URL base, não com a URL do alvo (com path)
- [x] 1.3 `tests/test_email_queue.py` (teste automatizado obrigatório — toca autenticação do endpoint interno): asserção de que `oidc_token["audience"]` é a URL base, distinta do `http_request.url` (com path) — aceite: `pytest tests/test_email_queue.py` passa e falharia se o audience voltasse a ser omitido/igual ao alvo

## 2. Terraform — configuração de produção do e-mail

- [x] 2.1 `infra/cloudrun.tf`: injetar `FRONTEND_BASE_URL = local.web_url` no serviço `api` — aceite: env presente no template do serviço; `terraform fmt` limpo
- [x] 2.2 `infra/variables.tf`: `email_provider_from` com default `""` e descrição exigindo Sender Identity verificada no SendGrid — aceite: `terraform fmt` limpo; descrição deixa claro que o valor real vai em `terraform.tfvars`

## 3. SendGrid + Secret Manager (manual, fora do VCS)

- [x] 3.1 Verificar uma Sender Identity **ou** autenticar um domínio no SendGrid e anotar o remetente resultante — aceite: remetente aparece como "Verified" no painel do SendGrid (remetente verificado: `naturalbahia@gmail.com`)
- [x] 3.2 Confirmar que o secret `sendgrid-api-key` (Secret Manager) contém a API key real, não o placeholder `REPLACE_ME` de `infra/secrets.tf` — aceite: `gcloud secrets versions access latest --secret=sendgrid-api-key` retorna uma chave `SG.…` válida (não `REPLACE_ME`) — confirmado: prefixo `SG.`, 69 chars
- [x] 3.3 Definir `email_provider_from = "<remetente do 3.1>"` em `infra/terraform.tfvars` (gitignored) — aceite: valor bate exatamente com o remetente verificado (`naturalbahia@gmail.com`)

## 4. Deploy

- [x] 4.1 `terraform plan` (em `infra/`) e revisar o diff — aceite: diff restrito ao template do serviço `api` (novo `FRONTEND_BASE_URL`, novo valor de `EMAIL_FROM`); qualquer outro recurso pausa o apply para investigação — investigado: diff do `api` correto (EMAIL_FROM + FRONTEND_BASE_URL); recursos extras = infra do Épico 10 LGPD nunca aplicada (bucket `lgpd_solicitacoes` + IAM + `entrypoint_lgpd`), aceita conscientemente para full apply; `entrypoint_lgpd.py` confirmado no código
- [x] 4.2 `terraform apply` — aceite: nova revisão do serviço `api` `Ready`, sem erro no startup probe (`/health`) — `Apply complete! 2 added, 3 changed`; revisão `api-00025-nxw` Ready; envs `FRONTEND_BASE_URL` e `EMAIL_FROM=naturalbahia@gmail.com` confirmados
- [ ] 4.3 Publicar a imagem `api` com o código da seção 1 pelo fluxo normal (merge em `main` → `deploy.yml`) — aceite: revisão do serviço `api` com a tag = SHA do commit do fix (`gcloud run services describe api`)

## 5. Validação em produção

- [ ] 5.1 Solicitar "recuperar senha" para um e-mail **cadastrado real** e checar os logs do Cloud Run — aceite: `POST /internal/tasks/email` responde **200** (não mais 401) e há log `email.enviado event_id=recuperacao-senha:… to=…`
- [ ] 5.2 Confirmar o recebimento do e-mail e que o link é `https://web-…run.app/redefinir-senha/{token}` (não `localhost`) e conclui a redefinição — aceite: fluxo de redefinição de senha completa fim a fim a partir do link recebido
- [ ] 5.3 Solicitar recuperação para um e-mail **não cadastrado** — aceite: mesma mensagem genérica, nenhum log `email.*` correspondente (US 1.3 Cen.5 preservado)

## 6. Fechamento

- [ ] 6.1 Rodar `openspec verify` (ou `/opsx:verify`) comparando proposal/design/tasks/specs com o que foi feito — aceite: sem divergência crítica; delta de `fila-notificacoes` reflete o comportamento implementado
- [ ] 6.2 Sincronizar o delta de `fila-notificacoes` para `openspec/specs/` e arquivar o change — aceite: spec consolidada atualizada, change movido para `openspec/changes/archive/`
