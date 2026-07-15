## Why

O SETES.DOCS tem identidade e estrutura organizacional prontas (`identidade-e-estrutura-organizacional`, arquivado): existem usuários, perfis, unidades, tipos de processo e roteiros versionados. Mas **não existe a entidade `processo`** — e ela é a peça central de que todo o restante do produto depende. Sem `processo` não há Kanban, não há documentos (Épico 3), não há notificações de despacho (Épico 5), não há dashboard (Épico 6), não há consulta pública (Épico 7), não há auditoria (Épico 9) nem dados de interessado para a rotina LGPD (Épico 10).

Além de desbloquear os épicos seguintes, este change **fecha buracos explicitamente declarados** em changes já arquivados:

- `controle-acesso-por-unidade` adiou "para o change do Épico 2/3" a aplicação efetiva do filtro por unidade ao Kanban (US 1.4) e a listagem de processos atuados em "Meu Perfil" (US 1.5).
- `unidades-administrativas` codificou o bloqueio de desativação de unidade com processos em andamento (US 8.1 Cen.3), mas "a contagem é sempre zero" até `processo` existir.

Este change entrega o **núcleo transacional de processo e workflow roteirizado**: criar, despachar, devolver, ver o Kanban da unidade, ver o histórico e buscar. Fica de fora, para um change seguinte (Change B), o que é assíncrono ou de visibilidade externa: sigilo (US 2.6) e a rotina automática de arquivamento (US 2.5, primeiro Cloud Run Job).

## What Changes

- **US 2.1 — Criação de processo**: Servidor cria processo com assunto, tipo de processo, interessados e prazo (dias corridos). O sistema gera o número único `AAAA/NNNNNN` (sequencial de 6 dígitos, reiniciado por ano, expansível sem limite superior — detalhe de concorrência e expansão no design), status inicial "Aberto", unidade atual = unidade do Servidor. O processo **fixa (snapshot) o roteiro vigente** do tipo no momento da criação, consumindo o versionamento já existente em `roteiro`/`roteiro_etapa`. Validações: campos obrigatórios (US 2.1 Cen.2), CPF/CNPJ de interessado por dígito verificador (Cen.3/3b), e rejeição de tipo de processo com roteiro vazio (Cen.3c).
- **US 2.2 — Despacho para a próxima unidade**: Servidor da unidade atual aciona "Despachar"; o processo avança para a próxima unidade do roteiro-snapshot e passa a "Em Tramitação"; na última unidade, a ação vira confirmação de conclusão ("Concluído"), incluindo o caso de roteiro de unidade única (Cen.1–4). Cada despacho é um **evento imutável** no histórico (unidade origem/destino, responsável, data/hora).
- **US 2.2b — Devolução para a unidade anterior**: Servidor devolve o processo à unidade imediatamente anterior do roteiro, com motivo predefinido obrigatório e justificativa opcional; bloqueada na primeira unidade do roteiro (Cen.1–3). Devolução também é evento imutável no histórico.
- **US 2.3 — Quadro Kanban da unidade (Servidor)**: quadro de **visualização** (não drag-and-drop) com colunas Aberto / Em Tramitação / Concluído / Arquivado, cards com número, assunto, prazo e dias restantes, ordenados por prazo com destaque visual de vencidos (Cen.1–4). A coluna "Arquivado" existe na máquina de estados, mas nenhum processo a alcança neste change (a transição é o Change B).
- **US 2.4 — Histórico de tramitação**: linha do tempo imutável de cada movimentação (origem, destino, responsável, data/hora, status resultante), incluindo o estado vazio de processo recém-criado (Cen.1–2).
- **US 2.7 — Busca interna**: busca/filtro de processos **da própria unidade** por número exato, termo no assunto e intervalo de datas, com estado "sem resultados" (Cen.1–4). Consome as primitivas de autorização por unidade já existentes.
- **US 2.8 — Kanban consolidado (Gestor)**: quadro consolidado das unidades geridas pelo Gestor, com o nome da unidade atual em cada card e filtro por unidade (Cen.1–3).

**Fecha pendências de changes arquivados:**
- **US 1.4 (Cen.1–3)** — o filtro por unidade do Kanban, antes adiado, passa a ser efetivo: Servidor vê exclusivamente processos na sua unidade; acesso direto por URL a processo de outra unidade retorna "acesso negado" com registro em log de segurança.
- **US 1.5 (Cen.1)** — "Meu Perfil" passa a listar os processos em que o usuário atuou (número, assunto, data e tipo de ação). A lista de "documentos assinados" continua vazia (é escopo dos Épicos 3/4).
- **US 8.1 (Cen.3)** — a desativação de unidade passa a contar processos em andamento reais (deixa de ser sempre zero).

**Fora de escopo deste change** (vão para o Change B ou épicos seguintes):
- **US 2.5 — Arquivamento automático**: rotina diária (primeiro Cloud Run Job sobre a infra de `rotinas-agendadas`), com contrato de idempotência/retomada. → **Change B**.
- **US 2.6 — Sigilo de processo**: marcação/remoção de sigilo e indicador visual; prepara a consulta pública. → **Change B** (introduz a coluna `sigiloso` e seus eventos de histórico).
- **Épico 3 (documentos/anexos)**, **Épico 5 (notificações de despacho/prazo)**, **Épico 6 (dashboard)**, **Épico 7 (consulta pública)** — changes futuros. Em particular, **nenhuma notificação** de "novo processo recebido" (US 5.1/5.2) é disparada neste change; o despacho apenas move o processo e registra o evento.

## Capabilities

### New Capabilities
- `processos`: criação de processo com metadados e interessados, geração do número `AAAA/NNNNNN`, snapshot do roteiro na criação e busca interna por unidade (US 2.1, 2.7).
- `workflow-tramitacao`: máquina de estados do processo (Aberto → Em Tramitação → Concluído → Arquivado) e as ações que a movem — despacho e devolução — com histórico imutável de eventos (US 2.2, 2.2b, 2.4).
- `quadro-kanban`: visualização Kanban por unidade (Servidor) e consolidada por unidades geridas (Gestor), com ordenação por prazo e filtro (US 2.3, 2.8).

### Modified Capabilities
- `controle-acesso-por-unidade`: sai do escopo parcial — o filtro por unidade do Kanban (US 1.4) e a listagem de processos atuados em "Meu Perfil" (US 1.5 Cen.1) passam a ser efetivos agora que `processo` existe. Adiciona o cenário de acesso negado por URL direta a processo de outra unidade (US 1.4 Cen.2) com registro em log de segurança.
- `unidades-administrativas`: a desativação de unidade (US 8.1 Cen.3) passa a bloquear com base na contagem real de processos em andamento na unidade, honrando o contrato antes registrado como "sempre zero".

## Impact

- **Dependência de change anterior:** requer `identidade-e-estrutura-organizacional` arquivado — consome `usuario`, `unidade`, `tipo_processo`, `roteiro`/`roteiro_etapa` (roteiro versionado, para o snapshot), as primitivas de autorização por perfil/unidade (`get_current_user → require_perfil → require_acesso_unidade`) e a tabela `log_seguranca` (para o acesso negado da US 1.4 Cen.2). Transitivamente requer `bootstrap-infraestrutura` (Cloud SQL privado, baseline Alembic).
- **Tabelas PostgreSQL novas:**
  - `processo` (numero `AAAA/NNNNNN` único, assunto, tipo_processo_id FK → `tipo_processo`, roteiro_id FK → `roteiro` [snapshot do roteiro vigente na criação], status enum [aberto|em_tramitacao|concluido|arquivado], unidade_atual_id FK → `unidade`, unidade_origem_id FK → `unidade`, prazo_dias int, prazo_em date, criado_por_id FK → `usuario`, criado_em, concluido_em nullable)
  - `processo_interessado` (processo_id FK → `processo`, nome, documento nullable [CPF/CNPJ], tipo_documento enum [cpf|cnpj] nullable, tipo_participacao enum [requerente|representado|terceiro] nullable) — **dado pessoal de terceiro** (ver LGPD)
  - `tramitacao` (processo_id FK → `processo`, tipo_evento enum [criacao|despacho|devolucao|conclusao], unidade_origem_id FK → `unidade` nullable, unidade_destino_id FK → `unidade` nullable, responsavel_id FK → `usuario`, status_resultante enum, motivo enum nullable [devolução], justificativa text nullable, criado_em) — **histórico imutável, INSERT-only** (invariante do projeto; sucede o precedente de `log_seguranca`)
  - `processo_contador_ano` (ano PK, ultimo_sequencial) — suporte à geração atômica e reinício anual do número; a estratégia de concorrência (row lock vs. sequence) é decisão do design (US 2.1 Cen.1)
- **Máquina de estados:** o enum de status já nasce completo (inclui `arquivado`), mas **a transição para `arquivado` não é implementada aqui** — só a rotina do Change B a produz. Neste change as transições válidas são `aberto → em_tramitacao`, `em_tramitacao → em_tramitacao` (devolução/despacho intermediário) e `→ concluido`.
- **Secret Manager:** nenhum segredo novo.
- **Cloud Storage:** nenhum bucket novo — anexos são Épico 3.
- **Rate limiting:** N/A — todos os endpoints deste change são autenticados e internos; a consulta pública com rate limiting (`slowapi`) é Épico 7.
- **LGPD:** este change introduz, **pela primeira vez, dados pessoais de terceiros** (interessados externos ao órgão) em `processo_interessado`: nome e, opcionalmente, CPF/CNPJ. Base legal: exercício regular de competência/política pública do órgão (tratamento de processo administrativo), não consentimento. Coleta: mínima e vinculada ao processo. **Retenção e anonimização são tratadas em changes posteriores** — a não-exibição de CPF/CNPJ na consulta pública é o Épico 7 (US 7.1 Cen.3), e a anonimização irreversível (por solicitação do titular ou automática de arquivados) é o Épico 10 (US 10.2/10.3). Este change **não** expõe interessados a nenhum canal público; o dado só é acessível por usuários autenticados e autorizados por unidade. O histórico `tramitacao` registra responsável (dado pessoal funcional) sob a mesma política de retenção dos demais logs de auditoria.
- **Código:** nova migration Alembic (`processo`, `processo_interessado`, `tramitacao`, `processo_contador_ano`); novo router `processos` (criação, despacho, devolução, histórico, busca, Kanban) montado em `main.py`, consumindo as dependências de autorização existentes; validador de CPF/CNPJ; serviço de geração do número de processo. No frontend: telas de criação de processo, detalhe + histórico, Kanban do Servidor e Kanban consolidado do Gestor; "Meu Perfil" passa a popular a lista de processos atuados. Regenerar o contrato `packages/api-types` (`pnpm gen:types`). Testes: unitários de máquina de estados/histórico imutável/geração de número (obrigatórios — tocam histórico); E2E Playwright do fluxo de despacho (obrigatório — altera despacho).
