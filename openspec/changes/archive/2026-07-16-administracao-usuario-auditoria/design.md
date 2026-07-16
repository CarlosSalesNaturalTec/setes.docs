## Context

Fecha as duas últimas histórias de administração de usuário do Épico 8. A base já
existe: `usuario` (com `perfil` e `status: ATIVO | INATIVO | PENDENTE_PRIMEIRO_ACESSO`),
`log_seguranca` (trilha imutável, INSERT-only, enum `TipoEventoLog`), autorização por
perfil (`require_perfil(PerfilUsuario.ADMINISTRADOR)`) e o login já rejeita usuário
`INATIVO` (`routers/auth.py:71`). Os processos guardam a unidade atual
(`processo.unidade_atual_id`) e o responsável de cada movimentação em `tramitacao`
(`responsavel_id`, INSERT-only). Não há campo de "responsável atual" no processo — a
responsabilidade individual é derivada do histórico de tramitação.

O perfil **Auditor** é citado em specs arquivados (ex.: `restauracao-documento`, cenário
de acesso negado "Servidor, Gestor ou Auditor") mas **nunca foi materializado** em código.
Este change o materializa como uma permissão concedível, não como um quarto perfil.

## Goals / Non-Goals

**Goals:**
- Conceder/revogar permissão de auditoria (US 8.3) como flag `pode_auditar` ortogonal ao
  perfil, Admin-only, com registro imutável de cada concessão/revogação.
- Desativar usuário (US 8.4) com guarda de processos em andamento sob sua responsabilidade,
  com registro imutável.
- Deixar o gancho `pode_auditar` pronto para o Épico 9 consumir.

**Non-Goals:**
- **Consumo** da permissão de auditoria: leitura de processo sigiloso (US 9.1), relatórios
  consolidados (US 9.2). Nenhuma rota de auditoria, nenhuma alteração em regras de
  visibilidade de processo. `pode_auditar` é escrito e lido pela UI de admin, mas **nenhum
  fluxo de leitura de processo o consulta ainda**.
- Reativação de usuário e reatribuição de processos (fora das duas US; reatribuição já é
  coberta pela transferência/tramitação existentes).
- US 8.5-completo (parâmetros operacionais) — change dedicada posterior.

## Decisions

### D1 — `pode_auditar` como flag booleana ortogonal ao perfil (Opção A)
`usuario.pode_auditar BOOLEAN NOT NULL DEFAULT false`. Conceder = `true`; revogar =
`false`. O `perfil` (Servidor/Gestor/Administrador) **não é tocado**.

*Por que, e não as alternativas:* modelar Auditor como 4º valor de `PerfilUsuario`
exigiria, ao revogar, restaurar o perfil anterior (estado extra para "lembrar" de onde
veio) e colidiria com a invariante "Servidor pertence a exatamente uma unidade" (um
auditor-servidor perde a unidade?). A flag ortogonal casa exatamente com a semântica do
PRD US 8.3 Cen.2 ("a permissão é removida" → volta ao estado anterior sem memória) e com
a US 9.1 Cen.2 ("Auditor sem permissão explícita" → flag `false` cai no acesso negado do
Épico 9). A descrição da persona no PRD/CLAUDE.md ("permissão concedida pelo
Administrador") reforça a leitura de grant aditivo, não de troca de perfil.

### D2 — "Processos sob responsabilidade" para a guarda da US 8.4
A US 8.4 Cen.2 bloqueia a desativação quando o usuário "possui processos em andamento sob
sua responsabilidade". O modelo não tem "dono" de processo; a definição operacional
adotada é:

> Um processo conta contra a desativação do usuário U quando **(a)** seu `status` é
> `ABERTO` ou `EM_TRAMITACAO` (em andamento) **e (b)** U é o **responsável da última
> tramitação** do processo (o processo está "parado com ele"), **ou** U **criou** o
> processo e ele ainda não teve nenhuma tramitação.

Reusa exatamente o seam de atuação já existente (`processo_consulta.processos_atuados`
filtra por `tramitacao.responsavel_id` e `processo.criado_por_id`), restringindo a
processos em andamento e ao **último** evento por processo. Um novo serviço
`contar_processos_sob_responsabilidade(db, usuario) -> int` encapsula a regra.

*Por que, e não as alternativas:* contar todos os processos **da unidade** do servidor
seria amplo demais (bloquearia desativar qualquer servidor de uma unidade ativa, mesmo os
que nunca tocaram nada) e não é "sob responsabilidade dele". Contar todo processo que ele
já tocou no passado seria amplo na direção oposta (histórico é permanente — nunca poderia
desativar). "Último responsável de processo em andamento" é a leitura que corresponde a
"o processo está com ele agora" e é o que a mensagem "reatribua os processos antes de
desativar" pressupõe: reatribuir = despachar/tramitar para outro, o que remove U como
último responsável.

### D3 — Registro imutável (INSERT em `log_seguranca`)
Três novos valores de `TipoEventoLog` (enum nativo Postgres, via `ALTER TYPE ... ADD
VALUE`): `permissao_auditoria_concedida`, `permissao_auditoria_revogada`,
`usuario_desativado`. Cada rota grava uma linha com `usuario_id` = alvo e
`contexto = {"administrador_id": <id do admin>}`, no mesmo padrão de `RESET_SENHA_ADMIN`.
Segue a invariante do projeto: eventos são INSERT, nunca UPDATE.

### D4 — Rotas Admin-only e contrato
Em `routers/usuarios.py`, todas sob `require_perfil(PerfilUsuario.ADMINISTRADOR)`:
- `POST   /usuarios/{usuario_id}/permissao-auditoria` → concede (idempotente: conceder a
  quem já tem retorna 200 sem novo log duplicado — decisão: só loga em transição real).
- `DELETE /usuarios/{usuario_id}/permissao-auditoria` → revoga (idempotente idem).
- `POST   /usuarios/{usuario_id}/desativar` → desativa, com a guarda de D2 (422 com a
  mensagem de processos pendentes) e idempotência (desativar quem já está inativo → 422
  "Usuário já está inativo", sem novo log).

Tentativa por não-Administrador é barrada por `require_perfil` e registrada como
`acesso_negado` (comportamento já embutido na dependência de autorização). `UsuarioResponse`
passa a expor `pode_auditar: bool`. Como o schema do FastAPI muda, `packages/api-types`
é regenerado (`pnpm gen:types`), senão o job `types-drift` do CI falha.

## Migration Plan

**Alembic (schema antes de endpoint):**
1. `ALTER TABLE usuario ADD COLUMN pode_auditar BOOLEAN NOT NULL DEFAULT false;` — sem
   backfill (default cobre linhas existentes; nenhum usuário nasce auditor).
2. `ALTER TYPE tipo_evento_log ADD VALUE IF NOT EXISTS 'permissao_auditoria_concedida';`
   idem para `'permissao_auditoria_revogada'` e `'usuario_desativado'`. `ADD VALUE` não
   roda dentro de transação implícita no Postgres — seguir o padrão já usado nas migrations
   que estenderam enums neste repo (checar `EXPANSAO_NUMERO_PROCESSO`/eventos anteriores).

*Rollback:* a coluna e os valores de enum são aditivos e não-destrutivos; um downgrade
pode dropar a coluna `pode_auditar` (valores de enum em Postgres não são removíveis sem
recriar o tipo — aceitável deixá-los órfãos num downgrade, sem impacto funcional).

## Risks / Trade-offs

- **[Definição de "responsabilidade" (D2) pode divergir da intenção do órgão]** → a regra
  fica isolada num único serviço testável (`contar_processos_sob_responsabilidade`); se a
  interpretação mudar, altera-se num só ponto sem tocar rotas nem UI. Documentada aqui e
  referenciada na spec.
- **[Gancho `pode_auditar` sem consumidor pode passar por "código morto"]** → é
  deliberado e declarado (Non-Goal); o Épico 9 é o consumidor imediato e depende deste
  change. A UI de admin já o exibe e alterna, então não é inerte.
- **[`ALTER TYPE ADD VALUE` fora de transação]** → seguir o padrão de migration de enum já
  existente no repo para não quebrar o `alembic upgrade head` do CI/deploy.

## Open Questions

- Nenhuma bloqueante. A definição de D2 está adotada; caso o cliente queira "todos os
  processos da unidade" em vez de "último responsável", é troca localizada no serviço.
