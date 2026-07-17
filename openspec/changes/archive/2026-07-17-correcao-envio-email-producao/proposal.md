## Why

Em produção, **nenhum e-mail transacional é entregue** (recuperação de senha, primeiro
acesso, reset por Administrador, e-mails de processo/prazo). Um usuário solicitou "recuperar
senha" (2026-07-17): a API respondeu a mensagem genérica de sucesso (US 1.3 Cen.3/Cen.5),
mas nada chegou ao SendGrid — confirmado no Activity Feed do provedor.

A investigação nos logs do Cloud Run (serviço `api`) revelou a causa raiz e dois defeitos de
configuração de produção encadeados atrás dela:

1. **`/internal/tasks/email` responde `401 Unauthorized`** (log real:
   `POST /internal/tasks/email HTTP/1.1 401`). A Cloud Task é entregue, mas a verificação OIDC
   recusa o token. Causa: `app/email/queue.py` cria a task sem `audience` no `oidc_token`, então
   o Cloud Tasks assina o token com `aud` = **URL completa do alvo**
   (`https://api-…run.app/internal/tasks/email`), enquanto `security/oidc.py:require_tasks_invoker`
   valida contra `settings.oidc_audience` = **URL base sem o path**
   (`https://api-…run.app`). `aud` divergente → `JWTError` → 401. Como a fila usa
   `maxAttempts=1`, a mensagem é descartada sem redespacho — o e-mail nunca chega ao
   `send_email`. Os testes nunca pegaram isso porque fazem *fake* de `verify_google_oidc`
   (`tests/conftest.py`); é um defeito que só se manifesta na primeira chamada real Cloud Tasks
   → endpoint interno em produção.

2. **`EMAIL_FROM = no-reply@setes.docs`** (default de `var.email_provider_from`) — domínio
   fictício, **não** é uma Sender Identity verificada no SendGrid. Assim que o defeito (1) for
   corrigido e o envio chegar ao provedor, o SendGrid recusará com **HTTP 403** (recusa que
   sequer aparece no Activity Feed).

3. **`FRONTEND_BASE_URL` não é injetado no serviço `api`** (`infra/cloudrun.tf`) — a app cai no
   default `http://localhost:3000` (`app/config.py`), então todo link de e-mail
   (`/redefinir-senha/{token}`, `/primeiro-acesso/{token}`, link direto de processo) sai
   quebrado em produção, mesmo quando o envio funcionar.

Sem (1) corrigido, nenhum e-mail é entregue; com (1) mas sem (2)/(3), os e-mails ou são
recusados pelo provedor ou chegam com links inúteis. Os três precisam ser corrigidos juntos
para que o fluxo de e-mail funcione fim a fim.

## What Changes

- **Código (`app/email/queue.py`)**: assinar o `oidc_token` da Cloud Task com `audience`
  explícito = `settings.oidc_audience` (a URL base, a mesma string que o endpoint interno
  valida), em vez de deixar o Cloud Tasks inferir a URL do alvo com o path. `EnqueueConfig`
  ganha o campo `oidc_audience`.
- **Teste (`tests/test_email_queue.py`)**: travar a regressão — asserção de que o `aud`
  assinado é a URL base, **sem** o path do endpoint.
- **Terraform (`infra/cloudrun.tf`)**: injetar `FRONTEND_BASE_URL = local.web_url` no serviço
  `api`.
- **Terraform (`infra/variables.tf`)**: `email_provider_from` passa a ter default vazio e
  descrição explícita exigindo uma Sender Identity verificada no SendGrid; o valor real é
  definido em `infra/terraform.tfvars` (gitignored).
- **Operação (fora do VCS, manual)**: verificar a Sender Identity / autenticar o domínio no
  SendGrid; garantir que o secret `sendgrid-api-key` no Secret Manager contém a chave real (não
  o placeholder `REPLACE_ME` de `infra/secrets.tf`); `terraform apply`; redeploy da `api`.

Fora de escopo: qualquer mudança no contrato de e-mail (fila `maxAttempts=1`, ACK-sempre no
endpoint interno), no conteúdo dos e-mails, ou nas regras de negócio de recuperação de senha /
primeiro acesso — nada disso muda; este change apenas faz o caminho de entrega, já
especificado, funcionar em produção.

## Capabilities

### New Capabilities
(nenhuma)

### Modified Capabilities
- **fila-notificacoes** — o requisito "Endpoint interno protegido por OIDC" ganha um cenário
  explícito de que o token entregue pelo Cloud Tasks tem `aud` igual ao audience esperado pelo
  endpoint, para o caminho de aceitação (que hoje falha em produção) ser inequívoco e a
  regressão ficar travada. O comportamento pretendido não muda — o cenário "Chamada autenticada
  pelo Cloud Tasks é aceita" já existia; o defeito era o `aud` não bater.

`EMAIL_FROM` e `FRONTEND_BASE_URL` são **correções de configuração** que fazem requisitos já
especificados (entrega de e-mail em `alertas-email-processo`/`notificacoes-internas`; link de
recuperação em `autenticacao`) passarem a valer em produção — não alteram nenhum requisito de
capability, análogo ao change `correcao-pipeline-deploy-wif`.

## Impact

- **Depende de**: `bootstrap-infraestrutura` (arquivado — criou a fila `emails`, o endpoint
  `/internal/tasks/email` e o secret `sendgrid-api-key`) e `notificacoes-e-alertas` (arquivado
  — primeiro emissor real da fila). Requer também que `correcao-pipeline-deploy-wif` (arquivado)
  esteja aplicado, para o deploy chegar a produção.
- **Terraform**: `infra/cloudrun.tf` (novo env `FRONTEND_BASE_URL` no serviço `api`) e
  `infra/variables.tf` (`email_provider_from`). `terraform apply` cria uma nova revisão do
  serviço `api`. Revisar o `plan` — o diff deve se restringir ao template do serviço `api`.
- **Banco de dados**: nenhuma tabela nova ou afetada.
- **Secret Manager / Cloud Storage**: nenhum segredo novo. O secret existente
  `sendgrid-api-key` precisa conter o valor real (verificação manual — não versionado).
- **CI/CD**: `pnpm gen:types:check` não é afetado (nenhuma mudança de schema/rota FastAPI). O
  deploy segue o fluxo normal de `main`.
- **LGPD**: os e-mails transacionais deste fluxo não expõem dado pessoal de interessado (corpo
  restrito a número/assunto/unidade/link, conforme `notificacoes-e-alertas`); a correção não
  altera esse tratamento. Recuperação de senha trata e-mail de usuário (dado funcional), sem
  mudança de coleta/retenção.
- **Risco de execução**: `terraform apply` em produção sobre serviço em execução — o Cloud Run
  faz rollout gradual da nova revisão; se a revisão falhar no startup probe (`/health`), o
  tráfego permanece na revisão anterior. `EMAIL_FROM` vazio sem `terraform.tfvars` definido
  faria a app subir com remetente vazio (SendGrid recusaria) — por isso a task de `apply` exige
  confirmar o valor em `terraform.tfvars` antes.
