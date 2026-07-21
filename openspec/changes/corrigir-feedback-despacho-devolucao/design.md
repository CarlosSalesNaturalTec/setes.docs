## Context

O detalhe do processo (`apps/web/app/processos/[id]/page.tsx`, componente
`DetalheConteudo`) usa `carregar()` como função única de carregamento: ela busca
em paralelo `GET /processos/{id}` e `GET /processos/{id}/historico` e popula os
estados `processo`/`historico`. As ações `despachar()` e `devolver()` chamam
`carregar()` ao final, para refletir o novo estado.

O problema: despacho/devolução **movem** o processo para outra unidade
(`unidade_atual_id`). Ao chamar `carregar()` logo em seguida, o `GET /processos/{id}`
avalia a visibilidade contra a **unidade atual já atualizada** (agora fora do
escopo do Servidor de origem) e retorna **403** com
`"Acesso negado — você não tem permissão para visualizar este processo"`
(`_exigir_leitura_ao_processo`, `apps/api/app/routers/processos.py`). O `catch` de
`carregar()` engole esse 403 como erro de carregamento e o pinta na faixa de erro
— exibindo uma ação bem-sucedida como falha. O processo, corretamente, já saiu do
Kanban da unidade (filtro por `unidade_atual_id`).

O backend está conforme a spec (`workflow-tramitacao`, `controle-acesso-por-unidade`):
negar leitura de processo fora do escopo é o comportamento previsto (US 1.4 Cen.2).
A correção é exclusivamente de fluxo no cliente.

Fatos que a resposta da ação já fornece: `api.despacharProcesso` e
`api.devolverProcesso` retornam `ProcessoResponse`, que inclui `unidade_atual_id`
e `status` **já atualizados** — não é preciso reler o processo para conhecer o
novo estado.

## Goals / Non-Goals

**Goals:**
- Após despacho/devolução bem-sucedidos que **removem o processo do escopo** da
  unidade, comunicar sucesso (nomeando a unidade de destino) e navegar para o
  Kanban — sem a releitura que gera o 403 espúrio.
- Preservar o comportamento atual quando o processo **permanece** no escopo
  (conclusão na própria unidade, roteiro de unidade única): atualizar a tela e
  recarregar o histórico.
- Manter o fluxo de confirmação de conclusão (modal 409) e o tratamento de erros
  reais intactos.
- Cobrir despacho (US 2.2) e devolução (US 2.2b) com a mesma correção.

**Non-Goals:**
- Nenhuma mudança no backend, no contrato OpenAPI ou nos tipos gerados.
- Não conceder ao Servidor de origem leitura do processo despachado (isso seria
  mudança de regra de visibilidade, fora de escopo — ver Open Questions).
- Não alterar o Kanban, a notificação por e-mail nem o histórico imutável.

## Decisions

### Decisão 1 — Inferir "saiu do escopo" por mudança de `unidade_atual_id`

Comparar o `unidade_atual_id` **anterior** (o do `processo` em estado, antes da
ação) com o `unidade_atual_id` **retornado** pela `ProcessoResponse` da ação.

- **Mudou** → processo saiu do escopo → confirmação de sucesso + navegação ao
  Kanban, sem `carregar()`.
- **Igual** → processo permanece → `setProcesso(resposta)` + recarrega histórico.

**Por que essa heurística (e não outra):**
- *Alternativa A — comparar o escopo de unidades do usuário no front*: o front não
  tem, sozinho, a lista de unidades que o Servidor pode acessar; exigiria novo
  dado/endpoint. Rejeitada por acoplamento desnecessário.
- *Alternativa B — tratar por status (`concluido` fica, resto sai)*: falha no
  roteiro de unidade única e em qualquer caso onde a unidade não muda mas o status
  sim; menos preciso que comparar a unidade diretamente. Rejeitada.
- *Alternativa C — deixar o backend sinalizar "você ainda tem acesso"*: mudaria o
  contrato da API para um problema puramente de UI. Rejeitada (Non-Goal).

A comparação por `unidade_atual_id` é exata em relação ao que de fato determina a
visibilidade (a unidade atual do processo) e usa apenas dado já presente na
resposta.

### Decisão 2 — Não chamar `carregar()` no caminho "saiu do escopo"

A raiz do bug é a releitura. No caminho de saída de escopo, a ação simplesmente
não relê: usa a resposta para a mensagem de sucesso e navega para `/processos` via
`useRouter().push` (`next/navigation`, já usado no projeto). O Kanban é a
superfície natural pós-despacho e reflete corretamente a ausência do processo.

No caminho "permanece no escopo", mantém-se `setProcesso(resposta)` e um recarregar
apenas do histórico (`api.historicoProcesso(id)`), evitando a chamada de detalhe
redundante mas preservando a linha do tempo atualizada.

### Decisão 3 — Confirmação de sucesso

Exibir mensagem de sucesso nomeando a unidade de destino (ex.: "Processo
despachado para AJUR" / "Processo devolvido para COFIN"). O rótulo da unidade sai
do mapa `nomeUnidade` já montado no componente (a partir de `api.listarUnidades()`).
A forma exata (toast, faixa de sucesso persistida entre navegação, ou query param
na rota do Kanban) é detalhe de implementação; o requisito observável é: mensagem
de **sucesso**, com a unidade de destino, e ausência da mensagem de acesso negado.

### Fluxo (sequência)

```
Servidor        page.tsx (despachar/devolver)            API
   │  clica            │                                   │
   ├──────────────────▶│                                   │
   │                   │  unidadeAnterior = processo.unidade_atual_id
   │                   ├── POST /despachar (ou /devolver) ─▶│
   │                   │                                   │ move processo,
   │                   │                                   │ grava Tramitacao
   │                   │◀──── 200 ProcessoResponse ────────┤ (unidade_atual_id novo)
   │                   │                                   │
   │                   │ resposta.unidade_atual_id != unidadeAnterior ?
   │                   │        │                    │
   │                   │       SIM                  NÃO
   │                   │        │                    │
   │        ◀── sucesso + push('/processos')        setProcesso(resposta)
   │            (SEM re-fetch → sem 403)             + recarrega histórico
   │                   │                                   │
```

## Risks / Trade-offs

- **[Regressão no modal de conclusão]** O caminho de 409 (última etapa pede
  confirmação) e o `promptConclusao` não podem ser quebrados. → Mitigação: manter
  o `catch` que trata `ApiError.status === 409` **antes** da lógica de
  sucesso/navegação; testar o cenário de conclusão confirmada (permanece na tela,
  status "Concluído") e o de cancelamento (sem navegação).
- **[Falso positivo de "permanece"]** Se, por algum roteiro, a próxima etapa
  apontar para a **mesma** unidade, a heurística manteria a tela. → Aceitável: se
  a unidade não mudou, o Servidor de fato ainda tem acesso e não há 403; o pior
  caso é não navegar ao Kanban, sem erro ao usuário.
- **[Mensagem de sucesso perdida na navegação]** Se a confirmação for um toast
  local, ele some ao trocar de rota. → Mitigação: usar mecanismo que sobreviva à
  navegação (query param lido pelo Kanban, ou store de UI) OU exibir a confirmação
  antes de navegar com breve atraso. Decisão fina fica para a implementação/testes.
- **[Erro real mascarado como sucesso]** A lógica de sucesso só pode rodar quando
  a chamada da ação retorna 2xx. → Mitigação: manter a navegação/sucesso **dentro
  do `try`, após o `await` da ação**; qualquer rejeição cai no `catch` existente e
  é exibida como erro, sem navegação.

## Migration Plan

- Sem migration de banco, sem mudança de contrato, sem novo segredo/bucket.
- Deploy via pipeline padrão do front (Cloud Run, path-filtered para `apps/web`).
- Rollback: reverter o commit do front — não há estado persistido a desfazer.
- Validação pré-produção: fluxo E2E `05-processos-despacho.spec.ts` cobrindo
  despacho que sai do escopo, e verificação manual no ambiente com o processo
  2026/000007 (ou equivalente) confirmando ausência da mensagem de acesso negado.

## Open Questions

- **Forma da confirmação de sucesso** (toast vs. faixa no Kanban via query param):
  decidir na implementação, priorizando que a mensagem sobreviva à navegação.
- **Acompanhamento pós-despacho pelo Servidor de origem**: dar leitura do processo
  já despachado ao Servidor de origem é uma melhoria de produto separada (mudança
  de visibilidade, US 1.4/2.2) — não faz parte desta correção.
