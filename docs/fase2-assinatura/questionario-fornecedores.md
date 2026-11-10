# Fase 2 — Perguntas ao fornecedor de certificado em nuvem (PSC): Soluti

**Destinatário:** **Soluti** (Bird ID / VaultID). O e-CNPJ da instituição já está lá
(D1) e o cliente deixou a escolha conosco (D3). Os demais PSC (Valid/VIDaaS,
Safeweb/SafeID, Serpro/NeoID) ficam como alternativa, se a Soluti for inviável em
alguma pergunta ⚙️.

**Revisão de 2026-11-10:** o questionário foi reescrito depois das respostas do
cliente (`respostas-cliente.md`, 2026-10-13 e devolutiva de 2026-11-09) e
**dividido em dois envios**, para públicos diferentes:

| Envio | Para quem | Canal | Objetivo |
|---|---|---|---|
| **A — Comercial e contratual** | gerente de conta / comercial da Soluti | relacionamento do e-CNPJ existente, aberto por Compras/TI da INSTITUTO SETES | números para a Direção (custos, pendência 6) e caminho de contratação (D4) |
| **B — Técnico de integração** | pré-venda técnica / time de integração | INSTITUTO SETES, com o fornecedor do Despapelize em cópia (respostas técnicas direto a nós) | fechar as perguntas que mudam a arquitetura e o cronograma |

**Os dois envios podem sair no mesmo dia.** Nenhum depende da resposta do outro.

### Convenções

- ⚙️ = **a resposta muda nossa arquitetura ou nosso custo de infraestrutura.**
- ⏱ = **a resposta entra no caminho crítico do cronograma** (H1 = 11/2026).
- **A numeração é estável**: os números 1.1–8.5 são os mesmos da versão de
  2026-10-08, já citados no `README.md`, em `respostas-cliente.md` e em
  `estudo-tecnico.md`. As perguntas novas recebem números novos dentro da seção
  (ex.: 2.9, 7.6) ou seções novas (9 e 10). Uma seção pode ter perguntas nos dois
  envios: o número identifica a pergunta, o envio só define quem a recebe.
- Entre colchetes, a resposta do cliente que originou ou alterou a pergunta
  (ex.: **[D2]**).

---

# ENVIO A — Comercial e contratual

## Texto de apresentação (Envio A)

> Somos a **INSTITUTO SETES**, já cliente da Soluti (e-CNPJ). Estamos implantando
> assinatura digital **ICP-Brasil em nuvem** no nosso sistema interno de processos
> administrativos (Despapelize), desenvolvido por fornecedor contratado, que está em
> cópia e conduzirá a parte técnica.
>
> **Perfil de uso:**
> - cerca de **10 signatários**, todos pessoa física assinando em nome próprio
>   (e-CPF; não assinaremos com e-CNPJ);
> - documentos de movimentação de pessoal, compras, contratação de serviços e
>   pagamentos, gerados pelo próprio sistema em PDF;
> - volume estimado: **centenas de assinaturas por ano**, várias com mais de um
>   signatário no mesmo documento;
> - **carimbo de tempo** em todas as assinaturas;
> - implantação começando por um **piloto em uma unidade**.
>
> Gostaríamos de entender modelos de contratação e custos para esse perfil.

## 5. Carimbo de tempo (ACT): comercial

| # | Pergunta | Por que importa |
|---|---|---|
| 5.1 | Vocês operam **ACT própria** (RFC 3161), ou precisamos contratar o carimbo separadamente, com outra empresa? | Define se a `assinatura-carimbo-tempo` traz um segundo contrato. |
| 5.2 | Preço **por carimbo**. Há franquia ou pacote? | Custo recorrente por assinatura. O cliente prefere evitar custo por uso **[D5]**, mas decidiu pelo carimbo **[E1, devolutiva 3]**. Precisamos do número real. |
| 5.5 ⚙️ (nova) | Oferecem **carimbo de documento** para manter a verificabilidade de longo prazo (reaplicação periódica, padrão PAdES-LTA)? Com que preço e periodicidade? | O prazo de guarda depende do tipo de documento e a tabela ainda não veio **[E2, F2]**. Carimbo de longo prazo é custo recorrente **por documento guardado**, não só por assinatura. |

## 6. Ciclo de vida do certificado do titular: comercial e operação

| # | Pergunta | Por que importa |
|---|---|---|
| 6.1 | **Validade** oferecida (1, 3, 5 anos)? | Custo por pessoa por período. |
| 6.2 | A emissão por **videoconferência** está disponível, ou exige comparecimento presencial? | Deslocamento é custo e atrito de adoção. |
| 6.3 | Como é a **renovação**? Precisa repetir a validação presencial ou por videoconferência? | — |
| 6.4 | Se o titular **perder o celular**: qual o processo de recadastro do dispositivo e em quanto tempo ele volta a assinar? | O funcionário fica sem assinar nesse intervalo. Com assinatura obrigatória para algumas classes de documento **[B2]**, isso para a tramitação. |
| 6.6 | Há **painel administrativo** para a instituição acompanhar os certificados dos seus funcionários (emitidos, a vencer, revogados)? Ele funciona se o certificado foi **comprado pelo próprio funcionário**? | Gestão pela SETES sem planilha. A segunda parte vem de **[D2]**. |

## 7. Comercial

| # | Pergunta | Por que importa |
|---|---|---|
| 7.1 | Modelo de cobrança do certificado: por pessoa/ano? Há desconto por volume? | — |
| 7.2 ⚙️ | Há **custo por assinatura** ou por chamada de API, além do certificado? Franquia, créditos ou ilimitado? | O cliente prefere evitar custo por uso **[D5]**. Se houver, precisa ir à Direção antes da contratação. |
| 7.3 | Há **mínimo de contratação** (quantidade ou valor)? | — |
| 7.4 | Há componente **pago à parte** para formatos padronizados? No Bird ID há menção a um componente "CESS" para PAdES/CAdES/XAdES e ao "Bird ID Pro", com licenciamento próprio. Nosso plano é montar o PAdES do nosso lado: isso dispensa esse componente? | Evita pagar por algo que não usaremos. |
| 7.5 | Prazo de vigência e condições de reajuste. | — |
| 7.6 (nova) | Preço do e-CPF em nuvem **avulso** (comprado pela pessoa) comparado com um **pacote corporativo de ~10** comprado pela instituição. | Hoje cada funcionário paga o seu **[D2]**. Com ~10 pessoas, a instituição custear todos pode ter custo marginal e eliminar o risco de recusa (pendência 6). A Direção precisa dos dois números. |
| 7.7 (nova) | Existe modelo **corporativo**, em que a instituição compra e gerencia os certificados dos seus funcionários? O certificado continua sendo do titular? | Alternativa ao modelo de **[D2]**. |
| 7.8 (nova) | Com o perfil de uso do texto de apresentação, qual a **estimativa de custo anual total**: certificados, uso de API, carimbos de tempo e credencial da aplicação? | Número único para levar à Direção. |
| 7.9 (nova) | A contratação pode começar **pequena, para um piloto** em uma unidade, e crescer sem renegociar o contrato? | O cliente quer piloto primeiro **[H2]**. |

## 9. Proteção de dados (LGPD): contratual

| # | Pergunta | Por que importa |
|---|---|---|
| 9.3 (nova) | No serviço de assinatura em nuvem, a Soluti se considera **operadora** (trata dados em nome da instituição) ou **controladora** dos dados do titular? | Define o papel da Soluti no registro de tratamento e o que vai no contrato. |
| 9.4 (nova) | Existe **acordo de tratamento de dados** (DPA) ou cláusula LGPD padrão para a contratação da aplicação? Podemos receber uma cópia antes? | O DPO precisa analisar. A ratificação de F1 pelo DPO já está pendente (pendência 4). |
| 9.5 (nova) | Onde ficam os dados tratados (país)? Há **suboperadores**, por exemplo nuvem pública? | Nosso sistema roda nos EUA (`us-central1`), com transferência internacional documentada. Precisamos saber se a Soluti acrescenta outra. |

## 10. Contratação

| # | Pergunta | Por que importa |
|---|---|---|
| 10.1 ⏱ (nova) | A contratação da integração (aplicação cadastrada para assinar em nuvem) pode partir do **relacionamento atual do e-CNPJ**, ou é outro produto, com canal comercial próprio (por exemplo VaultID)? Quem é o contato? | O contrato pode ser iniciado "desde já" **[D4]**. Precisamos saber por onde. |
| 10.2 ⏱ (nova) | Quais **documentos** a instituição precisa apresentar e qual o **prazo** entre assinatura do contrato e liberação do acesso (sandbox e produção)? | O prazo é o caminho crítico. Ver também 3.5 no Envio B. |
| 10.3 (nova) | O contratante é a **INSTITUTO SETES**, assinado por **Ademilton Leal Coutinho, Diretor Presidente** **[D4, A5]**. O desenvolvedor do sistema pode ser o contato técnico no cadastro da aplicação, ou isso exige procuração ou outro instrumento? | Define quem opera o cadastro do lado da Soluti. Ver 3.4 no Envio B. |

---

# ENVIO B — Técnico de integração

## Texto de apresentação (Envio B)

> Somos o fornecedor do **Despapelize**, sistema de gestão de processos
> administrativos da **INSTITUTO SETES**, cliente da Soluti (e-CNPJ). A instituição
> está contratando assinatura em nuvem com vocês. A parte comercial segue em
> paralelo, pelo gerente de conta.
>
> Precisamos de assinatura **PAdES** em PDFs gerados pelo próprio sistema, com
> certificado **e-CPF em nuvem**, acionada **pelo navegador, sem instalação de
> software no computador do usuário**. Alvo de política: **PAdES AD-RT** (com
> carimbo de tempo).
>
> **Stack:** backend Python/FastAPI em **Google Cloud Run** (`us-central1`, EUA),
> frontend Next.js. Pretendemos montar a estrutura PAdES do nosso lado com
> **pyHanko**, em fluxo de assinatura diferida: **enviamos apenas o hash**,
> recebemos a assinatura e a embutimos no PDF.
>
> **Volume:** cerca de **10 signatários** (pessoa física, e-CPF), centenas de
> assinaturas por ano, com coassinatura frequente no mesmo documento.
>
> **Duas restrições nossas, não negociáveis:**
> 1. Nunca custodiamos chave privada de titular.
> 2. Nunca coletamos PIN estático de certificado. Se houver coleta de fator pela nossa
>    aplicação, apenas pelo serviço **"Autorização com Credenciais do Titular"** do
>    DOC-ICP-17.01, com fator de uso único (OTP).
>
> **As perguntas marcadas ⚙️ e ⏱ são as que mais nos ajudam a responder primeiro.**
> Podemos receber a documentação de API antes do contrato (8.1)?

## Prioridade de resposta (Envio B)

```
1º  3.1 · 3.5        certificado SSL exigido? prazos?     ⏱ caminho crítico
2º  1.1 · 1.5        modelo e duração da autorização      ⚙️ tamanho do frontend
3º  4.1              allowlist de IP?                     ⚙️ Cloud NAT + custo
4º  2.1 · 2.4        só hash? formato de saída?           ⚙️ plano pyHanko
5º  4.4 · 8.1        sandbox? documentação antes?         ⏱ testes antes do contrato
    o resto          pode chegar depois
```

## 1. Modelo de autorização  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 1.1 ⚙️ | Qual(is) serviço(s) de autorização vocês expõem: **"Autorização com Credenciais do Titular"** (fator coletado pela nossa aplicação e enviado no parâmetro `password`), **redirect** OAuth2 para uma página de vocês, **push** para o app, ou mais de um? | **É a pergunta de maior impacto no frontend.** Com credenciais do titular, basta um campo de código. Com redirect, o frontend precisa de um fluxo de saída e retorno que hoje não existe (a autenticação é própria, sem SSO). |
| 1.2 | Quais **tipos de fator** são aceitos: OTP (TOTP/HOTP, RFC 6238/6287/4226), biometria, push, certificado de atributo? | Define a tela e as mensagens de erro. |
| 1.3 | Suportam algum fator que **não dependa de smartphone**, como token OTP de hardware ou autenticador de desktop? | Rebaixada: todos os signatários têm celular **[C1]**. Continua útil como contingência para celular perdido (6.4). |
| 1.4 | Suportam **PKCE** (RFC 7636)? Obrigatório ou opcional? | — |
| 1.5 ⚙️ | **Duração da autorização:** uma assinatura por autorização, ou o token vale por horas ou dias e permite várias assinaturas? Há limite de assinaturas por token? | Define se o usuário autoriza a cada documento ou uma vez por turno. Afeta UX e o desenho da sessão de assinatura. Com coassinatura frequente **[B3]**, autorizar a cada documento pesa. |
| 1.6 | O fluxo é **síncrono** (resposta na mesma chamada) ou há **webhook/callback** de conclusão? | Cloud Run com `min-instances=0`: webhook exige endpoint público adicional. |
| 1.7 | Qual o **timeout** da autorização pendente? E o comportamento se o titular não responder? | Define o TTL da nossa sessão de assinatura. |
| 1.8 (nova) | Como **identificamos o titular** ao iniciar a autorização: CPF como dica de login, e-mail, outro? | Define se precisamos guardar o CPF do signatário antes da primeira assinatura (dado pessoal, LGPD). |

## 2. Contrato de assinatura  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 2.1 ⚙️ | O endpoint de assinatura aceita **apenas o hash** do documento, sem o arquivo? | Requisito nosso: o PDF não sai da nossa infraestrutura. |
| 2.2 | Codificação do hash: **hexadecimal** ou base64? | — |
| 2.3 | Algoritmos de digest suportados: **SHA-256 / SHA-384 / SHA-512**? | Precisa casar com a política ICP-Brasil vigente (DOC-ICP-01.01). |
| 2.4 ⚙️ | Formatos de saída: **RAW (PKCS#1 v1.5)**, **CMS-detached**, **PAdES completo**? | Se devolverem RAW/CMS, montamos o PAdES com pyHanko (nosso plano). Se oferecerem PAdES pronto, pode simplificar, mas perdemos controle sobre os atributos assinados. |
| 2.5 ⚙️ | Se oferecem PAdES: atendem às políticas **AD-RB** e **AD-RT** do DOC-ICP-15? Qual OID de política aplicam? | A alternativa é montarmos os atributos assinados (`signaturePolicyId`, `signingCertificateV2`) à mão. |
| 2.6 | Como obtemos a **cadeia de certificados do titular** (para embutir no CMS) antes ou junto da assinatura? Há endpoint de descoberta de certificados? | Na assinatura diferida do pyHanko, sem o certificado no início, `bytes_reserved` passa a ser obrigatório. Precisamos dimensionar. |
| 2.7 | Suportam **assinatura de múltiplos hashes em uma chamada** (lote)? | Vários documentos de um processo de uma vez. |
| 2.8 | Há **rate limit** por aplicação ou por titular? Quais os limites? | — |
| 2.9 (nova) | **Coassinatura:** titulares diferentes assinam o mesmo PDF em sequência (assinaturas incrementais), cada um com sua autorização. Há alguma restrição ou recomendação do lado de vocês? | Coassinatura é comum no cliente **[B3]**. |

## 3. Autenticação da aplicação  ⚙️ ⏱ (o prazo mais longo do projeto)

| # | Pergunta | Por que importa |
|---|---|---|
| 3.1 ⚙️⏱ | Exigem **certificado SSL ICP-Brasil** para o cadastro da aplicação, conforme o DOC-ICP-17.01? Em produção **e** em sandbox, ou só em produção? | É item de compra com semanas de lead time. Se o sandbox dispensar, começamos a integração antes da emissão. **Bloqueia a change `assinatura-qualificada-psc`.** |
| 3.2 ⚙️ | O certificado é usado em **mTLS** na chamada, em `client_id`/`client_secret`, ou nos dois? | Define como configuramos o cliente HTTP e o que guardamos no Secret Manager. |
| 3.3 | Qual o **tipo exato** do certificado exigido (certificado SSL A1 de aplicação/servidor? e-CNPJ? outro)? Quais ACs vocês aceitam? | Para cotar o produto certo, que não é o mesmo que e-CNPJ de assinatura. |
| 3.4 | O certificado precisa estar no nome da **instituição titular do sistema** (INSTITUTO SETES), ou pode ser da **empresa desenvolvedora**? | Muda quem compra e quem apresenta documentos. Ver 10.3 no Envio A. |
| 3.5 ⏱ | **Prazo** de (a) emissão do certificado e (b) aprovação do cadastro da aplicação do lado de vocês? | É o caminho crítico do cronograma. |
| 3.6 | Qual a **validade** desse certificado e como é a renovação? Há aviso prévio de vencimento? | O vencimento derruba a assinatura com falha de TLS. Precisamos de runbook e alerta. |
| 3.7 | Qual versão do **DOC-ICP-17.01** vocês implementam hoje (a vigente é a v3.0)? Podem nos indicar ou enviar o documento? | Não conseguimos abrir a v3.0; nossa análise se baseia na v2.x (`estudo-tecnico.md` §9.1). |
| 3.8 (nova) | O **e-CNPJ que a instituição já tem com a Soluti** serve, de alguma forma, como credencial da aplicação? Ou é obrigatório outro certificado? | Se servir, reduz o lead time de 3.5 **[D1]**. A instituição não usará o e-CNPJ para assinar documentos **[B5]**. |

## 4. Rede  ⚙️

| # | Pergunta | Por que importa |
|---|---|---|
| 4.1 ⚙️ | Exigem **allowlist de IP de origem**? | **Decisivo.** Hoje nosso Cloud Run usa `egress = PRIVATE_RANGES_ONLY`: o tráfego externo sai pelo pool compartilhado e rotativo do Google, **sem IP fixo**. Se exigirem allowlist, precisamos de Cloud Router + Cloud NAT com IP estático, com Terraform novo e custo mensal novo. |
| 4.2 | Quais **domínios e portas** precisamos liberar na saída? Incluindo ACT, OCSP e LCR. | — |
| 4.3 ⚙️ | Há restrição geográfica de origem das chamadas? Nossa infraestrutura está em **`us-central1` (EUA)**. | Pode ser impeditivo ou exigência contratual. |
| 4.4 ⏱ | Oferecem **sandbox**? Com certificados de teste? É gratuito? Quais as diferenças de comportamento em relação à produção? Dá para acessar **antes** do contrato? | Sem sandbox, não há como construir os testes automatizados obrigatórios antes da contratação. |

## 5. Carimbo de tempo (ACT): técnico

| # | Pergunta | Por que importa |
|---|---|---|
| 5.3 | A mesma credencial ou certificado da aplicação serve para a ACT, ou são contrato e autenticação separados? | Mais um segredo e mais um vencimento a monitorar. |
| 5.4 | Rate limit e SLA da ACT? | Se a ACT cair, a assinatura AD-RT falha. Precisamos decidir se degradamos para AD-RB ou abortamos. |
| 5.6 (nova) | Os endpoints de **OCSP e LCR** das ACs que emitem os e-CPF e os carimbos têm disponibilidade e retenção garantidas? Por quanto tempo? | Para embutir dados de validação no PDF (LTV) e manter a verificação de longo prazo **[E2]**. |

## 6. Ciclo de vida do certificado do titular: técnico

| # | Pergunta | Por que importa |
|---|---|---|
| 6.5 | Como consultamos programaticamente se o certificado de um titular está **válido, vencido ou revogado**, antes de tentar assinar? | Evita falha no meio do fluxo e atende ao cenário de certificado inválido do PRD (US 4.1 Cen.2). |
| 6.7 (nova) | A aplicação aceita e-CPF em nuvem **emitido por outra AC/PSC**, que o funcionário já tenha? Ou só os da Soluti? | Cada funcionário paga o seu **[D2]**, e alguns podem já ter certificado de outro fornecedor. |
| 6.8 (nova) | Como a **autorização dada à nossa aplicação é revogada**, pelo titular e pela instituição? Por exemplo, quando o funcionário sai: o certificado é dele, mas o vínculo com o sistema é da instituição. | Desligamento de funcionário **[F4]** com celular pessoal **[C2]**. |
| 6.9 (nova) | Um titular pode ter o aplicativo autorizador em **mais de um aparelho**? | Celular pessoal e corporativo coexistem **[C2]**. |

## 8. Documentação e suporte

| # | Pergunta | Por que importa |
|---|---|---|
| 8.1 ⏱ | A documentação de API é **pública** ou sob NDA? Podemos acessá-la **antes** de contratar, para avaliar viabilidade? | Permite desenhar a change antes do contrato. |
| 8.2 | Há SDK, coleção Postman ou exemplo de referência em **Python**? | — |
| 8.3 | **SLA** de disponibilidade do serviço de assinatura. Há página de status pública e histórico de incidentes? | — |
| 8.4 | Canal de suporte técnico **para integradores** (não o suporte ao usuário final). | — |
| 8.5 | Há **compatibilidade declarada com pyHanko**, ou algum caso de assinatura diferida em que só o hash trafega? Conhecem clientes nesse modelo? | — |
| 8.6 (nova) | Há **mudança normativa prevista** na ICP-Brasil (por exemplo, nova arquitetura de certificados) que afete integrações nos próximos anos? | Pergunta de cortesia. A informação apareceu com baixa confiança no estudo (`estudo-tecnico.md` §9.6). A fonte primária é o ITI. |

## 9. Proteção de dados (LGPD): técnico

| # | Pergunta | Por que importa |
|---|---|---|
| 9.1 (nova) | Quais dados vocês **registram** a cada autorização e assinatura (CPF, hash, IP de origem, horário, dispositivo)? | Entra no registro de tratamento e na proposal da change (tratamento LGPD declarado é regra vinculante). |
| 9.2 (nova) | Por quanto tempo esses registros são mantidos? A instituição pode obtê-los, por exemplo como prova em disputa? | Complementa nossa trilha de auditoria. |

---

## Fora deste questionário (verificação nossa ou junto ao ITI)

Não são perguntas para a Soluti; ficam em `estudo-tecnico.md` §9:

- API do VALIDAR do ITI: hospedada ou instalável (§9.3). Alimenta a
  `assinatura-verificacao-fundacao`, que não depende de fornecedor.
- OIDs e atributos obrigatórios do DOC-ICP-15.03 (§9.4): ler na fonte.
- DOC-ICP-17.01 v3.0 (§9.1): pedido à Soluti em 3.7, mas a fonte é o ITI.

---

## Como usar as respostas

1. **Envio B: comparar primeiro 3.1, 3.5, 1.1, 1.5, 4.1 e 2.4.** São as que mudam a
   arquitetura e o cronograma. Se alguma for inviável na Soluti (ex.: exige IP fixo
   e só redirect com autorização por documento), reabrir a comparação com os outros
   PSC antes de contratar.
2. **3.5 e 10.2 entram no cronograma imediatamente**, em paralelo à
   `assinatura-verificacao-fundacao`, que não depende de fornecedor. A soma dos dois
   prazos diz se 11/2026 **[H1]** é real para alguma parte do caminho qualificado.
3. **Envio A: 7.6, 7.7 e 7.8 voltam para a Direção.** Com os números, a Direção
   decide se mantém "cada funcionário paga o seu" **[D2]**. Essa decisão é a
   pendência 6, que bloqueia a `assinatura-qualificada-psc`.
4. **5.2, 5.5 e 7.2 voltam para a Direção** como custo recorrente anual, porque o
   cliente prefere evitar custo por uso **[D5]**.
5. **9.1–9.5 vão para o DPO** junto com a ratificação de F1 (pendência 4).
6. **1.3, 6.2 e 6.4 voltam para o cliente** se revelarem restrição de adoção ou
   custo de operação.
7. Registrar as respostas na tabela abaixo e atualizar `estudo-tecnico.md` §9 conforme
   os pontos forem sendo fechados. Quando a credencial e o certificado da aplicação
   forem emitidos, atualizar a pendência 8 em `respostas-cliente.md` e o bloqueio (a)
   da `assinatura-qualificada-psc` em `openspec/config.yaml`.

---

## Registro dos envios

| Envio | Destinatário (nome / área) | Enviado por | Data | Respondeu? | Observações |
|---|---|---|---|---|---|
| A — Comercial | | Compras/TI INSTITUTO SETES | | ⬜ | |
| B — Técnico | | Compras/TI INSTITUTO SETES | | ⬜ | |

## Registro das respostas prioritárias

| # | Resposta da Soluti | Consequência para nós |
|---|---|---|
| 3.1 | | |
| 3.5 | | |
| 1.1 | | |
| 1.5 | | |
| 4.1 | | |
| 2.4 | | |
| 4.4 | | |
| 8.1 | | |
| 7.6 / 7.8 | | |
| 10.1 / 10.2 | | |

As demais respostas podem ser registradas em `respostas-fornecedores.md`, ao lado,
preservando a numeração.
