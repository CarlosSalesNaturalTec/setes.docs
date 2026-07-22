## 1. Migration e schema (antes de endpoint/UI)

- [x] 1.1 Migration Alembic criando índice `ix_processo_unidade_origem_id` em `processo.unidade_origem_id` (sem mudança de dado). Aceite: `uv run alembic upgrade head` aplica e `downgrade -1` remove o índice.
- [x] 1.2 `schemas/processo.py`: adicionar `somente_leitura: bool` e `devolvido: bool` ao `CardProcessoResponse`, com docstring registrando que são contextuais ao usuário da requisição. Aceite: schema OpenAPI expõe os dois campos.

## 2. Backend — escopo de consulta (design D1, D3, D4)

- [x] 2.1 `services/processo_consulta.py::listar_kanban`: escopo `unidade_atual IN escopo OR (unidade_origem IN escopo AND NOT sigiloso)`; novo parâmetro `incluir_finalizados: bool = False` excluindo `concluido`/`arquivado` quando falso. Aceite: query única, `total` coerente com o filtro.
- [x] 2.2 `services/processo_consulta.py`: cálculo em lote de `devolvido` (último evento de `tramitacao` da página é `DEVOLUCAO` e processo na unidade do escopo do usuário) e de `somente_leitura` (`unidade_atual ∉ escopo`; `False` para Administrador). Aceite: uma consulta em lote para os ids da página, sem N+1 e sem UPDATE em `tramitacao`.
- [x] 2.3 `services/processo_consulta.py::buscar`: mesmo escopo ampliado do Kanban (origem sem sigiloso). Aceite: busca e Kanban nunca divergem sobre visibilidade.
- [x] 2.4 `routers/processos.py`: expor `incluir_finalizados` como query param de `GET /processos/kanban` e repassar aos cards os novos campos. Aceite: default `false` omite finalizados; `true` os retorna.
- [x] 2.5 Testes pytest de visibilidade (obrigatórios — histórico de tramitação/dados pessoais): despachado visível por origem como `somente_leitura`; sigiloso fora da unidade ausente do Kanban e da busca; `devolvido` verdadeiro após devolução e falso após novo despacho; `incluir_finalizados` filtrando status; Gestor vê origem das geridas; **acesso negado**: Servidor de terceira unidade não vê processo alheio no Kanban/busca.

## 3. Backend — leitura do detalhe pela origem (design D5)

- [x] 3.1 `routers/processos.py::_exigir_leitura_ao_processo`: novo ramo permitindo leitura quando `tem_acesso_a_unidade(unidade_origem_id)` e o processo não é sigiloso; ordem das checagens preservada (`pode_auditar` → unidade atual → origem); sigiloso fora da unidade atual segue caindo em "Acesso restrito" com `acesso_negado` no log. Escrita (`_exigir_acesso_ao_processo`) intocada. Aceite: detalhe/histórico/documentos legíveis pela origem; docstring atualizada.
- [x] 3.2 Testes pytest de autorização (obrigatórios): leitura do detalhe/histórico/documentos por origem OK; **acesso negado** com log em: escrita por origem (despachar, devolver, sigilo, anexar/remover documento), leitura por origem de sigiloso, leitura por unidade sem vínculo algum.

## 4. Contrato

- [x] 4.1 `pnpm gen:types` e commit de `packages/api-types/{openapi.json,schema.ts}`. Aceite: `pnpm gen:types:check` verde.

## 5. Frontend — tela de Processos (design D2, D4, D6)

- [x] 5.1 `app/processos/page.tsx` + `lib/processo-ui.ts`: checkbox "Exibir concluídos e arquivados" no cabeçalho, default desmarcado, controla `incluir_finalizados` da chamada, persiste em `localStorage` (`setes:processos:exibir-finalizados`), todos os perfis; desmarcado, colunas Concluído/Arquivado ocultas e contador refletindo só o visível. Aceite: preferência sobrevive a reload.
- [x] 5.2 Cards/linhas: estilo acinzentado (fundo cinza + opacidade) quando `somente_leitura`; badge "↩ Devolvido" + borda esquerda âmbar quando `devolvido` (borda vermelha de vencido prevalece, badge permanece). Aceite: os dois estados visíveis em Kanban e Lista.
- [x] 5.3 `app/processos/[id]/page.tsx`: modo leitura quando Servidor com `processo.unidade_atual_id !== usuario.unidade_id` — ocultar Despachar/Devolver/sigilo/anexar-remover documentos, reutilizando o padrão read-only do Administrador. Aceite: nenhum controle de ação renderizado no acompanhamento.
- [x] 5.4 Testes Vitest: checkbox (default, toggle, persistência, contador), card acinzentado, badge de devolvido, detalhe em modo leitura para Servidor fora da unidade atual.

## 6. E2E Playwright (obrigatório — fluxo de despacho/devolução)

- [x] 6.1 Cenário: Servidor A (origem) cria e despacha → processo aparece acinzentado no Kanban de A com detalhe read-only (sem botões de ação) → Servidor B devolve → card de A exibe "↩ Devolvido" e volta acionável → A despacha de novo → destaque some. Incluir verificação de que sigiloso na unidade B some do Kanban de A. Aceite: suíte `pnpm test:e2e` verde.

## 7. Documentação mestre

- [x] 7.1 `docs/PRD.md` US 1.4 Cen.1: registrar a regra revisada (visibilidade = unidade atual ∪ unidade de origem, somente leitura fora da unidade atual, sigiloso excluído do acompanhamento) mantendo Cen.2/Cen.3 coerentes. Aceite: PRD sem contradição com as specs deste change.
- [x] 7.2 `docs/manual-usuario.md`: seção da tela de Processos atualizada (acompanhamento acinzentado, destaque de devolução, checkbox de finalizados). Aceite: capturas/descrições coerentes com a UI final.
