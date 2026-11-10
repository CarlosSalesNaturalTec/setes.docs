# Tasks

> Sem migration e sem Terraform nesta change (design.md, "Migration Plan"). As
> seções de schema/endpoint/UI abaixo seguem a separação exigida mesmo assim:
> schemas Pydantic (contrato) antes do endpoint, endpoint antes da UI.

## 1. Dependências e trust store (D5)

- [x] 1.1 Adicionar `pyhanko` e `pyhanko-certvalidator` a `apps/api/pyproject.toml`
  e atualizar o lock com `uv sync --extra dev`. **Aceite**: `uv run python -c "import
  pyhanko, pyhanko_certvalidator"` sem erro; `uv run ruff check .` e `uv run pytest`
  verdes sem outras mudanças.
- [x] 1.2 Levantar no repositório oficial do ITI as AC Raiz ICP-Brasil **vigentes**,
  baixá-las para `apps/api/app/trust/icp_brasil/` e escrever `MANIFESTO.json` (nome,
  versão, SHA-256, `not_after`, URL de origem, data do download). Não incluir AC Raiz
  do Governo Federal (gov.br) nem raízes expiradas (D5). **Aceite**: `sha256sum` de
  cada arquivo confere com o manifesto; manifesto lista a URL do ITI de cada raiz.
  **Feito:** 10 AC Raiz vigentes (v4–v13) baixadas de `acraiz.icpbrasil.gov.br` com
  TLS verificado; v1 indisponível no repositório e v2/v3 expiradas ficam fora.
- [x] 1.3 Implementar o carregador lazy das âncoras com cache em memória e falha
  fechada (arquivo ausente ou hash divergente → conjunto "não carregado" +
  `logger.error`, sem dado pessoal). **Aceite**: pytest cobre carregamento íntegro,
  hash adulterado e arquivo faltando; o caso adulterado não devolve nenhuma âncora.
- [x] 1.4 Teste de vencimento: falha se alguma âncora do manifesto estiver a menos de
  180 dias do `not_after` (D5). **Aceite**: teste passa hoje e falha ao simular a data
  com `not_after - 179 dias`.
- [x] 1.5 Adicionar `DEV_TRUST_ANCHOR_TESTE` (bool, default `false`) e
  `DEV_TRUST_ANCHOR_PATH` em `app/config.py`, com comentário no padrão de
  `DEV_EMAIL_INBOX` ("nunca em produção"); o caminho só é lido com a flag `true` (D8).
  **Aceite**: pytest prova que, com caminho preenchido e flag `false`, a âncora extra
  não entra no conjunto; com flag `true`, entra somada às do manifesto.

## 2. PKI de teste descartável (fixtures)

- [x] 2.1 Criar em `apps/api/tests/` um helper que gera com `cryptography`: raiz de
  teste, AC intermediária, certificado de signatário com `otherName` OID
  `2.16.76.1.3.1` (CPF fictício), certificado revogado, certificado expirado, uma TSA
  de teste, e a LCR correspondente. **Aceite**: o helper roda offline e em < 2 s; um
  teste de sanidade valida a cadeia gerada com `pyhanko_certvalidator`.
- [x] 2.2 Helper que produz PDFs de teste com pyHanko: assinado íntegro; adulterado
  nos bytes cobertos; com revisão incremental após a assinatura; com duas
  assinaturas; com carimbo de tempo; sem assinatura; corrompido; criptografado; e um
  assinado por raiz não confiável (simula gov.br). **Aceite**: cada PDF é gerado em
  teste, nada binário é commitado exceto se o tempo de geração exigir — nesse caso,
  justificar no PR. **Feito (2.1 e 2.2):** em `apps/api/scripts/pki_teste.py` (não em
  `tests/`), para o Playwright reutilizar como servidor (D8); nenhum binário commitado.

## 3. Serviço de verificação (D2, D3, D6)

- [x] 3.1 Definir em `apps/api/app/schemas/` o contrato `ResultadoVerificacao`:
  `situacao` (`assinado`/`sem_assinatura`/`ilegivel`), `resumo`, lista de
  assinaturas (ordem, `veredito`, `mensagem`, nome, CPF opcional, AC emissora,
  data/hora, `origem_data` `carimbo`/`declarada`, ACT opcional, expiração opcional) e
  enum `VereditoAssinatura`. **Aceite**: `uv run python scripts/export_openapi.py`
  mostra os schemas; enum fechado, sem campo de texto livre para o veredito.
- [x] 3.2 Implementar `app/services/verificacao_assinatura.py` com as mensagens
  `MSG_*` da spec, leitura do PDF para `BytesIO`, enumeração das assinaturas e a
  **ordem de avaliação** de D2. **Aceite**: pytest — um teste por veredito com os PDFs
  da tarefa 2.2, conferindo `veredito` e o texto exato de `mensagem`.
- [x] 3.3 Classificação de cadeia em duas passadas (soft-fail para distinguir
  "sem caminho até âncora" de "revogado"/"rede"; hard-fail só para cadeia ICP-Brasil)
  e mapeamento das classes de erro do certvalidator (D3). **Aceite**: pytest com um
  caso por classe — sem âncora → `fora_icp_brasil`; revogado → `invalida`; LCR
  indisponível/vencida → `inconclusiva`; âncoras não carregadas → `inconclusiva`.
  **Revisado na implementação:** uma passada em hard-fail basta — a subindicação ETSI
  do pyHanko já separa os casos (design.md D3).
- [x] 3.4 Orçamento de rede: timeout 5 s por requisição, 15 s por verificação, cache
  de LCR em memória por `next_update`, OCSP preferido (D3). **Aceite**: pytest com
  fetcher falso que demora além do teto → `inconclusiva` em ≤ 16 s; segunda
  verificação reutiliza a LCR em cache (fetcher chamado uma vez).
- [x] 3.5 Extração de dados (D6): nome do CN sem sufixo `:CPF`, CPF do OID
  `2.16.76.1.3.1`, emissor, data por carimbo × declarada, regra de expiração com e sem
  carimbo, fuso `America/Sao_Paulo`. **Aceite**: pytest cobre CPF presente, CPF
  ausente (`null`), expirado com carimbo anterior (`valida` + sufixo de expiração) e
  expirado sem carimbo (`inconclusiva`, mensagem de expiração).
- [x] 3.6 Agregação do documento pelo pior veredito e casos `sem_assinatura` /
  `ilegivel` (D2). **Aceite**: pytest — PDF com assinatura válida + revogada →
  `resumo = invalida`; PDF sem assinatura e PDF criptografado/corrompido devolvem as
  mensagens da spec, sem lista de assinaturas.

## 4. Endpoint e regra de acesso (D1, D4)

- [x] 4.1 Rota `GET /processos/{processo_id}/documentos/{documento_id}/verificacao`
  em `routers/documentos.py`, com o prólogo `_carregar_processo` →
  `_exigir_leitura_ao_processo` → `obter_visivel` → checagem de PDF (422
  `MSG_VERIFICACAO_SOMENTE_PDF`) antes de abrir o storage. Citar `(D1)` na docstring.
  **Aceite**: pytest com o `client` real cobre 200 (unidade atual), 422 (PNG), 404
  (removido) e 401 (sem token).
- [x] 4.2 Testes de **acesso negado** explícitos (regra vinculante): Servidor de outra
  unidade → 403 + `acesso_negado` em `log_seguranca` e storage **não** lido; unidade
  de origem com processo sigiloso → 403 + `acesso_negado`; auditor sem acesso à
  unidade → 200 + `acesso_auditoria`. **Aceite**: os três testes verdes, com
  asserção de que o storage falso não recebeu `abrir`.
- [x] 4.3 Teste de **não persistência** (D4, LGPD): após verificar PDF de terceiro, nenhum
  evento novo em `tramitacao`, nenhuma linha nova em tabela alguma além do que
  `_exigir_leitura_ao_processo` já grava, nenhuma ocorrência do CPF/nome em
  `caplog`, e `documento` (hash, tamanho, `objeto_chave`) inalterado. **Aceite**: teste
  verde contando linhas por tabela antes/depois.
- [x] 4.4 Garantir que a consulta pública não ganhou rota nem campo de assinatura
  (G1). **Aceite**: pytest varre as rotas `/publico/*` do OpenAPI e não encontra
  `verificacao` nem schemas de assinatura nas respostas públicas.
- [x] 4.5 Rodar `pnpm gen:types` e commitar `packages/api-types` (`openapi.json` +
  `schema.ts`). **Aceite**: `pnpm gen:types:check` verde.

## 5. Frontend (D7, D9)

- [x] 5.1 Adicionar `api.verificarAssinatura(processoId, documentoId)` em
  `apps/web/lib/api.ts`, tipado por `@setes/api-types`, sem `any`. **Aceite**:
  `pnpm --filter @setes/web typecheck` verde; teste Vitest colocado em
  `lib/api.test.ts` cobre a chamada.
- [x] 5.2 Em `documentos-section.tsx`: botão "Verificar Assinatura" só para
  `application/pdf`; painel inline com estado "Verificando assinatura…", resumo, uma
  linha por assinatura (ícone/cor por veredito), "não informado no certificado" para
  CPF nulo, data com indicação "comprovada por carimbo de tempo" × "declarada pelo
  signatário (sem carimbo de tempo)", aviso fixo e link para
  `https://validar.iti.gov.br` (nova aba, `rel="noopener noreferrer"`). Resultado não
  vai para estado global nem `localStorage`. **Aceite**: Vitest em
  `documentos-section.test.tsx` cobre botão ausente em DOCX/PNG, os seis vereditos
  renderizados com a mensagem da API, o link do ITI e o descarte ao fechar.
- [ ] 5.3 Conferir o painel no layout mobile existente. **Aceite**: o spec mobile da
  tarefa 6.2 passa sem rolagem horizontal.

## 6. E2E Playwright (obrigatório — documentos é fluxo crítico)

- [ ] 6.1 Em `apps/web/e2e/global-setup.ts` (ou helper), gerar a PKI e os PDFs de
  teste, subir o servidor HTTP estático da LCR, e em `playwright.config.ts` ligar
  `DEV_TRUST_ANCHOR_TESTE=true` + `DEV_TRUST_ANCHOR_PATH` na API (D8). **Aceite**: a
  suíte existente continua verde com a mudança.
- [ ] 6.2 Novo `apps/web/e2e/20-verificacao-assinatura.spec.ts`: Servidor anexa PDF
  assinado válido → "Assinatura válida — documento íntegro" com nome, CPF, AC e link
  do ITI; PDF adulterado → mensagem de INVÁLIDA com alerta; PDF sem assinatura →
  "Este documento não contém assinatura digital."; DOCX sem botão; Servidor de outra
  unidade não acessa a verificação. **Aceite**: `cd apps/web && pnpm test:e2e` verde.

## 7. Documentação, PRD e manual

- [x] 7.1 `docs/PRD.md`, US 4.2: nota "(change assinatura-verificacao-fundacao)"
  registrando os vereditos adicionais (inconclusiva, fora da ICP-Brasil, alteração
  posterior, sem assinatura, ilegível), a regra de Cen.3 sem carimbo → inconclusiva,
  e que esta fatia cobre PDFs assinados fora do sistema (G3). Não reescrever os
  cenários existentes. **Aceite**: diff do PRD só acrescenta a nota; Cen.1–3
  intactos.
- [x] 7.2 Manual: seção "Verificar assinatura" em `docs/manual/servidor/documentos.md`
  (o que cada resultado significa, por que pode dar inconclusivo, o que é "fora da
  ICP-Brasil" com o exemplo gov.br, como obter o veredito oficial no ITI); ajustar
  `docs/manual/fora-do-escopo.md` (assinar continua fora; verificar passa a existir);
  termos novos em `docs/manual/glossario.md` (ICP-Brasil, carimbo de tempo).
  **Aceite**: `mkdocs build --strict` local verde.
- [x] 7.3 Atualizar `docs/fase2-assinatura/README.md` (linha do tempo) e
  `respostas-cliente.md` ("Changes a propor") indicando a change em andamento.
  **Aceite**: os dois arquivos citam `assinatura-verificacao-fundacao` com a data.

## 8. Gate de conformidade manual (não automatizável — estudo §8.3)

- [ ] 8.1 Obter ao menos três PDFs reais: um assinado com e-CPF ICP-Brasil, um
  assinado via gov.br e um ICP-Brasil com carimbo de tempo (se disponível). Verificar
  cada um no Despapelize (ambiente local ou de validação) e no
  `https://validar.iti.gov.br`. **Aceite**: tabela em
  `openspec/changes/assinatura-verificacao-fundacao/conformidade.md` com, por
  arquivo, o veredito local, o veredito do ITI, o tempo de verificação observado e a
  justificativa de cada divergência; nenhum caso em que o local diga `valida` e o ITI
  diga Reprovado. Os PDFs reais **não** são commitados (dados pessoais de terceiros).

## Workflow follow-up

- Ao arquivar: retirar a linha `assinatura-verificacao-fundacao: LIBERADA` do bloco
  `context` de `openspec/config.yaml` (a própria lista exige) e atualizar o parágrafo
  de `CLAUDE.md` que diz "não há capability, spec Playwright nem código de
  assinatura".
- Em `assinatura-qualificada-psc`: mover as âncoras para GCS com atualização pelo job
  diário (D5) e reutilizar `verificacao_assinatura` para conferir as assinaturas
  aplicadas pelo sistema.
