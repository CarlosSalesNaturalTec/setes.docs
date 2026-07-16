## Why

O change `gestao-documental` (Épico 3, fatia A) entregou o soft-delete de anexos
— `Documento.removido_em` / `removido_por_id` / `purgar_em`, com 30 dias de
retenção e purga física pelo job diário — mas **deixou a restauração
explicitamente fora de escopo**, como change irmão futuro. Esta é a dívida:
enquanto o documento está em retenção (`removido_em IS NOT NULL AND purgar_em >
agora`), o dado ainda existe no bucket e no banco, mas **não há como o
Administrador trazê-lo de volta**. A US 8.7 fecha essa ponta.

A restauração só faz sentido depois que o soft-delete existe — daí ser um change
**irmão** de `gestao-documental`, e não parte dele, no mesmo padrão de
`arquivamento-automatico → sigilo-de-processo`. Nenhuma infra nova: a tabela
`documento`, o adaptador de storage e o evento imutável de histórico já existem;
este change adiciona a **operação inversa** do soft-delete e a **área
administrativa "Documentos Removidos"**.

## What Changes

- **US 8.7 Cen.1 — Restaurar documento dentro da retenção**: o Administrador
  acessa "Documentos Removidos" (área de administração), localiza um documento em
  retenção (soft-deleted há < 30 dias) e aciona "Restaurar". O documento volta a
  aparecer na lista de anexos do processo de origem (`removido_em`,
  `removido_por_id`, `purgar_em` voltam a `NULL`), a restauração é registrada como
  **evento imutável** no histórico do processo (novo tipo `restaurar_documento`,
  com Administrador e data/hora), e o documento sai da área de retenção.
- **US 8.7 Cen.2 — Documento já purgado (> 30 dias)**: documentos cujo `purgar_em`
  já expirou (purgados fisicamente pelo job diário) **não aparecem** na listagem;
  uma tentativa de restaurá-los retorna "não encontrado". A tela exibe no rodapé
  "Documentos removidos há mais de 30 dias são excluídos permanentemente e não
  podem ser restaurados".
- **US 8.7 Cen.3 — Área de retenção vazia**: sem documentos em retenção, a área
  exibe "Nenhum documento em período de retenção".
- **Área administrativa cross-unidade**: a listagem é **do Administrador** (acesso
  irrestrito, PRD perfil Administrador), não filtrada por unidade — o Admin vê
  documentos removidos de qualquer processo de qualquer unidade. Reusa
  `require_perfil(ADMINISTRADOR)`.

**Fora de escopo deste change:**
- **Alteração da regra de purga** (US 3.1 Cen.3) — a retenção de 30 dias e o passo
  `purgar_documentos_vencidos` do job diário permanecem exatamente como estão.
- **Restauração após a purga física** — irreversível por design (LGPD); depois de
  purgado, o documento não é recuperável.
- **Assinatura (Épico 4)**, notificações, dashboard, auditoria, anonimização LGPD.

## Capabilities

### New Capabilities
_(nenhuma — a restauração estende a capability de gestão documental existente)_

### Modified Capabilities
- `gestao-documental`: a capability dona do ciclo de vida do documento ganha a
  **operação de restauração** (inversa do soft-delete) e a **área administrativa
  "Documentos Removidos"** — listagem dos documentos em retenção e a ação de
  restaurar, restritas ao Administrador. A retenção de 30 dias e a purga física
  não mudam; a restauração opera na janela entre o soft-delete e a purga.
- `workflow-tramitacao`: o histórico imutável passa a admitir **mais um tipo de
  evento** — `restaurar_documento` — registrando a restauração de um anexo
  (Administrador responsável, data/hora), sem alterar a máquina de estados nem o
  status do processo.

## Impact

- **Dependência de change anterior:** requer `gestao-documental` **arquivado antes
  deste** (irmão em fluxo — hoje com PR aberto). Consome `documento`
  (`removido_em`/`removido_por_id`/`purgar_em`, já existentes), `services/documento.py`
  (`remover`/`purgar_documentos_vencidos` — a restauração é a inversa),
  `tramitacao` (novo tipo de evento) e `require_perfil(ADMINISTRADOR)`. Encadeia na
  migration `0006`.
- **Tabelas PostgreSQL** (migration `0007_restauracao_documento`, encadeada em
  `0006_gestao_documental`): **nenhuma tabela nova, nenhuma coluna nova**. Apenas
  `ALTER TYPE tipo_evento_tramitacao ADD VALUE 'restaurar_documento'` (em
  transação própria — limitação do Postgres, como em `0006`). O `downgrade` não
  remove o valor do enum (documentar; inócuo).
- **Máquina de estados:** **nenhuma alteração** — restaurar documento é ortogonal
  ao status; `processo_estado.py` não muda. O status é apenas **lido** para compor
  o `status_resultante` do evento.
- **Cloud Storage:** nenhum bucket novo, **nenhuma operação de storage** — o objeto
  nunca saiu do bucket durante a retenção (a purga física é que o remove, e
  documento purgado não é restaurável). Restaurar é puramente uma mudança de estado
  no banco.
- **Secret Manager / Rate limiting:** N/A — endpoints autenticados Admin-only.
- **LGPD:** a restauração **retorna à visibilidade** conteúdo que pode conter dado
  pessoal, mas apenas: (a) **dentro da janela de retenção** de 30 dias (após a
  purga, irreversível, nada volta); (b) **por Administrador** (acesso irrestrito,
  ação legítima de correção de exclusão indevida — a própria US 8.7); (c) com
  **registro imutável** no histórico (quem restaurou, quando). Nenhum dado pessoal
  novo é coletado; a irreversibilidade da anonimização/purga permanece intacta.
- **Código:** migration `0007`; valor `RESTAURAR_DOCUMENTO` no enum
  `TipoEventoTramitacao`; em `services/documento.py`,
  `listar_removidos_em_retencao(db, agora)` (cross-processo:
  `removido_em IS NOT NULL AND purgar_em > agora`) e `restaurar(db, documento,
  admin)` (limpa `removido_em`/`removido_por_id`/`purgar_em`, **re-resolve
  `nome_exibicao`** se houver colisão com anexo visível — ver design, insere evento
  `restaurar_documento`); novo router `routers/documentos_removidos.py`
  (`GET /admin/documentos-removidos`, `POST /admin/documentos-removidos/{id}/restaurar`)
  montado em `main.py`, Admin-only; schemas de resposta com número/assunto do
  processo para a listagem. Frontend: rota `app/admin/documentos-removidos` com a
  lista, a ação "Restaurar" e os estados vazio/rodapé. Regenerar
  `packages/api-types` (`pnpm gen:types`). Testes: unit/integração da restauração
  + **evento imutável**, do filtro de retenção (não lista purgados), do 404 em
  documento purgado e da re-resolução de nome (obrigatórios — tocam histórico de
  tramitação e dado pessoal); componente (Vitest/RTL) da área administrativa.
  **Sem E2E Playwright obrigatório** — a regra literal do `config.yaml` cobre
  login/despacho/assinatura/consulta pública; restauração é ação administrativa
  rara e coberta por testes de integração (o E2E do fluxo de anexo já vive em
  `gestao-documental`).
