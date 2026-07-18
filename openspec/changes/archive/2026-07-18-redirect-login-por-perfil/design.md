## Context

Após o login (`apps/web/app/login/page.tsx:33`) e na raiz autenticada
(`apps/web/app/page.tsx:16`), o frontend hoje envia **todo** usuário para `/perfil`,
independentemente do perfil. Isso é comportamento puramente de navegação no cliente — o
backend já emite a sessão com o perfil e a flag `pode_auditar` no payload
(`Schemas["UsuarioResumo"]`), e o `auth-provider` já expõe `usuario` a ambas as telas.

Constraint central: os destinos precisam coincidir com o que cada perfil tem permissão de
ver, para nunca cair em "acesso negado":
- `/dashboard` — `ProtectedShell perfisPermitidos={["gestor"]}` + backend `require_perfil(GESTOR)`.
- `/admin/unidades` — restrito a Administrador.
- `/auditoria/relatorios` — exige `pode_auditar` (ortogonal ao perfil).
- `/processos` — aberto a qualquer sessão autenticada.

Change de frontend apenas; sem migrations, sem mudança de contrato OpenAPI.

## Goals / Non-Goals

**Goals:**
- Uma fonte única de verdade para o destino pós-autenticação: `rotaInicial(usuario)`.
- Aplicá-la nos dois pontos de entrada (login e raiz) sem duplicar lógica.
- Cascata determinística: auditoria sobrepõe perfil; senão servidor→processos,
  gestor→dashboard, admin→unidades.

**Non-Goals:**
- Não altera autorização de backend nem o menu de navegação (o link "Dashboard" continua só
  para gestor, etc.).
- Não remove a rota `/perfil` — apenas deixa de ser landing automática.
- Não introduz "última página visitada" nem deep-link pós-login (`?next=`); fica para um
  change futuro se necessário.

## Decisions

**1. Helper puro isolado em `apps/web/lib/rota-inicial.ts`.**
Função sem efeitos colaterais `rotaInicial(usuario: UsuarioResumo): string`, testável em
unidade (Vitest) sem montar componente. Alternativa considerada: inline em cada página —
rejeitada porque as duas telas divergiriam com o tempo (o bug que estamos corrigindo).

**2. Chaveia sobre o tipo já existente, não sobre strings soltas.**
Usa `Schemas["UsuarioResumo"]["perfil"]` como discriminante e trata `pode_auditar` como
guarda de precedência **antes** do switch de perfil. Assim, se o enum de perfil ganhar um
valor novo, o `switch` exaustivo do TypeScript acusa o caso faltante em compile-time.

**3. Ordem da cascata: auditoria primeiro.**
Decisão de produto já fechada — a permissão de auditoria é a razão de ser desse usuário, então
sobrepõe o destino que o perfil teria isoladamente. Um Gestor-auditor cai em
`/auditoria/relatorios`, não em `/dashboard`.

**4. Fallback defensivo.** Caso teórico de perfil não mapeado e sem auditoria: retorna
`/processos` (tela acessível a qualquer sessão) em vez de lançar, evitando tela branca.

Fluxo (login e raiz convergem no mesmo helper):

```
                 ┌─────────────────────────┐
  login OK  ─────▶                          │
                 │   rotaInicial(usuario)   │
  raiz "/"  ─────▶   (já autenticado)       │
  (autenticado)  └────────────┬────────────┘
                              │
               pode_auditar? ──sim──▶ /auditoria/relatorios
                    │ não
                    ▼
        perfil = servidor  ──▶ /processos
        perfil = gestor    ──▶ /dashboard
        perfil = administrador ─▶ /admin/unidades
        (fallback)         ──▶ /processos
```

## Risks / Trade-offs

- **[Menu ainda mostra "Meu Perfil" como primeiro link]** → Sem mitigação necessária:
  `/perfil` continua válido e acessível; só perde o status de landing. Nenhuma regressão de
  acesso.
- **[Redirect na raiz roda em `useEffect` após hidratação]** → Comportamento idêntico ao
  atual (a raiz já fazia `router.replace` em effect); só muda o alvo. Sem flash adicional
  além do que já existe.
- **[Novo perfil futuro sem caso no switch]** → Mitigado pelo switch exaustivo tipado
  (erro de compilação) + fallback em runtime para `/processos`.

## Migration Plan

Deploy padrão do frontend (Cloud Run, traffic splitting). Sem migration de banco, sem
coordenação com backend. Rollback = reverter o commit; nenhuma mudança de estado
persistente para desfazer.

## Open Questions

Nenhuma — as decisões de produto (destino do Admin = `/admin/unidades`; auditoria sobrepõe)
já foram confirmadas.
