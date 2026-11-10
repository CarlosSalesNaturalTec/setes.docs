## Why

O Épico 4 foi retomado em 2026-11-09 (change `retomada-epico-assinatura`, arquivada),
mas só uma fatia está liberada em `openspec/config.yaml`: esta. Ela entrega a
**US 4.2 (Verificar Assinatura)** para PDFs **assinados fora do Despapelize** e
anexados por upload — o caso que a SETES pediu em **G3** ("um fornecedor envia um
contrato já assinado; o funcionário quer confirmar ali mesmo que a assinatura é
legítima" → *"Sim, isso seria útil"*).

Por que agora, e por que primeiro:

- **É a única fatia que cabe no prazo H1 (11/2026)** — não depende de contratação da
  Soluti, de certificado SSL institucional, de ACT nem de nenhuma das pendências
  4–8 de `docs/fase2-assinatura/respostas-cliente.md`.
- **Derrisca o pedaço técnico mais difícil antes de a SETES comprar qualquer coisa**:
  validar cadeia ICP-Brasil e revogação com pyHanko (`estudo-tecnico.md` §6). O
  verificador construído aqui é o mesmo que `assinatura-qualificada-psc` usará para
  conferir as assinaturas que o próprio sistema aplicar.
- **Os critérios da US 4.2 têm dois vereditos; o mundo real tem mais.** Um PDF vindo
  de fora pode estar íntegro e assinado por uma cadeia que não é ICP-Brasil (o caso
  mais comum é a assinatura **gov.br**, emitida pela AC do Governo Federal — avançada,
  não qualificada), pode ter revogação impossível de consultar no momento, ou ter sido
  alterado depois da assinatura sem invalidá-la. Afirmar "válida" ou "INVÁLIDA" nesses
  casos seria falso. Esta change registra no PRD os estados adicionais antes de
  implementá-los, alinhados ao ETSI EN 319 102-1 (o mesmo padrão do VALIDAR do ITI).

**Depende de:** `retomada-epico-assinatura` arquivada (2026-11-09-retomada-epico-assinatura).

## What Changes

- **Nova ação "Verificar assinatura"** em todo documento PDF visível do processo
  (inclusive os gerados por modelo), sem detecção prévia nem coluna nova: um PDF sem
  assinatura responde "Este documento não contém assinatura digital."
- **Novo endpoint de leitura** `GET /processos/{id}/documentos/{doc_id}/verificacao`,
  com a **mesma regra de acesso de leitura** do conteúdo do documento (G2: "qualquer
  funcionário que tenha acesso ao processo") — inclusive acesso negado e auditoria.
- **Validação local com pyHanko + pyhanko-certvalidator**: integridade criptográfica
  (ByteRange/digest), cobertura do arquivo (alteração posterior à assinatura), cadeia
  até as âncoras ICP-Brasil, revogação (LCR/OCSP) e carimbo de tempo quando presente
  no próprio PDF.
- **Seis vereditos**, por assinatura e agregados por documento: válida, inválida,
  indeterminada, íntegra-mas-não-ICP-Brasil, íntegra-com-alteração-posterior,
  sem assinatura. Revogação não consultável **nunca** resulta em "válida".
- **Link explícito para o VALIDAR do ITI** (`validar.iti.gov.br`) como veredito
  oficial. O verificador local não valida política de assinatura (LPA/DOC-ICP-15.03)
  e o texto da tela diz isso.
- **Âncoras ICP-Brasil versionadas no repositório**, com hash SHA-256 fixado e
  verificado no carregamento (lazy, na primeira verificação). Trust store em GCS com
  atualização pelo job diário fica para `assinatura-qualificada-psc`.
- **Flag dev/E2E-only** para acrescentar uma âncora de teste ao trust store (padrão
  `DEV_EMAIL_INBOX`); ignorada fora de dev.
- **PRD, Épico 4, US 4.2**: nota acrescentando os vereditos adicionais e o escopo
  desta fatia. O Cen.3 (certificado expirado, válido na data) só é afirmado quando o
  PDF traz carimbo de tempo verificável; sem ele, o veredito é indeterminado.
- **Manual**: `docs/manual/servidor/documentos.md` ganha a seção de verificação;
  `docs/manual/fora-do-escopo.md` deixa de dizer que não há verificação.
- **`openspec/config.yaml`**: ao arquivar, retirar a linha de
  `assinatura-verificacao-fundacao` da lista de bloqueios (como a própria lista exige).

Fora desta change: assinar documentos (US 4.1), tabela `DocumentoAssinatura`,
carimbo emitido pelo sistema, trust store em GCS, aba "Documentos assinados" do perfil,
qualquer exibição na consulta pública (G1).

## Capabilities

### New Capabilities
- `verificacao-assinatura`: verificação, sob demanda, de assinaturas digitais
  embutidas em documentos PDF do processo — vereditos, dados do signatário extraídos
  do certificado, regra de acesso, trust store ICP-Brasil e limites declarados do
  veredito local. `assinatura-qualificada-psc` reutilizará esta capability para as
  assinaturas aplicadas pelo sistema.

### Modified Capabilities
<!-- Nenhuma. A seção de documentos ganha uma ação, mas os requisitos de
     gestao-documental (anexar, remover, visualizar, reter, purgar) não mudam. -->

## Impact

- **Banco**: **nenhuma tabela nova ou alterada, nenhuma migration.** A verificação é
  efêmera (D4 do design); usa `documento` e `processo` só para leitura.
- **Cloud Storage / Secret Manager**: nenhum bucket novo, nenhum segredo novo. Lê o
  objeto do bucket `documentos` existente.
- **Rede**: egress HTTPS para os pontos de distribuição de LCR e respondedores OCSP das
  ACs, já possível pelo gateway padrão do Cloud Run (`egress = "PRIVATE_RANGES_ONLY"`);
  sem IP fixo e sem Cloud NAT. A suíte pytest roda offline.
- **Dependências**: `pyhanko` e `pyhanko-certvalidator` em `apps/api/pyproject.toml`.
- **Código**: `apps/api/app/services/verificacao_assinatura.py` (novo),
  `apps/api/app/schemas/` (resposta da verificação), rota em
  `apps/api/app/routers/documentos.py`, âncoras em `apps/api/app/trust/icp_brasil/`,
  `app/config.py` (flag dev), `packages/api-types` (regenerado),
  `apps/web/app/processos/[id]/documentos-section.tsx` (ação + painel de resultado).
- **Testes**: pytest com PKI descartável gerada em teste; Playwright novo
  (documentos é fluxo crítico); gate manual contra o VALIDAR do ITI.
- **LGPD**: a verificação **extrai nome e CPF do signatário** de dentro do
  certificado embutido no PDF — frequentemente de **terceiros** (fornecedores), que não
  são `ProcessoInteressado`. Tratamento declarado:
  - **Coleta**: nenhuma nova. Os dados já estão no arquivo que o usuário anexou; o
    sistema só os lê do documento sob demanda (finalidade: conferir a autenticidade do
    documento do processo — legítimo interesse/execução de contrato, mesma base do
    anexo).
  - **Retenção**: **nenhuma**. O resultado é devolvido na resposta e não é gravado em
    banco, log ou cache; `log_seguranca` registra apenas acessos negados/de auditoria,
    como já faz, sem CPF.
  - **Exibição**: só para quem já pode ler o documento inteiro (onde o mesmo CPF já é
    visível abrindo o PDF). Nunca na consulta pública (G1).
  - **Anonimização**: não se aplica — não há dado persistido para anonimizar. O CPF
    continua dentro do PDF, sob o regime de retenção e purga já existente dos
    documentos (`gestao-documental`); a questão de anonimizar CPF de **assinaturas
    aplicadas pelo sistema** (F1) é de `assinatura-qualificada-psc`.
