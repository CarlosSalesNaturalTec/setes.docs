# Fase 2 — Assinatura Digital: estudo técnico

**Data:** 2026-10-08 · **Natureza:** estudo de viabilidade (não é change, não autoriza implementação)
**Ler antes:** `README.md` deste diretório (os dois portões que bloqueiam a implementação)

Este documento consolida o estudo para que ele não dependa de uma sessão de chat.
Tudo aqui é **análise**, não decisão: as decisões pendentes estão em
`questionario-cliente.md`.

---

## 1. Por que o caminho técnico é único

Se o requisito é assinatura **qualificada** + pelo navegador + sem instalação,
existe exatamente **um** caminho possível. Não por preferência — por restrição:

```
  Premissa do PRD (docs/PRD.md:569)
  "assinar pelo navegador, sem instalar software adicional"
                     │
      ┌──────────────┼──────────────────┬─────────────────────┐
      ▼              ▼                  ▼                     ▼
  (A) MANTER     (B) RELAXAR        (C) RELAXAR          (D) REBAIXAR
  a premissa     "sem instalar"     "ICP-Brasil"         o requisito
      │              │                  │                     │
  Certificado    A3 token/card      A1 (.pfx) com        assinatura
  A3 EM NUVEM    via extensão +     upload da chave      avançada
  (PSC/HSM)      middleware nativo  pro servidor         (Lei 14.063)
      │              │                  │                     │
  ✅ qualificada  ✅ qualificada      ✅ qualificada        ❌ NÃO é
  ✅ zero install ❌ instala driver   ❌❌ INACEITÁVEL       qualificada
  💰 cert/usuário    + extensão      chave privada sai    ✅ grátis
                 ❌ Windows-cêntrico da custódia do       ✅ zero install
                                     titular — destrói
                                     o não-repúdio
```

**(C) deve ser descartado de saída:** subir um `.pfx` para o servidor coloca a chave
privada do titular sob nossa custódia e aniquila o não-repúdio, que é o único motivo
de existir do épico.

**(A)** é o caminho qualificado. **(D)** é o caminho avançado — e pode ser suficiente
(ver §2). A escolha entre (A) e (D) é a pergunta A1/A2 do questionário.

### Tipos de certificado

| | A1 | A3 token/cartão | **A3 em nuvem** (PSC) | gov.br avançada |
|---|---|---|---|---|
| Chave privada | arquivo | hardware local | **HSM do PSC** | servidor gov |
| Validade | 1 ano | 1–5 anos | 1–5 anos | — |
| Instala algo? | importa arquivo | driver + extensão | **nada** | nada |
| Nível legal | qualificada | qualificada | **qualificada** | avançada |
| Autorização | senha local | PIN no token | **app do titular** | gov.br + 2FA |
| Serve à premissa? | não (risco) | não | **sim** | sim, outro nível |

**e-CPF, não e-CNPJ.** US 4.1 fala de "**minha** manifestação" — ato de pessoa
natural. e-CNPJ representa a SETES como pessoa jurídica; o PRD não descreve atos
institucionais. Escopo sugerido: **e-CPF A3 em nuvem** (pergunta B5 confirma).

**PSC** = Prestador de Serviço de Confiança, empresa credenciada pelo ITI para
operar o HSM guardando chaves de terceiros. Credenciados conhecidos: BirdID
(Soluti/VaultID), VIDaaS (Valid), SafeID (Safeweb), NeoID (Serpro), RemoteID.

---

## 2. Avançada × Qualificada — a diferença é ônus da prova, não validade

**Assinatura avançada tem validade jurídica.** "Sem validade plena" é atalho
impreciso. A diferença não é válida × inválida — é **quem precisa provar o quê
quando alguém nega ter assinado.**

Lei 14.063/2020, art. 4º:

| | Simples (I) | **Avançada (II)** | **Qualificada (III)** |
|---|---|---|---|
| Como funciona | identifica o signatário | certificados **não** ICP-Brasil, ou outro meio de comprovar autoria e integridade | certificado ICP-Brasil (MP 2.200-2, art. 10) |
| Condição de validade | — | **"desde que admitido pelas partes como válido ou aceito pela pessoa a quem for oposto o documento"** | nenhuma — vale por si |
| Presunção legal | não | **não** | **sim** (MP 2.200-2, art. 10) |
| Confiabilidade (art. 4º §1º) | menor | intermediária | **a mais elevada** |

A oração condicional do inciso II é **toda** a diferença. A presunção não vem da Lei
14.063 — vem da **MP 2.200-2, art. 10**: documentos assinados com certificado
ICP-Brasil **presumem-se verdadeiros em relação aos signatários**. É presunção
*relativa* (quem contesta prova a falsidade). O §2º do mesmo artigo admite outros
meios **desde que aceitos pelas partes** — base jurídica de tudo que é
avançado/simples.

Quando um servidor diz *"não fui eu que assinei"*:

```
QUALIFICADA                            AVANÇADA
  o ônus é de quem NEGA                  o ônus é NOSSO
  ┌──────────────────┐                   ┌──────────────────┐
  │ "não fui eu"     │                   │ "não fui eu"     │
  └────────┬─────────┘                   └────────┬─────────┘
           ▼                                      ▼
  ele prova que não foi            nós provamos que foi:
  (perícia, revogação…)            logs, trilha de auditoria,
           │                       hash, aceite prévio do termo
           ▼                                      │
  presunção legal nos                             ▼
  protege por padrão               se a prova for boa → vale
                                   se for fraca → cai
```

### O achado mais importante do estudo

**A SETES já tem quase toda a infraestrutura de prova que a assinatura avançada
exige.** Os quatro requisitos do inciso II contra o que o código já faz:

| Requisito legal (art. 4º II) | Estado no Despapelize |
|---|---|
| associada ao signatário de forma única | ✅ usuário autenticado, e-mail único, JWT |
| modificação posterior detectável | ✅ `hash_sha256` por documento, `tramitacao` INSERT-only, `log_seguranca` |
| trilha probatória | ✅ Épico 8 inteiro (auditoria + relatórios) |
| **controle exclusivo com elevado nível de confiança** | ⚠️ **só senha** — lacuna real |
| **aceita pelas partes** | ❌ falta termo de aceite |

Duas lacunas, as duas baratas:

1. **Segundo fator no ato de assinar** — não no login, só ao assinar. Reforça
   "controle exclusivo".
2. **Termo de Uso de Assinatura Eletrônica** aceito no fluxo `primeiro-acesso` — é
   literalmente o "admitido pelas partes" do inciso II. Código pequeno, peso
   jurídico grande.

**O caminho avançado custa da ordem de 10% do esforço do qualificado**, com zero
procurement e zero custo recorrente, reaproveitando o que já existe.

⚠️ **Ressalvas de precisão (verificar antes de usar em parecer):**
- As fontes divergem se o art. 4º III cita o §1º ou o §2º do art. 10 da MP 2.200-2.
  Conferir o texto oficial no Planalto.
- Vi o REsp 2.159.442/PR (STJ, 2024) citado em blog aceitando avançada — **não
  confirmado em fonte primária**. Não usar como jurisprudência firmada.

---

## 3. Arquitetura — a chave privada nunca chega ao nosso servidor

Vale para nuvem e para token. Consequência: assinar **não é uma requisição** — é um
protocolo de 3 passos com estado no meio (*deferred / interrupted signing*).

```
 ┌────────┐         ┌─────────────────┐        ┌──────────┐      ┌─────┐
 │Servidor│         │ FastAPI + pyHanko│        │ PSC/HSM  │      │ ACT │
 │(browser)│        │   (nosso código) │        │  (nuvem) │      │RFC3161│
 └───┬────┘         └────────┬────────┘        └────┬─────┘      └──┬──┘
     │ POST /assinaturas     │                      │               │
     ├──────────────────────▶│                      │               │
     │                       │ 1. incremental update do PDF:        │
     │                       │    /Sig dict, ByteRange,             │
     │                       │    bytes_reserved (obrigatório —     │
     │                       │    cert desconhecido ainda)          │
     │                       │ 2. monta SignedAttributes:           │
     │                       │    messageDigest, signingCertV2,     │
     │                       │    signaturePolicyId (OID AD-RB/RT)  │
     │                       │ 3. grava SessaoAssinatura (TTL)      │
     │  {sessao, digest}     │                      │               │
     │◀──────────────────────┤                      │               │
     │ OAuth2 authorize + PKCE (RFC 6749 + 7636)    │               │
     │  — titular autoriza NO APP DELE —            │               │
     ├──────────────────────────────────────────────▶│               │
     │◀─────── code ────────────────────────────────┤               │
     │ POST /assinaturas/{sessao}/concluir {code}   │               │
     ├──────────────────────▶│                      │               │
     │                       │ token + POST /signature              │
     │                       │  ⚠️ envia só o HASH, nunca o arquivo │
     │                       ├─────────────────────▶│               │
     │                       │◀── PKCS#1 raw ───────┤               │
     │                       │ 4. embute CMS no gap reservado       │
     │                       │ 5. pede carimbo de tempo             │
     │                       ├──────────────────────────────────────▶│
     │                       │◀──── TimeStampToken ─────────────────┤
     │                       │ 6. PDF assinado → GCS (nova chave)   │
     │                       │ 7. INSERT assinatura + INSERT        │
     │   PDF assinado        │    tramitacao(assinar_documento)     │
     │◀──────────────────────┤                      │               │
```

### Biblioteca: pyHanko

Única opção Python madura para PAdES com assinador externo.

- Já **não exige** o certificado do signatário no início do fluxo
  (`async_digest_doc_for_signing`) — exatamente o caso de assinatura remota.
- Sem certificado, a estimativa de tamanho é desabilitada e **`bytes_reserved` passa
  a ser obrigatório**.
- O ICP-Brasil aperta aqui: na norma do ITI, o **único atributo não assinado
  permitido** em PAdES ICP-Brasil é o `id-aa-signatureTimeStampToken`, porque a
  estrutura tem tamanho pré-registrado no `ByteRange`. **Dimensionar esse buffer
  errado quebra a assinatura — é o ponto de maior risco de implementação.**

⚠️ **Não existe documentação do pyHanko que mencione perfis ICP-Brasil prontos
(AD-RB/AD-RT).** A política de assinatura (OID) e os atributos terão de ser montados
à mão contra as tabelas do DOC-ICP-15.01/15.03. Há um PR de terceiros alegando
validar com pyHanko, mas com CA de teste e com a política AD-RB opt-in por uma regra
de dicionário PDF não resolvida — **não é evidência de conformidade**.

### HSM e o certificado SSL de aplicação

**HSM = Hardware Security Module.** Equipamento criptográfico à prova de violação; a
chave privada nasce dentro e **não pode sair**. Um token USB de e-CPF já é um HSM
pessoal. "A3 em nuvem" é o mesmo princípio com a caixa no datacenter do PSC — mesma
classe legal A3, mesma assinatura qualificada.

**São DUAS autenticações distintas, frequentemente confundidas:**

```
┌─────────────────────────────────────────────────────────────────┐
│  1️⃣  A PESSOA → PSC                                             │
│     "Eu, José, autorizo esta assinatura"                        │
│     app do PSC no celular, biometria/PIN                        │
│     🚫 nosso sistema NUNCA vê isso (DOC-ICP-17.01 proíbe)       │
├─────────────────────────────────────────────────────────────────┤
│  2️⃣  A APLICAÇÃO → PSC                                          │
│     "Eu sou o Despapelize, aplicação registrada nº 123,         │
│      e peço uma assinatura em nome do José"                     │
│     ⟶ a norma exige CERTIFICADO SSL ICP-BRASIL (mTLS),          │
│       não uma chave de API qualquer                             │
└─────────────────────────────────────────────────────────────────┘
```

O PSC guarda a chave privada de milhares de pessoas; não pode aceitar que qualquer
cliente HTTP peça assinaturas. Daí exigir que a aplicação chamadora seja
identificada criptograficamente por certificado de AC credenciada.

**Analogia:** o e-CPF é o crachá do funcionário; o certificado SSL é a credencial do
prédio que deixa nosso software passar da porta do cofre. **O SSL não assina nada.**

É produto distinto (certificado de servidor/aplicação SSL sob ICP-Brasil), vendido
por Certisign, Serpro, Valid, Safeweb. **Não é e-CNPJ de assinatura.**

⚠️ Requisito lido no **DOC-ICP-17.01 v2.0/v2.3**; a versão vigente é a **v3.0** e não
foi possível abri-la. Na prática os provedores variam — muitos emitem
`client_id`/`client_secret` e usam o SSL só para mTLS; alguns só exigem em produção.
**Confirmar com cada provedor** — e é a primeira pergunta de uma conversa comercial,
porque a emissão para pessoa jurídica tem **semanas de lead time** e bloqueia tudo.

---

## 4. Três critérios de aceite do PRD são impossíveis como escritos

Não é detalhe de redação — é a marca de que o Épico 4 foi escrito presumindo acesso
do navegador ao smart card.

A regra geral do **DOC-ICP-17.01**: *"As aplicações não deverão coletar fatores de
autenticação do titular"* + *"os PSC deverão se comunicar diretamente com equipamento
do titular, previamente identificado e cadastrado junto ao PSC de forma segura"*.

⚠️ **Mas há uma exceção explícita na norma, e ela importa:**

> *"Excetua-se desta regra o Serviço 'Autorização com Credenciais do Titular'"* —
> serviço que obtém do titular a autorização de uso da chave privada **solicitando
> fatores de autenticação**, com os valores concatenados e enviados no parâmetro
> `password`, sendo que **no mínimo um fator deve ser válido para uma única
> solicitação (OTP)**.

Ou seja: existe um caminho normativo em que o **nosso** formulário coleta o fator. O
que **não** existe é coletar um *PIN estático de certificado* — o fator é um **código
de uso único**, gerado no dispositivo cadastrado do titular.

Tipos de fator aceitos (da Declaração de Práticas da Certisign, não da norma em si):
**OTP conforme RFC 6238 (TOTP), RFC 6287 e RFC 4226 (HOTP)**, biometria, certificado
de atributo e push notification.

| US | Como está no PRD | Por que não fecha | Como reescrever |
|---|---|---|---|
| 4.1 Cen.1 (`:575`) | "insiro o PIN do certificado" | não é PIN estático: é **OTP de uso único** gerado no app do titular. Via "Autorização com Credenciais do Titular", nosso formulário **pode** coletá-lo | "informo o código de uso único do aplicativo do meu provedor de certificado" |
| 4.1 Cen.3 (`:582`) | "PIN incorreto 3× → bloqueio 30min + e-mail" | o bloqueio da credencial é do PSC; nós só vemos "autorização negada", sem saber o motivo | nossa camada antiabuso sobre *autorizações negadas* — viável, já existem `tentativas_login_falhas`/`bloqueado_ate` e slowapi |
| 4.1 Cen.5 (`:589`) | "token/smart card não conectado" | não existe token no fluxo em nuvem | "nenhum certificado em nuvem vinculado à sua conta" |

### Por que celular, e se há alternativa

A norma diz **"equipamento"**, não "celular". O requisito real é um dispositivo
**cadastrado previamente** no PSC, por canal seguro, com ao menos um fator de uso
único. O celular é **prática de mercado, não imposição legal** — é como todos os
fornecedores implementam hoje:

- **Bird ID** (Soluti): o OTP nasce no aplicativo; **mesmo a versão para computador
  usa o código gerado no app**.
- **VIDaaS** (Valid): a aprovação acontece no aplicativo no smartphone.
- **SafeID** (Safeweb): funciona por aplicativo no celular; sistemas não integrados
  usam o SafeID Desktop, que não dispensa o cadastro do aparelho.

Como o fator é da família TOTP/HOTP, um **token OTP de hardware** seria tecnicamente
concebível — mas **nenhum provedor pesquisado oferece**. → ver §9, item 7: é pergunta
para o fornecedor, não para o cliente.

O aplicativo é sempre **do fornecedor do certificado**, nunca o nosso: o Despapelize
pede a assinatura ao PSC; o PSC chama o titular no aplicativo dele.

E um quarto, mais sutil — **US 4.2 Cen.3** (`:604-607`): *"Certificado expirado em
[data], mas válido na data da assinatura"*. Provar isso exige carimbo de tempo
confiável. Sem ACT, a data é auto-declarada e não prova nada.

```
AD-RB (PAdES-BES)  ── sem carimbo ──▶ US 4.2 Cen.3 impossível de provar
AD-RT (PAdES-T)    ── + ACT ────────▶ ✅ alvo da Fase 2
AD-RA (PAdES-LTV)  ── + DSS/VRI ────▶ validade de longo prazo (CRL/OCSP expiram
                                        antes dos processos arquivados)
```

**AD-RT como alvo**, com o código estruturado para alcançar AD-RA depois — processos
arquivados vivem anos e CRL/OCSP não. ACT (Autoridade de Carimbo do Tempo) é serviço
**pago por carimbo** (pergunta E1).

---

## 5. Modelo de dados — a colisão mais profunda

`apps/api/app/db/models.py:572-611` (`Documento`) tem `objeto_chave` **UNIQUE**,
`hash_sha256`, `tamanho_bytes`, soft-delete e purga. Mas **assinar PAdES muda os
bytes do arquivo**, e coassinar (US 4.1 Cen.4) muda outra vez.

```
(A) Mutar no lugar          (B) Nova linha Documento      (C) Evento INSERT-only
    overwrite no GCS            por assinatura                 com rendição própria
    UPDATE hash/tamanho         ┌──────────┐                   ┌──────────┐
    ┌──────────┐                │parecer   │                   │ Documento│ ← identidade
    │ Documento│                │parecer(as│                     └────┬─────┘   estável
    └──────────┘                │parecer(as│                          │ 1:N
    ❌ destrói o hash do        └──────────┘                   ┌──────▼─────────────┐
       original (prova)         ❌ polui a lista              │DocumentoAssinatura │
    ❌ contraria "histórico     ❌ quebra modelo_id            │ (INSERT-only)      │
       imutável"                   (proveniência)              │ ordem 1,2,3…       │
                                                               │ nivel (avanç/qual) │
                                                               │ objeto_chave_result│
                                                               │ hash_result        │
                                                               └────────────────────┘
                                                               ✅ casa com os invariantes
                                                                  já estabelecidos no repo
```

**(C) é a única que respeita as regras vinculantes** do `openspec/config.yaml`
("histórico imutável — nunca UPDATE, sempre INSERT de novo evento"). Segue o padrão
já usado duas vezes: estado derivado em vez de coluna textual. Aqui: *a rendição
corrente do documento é a última assinatura, ou o upload original se não houver
nenhuma*. **Sem tabela de versão separada — o evento de assinatura É a versão.**

Cada linha guarda: ordem, signatário (FK `usuario`), **nivel** (`avancada` |
`qualificada` — é o que viabiliza o modelo híbrido da pergunta A4), CPF e nome
extraídos do certificado, AC emissora, `objeto_chave_resultante`,
`hash_sha256_resultante`, política (OID), `TimeStampToken`, data/hora do carimbo.

Em paralelo, novo `TipoEventoTramitacao.ASSINAR_DOCUMENTO` — ortogonal ao status,
exatamente como `REMOVER_DOCUMENTO` e `RESTAURAR_DOCUMENTO` já são
(`models.py:97-99`). Registro duplo: o histórico do processo mostra o ato, a tabela de
assinatura guarda a criptografia.

### Três invariantes atuais que a assinatura quebra

1. **Purga destrói prova.** `purgar_documentos_vencidos`
   (`app/services/documento.py`) apaga fisicamente do GCS após 30 dias (D7).
   Documento assinado é prova de ato jurídico. → pergunta **B7**.
2. **Janela de remoção vs. assinatura.** Remover é permitido em `Aberto` ou
   pós-devolução-pré-redespacho — a mesma janela em que se assina. Dá para assinar e
   depois remover. Precisa de regra: **assinar sela o documento**. → **B7**.
3. **LGPD: o CPF do signatário não pode ser anonimizado.** E não é escolha nossa — o
   CPF está dentro do certificado embutido no CMS do próprio PDF. **Anonimizar
   quebra a assinatura.** Colide de frente com `PRD.md:953-959`, que configura
   anonimização 5 anos após o arquivamento, e com
   `app/services/anonimizacao_lgpd.py` (que hoje só trata `ProcessoInteressado`).
   → pergunta **F1**, e a decisão precisa de nome registrado.

---

## 6. Verificação (US 4.2)

Dois caminhos, não excludentes:

- **Validação local** com pyHanko + âncoras ICP-Brasil (AC Raiz v1…v13 no repositório
  do ITI) + CRL/OCSP. Controle total, mas passamos a ser donos da *frescura* do trust
  store: rotação de AC Raiz, atualização da LPSC. CRL tem `next_update` — a validação
  precisa **falhar alto** se o trust store estiver velho, nunca passar silenciosamente.
- **VALIDAR do ITI** (`validar.iti.gov.br`) — veredito autoritativo, segue ETSI EN
  319 102-1, devolve Aprovado/Reprovado/Indeterminado. Existe uma página "API
  Verificador de Conformidade" no ITI, mas **a documentação pública encontrada é só
  termo de licença de software** — provavelmente componente para baixar, não API
  hospedada. **Não prometer integração programática antes de confirmar.**

Recomendação: validação local para o botão "Verificar Assinatura" + caminho explícito
para o usuário obter o veredito oficial no ITI.

**Esta é a fatia de custo zero** — não precisa de certificado, fornecedor nem
contrato, e derrisca o pedaço técnico mais difícil. Ver pergunta **G3**.

---

## 7. Infra GCP — sete consequências concretas

Analisado contra o Terraform real em `infra/`.

### a) A sessão de assinatura **não pode** ficar em memória

`infra/cloudrun.tf`: `min_instance_count = 0`,
`max_instance_request_concurrency = 80`, autoscaling. O fluxo tem 3 passos com estado
no meio — **a requisição 2 pode cair em outra instância** que a requisição 1.

O repositório já documenta essa armadilha: `# rate limit em memória do processo (D6)`,
com `limiter.reset()` na fixture `client` porque o contador vaza entre testes. Mesma
classe de erro. → `SessaoAssinatura` é **tabela no Postgres** com TTL, limpeza no job
diário. Não negociável.

### b) Hoje **não existe IP de saída fixo**

`infra/cloudrun.tf:59` → `egress = "PRIVATE_RANGES_ONLY"`. Só faixas privadas passam
pela VPC; tráfego de internet sai pelo gateway padrão do Cloud Run, no **pool
compartilhado e rotativo de IPs do Google**. (`infra/jobs_scheduler.tf:33` idem.)

Se o PSC ou a ACT exigir **allowlist de IP**:

```hcl
egress = "ALL_TRAFFIC"          # ⚠️ passa a rotear TODO o tráfego externo
+ google_compute_router
+ google_compute_router_nat     # com IP estático reservado
```

Terraform novo, custo mensal novo (NAT por hora + por GB), e passa a rotear SendGrid
e APIs Google pelo NAT. **Perguntar ao provedor na primeira conversa comercial.**

### c) O certificado SSL vai para o Secret Manager — e **expira**

`infra/secrets.tf` tem
`local.secret_ids = ["db-password", "jwt-signing-key", "sendgrid-api-key"]`. Entram
dois: `psc-client-secret` e `psc-mtls-cert` (cadeia + chave privada em PEM),
carregados no startup para o cliente `httpx` em mTLS. Padrão já estabelecido, mais o
binding em `infra/iam.tf:39`.

**Não precisa de Cloud HSM nem Cloud KMS do nosso lado** — vale dizer explicitamente
ao cliente para não comprar o que não precisa. Nunca guardamos chave de *assinatura*.

⚠️ **Mina operacional:** o certificado SSL expira (A1 = 1 ano). Quando expirar, a
assinatura para **de uma vez**, com falha de handshake TLS. Precisa de runbook de
renovação e verificação de validade no job diário alertando antes do vencimento. É o
tipo de coisa que derruba produção 11 meses depois do lançamento.

Nota: `secrets.tf` fixa replicação em `var.region` (us-central1), então a chave
institucional da SETES fica fora do Brasil. Não é dado pessoal, não é questão de
LGPD — mas pertence ao registro de riscos do cliente, ao lado de
`docs/lgpd-transferencia-internacional-us-central1.md`.

### d) Documento assinado precisa de outro regime de retenção

`infra/storage.tf`: o bucket `documentos` tem versionamento + soft-delete de 30 dias,
mas **nenhuma `retention_policy`**. E o job diário apaga fisicamente os purgados.
**Documento assinado é prova — purgar destrói a prova.**

O GCS oferece `retention_policy` (com `is_locked` opcional) que torna objetos
**imutáveis até a retenção expirar** — o que **bloquearia o job de purga** naquele
bucket.

→ Terceiro bucket, `${project_id}-documentos-assinados`, com regime próprio. **O
precedente já está no repo**: o comentário de `storage.tf` sobre `lgpd_solicitacoes`
diz *"não compartilha retenção/acesso com o bucket de documentos de processo"*
(Épico 10, D6). Mesmo raciocínio.

⚠️ `is_locked = true` é **irreversível** — nunca mais se encurta a retenção nem se
apaga o bucket antes do prazo. Recomendação: começar com retention policy **sem
lock** (já bloqueia exclusão, admin reverte) e travar só depois que o jurídico fixar
o prazo. → pergunta **F3**.

### e) Trust store e egress de validação

HTTPS de saída para `acraiz.icpbrasil.gov.br` e para LCR/OCSP de cada AC. Guardar
cadeias e LCRs em **GCS, não embutidas na imagem** — rotação de AC Raiz sem redeploy.
Atualização no job diário existente (`app/jobs/entrypoint.py`, padrão idempotente por
seleção de estado; `sa-jobs` já tem `objectAdmin` no bucket por `infra/iam.tf:94`).
A suíte pytest roda offline — **não pode depender desse egress**.

### f) Cold start

`min_instance_count = 0` foi escolha deliberada de custo zero em ocioso. Carregar e
parsear o trust store no startup piora um caminho já frio — melhor lazy-load na
primeira assinatura/verificação, com cache das âncoras.

### g) Escopo de formato

PAdES só cobre PDF. Hoje aceitamos `DOC/DOCX/JPG/PNG`
(`app/services/documento.py:37-44`). Sugestão: restringir assinatura a **PDF** na
Fase 2 — inclui os gerados por `ModeloDocumento` via `fpdf2`, que são os candidatos
naturais. CAdES-detached para os demais formatos fica como opção posterior. →
pergunta **B1**.

---

## 8. Testes — três camadas, uma não automatizável

Regras vinculantes do `openspec/config.yaml`: documentos é fluxo crítico →
**Playwright obrigatório**; toca dados pessoais e histórico → **teste automatizado
obrigatório**.

1. **pytest** — PKI de teste descartável (CA + folha geradas com `cryptography`),
   assinatura com chave local, validação contra essa CA injetada como âncora. Prova o
   fluxo, **não prova conformidade ICP-Brasil**.
2. **Playwright** — precisa de **PSC falso**, e o repo já tem o padrão exato:
   `DEV_EMAIL_INBOX=true` / `DEV_DB_RESET=true` em `apps/web/playwright.config.ts`,
   endpoints `/internal/dev/*` que respondem 404 sem a flag. Um `DEV_PSC_FAKE=true`
   com authorize/sign falsos assinando com chave de teste encaixa na convenção.
3. **Gate de conformidade manual** — assinar com e-CPF real, validar em
   `validar.iti.gov.br`, arquivar o comprovante. Uma vez por release. Não
   automatizável; **tem que ser tarefa explícita com critério de aceite**, senão
   nunca acontece.

---

## 9. Pontos ainda em aberto (técnicos, não do cliente)

1. **DOC-ICP-17.01 v3.0** — não foi possível abrir. Os requisitos OAuth2 citados aqui
   vêm das v2.0/2.3. Baixar no portal do ITI e conferir a seção OAuth2 antes de
   desenhar o fluxo.
2. **Redirect vs. sessão longa.** O BirdID expõe `POST /v0/oauth/signature` com
   `access_token` — se a autorização OAuth2 vale por dias, o redirect acontece uma
   vez e as assinaturas seguintes são chamada de backend. **Muda radicalmente a UX e
   simplifica muito o frontend** (que hoje não tem nenhum fluxo de redirect externo —
   a autenticação é JWT próprio, sem SSO). Confirmar duração de sessão **com cada
   provedor**, não com intermediários.
3. **API do VALIDAR do ITI** — existe como API hospedada ou é componente para instalar?
4. **Tabelas de atributos do DOC-ICP-15.03** (v9.1 compilada) — OIDs de política e
   atributos assinados obrigatórios para PAdES precisam ser lidos na fonte.
5. **Quem pode assinar e quando.** US 4.1 diz "processo da minha unidade"; Cen.4
   admite coassinatura por "outro usuário". Precisa de cenário de **acesso negado
   explícito** (regra vinculante). → perguntas **B6**, **G2**.
6. **Baixa confiança:** apareceu menção a migração da ICP-Brasil para nova
   arquitetura de certificados até 2029. Não confirmado. Checar com o ITI se afeta
   decisão de longo prazo.
7. **Fator de autorização sem smartphone.** O fator é da família TOTP/HOTP, então um
   token OTP de hardware seria concebível, mas nenhum provedor pesquisado oferece —
   em todos (Bird ID, VIDaaS, SafeID) o código nasce no aplicativo de celular.
   **Pergunta para o fornecedor, não para o cliente:** *"vocês suportam algum fator de
   autorização que não dependa de smartphone — token OTP de hardware, por exemplo?"*
   Importa porque a resposta de C1 pode revelar que parte do quadro não tem celular.
8. **Qual serviço de autorização cada PSC expõe.** Confirmar se o provedor implementa
   o "Autorização com Credenciais do Titular" (fator coletado no nosso formulário,
   sem redirect) ou só o fluxo de redirect/push. Define se o frontend precisa de um
   fluxo de saída e retorno — que hoje não existe no projeto — ou de um simples campo
   de código. É a diferença entre uma mudança grande e uma pequena no `apps/web`.

---

## 10. Fontes consultadas

**Normas e órgãos oficiais**
- [ITI — Documentos Principais (versões vigentes)](https://www.gov.br/iti/pt-br/assuntos/legislacao/documentos-principais)
- [DOC-ICP-17.01 v2.3 — procedimentos operacionais dos PSC (PDF)](https://www.gov.br/iti/pt-br/assuntos/legislacao/documentos-principais/DOCICP17.01verso2.3PROCEDIMENTOSOPERACIONAISMNIMOSPARAOSPRESTADORESDESERVIODECONFIANADAICPBRASIL.pdf)
- [IN ITI nº 03/2021 — DOC-ICP-15.03 (políticas de assinatura)](https://repositorio.iti.gov.br/instrucoes-normativas/IN2021_03_DOC-ICP-15.03.htm)
- [DOC-ICP-15.01 — requisitos de geração e verificação de assinaturas](https://www.gov.br/iti/pt-br/central-de-conteudo/doc-icp-15-01-v-3-0-req-gera-e-verif-de-assin-dig-na-icp-brasil-pdf)
- [ITI — Repositório AC-Raiz (v1 a v13 + LCRs)](https://www.gov.br/iti/pt-br/assuntos/repositorio/repositorio-ac-raiz)
- [ITI — Lista de Prestadores de Serviço de Confiança (LPSC)](https://www.gov.br/iti/pt-br/assuntos/repositorio/lista-de-prestadores-de-servico-de-confianca-da-icp-brasil)
- [ITI — Verificador de Conformidade (VALIDAR)](https://app-verificador.iti.gov.br/)
- [ITI — API Verificador de Conformidade](https://antigo.iti.gov.br/aplicativos/111-aplicativos/4127-api-verificador-de-conformidade)
- [ITI — certificado digital em nuvem (FAQ)](https://www.gov.br/iti/pt-br/acesso-a-informacao/perguntas-frequentes/certificacao-digital)

**Base legal**
- [Lei 14.063/2020, art. 4º](https://www.jusbrasil.com.br/topicos/336997151/artigo-4-da-lei-n-14063-de-23-de-setembro-de-2020)
- [Classificação das assinaturas eletrônicas (UFVJM)](https://portal.ufvjm.edu.br/protic/central-de-servicos/assinatura-eletronica/classificacao-das-assinaturas-eletronicas)
- [Assinatura eletrônica avançada — orientações técnicas IRTDPJ](https://irtdpjbrasil.org.br/files/orientacoes-tecnicas/assinatura-eletronica-avancada.pdf)
- [MP 2.200-2, Lei 14.063 e jurisprudência](https://geracontratos.com.br/recursos/lei-assinatura-eletronica-brasil)
- [Modalidades e cautelas (Lexology)](https://www.lexology.com/library/detail.aspx?g=6c746239-f99d-40ca-9b31-eb2e9ddf4578)
- [STJ admite assinaturas fora da ICP-Brasil (Migalhas)](https://www.migalhas.com.br/quentes/451284/stj-admite-assinaturas-digitais-fora-da-icp-brasil-entenda-o-tema)

**Implementação**
- [pyHanko — Signing functionality](https://docs.pyhanko.eu/en/latest/lib-guide/signing.html)
- [pyHanko — interrupted signing sem certificado inicial (discussão #453)](https://github.com/MatthiasValvekens/pyHanko/discussions/453)
- [VaultID/BirdID — docs de assinatura em nuvem](https://docs.vaultid.com.br/workspace/cloud/api/uso-de-certificado/assinatura-digital)
- [Certillion — provedores de certificado em nuvem suportados](https://certillion.com/en/api/overview/)
- [AARB — ITI atualiza políticas de assinatura (DOC-ICP-15.03)](https://www.aarb.org.br/newsletter/iti-atualiza-politicas-de-assinatura-da-icp-brasil-doc-icp-15-03/)
