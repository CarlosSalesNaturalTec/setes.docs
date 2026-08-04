## Why

O sistema é hoje apresentado ao usuário como **SETES.DOCS** — nome que mistura o
produto e o cliente numa string só. O cliente pediu a separação: o produto passa a
se chamar **Despapelize**, e **SETES** passa a aparecer como *subtítulo*, no papel
de cliente/instituição, não como parte do nome do sistema.

A mudança é de apresentação e comunicação, não de comportamento. Ela é feita agora,
antes da produção de material de apoio ao usuário (change `manual-mkdocs`), para que
o manual já nasça com o nome definitivo em vez de precisar ser reescrito.

## What Changes

- **Nome exibido do produto passa a ser "Despapelize"** em toda a interface: aba do
  navegador (`metadata.title`), tela de Login, sidebar do shell autenticado, tela de
  inicialização (`/setup`), página inicial e tela de primeiro acesso.
- **"SETES" passa a ser exibido como subtítulo da marca**, imediatamente abaixo ou ao
  lado do nome do produto. Na sidebar ele **substitui** o subtítulo atual
  `"SISTEMA ELETRÔNICO"`; na tela de Login ele é uma linha nova entre o título e o
  subtítulo existente `"Acesse sua conta"`, que permanece.
- **Assuntos de e-mail transacional** passam a usar "Despapelize" no lugar de
  "SETES.DOCS" — alerta de tentativas de login, recuperação de senha, redefinição
  solicitada pelo Administrador, boas-vindas/ativação de conta e aviso de sistema
  inicializado. O corpo da mensagem de boas-vindas também cita o nome.
- **Título da aplicação FastAPI** passa a ser "Despapelize API". Isso altera o
  contrato OpenAPI e **exige** `pnpm gen:types` com commit de `packages/api-types`,
  sob pena de o job `types-drift` do CI reprovar.
- **Documentação de projeto** (`docs/PRD.md`, `docs/manual-usuario.md`,
  `docs/primeiro-acesso-producao.md`, `README.md`, `CLAUDE.md`) passa a usar o nome
  novo, registrando "SETES" como cliente.
- **Fora do escopo deste change, por decisão explícita**: o nome do repositório
  (`setes.docs`), o caminho do diretório de trabalho, o ID do projeto GCP e os nomes
  de recursos Terraform. Renomear recurso em Terraform implica destroy/create de
  infraestrutura de produção — é uma decisão de outra natureza, e as descrições em
  `infra/variables.tf` e `infra/artifact_registry.tf` são texto livre sem efeito
  operacional. **Nenhum recurso de infraestrutura é tocado.**

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a apresentação da marca já é coberta por
`identidade-visual`; o que muda é o conteúdo textual da marca. -->

### Modified Capabilities

- `identidade-visual`: o título exibido no Login e na sidebar passa de "SETES.DOCS"
  para "Despapelize"; a marca passa a exibir "SETES" como subtítulo de cliente, e o
  subtítulo "SISTEMA ELETRÔNICO" da sidebar deixa de existir.

## Impact

- **Dependências**: nenhuma. Não depende de change anterior e não bloqueia
  `ajustes-ui-admin` (que pode correr em paralelo). **Bloqueia `manual-mkdocs`** —
  o manual deve ser escrito já com o nome novo.
- **Tabelas PostgreSQL**: **nenhuma** tabela nova ou alterada.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket novo
  no Cloud Storage. Nenhum segredo existente é renomeado.
- **Backend** (`apps/api`): `app/main.py` (docstring e `FastAPI(title=…)`),
  `app/routers/auth.py`, `app/routers/usuarios.py`, `app/routers/setup.py` (assuntos
  e corpo de e-mail). Nenhuma rota, schema ou regra de negócio muda.
- **Contrato**: `packages/api-types/openapi.json` muda (campo `info.title`) e **deve
  ser regenerado e commitado**. `schema.ts` provavelmente não muda, mas o
  `gen:types:check` compara o snapshot inteiro.
- **Frontend** (`apps/web`): `app/layout.tsx`, `app/login/page.tsx`, `app/page.tsx`,
  `app/setup/page.tsx`, `app/primeiro-acesso/[token]/primeiro-acesso-client.tsx`,
  `components/protected-shell.tsx`.
- **Testes**: qualquer asserção Vitest/Playwright sobre o texto "SETES.DOCS" precisa
  acompanhar. `apps/web/e2e/01-setup-login.spec.ts` é o candidato mais provável.
- **Infra** (`infra/`): **nenhuma alteração de recurso**. As descrições textuais em
  `variables.tf` e `artifact_registry.tf` podem ser atualizadas por higiene, sem
  efeito em `terraform plan`.
- **LGPD**: nenhum impacto. Nenhum dado pessoal é coletado, exibido, retido ou
  anonimizado de forma diferente — a mudança é exclusivamente de rótulo de marca.
- **PRD**: `docs/PRD.md` — atualizar o nome do produto e registrar SETES como cliente.
