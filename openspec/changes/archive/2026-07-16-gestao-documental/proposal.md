## Why

Os Épicos 1, 2 e 7 estão completos, mas o **Épico 3 — Gestão Documental está em
zero**: não existe entidade `documento`, nenhuma tabela, nenhum uso do Cloud
Storage por código de negócio. Sem anexos, um processo é só metadado — não há
onde colocar o parecer, o ofício, a nota fiscal que justificam a tramitação. O
Épico 3 é também **pré-requisito rígido do Épico 4 (Assinatura)** — só se assina
um documento — e da **US 8.7 (restauração de documento removido)**, além de
completar a promessa do Épico 9 (o auditor "visualiza todos os documentos
anexados"). É o próximo épico central e o que mais desbloqueia.

Este change entrega a **fatia A, hermética**: US 3.1 (anexar, listar, remover
por soft-delete) e US 3.2 (visualizar inline, baixar). A **restauração de
documento removido (US 8.7)** fica **fora**, como change irmão futuro — mesmo
padrão de `arquivamento-automatico → sigilo-de-processo` —, porque a restauração
só faz sentido depois que o soft-delete existir. A infra já está pronta:
`bootstrap-infraestrutura` (arquivado) provisionou o bucket
`${project_id}-documentos` (`infra/storage.tf`) com residência no Brasil,
`public_access_prevention = enforced` e IAM `storage.objectAdmin` para a `sa-jobs`
(já comentado em `infra/iam.tf` como necessário à "purga física de documentos
soft-deleted > 30d").

## What Changes

- **US 3.1 Cen.1 — Anexar documento**: Servidor com acesso ao processo (da
  unidade atual) faz upload de um arquivo (`PDF`, `DOC`, `DOCX`, `JPG`, `PNG`,
  até 20 MB). O conteúdo vai para o bucket; os metadados (nome original, tipo,
  tamanho, autor, data) viram uma linha em `documento` e o arquivo aparece na
  lista de anexos do processo.
- **US 3.1 Cen.2 / 2b — Rejeição de formato/tamanho/vazio**: formato não
  permitido (ex.: `.exe`) → "Formato de arquivo não permitido"; > 20 MB →
  "Arquivo excede o tamanho máximo de 20 MB"; 0 byte → "Não é possível anexar
  arquivo vazio…". Nada é gravado no bucket nem no banco.
- **US 3.1 Cen.5 — Nome duplicado**: anexar `parecer.pdf` quando já existe
  `parecer.pdf` **não sobrescreve** — o novo é renomeado para `parecer (1).pdf`
  (e `(2)`, `(3)`… conforme necessário) na lista; o objeto no bucket usa chave
  única independente do nome exibido. Ambos coexistem.
- **US 3.1 Cen.3 — Remover (soft-delete)**: com o processo **ainda não
  despachado**, o Servidor remove um anexo mediante confirmação; o documento sai
  da lista visível, o arquivo é **preservado em retenção por 30 dias** (soft-
  delete lógico no banco: `removido_em`, `removido_por_id`, `purgar_em`
  congelado = `removido_em + 30d`), e a **exclusão lógica é registrada como
  evento imutável no histórico** do processo (`tramitacao`, novo tipo
  `remover_documento`).
- **US 3.1 Cen.4 / 4c — Bloqueio de remoção após despacho**: se o processo já
  foi despachado (status `Em Tramitação`, `Concluído` ou `Arquivado`), a remoção
  é negada — "Não é possível remover documentos de um processo que já foi
  despachado".
- **US 3.1 Cen.4b — Exceção pós-devolução**: um processo devolvido está
  novamente na unidade com status `Em Tramitação`; ainda assim a remoção é
  **permitida** para QUALQUER documento (anexado antes ou depois da devolução),
  porque a unidade atual é a "dona" corrente do processo e o próximo despacho
  volta a travar (Cen.4c). A regra efetiva não é "pelo status", é "o processo
  está sob custódia da minha unidade **e** ainda não foi despachado a partir
  desta custódia" — detalhado no design.
- **US 3.2 Cen.1 — Visualizar inline**: `PDF` e imagens (`JPG`/`PNG`) abrem para
  visualização na própria tela do processo.
- **US 3.2 Cen.2 — Baixar**: qualquer anexo é baixado mantendo formato e nome
  originais.
- **US 3.2 Cen.3 — DOC/DOCX**: clicar sobre um `DOC`/`DOCX` inicia download
  automático com o aviso "Formato não permite visualização inline — o download
  será iniciado".
- **Purga física após retenção (novo passo do job diário)**: `job-manutencao-
  diaria` ganha um segundo passo — remover fisicamente do bucket e do banco os
  documentos cujo `purgar_em` já expirou. Idempotente e retomável, reusando o
  contrato já provado em `rotinas-agendadas` (seleção por estado atual). A
  **restauração dentro dos 30 dias (US 8.7) é change futuro** — este passo só
  fecha a ponta da retenção.

**Fora de escopo deste change:**
- **US 8.7 — Restauração de documento removido** (área "Documentos Removidos" do
  Admin, ação "Restaurar", evento `restaurar_documento`) → change irmão futuro.
- **Épico 4 — Assinatura Digital** (assinar/verificar; o `hash` do documento é
  gravado aqui como preparação de integridade, mas nenhuma assinatura é aplicada).
- **Notificações de anexação** (Épico 5), **dashboard** (Épico 6), **auditoria**
  (Épico 9), **anonimização LGPD de conteúdo** (Épico 10).
- **Versionamento de documentos** — fora do MVP por decisão de escopo do PRD
  (anexos são arquivos simples).

## Capabilities

### New Capabilities
- `gestao-documental`: a entidade `documento` e seu ciclo de vida ponta-a-ponta —
  anexar (com validação de formato/tamanho/vazio e renomeação de duplicados),
  listar, visualizar inline, baixar, remover por soft-delete (com bloqueio pós-
  despacho e exceção pós-devolução), e a purga física após 30 dias de retenção.
  É a dona do armazenamento no Cloud Storage e das regras de acesso ao conteúdo
  por unidade/perfil. Assinatura (Épico 4) e restauração (US 8.7) serão
  **consumidoras** desta capability, não suas donas.

### Modified Capabilities
- `workflow-tramitacao`: o histórico imutável passa a admitir **um novo tipo de
  evento** — `remover_documento` — registrando a exclusão lógica de um anexo
  (responsável, data/hora), sem alterar a máquina de estados nem o status do
  processo.

## Impact

- **Dependência de change anterior:** requer `processos-e-workflow` arquivado —
  consome `processo` (FK, leitura de `status`/`unidade_atual_id`), `tramitacao`
  (novo tipo de evento), o modelo de autorização por unidade
  (`_exigir_acesso_ao_processo` / `require_acesso_unidade` / `tem_acesso_a_unidade`)
  e `log_seguranca` (acesso negado). Transitivamente encadeia na migration `0005`.
  Reusa o contrato de idempotência de `rotinas-agendadas` (arquivado) para o
  passo de purga do job diário e a infra de bucket de `bootstrap-infraestrutura`
  (arquivado).
- **Tabelas PostgreSQL** (migration `0006_gestao_documental`, encadeada em
  `0005_sigilo_processo`):
  - **Nova tabela `documento`**: `id uuid PK`; `processo_id uuid NOT NULL FK
    processo(id)`; `nome_original varchar NOT NULL`; `nome_exibicao varchar NOT
    NULL` (com o sufixo `(n)` de desduplicação por processo); `objeto_chave
    varchar NOT NULL UNIQUE` (chave do objeto no bucket, ex.: `{processo_id}/{uuid}`);
    `tipo_conteudo varchar NOT NULL` (MIME validado); `tamanho_bytes bigint NOT
    NULL CHECK > 0`; `hash_sha256 char(64) NOT NULL` (integridade — preparação
    para o Épico 4); `anexado_por_id uuid NOT NULL FK usuario(id)`; `anexado_em
    timestamptz NOT NULL DEFAULT now()`; `removido_em timestamptz NULL`;
    `removido_por_id uuid NULL FK usuario(id)`; `purgar_em timestamptz NULL`
    (congelado = `removido_em + 30d`). Estado de soft-delete é **derivado**
    (`removido_em IS NULL` = visível), nunca campo de texto livre. Índice em
    `(processo_id) WHERE removido_em IS NULL` e em `(purgar_em) WHERE removido_em
    IS NOT NULL` (varredura da purga).
  - `tramitacao` — **sem alteração de schema**; um novo valor no enum
    `tipo_evento_tramitacao`: `remover_documento`. O evento tem `responsavel_id`
    = usuário que removeu (o CHECK `ck_tramitacao_responsavel` de `0004` segue
    satisfeito), `unidade_origem_id`/`unidade_destino_id` nulas e
    `status_resultante` = status atual do processo (remoção não altera status).
- **Máquina de estados:** **nenhuma alteração** — anexar/remover documento é
  ortogonal ao status; `processo_estado.py` não muda. O status é apenas **lido**
  para autorizar a remoção (Cen.4/4b/4c).
- **Cloud Storage:** **nenhum bucket novo** — reusa `${project_id}-documentos`
  (já provisionado). Introduz o **primeiro código de negócio que escreve/lê o
  bucket**: um adaptador de armazenamento (`services/storage.py`) com
  implementação real (google-cloud-storage) e uma implementação local
  (filesystem) para pytest/E2E, seguindo o padrão dev/prod do `email/provider.py`.
  Nova dependência Python `google-cloud-storage`. Envs novos no serviço `api`:
  `DOCUMENTOS_BUCKET` (nome do bucket) e um flag de storage local dev.
- **Secret Manager:** nenhum segredo novo (acesso ao bucket via SA do Cloud Run,
  ADC — sem chave JSON).
- **Rate limiting:** N/A — todos os endpoints deste change são autenticados por
  unidade/perfil; a consulta pública (`slowapi`) é Épico 7 e não expõe anexos.
- **LGPD:** documentos **contêm dados pessoais** (podem trazer nome/CPF de
  interessados no corpo). Tratamento declarado: (a) **residência** — bucket
  regional no Brasil; (b) **confidencialidade** — `public_access_prevention =
  enforced`, sem leitura pública; todo acesso a conteúdo passa pela API
  autenticada e autorizada por unidade/perfil (Servidor só da própria unidade —
  reusa `_exigir_acesso_ao_processo`), servido via **URL assinada de TTL curto**
  ou streaming pela API, nunca URL pública permanente; (c) **retenção** — anexo
  removido fica 30 dias em retenção lógica e depois é **purgado fisicamente e
  de forma irreversível** pelo job diário; (d) **auditabilidade** — a remoção é
  evento imutável no histórico. Nenhum dado pessoal novo é adicionado ao schema
  relacional; o conteúdo binário é o único vetor, e ele é protegido pelas quatro
  medidas acima.
- **Código:** migration `0006`; modelo `Documento` + enum `TipoConteudoDocumento`
  (ou validação MIME em serviço); novo valor em `TipoEventoTramitacao`;
  `services/storage.py` (adaptador GCS/local) e `services/documento.py`
  (anexar/listar/remover/desduplicar/servir, com as regras de custódia); passo
  de purga em `services/documento.py` + acréscimo no `app/jobs/entrypoint.py`;
  endpoints em `routers/documentos.py` (`POST /processos/{id}/documentos` upload
  multipart, `GET .../documentos` listar, `GET .../documentos/{doc_id}/conteudo`
  inline/stream, `GET .../documentos/{doc_id}/download`, `DELETE
  .../documentos/{doc_id}`), montado em `main.py`, todos reusando
  `_exigir_acesso_ao_processo`; schemas `DocumentoResponse`. Frontend: seção
  "Documentos" na tela de detalhe do processo (`app/processos/[id]`) com upload,
  lista, visualização inline (PDF/imagem), download e remoção com confirmação.
  Regenerar `packages/api-types` (`pnpm gen:types`). Testes: unit/integração de
  anexação, validações, desduplicação, soft-delete + **evento imutável**,
  bloqueio pós-despacho, exceção pós-devolução, e purga idempotente
  (obrigatórios — tocam histórico de tramitação e dado pessoal); componente
  (Vitest/RTL) da seção de documentos; **E2E Playwright** do fluxo anexar →
  visualizar → baixar → remover (o upload de anexo é ação frequente e crítica do
  MVP — incluído por prudência, embora o gatilho literal de E2E do `config.yaml`
  cubra login/despacho/assinatura/consulta pública).
