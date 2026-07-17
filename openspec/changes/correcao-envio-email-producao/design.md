## Context

O envio de e-mail é assíncrono via Cloud Tasks (fila `emails`, `maxAttempts=1`):

1. Um endpoint de negócio (ex.: `POST /auth/recuperar-senha`) chama `enqueue_email_seguro`
   (`app/email/queue.py`), que cria uma Cloud Task apontando para
   `POST /internal/tasks/email` do próprio serviço `api`, anexando um `oidc_token` da
   `sa-tasks-invoker`.
2. O Cloud Tasks entrega a task via HTTP ao endpoint interno.
3. `require_tasks_invoker` (`app/security/oidc.py`) valida o token OIDC; se ok,
   `process_email_task` (`app/main.py`) chama `send_email` (`app/email/provider.py`) → SendGrid.

Cada etapa falha em silêncio para o usuário: `/auth/recuperar-senha` sempre responde 200 com a
mensagem genérica (US 1.3 Cen.5); `enqueue_email_seguro` só loga em falha; `/internal/tasks/email`
sempre faz ACK (200) para não redespachar (`maxAttempts=1`). A única evidência do que acontece
está nos logs do Cloud Run.

**Evidência de produção (2026-07-17, `gcloud logging read`, serviço `api`):**

```
POST /auth/recuperar-senha HTTP/1.1  200 OK
POST /internal/tasks/email  HTTP/1.1  401 Unauthorized
```

A task É entregue ao endpoint interno, mas ele responde **401** — e 401 (não 403) significa que a
falha é na verificação do JWT (`oidc.py:68`, ramo `JWTError`), antes da checagem de identidade da
service account (que daria 403 em `oidc.py:79`). As únicas entradas de `verify_google_oidc` que
podem falhar são assinatura (chave do Google — ok), issuer (Google — ok) e **audience**.

**Descasamento de audience (causa raiz):**

| | valor |
|---|---|
| `aud` assinado pelo Cloud Tasks (audience omitido → URL do alvo) | `https://api-2j5ojmtaiq-rj.a.run.app/internal/tasks/email` |
| esperado por `require_tasks_invoker` (`settings.oidc_audience`) | `https://api-2j5ojmtaiq-rj.a.run.app` |

`config_from_settings` monta `target_url = f"{settings.oidc_audience}/internal/tasks/email"` e o
`oidc_token` da task não define `audience` — o Cloud Tasks então assina com a URL do alvo (com o
path). `OIDC_AUDIENCE` no Cloud Run (`infra/cloudrun.tf`, `local.oidc_audience`) é a URL base,
fixa, sem path. Logo `aud` nunca bate → 401 → mensagem descartada (`maxAttempts=1`) → `send_email`
nunca roda → SendGrid nunca é contatado (por isso o Activity Feed está vazio).

Os testes não pegaram porque `tests/conftest.py` sobrepõe `verify_google_oidc` por um fake — o
descasamento só existe no caminho real Cloud Tasks → Google → endpoint.

Atrás desse 401 há dois defeitos de configuração que só se manifestam depois dele corrigido:
- `EMAIL_FROM = no-reply@setes.docs` (default de `var.email_provider_from`) não é remetente
  verificado no SendGrid → HTTP 403 na entrega (recusa que nem aparece no Activity Feed).
- `FRONTEND_BASE_URL` não é setado no serviço `api` → default `http://localhost:3000`
  (`app/config.py`) → links de e-mail quebrados.

## Goals / Non-Goals

**Goals:**
- Fazer o endpoint interno aceitar o token OIDC entregue pelo Cloud Tasks, corrigindo o `aud`
  assinado — sem afrouxar a verificação.
- Fazer o e-mail, uma vez processado, ser aceito pelo SendGrid (remetente verificado) e conter
  links que funcionam em produção.
- Travar a regressão do `aud` em teste unitário (o fake de OIDC não cobre; a asserção é sobre o
  que o enqueue assina).

**Non-Goals:**
- Alterar o contrato de falha do e-mail (`maxAttempts=1`, ACK-sempre) ou o conteúdo/regras de
  negócio dos e-mails — inalterados.
- Adicionar retry/dead-letter à fila — fora de escopo (decisão de produto separada).
- Tornar `verify_google_oidc` testável de ponta a ponta contra o Google real — o fake permanece;
  a cobertura nova é sobre o lado emissor (audience assinado).

## Decisions

**D1 — Assinar o token com `audience` explícito = URL base, não afrouxar a validação.**
Adicionar `oidc_audience` a `EnqueueConfig` (preenchido de `settings.oidc_audience`) e passar
`"audience": config.oidc_audience` no `oidc_token` da task. Assim o `aud` assinado passa a ser
exatamente a string que `require_tasks_invoker` valida.

Alternativa considerada e descartada — mudar `require_tasks_invoker` para validar contra a URL
completa do alvo (`{oidc_audience}/internal/tasks/email`): descartada porque `OIDC_AUDIENCE` é um
contrato já publicado no Cloud Run como string base fixa (comentado em `infra/cloudrun.tf` como
"String fixa, não a URL do serviço"), reusável por outros endpoints `/internal/*` futuros;
prender a validação ao path de um endpoint específico é pior. Corrigir no emissor é o menor e mais
correto delta.

**D2 — `EMAIL_FROM` como Sender Identity verificada, configurada via `terraform.tfvars`.**
`var.email_provider_from` passa a ter default `""` e descrição exigindo remetente verificado; o
valor real (dependente do que a instituição verifica no SendGrid) vive em `terraform.tfvars`
(gitignored), não hardcoded no HCL versionado. Default vazio é preferível a um placeholder
plausível-mas-inválido (`no-reply@setes.docs`), que foi justamente a armadilha original.

**D3 — Injetar `FRONTEND_BASE_URL` do `local.web_url` já existente.**
`infra/cloudrun.tf` já tem `local.web_url` (usado no CORS). Reusá-lo como `FRONTEND_BASE_URL` do
serviço `api` mantém uma única fonte da URL do front e evita divergência.

## Migration Plan

Ordem obrigatória (o e-mail só funciona fim a fim com os três + os passos manuais do SendGrid):

1. **Código + teste** (`queue.py`, `test_email_queue.py`) — mergeados em `main`.
2. **SendGrid (manual, fora do VCS)** — verificar uma Sender Identity **ou** autenticar um
   domínio; anotar o remetente resultante. Confirmar que o secret `sendgrid-api-key` no Secret
   Manager contém a API key real (não `REPLACE_ME`).
3. **`terraform.tfvars`** — `email_provider_from = "<remetente verificado no passo 2>"`.
4. **`terraform plan`** — confirmar diff restrito ao template do serviço `api` (novo env
   `FRONTEND_BASE_URL`, mudança de `EMAIL_FROM`). Qualquer outro recurso no diff pausa o apply.
5. **`terraform apply`** — nova revisão do serviço `api`.
6. **Redeploy da imagem `api`** com o código do passo 1 (fluxo normal de `deploy.yml` ao mergear
   em `main`; a migration é no-op aqui, sem mudança de schema).
7. **Validação em produção** — solicitar recuperação de senha para um e-mail cadastrado real e
   confirmar nos logs `email.enviado event_id=… to=…` (não mais 401 em `/internal/tasks/email`),
   e o e-mail chegando com link `https://web-…run.app/redefinir-senha/{token}` funcional.

**Rollback**: reverter os dois arquivos Terraform e reaplicar restaura a revisão anterior; o
serviço `api` continua servindo (Cloud Run mantém a revisão saudável se a nova falhar no probe). A
mudança de código é isolada ao emissor de e-mail — sem efeito colateral em outros fluxos.

## Risks / Trade-offs

- [Risco] `terraform apply` com `email_provider_from` ainda vazio (tfvars não atualizado) subiria
  a `api` com remetente vazio → SendGrid recusa. Mitigação: passo 3 antes do 4/5 na ordem acima;
  a task de apply exige confirmar o valor.
- [Risco] O remetente verificado no SendGrid pode divergir do domínio institucional final (ainda
  não definido). Aceito: o valor é trocável em `terraform.tfvars` + `apply` sem novo deploy de
  código.
- [Trade-off] O fake de `verify_google_oidc` continua mascarando o caminho OIDC real; a nova
  asserção cobre só o `aud` assinado pelo emissor. Aceito — validar OIDC real exigiria e2e contra
  o Google, desproporcional ao fix; o passo 7 (validação em produção) fecha a lacuna
  manualmente.

## Open Questions

- Qual remetente será verificado no SendGrid (Single Sender vs. domínio autenticado) e qual
  domínio institucional final? — decisão da instituição; não bloqueia o code fix, só os passos
  2–3.
