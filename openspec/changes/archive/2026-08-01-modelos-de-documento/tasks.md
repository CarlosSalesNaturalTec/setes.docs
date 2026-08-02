## 1. Migration e schema (antes de endpoint/UI — design D6, D7, D8)

- [x] 1.1 Migration `0026_modelo_documento`: criar o enum `tipo_modelo_documento` (requerimento, oficio, memorando, despacho, parecer, nota_tecnica, relatorio, ata, contrato, outro); criar a tabela `modelo_documento` (`id` uuid PK, `nome` varchar(200), `categoria` varchar(200), `tipo` enum, `descricao` varchar(500) nullable, `conteudo` text, `ativo` boolean NOT NULL default true, `criado_por_id` FK→`usuario`, `criado_em` timestamptz); adicionar `documento.modelo_id` (FK→`modelo_documento`, nullable). `down_revision` = última revision vigente no momento do merge. Aceite: upgrade/downgrade limpos; `ruff check migrations/` verde; docstring citando `Change modelos-de-documento (design.md D1, D6, D7, D8)`.
- [x] 1.2 `db/models.py`: classe `ModeloDocumento`, enum `TipoModeloDocumento` e `Documento.modelo_id`. Comentários citando `(D1)`, `(D6)`, `(D7)`. Aceite: modelos batem exatamente com a migration.
- [x] 1.3 `db/dev_reset.py`: incluir `modelo_documento` na ordem de truncamento (depois de `documento`, pela FK). Aceite: `POST /internal/dev/reset` limpa a tabela sem violar FK.
- [x] 1.4 `apps/api/pyproject.toml`: adicionar `fpdf2` às dependências de runtime (D2). Aceite: `uv sync` instala; imagem do Cloud Run continua sem bibliotecas de sistema adicionais.

## 2. Backend — sanitização e render (design D2, D3)

- [x] 2.1 `services/modelo_documento.py::sanitizar_html`: whitelist estrita de tags (`p`, `br`, `b`, `strong`, `i`, `em`, `u`, `ul`, `ol`, `li`) e do atributo `align`, descartando silenciosamente tudo o mais. Aplicada na gravação do modelo e na geração do documento. Aceite: `<script>`, `on*`, `style`, `iframe` e atributos arbitrários são removidos.
- [x] 2.2 `services/modelo_documento.py::renderizar_pdf`: HTML sanitizado → bytes PDF via `fpdf2.write_html`, preservando negrito, itálico, sublinhado, alinhamento e listas. Aceite: bytes começam com a assinatura `%PDF`.
- [x] 2.3 Testes pytest de sanitização e render (obrigatórios — segurança): script e handlers removidos; tags permitidas preservadas; PDF gerado passa na validação de formato e no *sniffing* de MIME de `services/documento.py`.

## 3. Backend — catálogo de modelos (design D5, D6, D7)

- [x] 3.1 `schemas/modelos.py`: `ModeloResponse`, `CriarModeloRequest`, `EditarModeloRequest`, com `tipo` restrito ao enum e `categoria` como texto livre. Aceite: OpenAPI expõe os schemas.
- [x] 3.2 `services/modelo_documento.py`: listar (com filtro `ativo`), obter, criar, editar, desativar e reativar. **Nenhum caminho de exclusão física** — um modelo já utilizado é referenciado por `documento.modelo_id`. Aceite: nenhuma rota ou método de delete existe.
- [x] 3.3 `routers/modelos.py`: rotas de CRUD restritas ao Administrador via `require_perfil`; leitura do catálogo liberada a Servidor e Gestor (precisam escolher modelo). Aceite: escrita por não-Administrador retorna 403 com registro em `log_seguranca`.
- [x] 3.4 Testes pytest do catálogo (obrigatórios): CRUD completo; desativação preserva documentos já gerados; modelo inativo fora do catálogo de escolha; **acesso negado**: Servidor e Gestor recebem 403 em cada rota de escrita, com log.

## 4. Backend — geração do documento (design D1, D5, D6)

- [x] 4.1 `services/documento.py`: caminho de criação a partir de **bytes gerados**, reutilizando integralmente a validação de formato, o *sniffing*, o cálculo de `hash_sha256`, a gravação no bucket e a resolução de `nome_exibicao`. **Sem** enfraquecer a whitelist. Aceite: o documento gerado é indistinguível de um anexo enviado, exceto por `modelo_id`.
- [x] 4.2 `routers/documentos.py`: `POST /processos/{id}/documentos/gerar` recebendo `modelo_id` e `conteudo`, aplicando a autorização por unidade já existente (`_exigir_acesso_ao_processo`). Aceite: nenhuma alteração em `security/autorizacao.py`.
- [x] 4.3 Garantir que o documento gerado segue as regras existentes de soft-delete, bloqueio de remoção após a saída do processo da unidade, retenção e purga física. Aceite: nenhuma exceção introduzida para documentos gerados.
- [x] 4.4 Testes pytest de geração (obrigatórios — dados pessoais e documentos): documento gerado aparece na lista de anexos e é baixável; `modelo_id` registrado; soft-delete e restauração funcionam; purga remove o objeto do bucket; conteúdo com dados pessoais não vaza para a consulta pública; **acesso negado**: gerar documento em processo de outra unidade é rejeitado com log.

## 5. Contrato

- [x] 5.1 `pnpm gen:types` e commit de `packages/api-types/{openapi.json,schema.ts}`. Aceite: `pnpm gen:types:check` verde.

## 6. Frontend — catálogo e editor

- [x] 6.1 Componente de editor de texto formatado com barra restrita a negrito, itálico, sublinhado, alinhamento e listas, emitindo HTML compatível com a whitelist do D3. Aceite: nenhum controle da barra produz tag fora da whitelist.
- [x] 6.2 Nova rota `/admin/modelos`: listagem com filtro por tipo e situação, formulário de criação/edição (nome, categoria, tipo, descrição, conteúdo no editor), desativar/reativar. Advertência na tela de que o modelo não deve conter dados pessoais reais, apenas marcações de lacuna. Aceite: nenhuma ação de exclusão na UI.
- [x] 6.3 `app/processos/novo/page.tsx`: opção de escolher um modelo ativo do catálogo; ao escolher, o editor carrega o conteúdo do modelo para edição livre; ao salvar o processo, o texto é enviado para geração do documento. Aceite: criar processo sem modelo continua funcionando exatamente como antes.
- [x] 6.4 Destaque visual das lacunas remanescentes no editor, como lembrete, **sem** bloquear a geração (D4). Aceite: gerar com lacuna pendente é permitido e emite apenas aviso.
- [x] 6.5 Testes Vitest: editor produz apenas tags da whitelist; seleção de modelo carrega o conteúdo; criação sem modelo preservada; destaque de lacuna não bloqueia o envio.

## 7. Testes E2E Playwright (obrigatório — altera fluxo de documentos)

- [x] 7.1 Cenário: Administrador cadastra um modelo de "Requerimento" com lacunas → Servidor cria processo escolhendo esse modelo, substitui as lacunas e salva → o PDF aparece na lista de anexos do processo e é baixável → o Servidor remove o documento e o Administrador o restaura na área de documentos removidos. Aceite: `pnpm test:e2e` verde.

## 8. Documentação mestre

- [x] 8.1 `docs/PRD.md`: Épico 2 (US 2.1 — abertura de processo a partir de modelo) e Épico 3 (documentos gerados pelo sistema, sujeitos às mesmas regras dos anexos). Aceite: PRD sem contradição com as specs deste change.
- [x] 8.2 `docs/manual-usuario.md`: nova seção de Modelos (cadastro pelo Administrador, uso na abertura de processo, orientação sobre lacunas e sobre não incluir dados pessoais no modelo). Aceite: descrições coerentes com a UI final.
