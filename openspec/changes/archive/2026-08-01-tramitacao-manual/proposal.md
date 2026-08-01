## Why

O sistema roteia processos **automaticamente**: cada tipo de processo tem um
Roteiro (sequência ordenada de unidades), e o despacho apenas avança
`ordem_atual` para a próxima etapa. O servidor nunca escolhe o destino — o
roteiro escolhe por ele. A conclusão é um **efeito colateral** do despacho: ao
despachar na última etapa, o sistema pergunta "deseja concluir?".

Na avaliação da primeira entrega o cliente rejeitou esse modelo
(`docs/Ajustes SETES DOCS.pdf`): *"a tramitação automática entre unidades
conforme o tipo de processo deixará de existir"*. O servidor passa a escolher
explicitamente **unidade, setor e servidor** de destino, com uma **mensagem**, e
o processo tramita até que alguém conclua ou arquive.

O cliente também identificou um caso que o modelo atual não cobre: **um servidor
atribuído indevidamente**. Hoje não existe forma de corrigir isso — devolver
seria semanticamente errado (a unidade estava certa, a pessoa é que não). Daí o
terceiro tipo de ação: **Reatribuir**.

Este é o **segundo** dos seis changes dos ajustes pós-avaliação, e o de maior
risco: remove o roteiro, muda a espinha do domínio de *unidade* para
*unidade → setor → servidor*, e reverbera em toda a suíte de testes.

## What Changes

- **Roteiro removido por completo**: tabelas `roteiro` e `roteiro_etapa`
  eliminadas, colunas `processo.roteiro_id` e `processo.ordem_atual` removidas,
  `services/roteiros.py` e `services/roteiro_snapshot.py` excluídos, e a seção de
  configuração de roteiro sai de `/admin/tipos-processo`. **Tipo de processo
  permanece** — é usado em filtro de Kanban, dashboard e no prazo de anonimização
  LGPD.
- **Processo passa a registrar responsável atual**: novas colunas
  `processo.setor_atual_id` e `processo.servidor_atual_id`. Na criação, o
  processo **nasce atribuído ao criador** (`servidor_atual_id = criado_por_id`),
  o que o faz aparecer no Kanban do autor antes de qualquer tramitação.
- **Três tipos de ação de tramitação**, substituindo o despacho roteirizado:
  - **Envio** — destino livre (unidade, setor e servidor), com mensagem.
    O servidor de destino SHALL ser diferente do servidor atual.
  - **Devolução** — retorna ao **remetente anterior**, resolvido automaticamente
    do histórico; exige motivo e justificativa. É a ação para quando a **unidade**
    estava errada.
  - **Reatribuir** — corrige atribuição indevida: permanece na **mesma unidade**,
    podendo trocar de **setor** e obrigatoriamente de **servidor**; exige
    justificativa. **Não altera o status** e **não reseta o prazo**.
- **Conclusão vira ação explícita própria**, com botão dedicado — deixa de ser
  consequência de despachar na última etapa do roteiro.
- **Histórico ganha as dimensões novas**: `tramitacao` recebe
  `setor_origem_id`/`setor_destino_id`, `servidor_origem_id`/`servidor_destino_id`
  e `mensagem`. Continua **INSERT-only** — nenhuma rota de update ou delete.
- **Notificações passam a ser por pessoa**, não mais fan-out para todos os
  servidores da unidade de destino. Dois tipos novos: aviso ao servidor que
  recebeu o processo por reatribuição, e aviso ao remetente original de que seu
  destino foi corrigido.
- **Tela/modal de Tramitação** no detalhe do processo, com selects em cascata
  unidade → setor → servidor conforme o tipo de ação escolhido.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a tramitação já é coberta por
`workflow-tramitacao`; o que muda são seus requisitos. -->

### Modified Capabilities

- `workflow-tramitacao`: despacho roteirizado e devolução para "etapa anterior"
  são **removidos** e substituídos por Envio, Devolução e Reatribuir com destino
  explícito; conclusão vira ação própria; o histórico imutável ganha setor,
  servidor e mensagem. A máquina de estados permanece **inalterada**.
- `processos`: o snapshot de roteiro na criação é **removido**; o processo passa
  a nascer atribuído ao criador, com setor e servidor atuais.
- `tipos-processo-e-roteiros`: os requisitos de definição, versionamento e
  validação de **roteiro** são **removidos**; permanecem os de gestão de tipo de
  processo e prazo de anonimização LGPD. A capability é renomeada para
  `tipos-processo` na consolidação.
- `notificacoes-internas`: destinatário passa a ser o **servidor de destino**, e
  não todos os servidores da unidade; dois tipos novos de notificação para o
  fluxo de reatribuição.

## Impact

- **Dependências**: requer `setores-e-cadastro-usuario` (este change consome
  `setor` no destino da tramitação) e os arquivados `processos-e-workflow`,
  `notificacoes-e-alertas` e `visibilidade-processos-origem`. É **pré-requisito**
  de `kanban-por-servidor`.
- **Tabelas PostgreSQL**: **removidas** `roteiro` e `roteiro_etapa`;
  **alterada** `processo` (+`setor_atual_id` FK→`setor`, +`servidor_atual_id`
  FK→`usuario`, −`roteiro_id`, −`ordem_atual`); **alterada** `tramitacao`
  (+`setor_origem_id`, +`setor_destino_id` FK→`setor`, +`servidor_origem_id`,
  +`servidor_destino_id` FK→`usuario`, +`mensagem` text); **alterado** o enum
  `tipo_evento_tramitacao` (+`reatribuicao`, `despacho` renomeado para `envio`)
  e o enum `tipo_notificacao` (+2 valores).
- **Migrations**: `0022_processo_setor_servidor_atual`,
  `0023_tramitacao_setor_servidor_mensagem`, `0024_remover_roteiro`.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket
  novo no Cloud Storage.
- **Backend** (`apps/api`): `db/models.py`, `services/processo.py` (reescrito),
  `services/notificacao.py` (destinatário por pessoa),
  `services/processo_consulta.py`, `routers/processos.py`,
  `routers/tipos_processo.py`, `schemas/processo.py`,
  `schemas/tipos_processo.py`, `db/dev_reset.py`. **Excluídos**:
  `services/roteiros.py`, `services/roteiro_snapshot.py`.
  `services/processo_estado.py` fica **intocado** (ver design D4).
- **Testes**: `tests/helpers_processo.py` é o ponto de maior reverberação — quase
  toda a suíte cria processos por ele e ele exige roteiro. Atualizá-lo afeta
  ~20 arquivos de teste de uma vez. `tests/test_roteiros.py` é removido.
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados
  (`pnpm gen:types`; CI `gen:types:check`).
- **Frontend** (`apps/web`): `app/processos/[id]/page.tsx` (modal de tramitação,
  botão Concluir), `app/processos/novo/page.tsx` (sem roteiro),
  `app/admin/tipos-processo/page.tsx` (remoção da configuração de roteiro),
  `lib/api.ts`, `lib/processo-ui.ts`.
- **E2E**: `05-processos-despacho.spec.ts` reescrito;
  `04-unidades-tipos-processo`, `13-admin-readonly-processos` e
  `14-visibilidade-processos-origem` ajustados. Por alterar despacho, o change
  **exige** E2E Playwright (config OpenSpec vinculante).
- **LGPD**: nenhuma coleta nova de dado pessoal de interessado. O histórico passa
  a registrar **qual servidor** deteve o processo em cada etapa — dado pessoal de
  servidor, com finalidade de rastreabilidade administrativa e retenção
  acompanhando o histórico imutável do processo. Não é exposto na consulta
  pública. Por tocar histórico de tramitação e dados pessoais, o change **exige**
  testes automatizados pytest, incluindo cenários de acesso negado.
- **PRD**: `docs/PRD.md` Épico 2 (US 2.1, 2.2, 2.2b, 2.4) reescrito — o modelo
  roteirizado descrito ali deixa de valer.
