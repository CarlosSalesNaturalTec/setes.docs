## 1. Favicon

- [x] 1.1 Adicionar `apps/web/app/icon.svg` (ícone simples SETES.DOCS). Aceite: arquivo existe e é SVG válido.
- [x] 1.2 Declarar `metadata.icons` em `apps/web/app/layout.tsx`. Aceite: `GET /favicon.ico` (ou o ícone gerado) responde 200, não mais 500.

## 2. Backend — editar o próprio nome

- [x] 2.1 Criar schema `AtualizarMeuPerfilRequest` (campo `nome: str`, `min_length=1`, `max_length=200`) em `app/schemas/`. Aceite: valida vazio e >200 chars.
- [x] 2.2 Implementar `PATCH /usuarios/me/perfil` em `app/routers/usuarios.py` usando `get_current_user`; grava só `nome` (strip) e retorna `MeuPerfilResponse`. Aceite: e-mail e perfil inalterados.
- [x] 2.3 (dado pessoal — obrigatório) Testes pytest: sucesso, nome vazio/espaços rejeitado, >200 chars rejeitado, e-mail/perfil não afetados, sem sessão → 401. Aceite: todos passam contra Postgres real.

## 3. Backend — reativar unidade

- [x] 3.1 Implementar `POST /unidades/{unidade_id}/reativar` (Admin-only) em `app/routers/unidades.py`: seta `ativo = True`, não toca `Usuario.unidade_id`, idempotente. Aceite: 404 para unidade inexistente.
- [x] 3.2 Testes pytest: reativa inativa; não revincula servidores desvinculados; idempotente em unidade já ativa; Gestor/Servidor → 403 com `log_seguranca`. Aceite: todos passam.

## 4. Backend — rejeitar unidade inativa em roteiro

- [x] 4.1 Ajustar `_validar_unidades` em `app/routers/tipos_processo.py` para contar apenas `Unidade.ativo == True`, disparando "Unidade inválida no roteiro" quando houver ID inativo. Aceite: vale para criar e versionar roteiro.
- [x] 4.2 Testes pytest: criar tipo com unidade inativa → 422; versionar roteiro com unidade inativa → 422 e roteiro vigente mantido; roteiro só com ativas → sucesso. Aceite: todos passam.

## 5. Contrato

- [x] 5.1 Rodar `pnpm gen:types` e commitar o snapshot atualizado em `packages/api-types`. Aceite: `pnpm gen:types:check` passa (sem defasagem) incluindo os novos endpoints.

## 6. Frontend — Meu Perfil (editar nome)

- [x] 6.1 Adicionar `atualizarMeuPerfil` em `apps/web/lib/api.ts` (tipado, sem `any`). Aceite: usa `@setes/api-types`.
- [x] 6.2 Adicionar form de edição de nome em `app/perfil/page.tsx` (max 200, mensagens de erro, atualização de estado + header de sessão). Aceite: nome muda na tela sem reload.
- [x] 6.3 Teste Vitest/RTL do form (sucesso e erro de validação). Aceite: passa.

## 7. Frontend — Unidades (reativar + remover gestor)

- [x] 7.1 Adicionar `reativarUnidade` em `lib/api.ts`. Aceite: tipado.
- [x] 7.2 Em `app/admin/unidades/page.tsx`: exibir botão "Reativar" quando `!unidade.ativo` (e manter "Desativar" quando ativa). Aceite: alterna corretamente após recarregar.
- [x] 7.3 Remover o `<select>` de "Gestor responsável" do `CadastroUnidadeForm` e parar de enviar `gestor_responsavel_id`. Aceite: cadastro funciona só com nome/sigla.

## 8. Frontend — Tipos de Processo (só unidades ativas)

- [x] 8.1 No `EditorRoteiro` (`app/admin/tipos-processo/page.tsx`), popular o `<select>` apenas com unidades `ativo`. Aceite: unidades inativas não aparecem como opção.

## 9. Frontend — Admin read-only em Processos

- [x] 9.1 Em `app/processos/page.tsx`, condicionar "Novo processo" a `perfil === "servidor"`. Aceite: Admin não vê o botão.
- [x] 9.2 Em `app/processos/[id]/page.tsx`, condicionar "Despachar", "Devolver" e toggle de sigilo a `perfil === "servidor"`. Aceite: Admin vê o processo mas sem controles de ação.
- [x] 9.3 (altera superfície de despacho — obrigatório) E2E Playwright: Admin autenticado abre Processos e o detalhe, e nenhum controle de ação (Novo/Despachar/Devolver/sigilo) é exibido. Aceite: teste passa.

## 10. Frontend — polimento das tabelas de admin

- [x] 10.1 Refinar o design das tabelas de `admin/usuarios` e `admin/unidades` (espaçamento, zebra/hover, cabeçalho). Aceite: consistente entre as duas telas.
- [x] 10.2 Substituir as ações em texto por ícones com `aria-label` e `title` em ambas as telas (Editar, Desativar, Reativar, Transferir unidade, Unidades geridas, Resetar senha, Auditoria, Desativar usuário). Aceite: cada ícone tem rótulo acessível.
- [x] 10.3 Ajustar/revisar testes RTL existentes que localizam ações por texto para usar `aria-label`/role. Aceite: `pnpm --filter @setes/web test` verde.

## 11. Verificação final

- [x] 11.1 Rodar `uv run ruff check .`, `uv run pytest`, `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test`, `pnpm gen:types:check`. Aceite: tudo verde.
