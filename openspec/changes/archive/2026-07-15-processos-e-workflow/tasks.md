> **Nota sobre testes E2E:** onde uma tarefa exige teste E2E, ele pode ser realizado via **Playwright** (`apps/web`, `pnpm test:e2e`) **ou pela extensão Claude in Chrome, quando aplicável** — dirigindo o fluxo real no navegador. O teste E2E do **despacho** é obrigatório (regra `tasks` do `config.yaml`: despacho exige E2E).

## 1. Schema — migration Alembic `0003_processos_workflow`

- [x] 1.1 Definir os enums em `models.py` (`StatusProcesso` [aberto|em_tramitacao|concluido|arquivado], `TipoEventoTramitacao` [despacho|devolucao|conclusao], `TipoDocumentoInteressado` [cpf|cnpj], `TipoParticipacaoInteressado` [requerente|representado|terceiro], `MotivoDevolucao` [documentacao_insuficiente|correcao_dados|diligencia_complementar]) e novos valores em `TipoEventoLog` (`expansao_numero_processo`, `alerta_capacidade`) — aceite: `import app.db.models` sem erro; enums refletidos no metadata
- [x] 1.2 Criar migration `0003_processos_workflow` (`down_revision="0002_identidade_estrutura"`, revision ≤ 32 chars) com os enums de 1.1 e a tabela `processo_contador_ano` (`ano` PK, `ultimo_sequencial` not null) — aceite: `alembic upgrade head` roda limpo a partir de `0002`
- [x] 1.3 Na mesma migration, criar `processo` (`numero` unique, `assunto`, `tipo_processo_id` FK, `roteiro_id` FK → `roteiro`, `status`, `unidade_atual_id` FK, `unidade_origem_id` FK, `ordem_atual`, `prazo_dias`, `prazo_em` date, `criado_por_id` FK, `criado_em` server_default now, `concluido_em` nullable) — aceite: `\d processo` mostra as 6 FKs e o unique em `numero`
- [x] 1.4 Criar `processo_interessado` (`processo_id` FK, `nome` not null, `documento` nullable, `tipo_documento` nullable, `tipo_participacao` nullable) — aceite: insere interessado só com `nome` (demais NULL) sem erro
- [x] 1.5 Criar `tramitacao` (`processo_id` FK, `tipo_evento`, `unidade_origem_id` FK nullable, `unidade_destino_id` FK nullable, `responsavel_id` FK, `status_resultante`, `motivo` nullable, `justificativa` text nullable, `criado_em` server_default now) — aceite: insere evento de despacho com origem/destino preenchidos e de conclusão com destino NULL
- [x] 1.6 Criar índices: `processo(unidade_atual_id, status)`, `processo(tipo_processo_id)`, `processo(criado_por_id)`, `tramitacao(processo_id, criado_em)`, `tramitacao(responsavel_id)`, `processo_interessado(processo_id)` — aceite: índices visíveis em `\di`
- [x] 1.7 Escrever `downgrade()` completo (ordem reversa: índices → tramitacao → processo_interessado → processo → processo_contador_ano → enums) e testar ciclo `alembic downgrade -1` + `upgrade head` — aceite: ciclo up/down/up roda sem erro em banco local

## 2. Domínio — serviços de suporte

- [x] 2.1 Implementar validador de CPF/CNPJ em `app/services/documento_fiscal.py` (dígito verificador, Python puro) — aceite: valida CPF/CNPJ corretos e rejeita dígito verificador inválido e sequências triviais
- [x] 2.2 Teste automatizado do validador CPF/CNPJ (casos válidos, dígito inválido, formatação com/sem máscara) — **obrigatório por tocar dado pessoal (CPF/CNPJ)**
- [x] 2.3 Implementar `app/services/numero_processo.py`: alocação atômica via `INSERT ... ON CONFLICT (ano) DO UPDATE SET ultimo_sequencial = ...+1 RETURNING`, formatação `f"{ano}/{seq:06d}"` com expansão natural de dígitos; registrar `log_seguranca` (`expansao_numero_processo` ao cruzar 10^6/10^7; `alerta_capacidade` ao atingir 10^7) — aceite: sequencial 999999→1000000 produz `AAAA/1000000` (7 dígitos) e grava o log de expansão
- [x] 2.4 Teste automatizado da numeração: reinício por ano, unicidade sob concorrência simulada (duas alocações no mesmo ano não colidem), expansão de dígitos e ausência de gap por rollback de transação — **obrigatório (invariante de número do processo)**
- [x] 2.5 Implementar `app/services/roteiro_snapshot.py`: resolver o `Roteiro` vigente do tipo e suas etapas ordenadas; helpers `proxima_etapa(ordem_atual)`, `etapa_anterior(ordem_atual)`, `is_ultima(ordem_atual)`, `is_primeira(ordem_atual)` — aceite: rejeita tipo sem roteiro vigente ou com roteiro de zero etapas
- [x] 2.6 Implementar a máquina de estados em `app/services/processo_estado.py` (tabela de transições válidas; `arquivado` não alcançável neste change) — aceite: transição inválida levanta erro de domínio; `→ arquivado` não é permitida por nenhuma ação

## 3. Criação de processo (US 2.1)

- [x] 3.1 Schemas Pydantic (`app/schemas/processo.py`): entrada de criação (assunto, tipo_processo_id, prazo_dias, lista de interessados com validação CPF/CNPJ de 2.1) e saída (número, status, unidade_atual, prazo_em) — aceite: payload sem assunto/tipo é rejeitado com 422 destacando os campos
- [x] 3.2 Endpoint `POST /processos` (perfil Servidor; unidade atual = unidade do criador): valida tipo com roteiro (2.5), aloca número (2.3), grava `processo` (status `aberto`, `ordem_atual=0`, `unidade_origem_id=unidade_atual_id`, `prazo_em = date(criado_em)+prazo_dias`) e interessados, tudo em uma transação — aceite: cria processo `AAAA/000001`, status Aberto, e aparece no Kanban da unidade
- [x] 3.3 Tratar US 2.1 Cen.3c: tipo sem roteiro configurado → mensagem "Este tipo de processo não possui roteiro de tramitação configurado..." e criação bloqueada — aceite: retorno 422/409 com a mensagem exata
- [x] 3.4 Teste automatizado de criação: dados obrigatórios, número gerado, interessado com CPF inválido (Cen.3), CNPJ inválido (Cen.3b), tipo sem roteiro (Cen.3c), snapshot de roteiro fixado — **obrigatório por tocar dado pessoal (interessado) e histórico/número**

## 4. Despacho e devolução (US 2.2, 2.2b)

- [x] 4.1 Endpoint `POST /processos/{id}/despachar` (perfil Servidor, `require_acesso_unidade(processo.unidade_atual_id)`): se não última etapa → move para `proxima_etapa`, status `em_tramitacao`, `ordem_atual+1`, INSERT `tramitacao` (despacho); se última etapa → exige `confirmar=true` (senão 409 com prompt de conclusão), então status `concluido`, `concluido_em=now()`, INSERT `tramitacao` (conclusao) — tudo em uma transação — aceite: cobre Cen.1 (próxima unidade), Cen.2 (confirmação de conclusão), Cen.3 (cancelamento sem efeito), Cen.4 (roteiro de unidade única)
- [x] 4.2 Endpoint `POST /processos/{id}/devolver` (perfil Servidor, `require_acesso_unidade`): bloqueia se `ordem_atual==0` (Cen.2); exige `motivo` predefinido (Cen.3); move para `etapa_anterior`, status `em_tramitacao`, `ordem_atual-1`, INSERT `tramitacao` (devolucao com motivo/justificativa) — aceite: cobre Cen.1 (devolução para anterior), Cen.2 (bloqueio na primeira unidade), Cen.3 (motivo obrigatório)
- [x] 4.3 Garantir o cenário de acesso negado: Servidor de outra unidade que tenta despachar/devolver é rejeitado e a tentativa é gravada em `log_seguranca` — aceite: 403 + linha `acesso_negado` (PRD US 1.4 Cen.2)
- [x] 4.4 Teste automatizado de despacho/devolução: todas as transições da máquina de estados, imutabilidade do histórico (nenhum UPDATE/DELETE de evento), acesso negado gravado em log — **obrigatório por tocar histórico de tramitação**
- [x] 4.5 **Teste E2E do despacho** (Playwright ou extensão Claude in Chrome): login como Servidor → criar processo → despachar até a conclusão, verificando mudança de status e registro no histórico — **obrigatório (regra E2E de despacho)**

## 5. Histórico de tramitação (US 2.4)

- [x] 5.1 Endpoint `GET /processos/{id}/historico` (autorizado por unidade): retorna a linha do tempo ordenada por `criado_em` (origem, destino, responsável, data/hora, status resultante); processo recém-criado retorna lista vazia + `criado_em` do processo — aceite: cobre Cen.1 (linha do tempo) e Cen.2 (sem movimentações)
- [x] 5.2 Teste automatizado do histórico: ordem cronológica, estado vazio, e verificação de que eventos nunca são alterados após inseridos — **obrigatório por tocar histórico de tramitação**

## 6. Kanban e busca (US 2.3, 2.7, 2.8)

- [x] 6.1 Endpoint `GET /processos` (Kanban) com escopo por autorização: Servidor → `unidade_atual_id = user.unidade_id`; Gestor → `unidade_atual_id IN unidades geridas`, com `filtro_unidade` opcional; resposta agrupável por status com número, assunto, unidade atual, prazo e dias restantes — aceite: Servidor de COFIN nunca recebe processo de outra unidade; Gestor filtra por unidade gerida (US 2.8 Cen.2)
- [x] 6.2 Ordenação por prazo (vencido primeiro) e paginação (50/página acima de 500 processos ativos) no endpoint de Kanban — aceite: cards vencidos vêm no topo; página com >500 processos responde paginada
- [x] 6.3 Endpoint `GET /processos/busca` (US 2.7): filtros por número exato, termo no assunto e intervalo de datas, sempre restritos ao escopo de unidade do usuário — aceite: Cen.1 (número), Cen.2 (assunto restrito à unidade), Cen.3 (período), Cen.4 (sem resultados)
- [x] 6.4 Teste automatizado de Kanban/busca: escopo por unidade (Servidor e Gestor), acesso negado a processo fora de escopo, ordenação por prazo, estados vazios — **obrigatório (regra de visibilidade por unidade/perfil)**

## 7. Fechamento de pendências herdadas (US 1.4, 1.5, 8.1)

- [x] 7.1 Endpoint `GET /processos/{id}` (detalhe) com `require_acesso_unidade`; acesso direto por URL a processo de outra unidade → 403 "Acesso negado — você não tem permissão para visualizar este processo" + `log_seguranca` — aceite: PRD US 1.4 Cen.2 observável de ponta a ponta
- [x] 7.2 Popular "Meu Perfil" (US 1.5 Cen.1): listar processos onde `criado_por_id = user` OU há `tramitacao.responsavel_id = user`, com número, assunto, data e tipo de ação; manter "documentos assinados" vazio — aceite: usuário transferido ainda vê atuação na unidade anterior (US 1.4 Cen.3); recém-cadastrado vê "Nenhum processo registrado"
- [x] 7.3 Ativar a contagem real na desativação de unidade (US 8.1 Cen.3): `COUNT(processo WHERE unidade_atual_id = unidade AND status IN ('aberto','em_tramitacao'))` bloqueia a desativação com a mensagem que informa X pendentes — aceite: unidade com processo em andamento não desativa; sem pendências, desativa e desvincula usuários (Cen.4)
- [x] 7.4 Teste automatizado das pendências: acesso negado por URL (US 1.4 Cen.2), "Meu Perfil" populado/vazio (US 1.5), bloqueio/liberação de desativação de unidade (US 8.1 Cen.3/4) — **obrigatório (histórico de atuação + visibilidade por unidade)**

## 8. Frontend (Next.js — `apps/web`)

- [x] 8.1 Tela de criação de processo (`app/processos/novo`): formulário com assunto, tipo, prazo, interessados (nome + CPF/CNPJ com máscara + tipo de participação), consumindo `lib/api.ts` tipado — aceite: erros de campo obrigatório e CPF/CNPJ inválido exibidos inline
- [x] 8.2 Tela de Kanban (`app/processos`): colunas Aberto/Em Tramitação/Concluído/Arquivado (visualização, sem drag-and-drop), cards com número/assunto/prazo/dias restantes e destaque visual de vencidos (barra vermelha 4px, negrito, ícone); botão "Atualizar"; filtro de unidade para Gestor — aceite: cobre US 2.3 Cen.1/4 e US 2.8 Cen.1/2; estados vazios com mensagens do PRD
- [x] 8.3 Tela de detalhe do processo (`app/processos/[id]`): metadados, interessados, ações "Despachar"/"Devolver" (com modal de confirmação de conclusão e modal de motivo de devolução) e aba "Histórico" (linha do tempo) — aceite: modal de conclusão na última etapa (US 2.2 Cen.2) e bloqueio de devolução na primeira etapa (US 2.2b Cen.2)
- [x] 8.4 Atualizar "Meu Perfil" (`app/perfil`) para listar processos atuados (US 1.5 Cen.1) mantendo estado vazio quando não houver — aceite: seção populada e seção vazia renderizam corretamente
- [x] 8.5 Teste de componente (Vitest + RTL) das telas de criação e de detalhe (validação de formulário, render de modais, estados vazios do Kanban) — aceite: `pnpm --filter @setes/web test` verde

## 9. Contrato de tipos e verificação final

- [x] 9.1 Regenerar o contrato front↔back: `pnpm gen:types` e commitar `packages/api-types` atualizado — aceite: `pnpm gen:types:check` passa (snapshot não defasado)
- [x] 9.2 Rodar as suítes locais antes do PR: `uv run ruff check .`, `uv run pytest` (API) e `pnpm --filter @setes/web typecheck && pnpm --filter @setes/web test` (web) — aceite: todas verdes
- [x] 9.3 Executar o E2E de despacho (tarefa 4.5) contra a stack local (api+web+Postgres) — aceite: fluxo login→criar→despachar→concluir passa fim a fim
