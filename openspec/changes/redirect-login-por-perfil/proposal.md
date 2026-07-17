## Why

Hoje, após o login bem-sucedido — e ao acessar a raiz `/` já autenticado — **todos os
perfis caem em `/perfil`** ("Meu Perfil"), independentemente do que aquela persona faz no
dia a dia. Isso contradiz o critério de aceite da própria US 1.3 Cen.1 do PRD ("sou
direcionado ao **painel correspondente ao meu perfil**") e impõe um clique extra a cada
sessão: o Servidor precisa navegar até os Processos, o Gestor até o Dashboard. Cada persona
deve aterrissar direto na tela que é a razão de ser do seu trabalho.

## What Changes

- Introduz uma função única `rotaInicial(usuario)` (frontend) que resolve o destino
  pós-autenticação a partir de `perfil` e da flag `pode_auditar`, aplicando esta cascata:
  - `pode_auditar === true` → `/auditoria/relatorios` (**sobrepõe o perfil** — auditoria é a
    razão de ser desse usuário)
  - senão `servidor` → `/processos`
  - senão `gestor` → `/dashboard`
  - senão `administrador` → `/admin/unidades` (o Admin não tem dashboard; sua raiz é a
    configuração)
- Aplica `rotaInicial` nos **dois** pontos de entrada, para que não divirjam:
  - `apps/web/app/login/page.tsx` (hoje fixo em `/perfil`)
  - `apps/web/app/page.tsx` (raiz — ramo do usuário já autenticado, hoje fixo em `/perfil`)
- `/perfil` **deixa de ser landing automática**; continua acessível pelo link "Meu Perfil"
  já existente no menu (`protected-shell`).

Sem breaking changes de contrato: nenhuma rota/endpoint é removido; todos os destinos já
existem e o usuário já tem permissão de acessá-los (coerência garantida com
`controle-acesso-por-unidade` e `permissao-auditoria`).

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova — é um refinamento de comportamento de uma existente. -->

### Modified Capabilities
- `autenticacao`: a requirement **Login com credenciais** passa a definir o destino
  pós-login de forma explícita e determinística por perfil (com o override de auditoria),
  em vez do genérico "painel correspondente". Cobre também o redirecionamento da raiz `/`
  para usuário já autenticado.

## Impact

- **Recorte de roadmap**: Épico 1 (autenticação + controle de acesso). Depende do change de
  autenticação/login já arquivado e da capability `permissao-auditoria` (flag
  `pode_auditar`).
- **Código afetado (apenas frontend `apps/web`)**:
  - `apps/web/app/login/page.tsx` — troca `router.push("/perfil")` por
    `router.push(rotaInicial(usuario))`.
  - `apps/web/app/page.tsx` — troca `router.replace("/perfil")` do ramo autenticado por
    `router.replace(rotaInicial(usuario))`.
  - Novo helper (ex.: `apps/web/lib/rota-inicial.ts`) + teste unitário (Vitest).
  - Teste **E2E Playwright** cobrindo um cenário por perfil (servidor→processos,
    gestor→dashboard, admin→unidades) + o override de auditoria.
- **Sem impacto de dados**: nenhuma tabela PostgreSQL nova ou alterada; nenhum novo segredo
  no Secret Manager; nenhum novo bucket no Cloud Storage; nenhum dado pessoal
  coletado/retido/anonimizado (tratamento LGPD não se aplica).
- **Sem impacto de backend**: nenhuma mudança de schema/rota do FastAPI, logo **sem
  regeneração** de `packages/api-types`.
