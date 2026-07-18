## Context

Ajustes de acabamento pós-teste em produção, recortando capabilities já
entregues (gestão de usuários/unidades/tipos e Kanban). Não há épico novo,
tabela nova, segredo nem bucket. O trabalho se distribui entre correção de asset
(favicon), polimento de UI (tabelas + ícones), dois endpoints novos (editar
próprio nome; reativar unidade), um ajuste de validação de domínio (rejeitar
unidade inativa em roteiro) e gating de front por perfil (Admin read-only em
Processos). O contrato OpenAPI muda por causa dos dois endpoints novos, exigindo
`pnpm gen:types` + commit do snapshot em `packages/api-types`.

## Goals / Non-Goals

**Goals:**
- Corrigir o 500 do favicon com ativo de ícone servido pelo App Router.
- Dar ao usuário controle sobre o próprio nome (auto-serviço restrito a nome).
- Permitir reativar unidades inativas, sem revínculo automático de servidores.
- Fechar o bug de unidade inativa entrando em roteiro (front + back).
- Apresentar ao Administrador uma visão de Processos coerente (read-only).
- Refinar as tabelas de admin e trocar ações de texto por ícones acessíveis.

**Non-Goals:**
- Remover a coluna `Unidade.gestor_responsavel_id` do banco (fica dormente; sem
  migration neste change).
- Alterar o modelo de acesso do Gestor — continua 100% via `UnidadeGestor`.
- Permitir auto-edição de e-mail ou perfil.
- Dar ao Administrador (ou Gestor) qualquer poder de movimentar processos.
- Redesenho amplo de UI além das duas tabelas citadas.

## Decisions

### D1 — Favicon como ativo estático, não rota dinâmica
Adicionar `apps/web/app/icon.svg` (convenção de arquivo do App Router, servido
automaticamente) e declarar `metadata.icons` no `layout.tsx`. **Por quê SVG:**
não depende de `public/` (que não existe no projeto) e é copiado no build
`standalone`. Alternativa considerada: `favicon.ico` binário em `public/` —
descartada porque exigiria criar/gerenciar o diretório e um binário no repo.

### D2 — Editar próprio nome: `PATCH /usuarios/me/perfil`
Endpoint self-service usando `get_current_user` (sem ID manipulável na URL — o
alvo é sempre o dono do token, mantendo o padrão do `GET /usuarios/me/perfil`).
Corpo `{ nome: str }` com validação `min_length=1` (após strip) e
`max_length=200` (espelha `String(200)`). Só o campo `nome` é gravado.
**Alternativa considerada:** reaproveitar o PATCH de usuário por Administrador —
descartada porque aquele fluxo é Admin-only e opera por ID de terceiro; auto-
serviço precisa de rota própria sem exposição de ID.

### D3 — Reativar unidade: `POST /unidades/{id}/reativar` (simétrico a desativar)
Espelha `POST /unidades/{id}/desativar` (Admin-only, `require_perfil`). Apenas
seta `ativo = True`; **não** toca em `Usuario.unidade_id` (a desativação
desvinculou; a reativação não reverte). Idempotente para unidade já ativa.
**Alternativa considerada:** um único `PATCH` com `{ ativo: bool }` — descartada
para manter simetria com o `desativar` já existente e preservar a guarda de
processos pendentes exclusiva da desativação.

### D4 — Rejeitar unidade inativa no roteiro no `_validar_unidades`
A barreira efetiva é no backend: `_validar_unidades` passa a filtrar
`Unidade.ativo == True` na contagem, de modo que qualquer ID inativo cai no
`!= len(set(ids))` e dispara "Unidade inválida no roteiro" (mensagem já
existente). Vale para `criar_tipo_processo` e `atualizar_roteiro`, que já
compartilham essa função. No front, o `EditorRoteiro` filtra `unidades` por
`ativo` ao popular o `<select>` — conveniência, não a barreira.

### D5 — Admin read-only em Processos: gating por perfil no front
O backend já rejeita ações de processo para não-Servidor (`_require_servidor`),
então nada muda no back. No front, condicionar a renderização de "Novo
processo" (lista), "Despachar"/"Devolver"/toggle de sigilo (detalhe) a
`usuario.perfil === "servidor"`. Mantém o link "Processos" no menu para todos.
**Por quê no front:** evitar mostrar controle que sempre resultaria em 403 —
melhora UX sem duplicar regra de autorização (a fonte da verdade continua no
back).

### D6 — Remoção do "Gestor responsável" da UI de unidade
Remover o `<select>` de gestor do `CadastroUnidadeForm` e não introduzi-lo no
modo edição. Backend, schema e coluna permanecem intactos (campo dormente). O
`api.cadastrarUnidade` passa a não enviar `gestor_responsavel_id` (ou envia
`null`). Sem migration.

### D7 — Ícones nas ações: acessibilidade obrigatória
Cada ação vira botão/ícone com `aria-label` e `title` descritivos (ex.:
"Editar", "Desativar", "Reativar", "Transferir unidade"). Ações que expandem
inline (transferir unidade, unidades geridas) mantêm o comportamento; só o
gatilho vira ícone.

## Migrations Alembic

**Nenhuma.** Não há schema novo nem alterado. `Unidade.gestor_responsavel_id`
permanece na tabela sem migration de remoção (decisão D6 / Non-Goal).

## Sequência — editar próprio nome

```
Usuário        Front (perfil/page)      API (PATCH /usuarios/me/perfil)     DB
  │  edita nome        │                          │                         │
  ├───────────────────>│                          │                         │
  │                    │  api.atualizarMeuPerfil  │                         │
  │                    ├─────────────────────────>│                         │
  │                    │                          │ get_current_user (token)│
  │                    │                          │ valida nome 1..200      │
  │                    │                          │ UPDATE usuario.nome ─────>│
  │                    │  MeuPerfilResponse        │<────────────────────────┤
  │                    │<─────────────────────────┤                         │
  │  nome atualizado   │  atualiza estado + header │                         │
  │<───────────────────┤                          │                         │
```

## Risks / Trade-offs

- **[Coluna `gestor_responsavel_id` dormente confunde futuros devs]** → registrar
  no design (aqui) e no proposal que o campo é intencionalmente não usado; a
  remoção física fica para um change de limpeza futuro, se desejado.
- **[Gating de Admin só no front pode ser burlado via API]** → aceitável: o
  backend já barra (D5); o gating de front é apenas UX, não controle de acesso.
- **[Reativar sem revincular servidores pode surpreender o Admin]** → cenário
  explícito na spec e, na UI, deixar claro que a realocação de servidores é
  manual.
- **[Ícones sem rótulo prejudicam acessibilidade]** → `aria-label`/`title`
  obrigatórios (D7), cobertos por revisão de UI.
- **[Snapshot de tipos defasado após novos endpoints]** → rodar
  `pnpm gen:types` e o CI `gen:types:check` pega defasagem.

## Open Questions

- Nenhuma pendente. As três decisões de produto (Admin read-only; gestão só via
  Unidades geridas; edição livre de nome até 200 chars) já foram definidas.
