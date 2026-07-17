## 1. Helper de rota inicial

- [ ] 1.1 Criar `apps/web/lib/rota-inicial.ts` com `rotaInicial(usuario: Schemas["UsuarioResumo"]): string`, aplicando a cascata (auditoria sobrepõe; servidor→`/processos`, gestor→`/dashboard`, admin→`/admin/unidades`, fallback→`/processos`). Critério: função pura, sem imports de React/Next, switch de perfil exaustivo tipado.
- [ ] 1.2 Criar `apps/web/lib/rota-inicial.test.ts` (Vitest) cobrindo os 4 destinos por perfil, o override de auditoria sobre cada perfil e o fallback. Critério: `pnpm --filter @setes/web test -- rota-inicial` verde.

## 2. Aplicar nos pontos de entrada

- [ ] 2.1 Em `apps/web/app/login/page.tsx`, substituir `router.push("/perfil")` por `router.push(rotaInicial(usuario))`, obtendo `usuario` da sessão retornada pelo `login`. Critério: nenhum destino fixo `/perfil` remanescente no fluxo de sucesso.
- [ ] 2.2 Em `apps/web/app/page.tsx`, no ramo `if (usuario)`, substituir `router.replace("/perfil")` por `router.replace(rotaInicial(usuario))`, preservando intacto o ramo não-autenticado (`setupStatus` → `/login` ou `/setup`). Critério: usuário autenticado na raiz cai na rota do seu perfil.

## 3. Testes E2E (obrigatório — altera fluxo de login)

- [ ] 3.1 Teste Playwright: login como Servidor aterrissa em `/processos`. Critério: URL final `**/processos`.
- [ ] 3.2 Teste Playwright: login como Gestor aterrissa em `/dashboard`. Critério: URL final `**/dashboard`.
- [ ] 3.3 Teste Playwright: login como Administrador aterrissa em `/admin/unidades`. Critério: URL final `**/admin/unidades`.
- [ ] 3.4 Teste Playwright: login como usuário com `pode_auditar` aterrissa em `/auditoria/relatorios`, confirmando o override do perfil. Critério: URL final `**/auditoria/relatorios`.

## 4. Verificação final

- [ ] 4.1 Rodar `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web lint` e a suíte Vitest; ajustar testes existentes que assumiam `/perfil` como landing (ex.: `login/page.test.tsx`). Critério: typecheck, lint e unit verdes.
- [ ] 4.2 Rodar `cd apps/web && pnpm test:e2e` com os cenários novos. Critério: suíte E2E verde.
