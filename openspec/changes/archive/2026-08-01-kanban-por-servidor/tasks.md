## 1. Migration e schema (antes de endpoint/UI — design D7)

- [x] 1.1 Migration `0025_ix_tramitacao_servidores` criando `ix_tramitacao_servidor_destino` em `(servidor_destino_id, processo_id)` e `ix_tramitacao_servidor_origem` em `(servidor_origem_id, processo_id)`. `down_revision = "0024_remover_roteiro"`. Sem mudança de dado. Aceite: `upgrade head` aplica e `downgrade -1` remove os dois índices; `ruff check migrations/` verde.
- [x] 1.2 `schemas/processo.py`: adicionar `acao_requerida: bool` e `servidor_atual_nome: str` a `CardProcessoResponse`, com docstring registrando que são contextuais ao usuário da requisição. Aceite: OpenAPI expõe os campos.
- [x] 1.3 `schemas/dashboard.py`: `ContagensPorStatusResponse` com `total`, `abertos`, `em_tramitacao`, `concluidos`, `arquivados`. Aceite: OpenAPI expõe o schema.

## 2. Backend — escopo pessoal do quadro (design D1, D2, D3)

- [x] 2.1 `services/processo_consulta.py`: nova função de escopo pessoal do Servidor — `servidor_atual_id = eu OR criado_por_id = eu OR EXISTS(tramitacao com eu em servidor_origem/servidor_destino)`. Manter `unidades_visiveis` intacta (é usada por outros consumidores). Comentário citando `(D1)`. Aceite: uma única query, sem N+1.
- [x] 2.2 `services/processo_consulta.py::listar_kanban`: Servidor usa o escopo pessoal; Gestor e Administrador mantêm o escopo por unidade atual ∪ origem, exatamente como hoje. Aceite: nenhum processo fora do escopo é retornado para nenhum perfil.
- [x] 2.3 `services/processo_consulta.py`: preservar o filtro de sigilo — sigiloso fora da unidade atual do usuário continua excluído, inclusive para participante histórico (D3). Aceite: coberto por teste dedicado.
- [x] 2.4 `services/processo_consulta.py::atributos_contextuais`: adicionar `acao_requerida` (`servidor_atual_id == usuario.id`), mantendo `somente_leitura` e `devolvido` inalterados e o cálculo em lote. Aceite: uma consulta em lote para os ids da página, sem N+1.
- [x] 2.5 Carregar o nome do servidor atual para o card via eager loading (novo relacionamento `Processo.servidor_atual`), evitando N+1. Aceite: nenhuma query adicional por card.
- [x] 2.6 Testes pytest de escopo (obrigatórios — visibilidade de dados pessoais): Servidor vê processo que criou, que detém e pelo qual passou; NÃO vê processo da própria unidade que nunca tocou; Gestor que apenas reatribuiu não passa a ver o processo no quadro pessoal; sigiloso em outra unidade ausente mesmo para ex-detentor; Gestor mantém escopo por unidades geridas; **acesso negado**: Servidor de outra unidade não obtém o processo por nenhum ramo do escopo.

## 3. Backend — filtros e arquivados (design D4, D5)

- [x] 3.1 `routers/processos.py` + `services/processo_consulta.py`: substituir `incluir_finalizados` por `incluir_arquivados: bool = false`; Concluídos passam a ser sempre exibidos, Arquivados apenas com o param verdadeiro. Aceite: `total` do cabeçalho coerente com o filtro.
- [x] 3.2 `routers/processos.py` + `services/processo_consulta.py`: query params `tipo_processo_id`, `assunto` (ILIKE parcial), `data_inicial` e `data_final` (dia final inteiro), combináveis entre si e com `incluir_arquivados`, aplicados **após** o recorte de escopo. Aceite: nenhum filtro amplia o escopo autorizado.
- [x] 3.3 `services/processo_consulta.py::buscar`: manter o escopo por **unidade** (D6), sem estreitar para o conjunto pessoal; documentar a divergência deliberada em docstring citando `(D6)`. Aceite: docstring explica por que quadro e busca divergem.
- [x] 3.4 Testes pytest de filtro (obrigatórios): cada filtro isolado; os três combinados; combinação com `incluir_arquivados`; arquivados ausentes por padrão e presentes com o param; concluídos sempre presentes; **acesso negado**: filtro não traz processo fora do escopo pessoal.

## 4. Backend — cards de contagem do dashboard (design D8)

- [x] 4.1 `services/dashboard.py`: contagem por status em **uma única** consulta com `GROUP BY status` sobre o escopo de unidades do Gestor; `total` derivado da soma das parcelas. Aceite: total sempre igual à soma exibida.
- [x] 4.2 `routers/dashboard.py`: endpoint expondo as cinco contagens, restrito ao perfil Gestor e às unidades geridas, no mesmo padrão dos KPIs existentes. Aceite: perfil não autorizado recebe 403 com log.
- [x] 4.3 Testes pytest de dashboard: contagens corretas por status; total igual à soma; escopo restrito às unidades geridas; **acesso negado**: Gestor não obtém contagens de unidade que não gerencia; Servidor recebe 403.

## 5. Contrato

- [x] 5.1 `pnpm gen:types` e commit de `packages/api-types/{openapi.json,schema.ts}`. Aceite: `pnpm gen:types:check` verde.

## 6. Frontend — quadro de processos (design D2, D4, D5)

- [x] 6.1 `app/processos/page.tsx` + `lib/processo-ui.ts`: estilo sólido para `acao_requerida` e estilo discreto para acompanhamento, exibindo neste o nome do servidor detentor. Aceite: os dois estados distinguíveis em Kanban e em Lista.
- [x] 6.2 `app/processos/page.tsx`: checkbox "Exibir Arquivados", desmarcado por padrão, persistido em `localStorage` sob a chave nova `setes:processos:exibir-arquivados`. Aceite: preferência sobrevive a reload; a chave antiga não é lida.
- [x] 6.3 `app/processos/page.tsx`: barra de filtros com select de tipo de processo, campo de assunto (debounce de 300 ms) e seletor de período, combináveis, refletidos nos query params da chamada. Aceite: limpar os filtros restaura o quadro completo do escopo.
- [x] 6.4 `app/dashboard/page.tsx`: linha de cinco cards de contagem (Total, Abertos, Em Tramitação, Concluídos, Arquivados) no topo do dashboard. Aceite: valores conferem com o quadro do Gestor.
- [x] 6.5 Testes Vitest: card de ação vs card de acompanhamento; checkbox de arquivados (default, toggle, persistência); cada filtro e a combinação dos três; render dos cinco cards de contagem.

## 7. Testes E2E Playwright (obrigatório — altera visibilidade de processos)

- [x] 7.1 Ajustar `e2e/14-visibilidade-processos-origem.spec.ts` e demais specs afetadas ao novo escopo pessoal. Aceite: suíte E2E completa verde.
- [x] 7.2 Novo cenário: Servidor A cria processo (aparece como ação) → envia para B (passa a acompanhamento no quadro de A, com o nome de B) → C, da mesma unidade de A e sem ter tocado o processo, não o vê no quadro mas o abre por URL direta (autorização por unidade preservada) → B conclui → o processo permanece visível para A como concluído → após arquivamento, some do quadro de A até que "Exibir Arquivados" seja marcado. Aceite: `pnpm test:e2e` verde.

## 8. Documentação mestre

- [x] 8.1 `docs/PRD.md` US 1.4, US 2.3 e US 2.8: registrar o escopo pessoal do quadro do Servidor, a distinção ação/acompanhamento, o padrão de arquivados e a manutenção do escopo por unidade para o Gestor e para a busca. Aceite: PRD sem contradição com as specs deste change.
- [x] 8.2 `docs/manual-usuario.md`: seção do quadro de processos atualizada (quadro pessoal, cards de ação e de acompanhamento, filtros, checkbox de arquivados) e seção do dashboard com os cinco cards. Aceite: descrições coerentes com a UI final.
