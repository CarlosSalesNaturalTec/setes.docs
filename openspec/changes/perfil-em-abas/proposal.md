## Why

A tela "Meu Perfil" empilha verticalmente quatro conteúdos distintos: os dados
do usuário, o formulário de troca de senha, a lista de processos em que atuou e
a lista de documentos assinados. Com os campos novos vindos de
`setores-e-cadastro-usuario` (telefone, cargo, chefia direta, setor), a página
fica ainda mais longa e exige rolagem para alcançar qualquer seção específica.

Na avaliação da primeira entrega o cliente pediu a separação em abas:
*"Meu Perfil / Separar em Tabs: Meu perfil, Trocar Senha, Processos em que atuei,
Documentos Assinados"* (`docs/Ajustes SETES DOCS.pdf`).

Este é o **quinto** dos seis changes dos ajustes pós-avaliação. É o menor de
todos: **reorganização de interface, sem alteração de contrato, de dados ou de
regra de negócio**. Não depende de nenhum outro change e pode ser feito a
qualquer momento — embora ganhe sentido depois de `setores-e-cadastro-usuario`,
que é quem adiciona os campos novos à aba de perfil.

## What Changes

- **Quatro abas** na tela "Meu Perfil", substituindo o empilhamento vertical:
  **Meu perfil**, **Trocar senha**, **Processos em que atuei** e **Documentos
  assinados**. Todo o conteúdo já existente é preservado, apenas redistribuído.
- **A aba "Meu perfil"** exibe os dados do usuário — incluindo os campos
  acrescentados por `setores-e-cadastro-usuario` (unidade, setor, cargo,
  telefone, chefia direta) — e mantém a edição do próprio nome, sem alteração de
  regra.
- **A aba "Documentos assinados" permanece um placeholder vazio**, com mensagem
  explicando que a assinatura digital pertence à Fase 2. O Épico 4 está
  formalmente fora do MVP (decisão de 2026-07-27) e **este change não o retoma**.
- **A aba ativa é preservada na URL** (query string), de modo que recarregar a
  página ou compartilhar o link mantenha a aba escolhida.
- **Navegação acessível por teclado**, com papéis ARIA de abas.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: "Meu Perfil" já é coberta por `gestao-usuarios`;
o que muda é a organização da tela. -->

### Modified Capabilities

- `gestao-usuarios`: a tela "Meu Perfil" passa a ser organizada em quatro abas,
  com a aba ativa refletida na URL e navegação acessível por teclado; a aba de
  documentos assinados permanece placeholder da Fase 2.

## Impact

- **Dependências**: nenhuma dependência técnica. Recomenda-se implementar após
  `setores-e-cadastro-usuario`, que é quem adiciona os campos exibidos na aba de
  perfil — caso contrário a aba nasce sem eles e precisa ser revisitada.
- **Tabelas PostgreSQL**: **nenhuma** tabela nova ou alterada.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket
  novo no Cloud Storage.
- **Backend** (`apps/api`): **nenhuma alteração**. Os dados de todas as quatro
  abas já são servidos pelo endpoint de "Meu Perfil" existente.
- **Contrato**: **nenhuma regeneração de tipos** — o contrato do FastAPI não
  muda, logo `packages/api-types` permanece intacto e o job de drift do CI segue
  verde sem ação.
- **Frontend** (`apps/web`): `app/perfil/page.tsx` (reorganização em abas),
  possível componente de abas reutilizável em `components/`.
- **LGPD**: nenhuma coleta nova de dado pessoal e nenhuma mudança de
  visibilidade — os mesmos dados, já exibidos ao próprio titular, apenas mudam de
  lugar na tela. Nenhum dado passa a ser exposto a terceiros.
- **PRD**: `docs/PRD.md` US 1.5 — registrar a organização da tela em abas.
