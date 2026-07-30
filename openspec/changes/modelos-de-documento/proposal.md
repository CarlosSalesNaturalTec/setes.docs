## Why

Hoje todo processo começa do zero: o servidor digita o assunto e anexa arquivos
produzidos fora do sistema. Na avaliação da primeira entrega o cliente pediu
**padronização de documentos "para evitar retrabalho na digitação e abertura de
novos processos"** (`docs/Ajustes SETES DOCS.pdf`).

A ideia é um catálogo de **Modelos** — textos pré-formatados com lacunas — que o
servidor escolhe na abertura do processo e completa com as informações reais do
caso, em vez de redigir cada requerimento, ofício ou memorando do início.

O documento resultante **é um documento do processo**, não um campo de texto:
tramita com o processo, é baixado como anexo, entra na retenção e na purga, e —
decisão do cliente — prepara o terreno para a assinatura digital da Fase 2
(Épico 4), que assina arquivos, não linhas de banco.

Este é o **quarto** dos seis changes dos ajustes pós-avaliação e o único
**independente** dos demais: não toca tramitação, quadro nem estrutura
organizacional, podendo ser desenvolvido em paralelo.

## What Changes

- **Novo catálogo de Modelos**, com CRUD restrito ao Administrador: nome,
  categoria, tipo (requerimento, ofício, memorando, despacho, parecer, nota
  técnica, relatório, ata, contrato, outro), descrição e **conteúdo formatado**.
- **Editor de texto formatado** limitado a negrito, itálico, sublinhado,
  alinhamento e listas — exatamente a formatação pedida pelo cliente. O conteúdo
  é armazenado como HTML **sanitizado** contra um conjunto restrito de tags.
- **Lacunas são texto livre**, não campos estruturados: o modelo traz marcações
  visuais que o servidor substitui digitando (decisão do cliente). Não há parser
  de placeholders nem formulário dinâmico gerado a partir do modelo.
- **Geração de documento na abertura do processo**: ao criar um processo, o
  servidor pode escolher um modelo, editar o texto livremente e salvar. O texto é
  **renderizado em PDF** e anexado ao processo pelo pipeline de anexos já
  existente — mesma validação, mesmo armazenamento, mesmo download, mesma
  retenção, mesmo soft-delete.
- **Documento gerado é imutável após salvo**, como qualquer anexo. Corrigir o
  texto significa remover o documento (soft-delete já reversível pelo
  Administrador) e gerar um novo.
- **Proveniência registrada**: o documento gerado guarda referência ao modelo que
  o originou, permitindo auditar quais modelos estão em uso.

## Capabilities

### New Capabilities

- `modelos-documento`: catálogo de modelos de documento (CRUD do Administrador,
  tipos, conteúdo formatado, desativação sem exclusão) e geração de documento de
  processo a partir de um modelo.

### Modified Capabilities

- `gestao-documental`: o acervo de documentos passa a incluir documentos
  **gerados pelo sistema** a partir de modelo, além dos enviados por upload —
  sujeitos às mesmas regras de formato, armazenamento, download, remoção,
  retenção e purga, e com a proveniência do modelo registrada.

## Impact

- **Dependências**: requer `gestao-documental` (arquivado). **Não** depende de
  `setores-e-cadastro-usuario`, `tramitacao-manual` nem `kanban-por-servidor` —
  pode ser desenvolvido em paralelo a eles.
- **Tabelas PostgreSQL**: **nova** tabela `modelo_documento` (`id` uuid PK,
  `nome`, `categoria`, `tipo` enum, `descricao`, `conteudo` text, `ativo`,
  `criado_por_id` FK→`usuario`, `criado_em`); **alterada** `documento`
  (+`modelo_id` FK→`modelo_documento`, nullable — nulo para anexos enviados por
  upload); **novo** enum `tipo_modelo_documento`.
- **Migrations**: `0026_modelo_documento`.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager. **Nenhum bucket
  novo** — o PDF gerado vai para o bucket de documentos já existente, pela mesma
  chave opaca.
- **Dependência nova de runtime**: biblioteca de geração de PDF em Python puro
  (`fpdf2`), escolhida por cobrir o subconjunto de formatação pedido sem exigir
  bibliotecas de sistema (cairo/pango) que inchariam a imagem do Cloud Run.
  Adicionada a `apps/api/pyproject.toml`.
- **Backend** (`apps/api`): novo `routers/modelos.py`, `schemas/modelos.py`,
  `services/modelo_documento.py` (CRUD + sanitização + render PDF);
  `services/documento.py` (caminho de criação a partir de bytes gerados,
  reutilizando validação e armazenamento); `db/models.py`; `db/dev_reset.py`.
- **Contrato**: `packages/api-types/{openapi.json,schema.ts}` regenerados
  (`pnpm gen:types`; CI `gen:types:check`).
- **Frontend** (`apps/web`): nova rota `/admin/modelos` (catálogo + editor),
  `app/processos/novo/page.tsx` (seleção de modelo e edição do texto),
  componente de editor de texto formatado, `lib/api.ts`.
- **LGPD**: o conteúdo preenchido pelo servidor **pode conter dados pessoais de
  interessados** (nome, CPF/CNPJ, endereço) — é justamente o caso de uso
  ("nome do solicitante, número de documento"). O documento gerado herda
  integralmente o tratamento já definido para anexos: armazenamento no bucket
  regional com acesso restrito, soft-delete com retenção, purga física ao fim da
  retenção e ausência na consulta pública. O **modelo em si** NÃO SHALL conter
  dados pessoais reais — apenas marcações de lacuna. Por tocar dados pessoais e
  documentos, o change **exige** testes automatizados pytest e, por alterar o
  fluxo de documentos, **exige** teste E2E Playwright (config OpenSpec
  vinculante).
- **PRD**: `docs/PRD.md` Épico 2 (US 2.1 — abertura com modelo) e Épico 3
  (documentos gerados pelo sistema) atualizados.
