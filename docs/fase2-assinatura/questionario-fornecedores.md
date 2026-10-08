# Fase 2 — Perguntas aos fornecedores de certificado em nuvem (PSC)

**Público:** equipe técnica / pré-venda de PSC credenciado pela ICP-Brasil.
**Diferente do `questionario-cliente.md`:** ali o público é não técnico; **aqui jargão é
esperado** — quem responde é integrador.

**Destinatários pretendidos:** Soluti/VaultID (Bird ID), Valid (VIDaaS), Safeweb
(SafeID), Serpro (NeoID/SerproID), e eventuais intermediários.

⚙️ = **a resposta muda nossa arquitetura ou nosso custo de infraestrutura.** Priorizar.

> **Quando enviar:** só depois das respostas de A1/A2 do `questionario-cliente.md`
> confirmarem o caminho **qualificado**. Se a SETES ficar no caminho avançado, este
> questionário não é necessário.

---

## Contexto a enviar junto (para a resposta vir útil)

> Somos o fornecedor do **Despapelize**, sistema de gestão de processos administrativos
> de uma instituição privada. Precisamos de assinatura **PAdES** em PDFs gerados pelo
> próprio sistema, com certificado **e-CPF A3 em nuvem**, acionada **pelo navegador,
> sem instalação de software no computador do usuário**.
>
> **Stack:** backend Python/FastAPI em **Google Cloud Run** (`us-central1`), frontend
> Next.js. Pretendemos montar a estrutura PAdES do nosso lado com **pyHanko**, em
> fluxo de assinatura diferida: **enviamos apenas o hash**, recebemos a assinatura e
> embutimos no PDF.
>
> **Volume estimado:** a confirmar (ordem de dezenas de signatários; dezenas a
> centenas de assinaturas/mês).
>
> **Duas restrições nossas, não negociáveis:**
> 1. Nunca custodiamos chave privada de titular.
> 2. Nunca coletamos PIN estático de certificado. Se houver coleta de fator pela nossa
>    aplicação, apenas via o serviço **"Autorização com Credenciais do Titular"** do
>    DOC-ICP-17.01, com fator de uso único (OTP).

---

## 1. Modelo de autorização  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 1.1 ⚙️ | Qual(is) serviço(s) de autorização vocês expõem: **"Autorização com Credenciais do Titular"** (fator coletado pela nossa aplicação e enviado no parâmetro `password`), **redirect** OAuth2 para página de vocês, **push** para o app, ou mais de um? | **É a pergunta de maior impacto no frontend.** Com credenciais do titular, basta um campo de código. Com redirect, o `apps/web` precisa de um fluxo de saída e retorno que hoje não existe no projeto (autenticação é JWT próprio, sem SSO). |
| 1.2 | Quais **tipos de fator** são aceitos: OTP (TOTP/HOTP, RFC 6238/6287/4226), biometria, push notification, certificado de atributo? | Define a tela e a mensagem de erro. |
| 1.3 ⚙️ | Vocês suportam algum fator que **não dependa de smartphone** — token OTP de hardware, autenticador de desktop? | Parte do quadro da cliente pode não ter smartphone. Se a resposta for "não", é restrição de adoção que precisa ir ao cliente antes da compra. |
| 1.4 | Suportam **PKCE** (RFC 7636)? Obrigatório ou opcional? | — |
| 1.5 ⚙️ | **Duração da autorização:** uma assinatura por autorização, ou o token vale por horas/dias permitindo várias assinaturas? | Define se o usuário autoriza a cada documento ou uma vez por turno. Impacta UX e o desenho da `SessaoAssinatura`. |
| 1.6 | O fluxo é **síncrono** (resposta na mesma chamada) ou há **webhook/callback** de conclusão? | Cloud Run com `min-instances=0` — webhook exige endpoint público adicional. |
| 1.7 | Qual o **timeout** da autorização pendente? E o comportamento se o titular não responder? | Define o TTL da nossa sessão de assinatura. |

---

## 2. Contrato de assinatura  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 2.1 ⚙️ | O endpoint de assinatura aceita **apenas o hash** do documento, sem o arquivo? | Requisito nosso: o PDF não sai da nossa infraestrutura. |
| 2.2 | Codificação do hash: **hexadecimal** ou base64? | — |
| 2.3 | Algoritmos de digest suportados: **SHA-256 / SHA-384 / SHA-512**? | Precisa casar com a política ICP-Brasil vigente (DOC-ICP-01.01). |
| 2.4 ⚙️ | Formatos de saída: **RAW (PKCS#1 v1.5)**, **CMS-detached**, **PAdES completo**? | Se devolverem RAW/CMS, montamos o PAdES com pyHanko (nosso plano). Se oferecerem PAdES pronto, pode simplificar — mas perdemos controle sobre os atributos assinados. |
| 2.5 ⚙️ | Se oferecem PAdES: atendem às políticas **AD-RB** e **AD-RT** do DOC-ICP-15? Qual OID de política aplicam? | A alternativa é montarmos os atributos assinados (`signaturePolicyId`, `signingCertificateV2`) à mão. |
| 2.6 | Como obtemos a **cadeia de certificados do titular** (para embutir no CMS) antes ou junto da assinatura? Há endpoint de descoberta de certificados? | pyHanko em assinatura diferida permite não conhecer o certificado no início, mas então `bytes_reserved` passa a ser obrigatório — precisamos dimensionar. |
| 2.7 | Vocês suportam **assinatura de múltiplos hashes em uma chamada** (lote)? | Coassinatura e assinatura de vários documentos de um processo. |
| 2.8 | Há **rate limit** por aplicação ou por titular? Quais os limites? | — |

---

## 3. Autenticação da aplicação  ⚙️ — e o prazo mais longo do projeto

| # | Pergunta | Por que importa |
|---|---|---|
| 3.1 ⚙️ | Exigem **certificado SSL ICP-Brasil** para o cadastro da aplicação, conforme DOC-ICP-17.01? Em produção **e** em sandbox, ou só produção? | É item de compra com semanas de lead time. Se sandbox dispensa, começamos a integração antes da emissão. |
| 3.2 ⚙️ | O certificado é usado em **mTLS** na chamada, em `client_id`/`client_secret`, ou nos dois? | Define como configuramos o cliente HTTP e o que guardamos no Secret Manager. |
| 3.3 | Qual o **tipo exato** do certificado exigido (certificado de aplicação/servidor SSL A1? e-CNPJ? outro)? Quais ACs vocês aceitam? | Para cotar o produto certo — não é o mesmo que e-CNPJ de assinatura. |
| 3.4 | O certificado precisa estar no nome da **instituição titular do sistema** (SETES), ou pode ser da **empresa desenvolvedora**? | Muda quem compra e quem fornece documentos. |
| 3.5 ⚙️ | **Prazo** de (a) emissão do certificado e (b) aprovação do cadastro da aplicação do lado de vocês? | É o caminho crítico do cronograma. |
| 3.6 | Qual a **validade** desse certificado e como é a renovação? Há aviso prévio de vencimento? | Vencimento derruba a assinatura com falha de TLS. Precisamos de runbook e alerta. |
| 3.7 | Qual a versão do **DOC-ICP-17.01** que vocês implementam hoje (v3.0 é a vigente)? | Não conseguimos abrir a v3.0; nossa análise se baseia na v2.x. |

---

## 4. Rede  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 4.1 ⚙️ | Exigem **allowlist de IP de origem**? | **Decisivo.** Hoje nosso Cloud Run usa `egress = PRIVATE_RANGES_ONLY`: o tráfego externo sai pelo pool compartilhado e rotativo do Google, **sem IP fixo**. Se exigirem allowlist, precisamos de Cloud Router + Cloud NAT com IP estático — Terraform novo e custo mensal novo. |
| 4.2 | Quais **domínios e portas** precisamos liberar na saída? | — |
| 4.3 | Há restrição geográfica de origem das chamadas? Nossa infraestrutura está em **`us-central1` (EUA)**. | Possível impeditivo ou exigência contratual. Vale perguntar explicitamente. |
| 4.4 | Oferecem **sandbox**? Com certificados de teste? É gratuito? Quais as diferenças de comportamento em relação à produção? | Sem sandbox, não há como construir os testes automatizados antes do contrato. |

---

## 5. Carimbo de tempo (ACT)

| # | Pergunta | Por que importa |
|---|---|---|
| 5.1 | Vocês operam **ACT própria** (RFC 3161) ou precisamos contratar separadamente? | Necessário para AD-RT, que é pré-requisito do cenário "válido na data da assinatura". |
| 5.2 | Preço **por carimbo**. Há franquia ou pacote? | Custo recorrente por assinatura — pergunta D5 do cliente. |
| 5.3 | A mesma credencial/certificado da aplicação serve para a ACT, ou é contrato e autenticação separados? | Mais um segredo e mais um vencimento a monitorar. |
| 5.4 | Rate limit e SLA da ACT? | Se a ACT cair, a assinatura AD-RT falha. Precisamos saber se degradamos para AD-RB ou abortamos. |

---

## 6. Ciclo de vida do certificado do titular

| # | Pergunta | Por que importa |
|---|---|---|
| 6.1 | **Validade** oferecida (1, 3, 5 anos)? | Custo por pessoa por período. |
| 6.2 | Emissão por **videoconferência** está disponível, ou exige comparecimento presencial? | Com dezenas de funcionários, deslocamento é custo e atrito reais de adoção. |
| 6.3 | Como é a **renovação**? Precisa repetir a validação presencial/videoconferência? | — |
| 6.4 | O titular **perdeu o celular**: qual o processo de recadastro do dispositivo e em quanto tempo ele volta a assinar? | Suporte operacional previsível — o funcionário fica sem assinar nesse intervalo. |
| 6.5 | Como consultamos programaticamente se o certificado de um titular está **válido, vencido ou revogado**, antes de tentar assinar? | Evita falha no meio do fluxo e atende ao cenário de certificado inválido do PRD (US 4.1 Cen.2). |
| 6.6 | Há **painel administrativo** para a instituição acompanhar certificados dos seus funcionários (emitidos, a vencer, revogados)? | Gestão pela SETES, sem depender de planilha. |

---

## 7. Comercial

| # | Pergunta |
|---|---|
| 7.1 | Modelo de cobrança do certificado: por pessoa/ano? Há desconto por volume? |
| 7.2 | Há **custo por assinatura** ou por chamada de API, além do certificado? Franquia, créditos ou ilimitado? |
| 7.3 | Há **mínimo de contratação** (quantidade ou valor)? |
| 7.4 | Existe componente **pago à parte** para formatos padronizados (p.ex. no Bird ID há menção a um componente "CESS" para PAdES/CAdES/XAdES, e ao "Bird ID Pro" com licenciamento próprio)? Nosso plano é montar o PAdES do nosso lado — isso dispensa esse componente? |
| 7.5 | Prazo de vigência e condições de reajuste. |

---

## 8. Documentação e suporte

| # | Pergunta |
|---|---|
| 8.1 | A documentação de API é **pública** ou sob NDA? Podemos ter acesso **antes** de contratar, para avaliar viabilidade? |
| 8.2 | Há SDK, coleção Postman ou exemplo de referência em **Python**? |
| 8.3 | **SLA** de disponibilidade do serviço de assinatura. Há página de status pública e histórico de incidentes? |
| 8.4 | Canal de suporte técnico **para integradores** (não o suporte ao usuário final). |
| 8.5 | Há **compatibilidade declarada com pyHanko** ou com algum caso de uso de assinatura diferida em que só o hash trafega? Conhecem clientes nesse modelo? |

---

## Como usar as respostas

1. **Comparar 1.1, 3.1, 4.1 e 2.4 entre os fornecedores primeiro.** São as quatro que
   mudam nossa arquitetura; o resto é comercial e pode ser negociado depois.
2. **1.3 e 6.2 voltam para o cliente.** Se nenhum fornecedor tiver fator sem
   smartphone, a resposta de C1 passa a ser restrição de adoção, não só informação. Se
   a emissão for presencial, é custo de operação que a SETES precisa aprovar.
3. **3.5 entra no cronograma imediatamente**, em paralelo ao desenvolvimento da fatia 1
   (verificação), que não depende de fornecedor nenhum.
4. Registrar as respostas aqui mesmo, numa tabela por fornecedor, ou em arquivo
   `respostas-fornecedores.md` ao lado — e atualizar `estudo-tecnico.md` §9 (pontos em
   aberto) conforme forem sendo fechados.

---

## Registro das respostas

| Fornecedor | Contato | Data do contato | Respondeu? | Observações |
|---|---|---|---|---|
| Soluti / VaultID (Bird ID) | | | ⬜ | |
| Valid (VIDaaS) | | | ⬜ | |
| Safeweb (SafeID) | | | ⬜ | |
| Serpro (NeoID / SerproID) | | | ⬜ | |
