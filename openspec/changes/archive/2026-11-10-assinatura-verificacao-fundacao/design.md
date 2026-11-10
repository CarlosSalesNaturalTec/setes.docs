# Design

## Context

Motivação e escopo: ver `proposal.md`. Requisitos: `specs/verificacao-assinatura/spec.md`.
Fundamentação técnica: `docs/fase2-assinatura/estudo-tecnico.md` §6 (verificação),
§7e–f (trust store, egress, cold start) e §8 (testes).

Estado atual relevante:

- `Documento` (`apps/api/app/db/models.py`) guarda metadados; o conteúdo está no bucket
  `documentos`, lido via `get_storage(settings).abrir(objeto_chave)`.
- A leitura de documento já passa por `_exigir_leitura_ao_processo`
  (`routers/processos.py`): unidade atual → `pode_auditar` (com `acesso_auditoria`) →
  unidade de origem se não sigiloso; negativas gravam `acesso_negado` em
  `log_seguranca`. `documento_service.obter_visivel` devolve 404 para removido.
- Uploads aceitam PDF/DOC/DOCX/JPG/PNG até 20 MB; o `tipo_conteudo` gravado vem de
  sniffing, não da extensão.
- Cloud Run com `min_instance_count = 0` e `egress = "PRIVATE_RANGES_ONLY"`: há saída
  para a internet pelo gateway padrão, sem IP fixo.
- Nenhum código de assinatura existe; a dependência criptográfica atual é só
  `python-jose[cryptography]`.

## Goals / Non-Goals

**Goals:**
- Um serviço de verificação reutilizável por `assinatura-qualificada-psc` (a mesma
  função vai conferir as assinaturas que o sistema aplicar).
- Vereditos que nunca afirmam mais do que a verificação local sustenta.
- Zero migration, zero infra nova, zero segredo novo.
- Suíte pytest e E2E totalmente offline, sem depender de ICP-Brasil real.

**Non-Goals:**
- Validar política de assinatura ICP-Brasil (LPA, OIDs AD-RB/RT, atributos
  obrigatórios do DOC-ICP-15.03). Fica com o VALIDAR do ITI (D7).
- Validação de longo prazo (PAdES-LTA, DSS/VRI embutidos usados como fonte de
  revogação histórica). O verificador usa o DSS se existir, mas não o exige.
- Assinaturas CAdES destacadas (`.p7s`) e XAdES — só PAdES/CMS embutido em PDF.
- Trust store em GCS e atualização automática (D5).

## Decisions

### D1 — Endpoint de leitura síncrono, no router de documentos

`GET /processos/{processo_id}/documentos/{documento_id}/verificacao` em
`routers/documentos.py`, ao lado de `/conteudo` e `/download`, reutilizando
literalmente o mesmo prólogo: `_carregar_processo` → `_exigir_leitura_ao_processo` →
`obter_visivel`. A checagem de PDF (`tipo_conteudo == "application/pdf"`, senão 422
com `MSG_VERIFICACAO_SOMENTE_PDF`) acontece **antes** de abrir o objeto no storage.

`GET`, não `POST`: não muda estado (D4). Síncrono: o custo dominante é a consulta de
LCR/OCSP, limitada pelo orçamento de rede de D3; não justifica Cloud Tasks nem
polling.

*Alternativas:* endpoint em router novo `assinaturas.py` — rejeitada agora, porque
duplicaria a regra de acesso; `assinatura-qualificada-psc` cria esse router para o
fluxo de assinar, e esta rota pode migrar para lá sem mudar o contrato.

```
 Navegador            api (documentos.py)             verificacao_assinatura        GCS / ACs
    │ GET …/verificacao      │                                 │                        │
    ├───────────────────────▶│ get_current_user                │                        │
    │                        │ _exigir_leitura_ao_processo ──▶ log_seguranca (negado/   │
    │                        │ obter_visivel (404 removido)        auditoria)           │
    │                        │ tipo_conteudo ≠ PDF → 422       │                        │
    │                        │ storage.abrir → bytes ──────────┼───────────────────────▶│
    │                        ├────────────────────────────────▶│ âncoras (lazy, D5)     │
    │                        │                                 │ pyHanko: lê /Sig, para │
    │                        │                                 │ cada assinatura:       │
    │                        │                                 │  integridade/cobertura │
    │                        │                                 │  cadeia → âncoras      │
    │                        │                                 │  LCR/OCSP (D3) ───────▶│ ACs
    │                        │                                 │  carimbo (se houver)   │
    │                        │◀──────── ResultadoVerificacao ──┤ (nada é gravado — D4)  │
    │◀── 200 JSON ───────────┤                                 │                        │
    │ painel com vereditos + link VALIDAR (D7)                 │                        │
```

### D2 — Vereditos: enum fechado, ordem de avaliação fixa, agregação pelo pior

Por assinatura, `VereditoAssinatura` (enum de domínio em `schemas/`, nunca texto livre):

| Código | Quando | Mensagem (spec) |
|---|---|---|
| `valida` | íntegra, cobre o arquivo, cadeia ICP-Brasil, não revogada, válida no momento de referência | "Assinatura válida — documento íntegro" (+ sufixo de expiração, D6) |
| `alterada_apos_assinatura` | como `valida`, mas não cobre o arquivo inteiro | "Assinatura válida, mas o documento recebeu alterações…" |
| `fora_icp_brasil` | íntegra, sem caminho até âncora ICP-Brasil | "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil…" |
| `inconclusiva` | revogação indeterminável, âncoras corrompidas, expirado sem carimbo | uma das duas mensagens "Verificação inconclusiva — …" |
| `invalida` | digest/assinatura não confere, ou revogada | "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado" |

Por documento, `situacao`: `assinado` (com `resumo` = pior veredito na ordem
`invalida > inconclusiva > fora_icp_brasil > alterada_apos_assinatura > valida`),
`sem_assinatura` ou `ilegivel` (PDF corrompido/criptografado).

Ordem de avaliação por assinatura — a primeira regra que casa decide:

```
integridade criptográfica falhou ───────────────▶ invalida
âncoras não carregaram íntegras (D5) ───────────▶ inconclusiva
sem caminho até âncora ICP-Brasil ──────────────▶ fora_icp_brasil   (não consulta revogação)
revogado (antes do momento de referência) ──────▶ invalida
revogação indeterminável ───────────────────────▶ inconclusiva
expirado e sem carimbo válido anterior ─────────▶ inconclusiva
não cobre o arquivo inteiro ────────────────────▶ alterada_apos_assinatura
senão ──────────────────────────────────────────▶ valida
```

As **mensagens moram no backend** como constantes `MSG_*` do service, no mesmo padrão
de `services/documento.py`; a resposta traz `veredito` (código) **e** `mensagem`. O
frontend escolhe ícone/cor pelo código e exibe a mensagem sem reescrever. Assim os
textos do PRD ficam testados no pytest, em um lugar só.

*Alternativa:* só os dois vereditos do PRD — rejeitada: obrigaria a chamar de
"INVÁLIDA" uma assinatura gov.br íntegra, ou de "válida" uma cuja revogação não foi
consultada.

### D3 — Validação local com pyHanko, revogação em hard-fail com orçamento de rede

`pyhanko` + `pyhanko-certvalidator` (Python ≥ 3.11; o projeto é 3.12). Para cada
`EmbeddedPdfSignature`: `validate_pdf_signature` com um `ValidationContext` construído
sobre as âncoras de D5, `allow_fetching=True` e `revocation_mode="hard-fail"`. O
mapeamento de `PdfSignatureStatus` para D2 usa `intact`/`valid` (integridade),
`trusted` + tipo de erro de path building (ICP × fora), `revoked`, e
`coverage`/`modification_level` (cobertura).

Distinguir `fora_icp_brasil` exige saber se a falha de confiança é *ausência de
caminho* (sem âncora) e não *revogação* ou *rede*. **Revisado na implementação:** não
são necessárias duas passadas — a subindicação ETSI que o pyHanko devolve em
`trust_problem_indic` já separa os casos numa única validação em `hard-fail`:
`NO_CERTIFICATE_CHAIN_FOUND` (sem âncora → `fora_icp_brasil`), `REVOKED_NO_POE` /
`revoked` (→ `invalida`), `OUT_OF_BOUNDS_NO_POE` (expirado → regra de D6) e
`CERTIFICATE_CHAIN_GENERAL_FAILURE` (revogação indisponível → `inconclusiva`). Cada
classe tem teste próprio (`tests/test_verificacao_assinatura_servico.py`) — é o ponto
de maior risco desta change.

**Coassinatura não é alteração posterior.** Coassinar acrescenta uma revisão, então a
1ª assinatura de um PDF com duas nunca cobre `ENTIRE_FILE`. Uma assinatura que não
cobre o arquivo só vira `alterada_apos_assinatura` quando é a última, quando a última
não cobre o fim do arquivo, ou quando o que veio depois dela passa de preenchimento de
formulário/assinatura (`ModificationLevel > FORM_FILLING`: anotações, páginas).

**Logs (D4):** o pyHanko e o certvalidator logam, com traceback, o CN do certificado
— que na ICP-Brasil é `NOME:CPF` — a cada falha de validação. Os dois loggers são
silenciados no módulo do serviço; um teste garante que nenhum log contém nome ou CPF.

**Orçamento de rede:** timeout por requisição de LCR/OCSP de 5 s e teto total de
15 s por verificação; estourou → `inconclusiva`. LCR/OCSP baixados ficam em cache **em
memória do processo** (dado público, não pessoal — não conflita com D4) por meio de um
conjunto de *fetchers* do certvalidator compartilhado entre requisições e recriado a
cada **1 h** — um cache eterno prenderia a instância num veredito "inconclusiva" depois
do `next_update` da LCR. O cache é perdido no scale-to-zero, o que só custa latência.

**Leitura do arquivo:** pyHanko precisa de stream com seek; o objeto (≤ 20 MB) é lido
inteiro para `BytesIO`. Aceitável com o limite de upload atual.

*Alternativas:* VALIDAR do ITI como backend — rejeitada: a documentação pública
encontrada é termo de licença de componente, não API hospedada (`estudo-tecnico.md`
§6, §9.3), e enviaria documentos do processo a terceiro. Biblioteca Java (DSS da UE)
— rejeitada: segundo runtime no container.

### D4 — Verificação efêmera: nada é persistido

Nenhuma tabela, coluna, evento de tramitação, cache de resultado ou linha de log com
dados do signatário. O resultado vive só na resposta HTTP. `log_seguranca` continua
recebendo apenas o que `_exigir_leitura_ao_processo` já grava (sem CPF). Erros
técnicos são logados com `documento_id` e classe do erro, **nunca** com nome/CPF ou
DN do certificado.

Razões: os signatários de PDFs externos são terceiros, fora de `ProcessoInteressado` e
da anonimização (`anonimizacao_lgpd.py`); persistir criaria um conjunto novo de dados
pessoais sem finalidade, porque o veredito pode ser recalculado a qualquer momento a
partir do próprio documento. Verificar é leitura, não ato sobre o processo — não cabe
no histórico imutável.

*Alternativa:* evento INSERT-only `verificar_assinatura` como prova de que alguém
conferiu — rejeitada nesta fatia; se a SETES pedir, é aditiva (nova linha de evento,
sem CPF) e não muda o contrato do endpoint.

### D5 — Âncoras ICP-Brasil versionadas no repositório, com hash fixado

`apps/api/app/trust/icp_brasil/` contém os certificados das **AC Raiz da ICP-Brasil
vigentes** (DER/PEM, baixados do repositório oficial do ITI) e um `MANIFESTO.json` com,
para cada arquivo: nome da AC, versão, SHA-256, `not_after`, URL de origem e data do
download. Carregamento **lazy** na primeira verificação do processo (estudo §7f — não
piora o cold start do resto da API), com cache em memória.

Se qualquer arquivo não conferir com o SHA-256 do manifesto, ou faltar, o conjunto
inteiro é tratado como **não carregado**: toda assinatura vira `inconclusiva` e um
`logger.error` registra a falha. Falha fechada, nunca parcial.

Âncoras **não** incluídas de propósito: AC Raiz do Governo Federal (gov.br) —
assinatura avançada, cai em `fora_icp_brasil`; raízes ICP-Brasil já expiradas — o
escopo é não retroativo (H3) e PDFs antigos sem carimbo dariam `inconclusiva` de
qualquer forma.

Rotação de AC Raiz = PR que troca arquivo e manifesto + deploy. Um teste pytest
falha quando alguma âncora estiver a menos de 180 dias do `not_after`, para a rotação
não ser descoberta em produção.

*Alternativa:* GCS + atualização pelo job diário (estudo §7e) — adiada para
`assinatura-qualificada-psc`, que já vai mexer em Terraform/IAM (bucket de assinados,
secrets mTLS). As AC Raiz giram em anos; LCRs, que giram em dias, são buscadas online
(D3).

### D6 — Dados exibidos e momento de referência

- **Nome**: `CN` do subject do certificado do signatário (ICP-Brasil usa
  `NOME:CPF` em alguns perfis — o sufixo `:CPF` é removido do nome exibido).
- **CPF**: extraído do `otherName` ICP-Brasil OID `2.16.76.1.3.1` (dados de pessoa
  física; posições 9–19 do valor). Ausente ou ilegível → `null`, exibido "não
  informado no certificado". Exibido **completo**, como pede US 4.2 Cen.1: quem vê o
  resultado já pode abrir o PDF, onde o mesmo CPF está.
- **Autoridade certificadora**: `CN` do emissor do certificado do signatário.
- **Data/hora**: se houver `signatureTimeStampToken` válido (cadeia do TSA com âncoras
  de D5), é a data comprovada e o momento de referência da validação, com `origem_data
  = "carimbo"` e nome da ACT; senão é o `signingTime` declarado, com `origem_data =
  "declarada"`, e o momento de referência é **agora**.
- **Expiração** (US 4.2 Cen.3): certificado expirado + carimbo anterior ao
  `not_after` → `valida` com sufixo "Certificado expirado em [data], mas válido na
  data da assinatura."; sem carimbo → `inconclusiva` (mensagem de expiração).
- Datas exibidas em `America/Sao_Paulo`, `dd/mm/aaaa hh:mm`.

### D7 — Limite declarado e veredito oficial

Todo resultado com `situacao = assinado` traz o aviso fixo e o link para
`https://validar.iti.gov.br` (nova aba, `rel="noopener noreferrer"`). O sistema nunca
envia o arquivo; o usuário baixa (download já existente) e envia por conta própria.
Isso mantém honesto o rótulo "válida": significa "íntegra, cadeia ICP-Brasil, não
revogada", não "conforme à política ICP-Brasil".

### D8 — Âncora de teste via flag dev/E2E-only

Duas variáveis em `app/config.py`, no padrão de `DEV_EMAIL_INBOX`: a flag booleana
`DEV_TRUST_ANCHOR_TESTE` (default `false`, nunca setada pelo Cloud Run) e
`DEV_TRUST_ANCHOR_PATH` (caminho de um PEM). O caminho **só é lido com a flag
`true`**; sem ela é ignorado mesmo se preenchido (cenário da spec). A âncora de teste
**não** entra no manifesto de D5 nem é conferida por hash — é somada ao conjunto já
validado. O Playwright gera (no `global-setup.ts`) uma PKI descartável, liga a flag,
aponta o caminho para a raiz de teste e anexa PDFs assinados com ela. Sem flag, a
mesma raiz cai em `fora_icp_brasil`.

A PKI de teste vive em `apps/api/scripts/pki_teste.py`, usado de dois jeitos: o
pytest importa (tudo em memória) e o Playwright o sobe como **primeiro `webServer`**,
antes da API — ele grava raiz, LCR e PDFs em `apps/web/e2e/.pki/` (gitignored) e serve
a pasta por HTTP local, para onde aponta o ponto de distribuição da LCR dos
certificados de teste. Os testes de endpoint do pytest fazem o mesmo com um servidor
HTTP em porta aleatória, exercitando o mesmo caminho de busca online de produção. No pytest, o `ValidationContext` recebe LCRs/OCSP
pré-carregados (`crls=`, `ocsps=`) e `allow_fetching=False` — nada sai para a rede.

*Alternativa:* endpoint `/internal/dev/trust-anchor` para injetar a âncora em runtime
— rejeitada: estado mutável global em memória, o mesmo problema do rate limit (D6 de
outra change); variável de ambiente lida no startup é mais simples.

### D9 — Frontend: ação por linha e painel inline

Em `documentos-section.tsx`, botão "Verificar Assinatura" para `tipo_conteudo ===
"application/pdf"`, ao lado de visualizar/baixar. O resultado abre num painel inline
abaixo da linha do documento (não modal — a lista continua utilizável e o painel cabe
no layout mobile já existente): resumo do documento, uma linha por assinatura
(ícone/cor por veredito: verde válida; âmbar alterada/fora/inconclusiva; vermelho
inválida), aviso e link do D7. Estado de carregamento "Verificando assinatura…"
(pode levar segundos — D3). O resultado **não é guardado** no estado global nem em
`localStorage` (D4); fechar o painel descarta.

## Risks / Trade-offs

- [Mapeamento dos erros do certvalidator para os vereditos é sutil (soft vs hard-fail,
  path building × revogação)] → teste pytest por classe de erro com PKI descartável;
  gate manual com PDFs reais (tarefa de conformidade).
- [Revogação lenta ou fora do ar torna a tela "inconclusiva" com frequência] →
  orçamento de 15 s, cache de LCR em memória; a mensagem orienta a tentar de novo ou
  usar o VALIDAR. É o comportamento correto: falhar alto (estudo §6).
- [LCRs grandes de ACs ICP-Brasil (vários MB) em instância fria] → OCSP preferido;
  cache por `next_update`; medir no gate manual e registrar o tempo observado.
- [Rotação de AC Raiz exige deploy] → teste de vencimento a 180 dias (D5); migração
  para GCS em `assinatura-qualificada-psc`.
- [Usuário lê "válida" como "conforme ICP-Brasil"] → aviso fixo do D7 em todo
  resultado; documentado no manual.
- [CPF de terceiros exibido na tela] → só a quem já lê o documento (mesmo dado do
  PDF); nada persistido (D4); declarado na proposal.
- [pyHanko não tem perfis ICP-Brasil prontos] → irrelevante para verificar CMS/cadeia;
  relevante só para a política, que está fora (D7).
- [PDF de 20 MB lido inteiro em memória com concorrência 80 por instância] → pior caso
  teórico alto, uso real baixo (≈10 signatários); se aparecer pressão de memória,
  limitar verificações concorrentes por instância com semáforo — não antecipar.

## Migration Plan

Sem migration Alembic, sem Terraform. Deploy normal da api e do web. Rollback:
reverter o deploy — não há estado gravado a desfazer. Feature visível assim que o web
publicar; não há flag de produto.

## Open Questions

- Lista exata das AC Raiz ICP-Brasil vigentes a incluir (v5, v10, v11, v12…): é
  levantamento na fonte oficial do ITI durante a tarefa de âncoras, registrado no
  manifesto — não muda nenhuma decisão acima.
- Para e-CNPJ de terceiros, exibir também o CPF do responsável (OID `2.16.76.1.3.4`)?
  Hoje fica "não informado"; acrescentar depois é aditivo.
