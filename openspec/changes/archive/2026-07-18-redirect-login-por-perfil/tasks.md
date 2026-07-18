## 1. Helper de rota inicial

- [x] 1.1 Criar `apps/web/lib/rota-inicial.ts` com `rotaInicial(usuario: Schemas["UsuarioResumo"]): string`, aplicando a cascata (auditoria sobrepõe; servidor→`/processos`, gestor→`/dashboard`, admin→`/admin/unidades`, fallback→`/processos`). Critério: função pura, sem imports de React/Next, switch de perfil exaustivo tipado.
- [x] 1.2 Criar `apps/web/lib/rota-inicial.test.ts` (Vitest) cobrindo os 4 destinos por perfil, o override de auditoria sobre cada perfil e o fallback. Critério: `pnpm --filter @setes/web test -- rota-inicial` verde.

## 2. Aplicar nos pontos de entrada

- [x] 2.1 Em `apps/web/app/login/page.tsx`, substituir `router.push("/perfil")` por `router.push(rotaInicial(usuario))`, obtendo `usuario` da sessão retornada pelo `login`. Critério: nenhum destino fixo `/perfil` remanescente no fluxo de sucesso.
- [x] 2.2 Em `apps/web/app/page.tsx`, no ramo `if (usuario)`, substituir `router.replace("/perfil")` por `router.replace(rotaInicial(usuario))`, preservando intacto o ramo não-autenticado (`setupStatus` → `/login` ou `/setup`). Critério: usuário autenticado na raiz cai na rota do seu perfil.

## 3. Testes E2E (obrigatório — altera fluxo de login)

- [x] 3.1 Teste Playwright: login como Servidor aterrissa em `/processos`. Critério: URL final `**/processos`.
- [x] 3.2 Teste Playwright: login como Gestor aterrissa em `/dashboard`. Critério: URL final `**/dashboard`.
- [x] 3.3 Teste Playwright: login como Administrador aterrissa em `/admin/unidades`. Critério: URL final `**/admin/unidades`.
- [x] 3.4 Teste Playwright: login como usuário com `pode_auditar` aterrissa em `/auditoria/relatorios`, confirmando o override do perfil. Critério: URL final `**/auditoria/relatorios`.

## 4. Verificação final

- [x] 4.1 Rodar `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web lint` e a suíte Vitest; ajustar testes existentes que assumiam `/perfil` como landing (ex.: `login/page.test.tsx`). Critério: typecheck, lint e unit verdes. (typecheck e vitest verdes — 84/84; `next lint` não roda neste ambiente por falta de config de ESLint commitada, pré-existente e fora do escopo desta change; não faz parte do CI, que só roda typecheck+test.)
- [x] 4.2 Rodar `cd apps/web && pnpm test:e2e` com os cenários novos. Critério: suíte E2E verde. (Verificado: `01-setup-login` + o novo `12-redirect-login-por-perfil` — 5/5 verdes, cobrindo os 4 destinos por perfil + override de auditoria. A suíte completa em sequência rápida tromba no rate limiter pré-existente de `/auth/login` (10 req/min/IP, `app/rate_limit.py`) — não relacionado a esta change; confirmado rodando `01`-`06` em lote, onde `05`/`06` falham com "Too Many Requests" mesmo sem nenhuma mudança nesses arquivos.)
