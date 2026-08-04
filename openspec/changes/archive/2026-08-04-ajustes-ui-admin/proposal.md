## Why

Três ajustes de interface pedidos pelo cliente, todos nas telas administrativas e
todos de apresentação — nenhum altera regra de negócio, contrato ou banco:

1. **Modelos de documento** empilha numa única página o formulário de cadastro, os
   filtros e a lista de modelos. O formulário é longo (inclui o editor formatado de
   conteúdo), então quem só quer consultar o catálogo precisa rolar por ele toda vez.
2. **Tipos de processo** exibe cada tipo como um card com um mini-formulário de prazo
   de anonimização embutido. Com poucos tipos já fica verboso, e comparar prazos entre
   tipos — que é o uso real da tela — exige varrer cards verticalmente.
3. A aba **"Documentos assinados"** de "Meu Perfil" informa que a assinatura digital
   virá em fase futura, mas não diz ao usuário o que ele pode fazer a respeito. Como
   o certificado digital ICP-Brasil é obtido **fora do sistema**, junto a uma
   Autoridade Certificadora, e leva tempo, o cliente pediu que a mensagem oriente a
   solicitá-lo desde já.

Agrupados num change só por serem o mesmo tipo de trabalho — relayout de tela admin,
mesma camada, mesmo tipo de teste — e por não terem dependência entre si nem com
nenhum outro change.

## What Changes

- **Modelos de documento (`/admin/modelos`) passa a ter duas abas**: **"Novo modelo"**
  (ficha de cadastro) e **"Modelos cadastrados"** (filtros + lista). Reusa o componente
  `components/tabs.tsx` já existente — criado em `perfil-em-abas` (D4), com semântica
  ARIA e navegação por setas — sem componente novo.
- **A aba ativa é refletida na URL** por query string, seguindo o mesmo padrão de
  "Meu Perfil": recarregar ou compartilhar o endereço preserva a aba; valor ausente
  ou inválido recai na aba padrão.
- **Após cadastrar um modelo com sucesso, a interface alterna para a aba de listagem**,
  dando confirmação visual de que o modelo entrou no catálogo — em vez de permanecer
  numa ficha vazia sem sinal do resultado.
- **Tipos de processo (`/admin/tipos-processo`) passa a listar os tipos já cadastrados
  em tabela**, com colunas Nome, Prazo de anonimização LGPD (anos) e a ação de salvar
  o prazo. O formulário de cadastro de novo tipo permanece acima da tabela, inalterado.
- **A edição de prazo continua inline, por linha**, com o mesmo comportamento atual:
  campo numérico, mínimo 1 ano, salvamento individual, erro exibido junto da linha.
  **Relayout puro** — não são introduzidas edição de nome, desativação nem exclusão de
  tipo de processo, que não existem hoje.
- **A mensagem da aba "Documentos assinados"** passa a ser: *"A assinatura digital de
  documentos será disponibilizada em uma fase futura do produto. Para se preparar,
  solicite seu Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora."*
  A aba continua **sem** botão de assinatura, campo de certificado ou qualquer controle
  — o texto orienta uma ação **externa ao sistema** e não sugere funcionalidade
  disponível. **O Épico 4 permanece fora do escopo e não é retomado por este change.**

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: as três telas já são cobertas por capabilities
existentes; o que muda é a organização e o texto. -->

### Modified Capabilities

- `modelos-documento`: a tela de administração do catálogo passa a ser organizada em
  duas abas (cadastro e listagem), com a aba ativa refletida na URL e alternância
  automática para a listagem após cadastro bem-sucedido.
- `tipos-processo`: os tipos já cadastrados passam a ser apresentados em tabela, com o
  prazo de anonimização editável por linha.
- `gestao-usuarios`: a mensagem da aba "Documentos assinados" passa a orientar a
  solicitação do Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora,
  mantendo a proibição de qualquer controle de assinatura na aba.

## Impact

- **Dependências**: nenhuma. Independente de `renomear-sistema-despapelize` — pode
  correr em paralelo. Precede `manual-mkdocs`, que documenta essas telas.
- **Tabelas PostgreSQL**: **nenhuma** tabela nova ou alterada.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket novo no
  Cloud Storage.
- **Backend** (`apps/api`): **nenhuma alteração**. Os três ajustes consomem endpoints
  que já existem, com os mesmos payloads.
- **Contrato**: **nenhuma regeneração de tipos** — o contrato do FastAPI não muda,
  `packages/api-types` permanece intacto e o job de drift do CI segue verde sem ação.
- **Frontend** (`apps/web`): `app/admin/modelos/page.tsx`,
  `app/admin/tipos-processo/page.tsx`, `app/perfil/page.tsx`. `components/tabs.tsx` é
  **reusado sem alteração**.
- **Testes**: `app/perfil/perfil-abas.test.tsx` afirma o texto antigo da aba e precisa
  acompanhar. `e2e/16-modelos-documento.spec.ts` navega a tela de modelos e precisa
  selecionar a aba antes de interagir com o formulário ou a lista.
- **LGPD**: nenhuma coleta nova de dado pessoal e nenhuma mudança de visibilidade. O
  aviso de não incluir dados pessoais em modelo permanece exibido na ficha de cadastro.
  O prazo de anonimização por tipo de processo continua com a mesma semântica — só
  muda a apresentação do campo.
- **PRD**: `docs/PRD.md` US 1.5 (texto da aba de documentos assinados) e as US de
  administração de modelos e tipos de processo — registrar a nova organização de tela.
