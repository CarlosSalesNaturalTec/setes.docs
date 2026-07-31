## 1. Migration e schema (antes de endpoint/UI)

- [x] 1.1 Migration `0020_setor` criando a tabela `setor` (`id` uuid PK, `unidade_id` FK→`unidade` NOT NULL, `nome` varchar(200), `sigla` varchar(20), `ativo` boolean NOT NULL default true), índice em `unidade_id` e `UniqueConstraint(unidade_id, sigla)`. `down_revision = "0019_ix_unidade_origem"`. Aceite: `uv run alembic upgrade head` aplica e `downgrade -1` remove a tabela; `uv run ruff check migrations/` verde.
- [x] 1.2 Migration `0021_usuario_setor_e_campos` adicionando `usuario.setor_id` (FK→`setor`, nullable), `usuario.telefone` varchar(30), `usuario.cargo` varchar(200), `usuario.chefia_direta` varchar(200) — todos nullable. `down_revision = "0020_setor"`. Aceite: upgrade/downgrade limpos; docstring citando `Change setores-e-cadastro-usuario (design.md D1, D2, D4, D7)`.
- [x] 1.3 `db/models.py`: classe `Setor` e novos campos em `Usuario`, com relacionamento `Unidade.setores` e `Usuario.setor`. Comentários citando `(D1)`, `(D2)`, `(D4)`. Aceite: `uv run ruff check .` verde e modelos refletem exatamente as migrations.
- [x] 1.4 `db/dev_reset.py`: incluir `setor` na ordem de truncamento (antes de `unidade`, depois de `usuario`). Aceite: `POST /internal/dev/reset` limpa a tabela nova sem violar FK.

## 2. Backend — Setor (design D1, D3)

- [x] 2.1 `schemas/unidades.py`: `SetorResponse`, `CadastrarSetorRequest`, `EditarSetorRequest`. Aceite: OpenAPI expõe os schemas.
- [x] 2.2 `services/unidades.py`: `listar_setores`, `cadastrar_setor` (sigla única na unidade), `editar_setor`, `desativar_setor` (bloqueia se houver Servidor **ativo** vinculado, 422 com a contagem), `reativar_setor`. Aceite: nenhuma exclusão física em nenhum caminho.
- [x] 2.3 `services/unidades.py::desativar_unidade`: cascatear desativação para os setores da unidade; `reativar_unidade` NÃO reativa setores (D3). Aceite: cascata coberta por teste.
- [x] 2.4 `routers/unidades.py`: rotas `GET/POST /unidades/{id}/setores`, `PATCH /setores/{id}`, `POST /setores/{id}/desativar`, `POST /setores/{id}/reativar` — todas restritas ao Administrador via `require_perfil`. Aceite: perfil não-Administrador recebe 403 com registro em `log_seguranca`.
- [x] 2.5 Testes pytest de Setor (obrigatórios): CRUD completo; sigla duplicada na mesma unidade rejeitada; sigla repetida em unidades diferentes aceita; desativação bloqueada com servidor ativo; cascata ao desativar a unidade; reativação de unidade não reativa setores; **acesso negado**: Servidor e Gestor recebem 403 em cada rota de escrita, com log.

## 3. Backend — Usuário (design D2, D4, D5)

- [x] 3.1 `schemas/usuarios.py`: `setor_id`, `telefone`, `cargo`, `chefia_direta` em `UsuarioResponse`, `CadastroUsuarioRequest`, `AtualizarMeuPerfilRequest` e `MeuPerfilResponse`. Aceite: OpenAPI expõe os campos.
- [x] 3.2 `services`/`routers/usuarios.py`: validar que `setor_id` é obrigatório quando `perfil == servidor` (422) e que `setor.unidade_id == usuario.unidade_id` (422) — no cadastro e em toda edição, inclusive transferência de unidade. Aceite: transferir de unidade sem trocar o setor é rejeitado com mensagem clara.
- [x] 3.3 `routers/usuarios.py`: query param `nome: str | None` em `GET /usuarios` aplicando `ilike` parcial case-insensitive. Aceite: busca por fragmento retorna correspondências; ausente, lista completa.
- [x] 3.4 Testes pytest de usuário (obrigatórios — dados pessoais): cadastro de Servidor sem setor rejeitado; setor de outra unidade rejeitado; Gestor/Administrador sem setor aceitos; filtro por nome parcial e case-insensitive; novos campos persistidos e devolvidos em "Meu Perfil"; **acesso negado**: não-Administrador não cadastra usuário.

## 4. Contrato

- [x] 4.1 `pnpm gen:types` e commit de `packages/api-types/{openapi.json,schema.ts}`. Aceite: `pnpm gen:types:check` verde.

## 5. Frontend (design D5, D6)

- [x] 5.1 `app/admin/unidades/page.tsx`: seção de Setores da unidade selecionada — listar, cadastrar, editar, desativar/reativar, com confirmação exibindo a contagem de setores afetados ao desativar a unidade. Aceite: nenhuma ação de exclusão na UI.
- [x] 5.2 `app/admin/usuarios/page.tsx`: extrair o formulário inline para componente e montá-lo em **modal** acionado por "Novo usuário"; incluir os campos telefone, cargo, chefia direta e o select de Setor em cascata com a Unidade (setores da unidade escolhida, apenas ativos). Aceite: o índice não renderiza mais formulário inline.
- [x] 5.3 `app/admin/usuarios/page.tsx`: campo de filtro por nome no espaço liberado, com debounce de 300 ms, chamando `GET /usuarios?nome=`. Aceite: lista filtra sem recarregar a página.
- [x] 5.4 `app/perfil/page.tsx`: exibir unidade, setor, cargo, telefone e chefia direta. Aceite: campos vazios são omitidos em vez de exibirem "null".
- [x] 5.5 Testes Vitest: modal abre/fecha e submete; cascata Unidade→Setor limpa o setor ao trocar de unidade; filtro por nome com debounce; validação de setor obrigatório para Servidor no formulário.

## 6. Documentação mestre

- [x] 6.1 `docs/PRD.md`: Épico 1 (US 1.1/1.3) e Épico 8 (US 8.1/8.2) registrando Setor como segundo nível da estrutura organizacional e os novos campos de cadastro. Aceite: PRD sem contradição com as specs deste change.
- [x] 6.2 `docs/manual-usuario.md`: seções de administração de unidades e usuários atualizadas (setores, modal, filtro por nome). Aceite: descrições coerentes com a UI final.
