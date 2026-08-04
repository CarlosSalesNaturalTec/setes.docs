## 1. Backend — marca e contrato

- [x] 1.1 Criar a constante de prefixo de assunto de e-mail no backend (D2), junto do
  módulo que já centraliza o envio. **Aceite**: existe um único ponto que define o
  prefixo "Despapelize"; nenhum novo módulo de constantes é criado.
- [x] 1.2 Substituir os cinco assuntos de e-mail pela composição com a constante:
  `routers/auth.py:95` (alerta de tentativas de login), `routers/auth.py:200`
  (recuperação de senha), `routers/usuarios.py:108` (redefinição pelo Administrador),
  `routers/usuarios.py:192` (boas-vindas/ativação) e `routers/setup.py:72` (sistema
  inicializado). **Aceite**: `grep -rn "SETES.DOCS" apps/api/app/routers/` retorna
  zero.
- [x] 1.3 Atualizar o corpo do e-mail de boas-vindas (`routers/usuarios.py:194`), que
  cita o nome do sistema no texto da mensagem. **Aceite**: a mensagem lê "Despapelize"
  e permanece gramaticalmente correta.
- [x] 1.4 Atualizar `app/main.py` — docstring do módulo e `FastAPI(title="Despapelize
  API")`. **Aceite**: `uv run python scripts/export_openapi.py` produz `info.title`
  igual a "Despapelize API".
- [x] 1.5 **Regenerar o contrato**: `pnpm gen:types` e commitar `packages/api-types`
  (D3). **Aceite**: `pnpm gen:types:check` passa localmente; `openapi.json` reflete o
  título novo. Sem esta tarefa o job `types-drift` do CI reprova.
- [x] 1.6 Rodar `uv run ruff check .` e `uv run pytest` em `apps/api`. **Aceite**:
  lint limpo e suíte verde; nenhum teste afirmava o nome antigo, ou os que afirmavam
  foram atualizados.

## 2. Frontend — constante de marca e telas

- [x] 2.1 Criar o módulo de marca em `apps/web/lib/` exportando o nome do produto
  ("Despapelize") e o subtítulo de cliente ("SETES") como constantes (D1).
  **Aceite**: nenhuma tela precisa repetir as strings literais.
- [x] 2.2 Atualizar `app/layout.tsx` (`metadata.title`) consumindo a constante.
  **Aceite**: a aba do navegador exibe "Despapelize". Atenção — é a única superfície
  que não é JSX e a mais fácil de esquecer.
- [x] 2.3 Atualizar `app/login/page.tsx`: título "Despapelize" e **linha nova** de
  subtítulo de cliente "SETES" entre o `<h1>` e o "Acesse sua conta", que permanece
  (D4). **Aceite**: as três linhas aparecem na ordem título → cliente → chamada de
  ação, com hierarquia visual decrescente.
- [x] 2.4 Atualizar `components/protected-shell.tsx`: nome do produto no lugar de
  "SETES.DOCS" e **substituição** do subtítulo "Sistema Eletrônico" por "SETES" (D4).
  **Aceite**: o subtítulo antigo não sobrevive em nenhuma forma; o layout de 240px da
  sidebar não quebra.
- [x] 2.5 Atualizar as três telas restantes: `app/page.tsx`, `app/setup/page.tsx` e
  `app/primeiro-acesso/[token]/primeiro-acesso-client.tsx`. **Aceite**: todas
  consomem a constante do módulo de marca.
- [x] 2.6 Rodar `pnpm --filter @setes/web typecheck` e `pnpm --filter @setes/web test`.
  **Aceite**: typecheck limpo e Vitest verde.

## 3. Testes

- [x] 3.1 Varrer `apps/web/e2e/` e os `*.test.tsx` por asserções sobre "SETES.DOCS" e
  atualizá-las — `e2e/01-setup-login.spec.ts` é o candidato mais provável.
  **Aceite**: `grep -rn "SETES.DOCS" apps/web/e2e apps/web/**/*.test.tsx` retorna
  zero.
- [x] 3.2 Acrescentar ou estender asserção que cubra o subtítulo de cliente "SETES" no
  Login e na sidebar. **Aceite**: um teste falharia se o subtítulo fosse removido —
  hoje nada o protegeria.
- [x] 3.3 Rodar a suíte Playwright (`cd apps/web && pnpm test:e2e`). **Aceite**: suíte
  verde. Lembrar que ela não pode rodar em paralelo com o pytest (mesmo banco).

## 4. Documentação

- [x] 4.1 Atualizar `docs/PRD.md` — nome do produto e registro de SETES como cliente.
  **Aceite**: o PRD não contém mais "SETES.DOCS" como nome do sistema.
- [x] 4.2 Atualizar `docs/manual-usuario.md`, `docs/primeiro-acesso-producao.md`,
  `README.md` e `CLAUDE.md`. **Aceite**: nome novo em todos; nenhuma instrução
  operacional alterada por engano junto com o rename.
- [x] 4.3 Atualizar por higiene as descrições em `infra/variables.tf` e
  `infra/artifact_registry.tf`. **Aceite**: `terraform plan` não reporta nenhuma
  alteração de recurso — são campos `description`, sem efeito operacional.
- [x] 4.4 **Não** editar `openspec/changes/archive/**` nem `docs/history/**` (D5).
  **Aceite**: `git diff --stat` não lista nenhum arquivo sob esses caminhos.

## 5. Fechamento

- [x] 5.1 Verificação final: `grep -rn "SETES.DOCS" apps/ packages/ infra/` retorna
  **zero** ocorrências. **Aceite**: saída vazia — é o portão de fechamento do change.
- [x] 5.2 Conferir que nenhuma migration foi criada e que `git diff` não toca
  `apps/api/migrations/`, `db/models.py` nem nenhum recurso Terraform. **Aceite**:
  o diff é exclusivamente texto de apresentação, e-mail, docs e o snapshot de tipos.
