## Why

O Épico 5 do PRD (Notificações e Alertas) é a próxima fatia desbloqueada do MVP: os
Épicos 1, 2, 3, 7 e 8 estão prontos e o Épico 4 (assinatura) está condicionado a
Discovery Técnico. Hoje o servidor não tem como saber que um processo chegou à sua
unidade, foi concluído ou está com prazo a vencer sem varrer o Kanban manualmente — o que
contraria a métrica de sucesso "zero processos perdidos". A infraestrutura de e-mail
assíncrono (fila Cloud Tasks `emails`, `maxAttempts=1`, endpoint interno OIDC do spec
`fila-notificacoes`) já está provisionada e é usada apenas para e-mails de autenticação;
falta ligá-la aos eventos de processo. Todos os gatilhos já existem no domínio
(`Tramitacao` com eventos `DESPACHO`/`CONCLUSAO`, `processo.prazo_em`), então este change
é integração sobre fundação pronta, não fundação nova.

## What Changes

- **Notificação interna (sino) de novo processo recebido** — ao concluir um `DESPACHO`
  para outra unidade, gerar notificação para todos os servidores da unidade destino
  (US 5.1). Contador no ícone de sino, painel com número/assunto/unidade de origem.
- **Notificação interna de processo concluído** — ao registrar `CONCLUSAO`, notificar
  todos os servidores da unidade em que o processo foi concluído (US 5.3).
- **Notificação interna de alerta de prazo** — rotina diária notifica os servidores da
  unidade atual de processos com `prazo_em` dentro da janela configurada (US 5.4).
- **E-mail de novo processo recebido** — enfileira e-mail "Novo processo recebido — [Nº]"
  aos servidores da unidade destino no despacho, reutilizando a fila existente (US 5.2
  Cen.1).
- **E-mail de alerta de prazo próximo** — a mesma rotina diária enfileira e-mails "Prazo
  próximo — [Nº]" (US 5.2 Cen.2). Falha de entrega apenas registra em log, sem redespacho
  (`maxAttempts=1`) e **sem** afetar a notificação interna (US 5.2 Cen.3).
- **Marcação de leitura e persistência** — notificações têm estado lido/não-lido por
  usuário; contador só decrementa ao clicar na notificação ou em "Marcar todas como lidas";
  estado persiste entre sessões (US 5.1 Cen.2/Cen.3).
- **Expurgo automático de notificações lidas +30 dias** — rotina diária remove notificações
  **lidas** há mais de 30 dias; notificações **não lidas nunca são expurgadas** (US 5.1
  Cen.4/Cen.4b).
- **Novo parâmetro operacional configurável** — "Dias de antecedência para alerta de prazo"
  (padrão 2, US 8.5) em `sistema_config`, editável pelo Administrador e lido em runtime pela
  rotina de prazos (invariante "parâmetros operacionais são configuráveis em runtime").

Fora de escopo (fatias/épicos futuros): dashboard de KPIs (Épico 6), preferências de
notificação por usuário, notificação de devolução, push/web-sockets em tempo real (o sino
é atualizado por polling/refresh, como no PRD).

## Capabilities

### New Capabilities

- `notificacoes-internas`: notificação interna (sino) por servidor/unidade — geração nos
  eventos de despacho e conclusão, alerta de prazo pela rotina diária, estado lido/não-lido
  com contador persistente, listagem por 30 dias e cenários de "acesso negado"
  (só o próprio destinatário lê/marca suas notificações). US 5.1, 5.3, 5.4.
- `alertas-email-processo`: enfileiramento de e-mails de evento de processo (novo processo
  recebido e alerta de prazo) na fila Cloud Tasks existente, contrato de ACK-sempre em falha
  de entrega e desacoplamento em relação à notificação interna. US 5.2.

### Modified Capabilities

- `rotinas-agendadas`: acrescenta ao job diário (a) a rotina de verificação de prazos que
  gera notificações internas + e-mails e (b) a rotina de expurgo de notificações lidas
  +30d — ambas honrando o contrato de idempotência/retomada já definido (seleção pelo estado
  atual, não "os vencidos de ontem"). Documenta o novo parâmetro configurável lido pela
  rotina de prazos.

## Impact

- **Tabelas PostgreSQL**: nova tabela `notificacao` (PK UUID gerado na aplicação; FKs
  `usuario_id` → `usuario`, `processo_id` → `processo`, `unidade_id` → `unidade`; colunas
  `tipo` [novo_processo | concluido | alerta_prazo], `lida_em` nullable, `criado_em`).
  Alteração em `sistema_config` (singleton id=1): nova coluna
  `dias_antecedencia_alerta_prazo` (int, default 2).
- **Migrations Alembic**: uma para criar `notificacao`, uma para adicionar a coluna em
  `sistema_config` (com backfill do default nas linhas existentes).
- **API (FastAPI)**: novo router `notificacoes` (`GET /notificacoes`, contador,
  `POST /notificacoes/{id}/ler`, `POST /notificacoes/marcar-todas-lidas`); serviço de
  geração chamado dentro das transações de `despachar`/conclusão; extensão do parâmetro em
  `sistema_config` no router/serviço de configuração; extensão do job diário
  (`jobs/manutencao_diaria.py`) com as rotinas de prazo e expurgo.
- **Contrato frontend↔backend**: novas rotas/schemas exigem `pnpm gen:types` (o CI falha via
  `gen:types:check` se o snapshot em `packages/api-types` ficar defasado).
- **Web (Next.js)**: componente de sino no shell autenticado (contador + painel), consumo
  via `lib/api.ts` tipado; marcação de leitura.
- **Segredos/buckets**: nenhum novo — reutiliza a fila `emails` e o endpoint interno OIDC já
  provisionados.
- **LGPD**: e-mails de evento de processo endereçam **servidores** (dados funcionais, não de
  cidadão) e **não** carregam CPF/CNPJ de interessado; corpo limita-se a número, assunto e
  unidade. As notificações internas não introduzem novo dado pessoal de titular. Sem impacto
  de anonimização adicional.
- **Depende de**: `processos-e-workflow` arquivado (eventos de tramitação e `prazo_em`),
  `fila-notificacoes` arquivado (fila + endpoint interno) e `rotinas-agendadas` arquivado
  (job diário e contrato de idempotência).
