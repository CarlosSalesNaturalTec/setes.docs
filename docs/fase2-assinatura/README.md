# Fase 2 — Assinatura Digital: dossiê de decisão

> **Status: AGUARDANDO RESPOSTAS DO CLIENTE.**
> O Épico 4 do PRD (Assinatura Digital) **continua fora de escopo**. Este dossiê é o
> insumo da decisão de retomada — ele **não** retoma o épico e **não** autoriza
> implementação.

Diretório não publicado: `mkdocs.yml` aponta `docs_dir: docs/manual`, então nada aqui
vai para o GitHub Pages.

---

## Para que serve este diretório

A Fase 2 (assinatura de documentos) está bloqueada por decisões que **não são
técnicas** — são jurídicas, de custo e de operação, e pertencem à SETES. Em
2026-10-08 foi feito um estudo técnico e dele saiu um questionário para o cliente.

Este dossiê existe para que **o trabalho não dependa de uma sessão de chat**: quando
as respostas chegarem, qualquer pessoa (ou agente) lê estes quatro arquivos e tem
todo o contexto necessário para gerar as changes.

| Arquivo | O que é | Estado |
|---|---|---|
| `README.md` | Este índice + o que fazer quando as respostas chegarem | — |
| `questionario-cliente.md` | 33 perguntas em linguagem não técnica, enviadas à SETES | ✅ enviado em 2026-10-08 |
| `questionario-fornecedores.md` | Perguntas técnicas aos PSC (público integrador, jargão esperado) | ⬜ **enviar só se o caminho for o qualificado** |
| `estudo-tecnico.md` | O estudo completo: normas, arquitetura, colisões com o código atual, infra GCP, fatiamento | ✅ consolidado |
| `respostas-cliente.md` | Onde colar as respostas quando voltarem | ⬜ **vazio — aguardando** |

As quatro perguntas aos fornecedores que mudam nossa arquitetura — e que valem ser
comparadas antes de qualquer negociação comercial: **1.1** (modelo de autorização →
define o frontend), **2.4** (formato de saída da assinatura), **3.1** (certificado SSL
exigido → prazo mais longo do cronograma) e **4.1** (allowlist de IP → define se
precisamos de Cloud NAT).

---

## 🔴 Os dois portões que bloqueiam a implementação

### Portão 1 — Retomada formal do Épico 4

`openspec/config.yaml` diz, textualmente:

> *"Não proponha changes de assinatura sem decisão explícita de retomada do épico;
> MP 2.200-2/2001 e normas ICP-Brasil só voltam a ser conformidade obrigatória nesse
> caso."*

O mesmo consta em `CLAUDE.md`. **Essa proibição está em vigor.** Quando a retomada for
decidida, três arquivos precisam ser atualizados **na mesma change**, senão o próximo
agente esbarra na proibição:

1. `openspec/config.yaml` — bloco `context`, parágrafo sobre assinatura digital
2. `CLAUDE.md` — seção "Assinatura digital ICP-Brasil (Épico 4 do PRD) está FORA DE ESCOPO"
3. `docs/PRD.md` — bloco de status no início do Épico 4 (linhas ~558-568)

### Portão 2 — A premissa original do PRD é tecnicamente impossível

`docs/PRD.md:569` condiciona o Épico 4 a um Discovery Técnico confirmar que os
certificados são compatíveis com "as APIs de assinatura disponíveis nos navegadores".
O plano de contingência foi acionado — ou seja, **o Discovery concluiu que não são**.
Essa conclusão é permanente: nenhum navegador dá acesso a token/smart card.

**Consequência:** retomar o Épico 4 **não é implementar o que ficou pendente.** Três
critérios de aceite do PRD descrevem algo tecnicamente impossível *e* proibido pela
norma ICP-Brasil (ver `estudo-tecnico.md`, seção 4):

| US | O que o PRD pede | Por que não fecha |
|---|---|---|
| 4.1 Cen.1 (`PRD.md:575`) | "insiro o PIN do certificado" | DOC-ICP-17.01 proíbe a aplicação coletar fatores de autenticação |
| 4.1 Cen.3 (`PRD.md:582`) | "PIN incorreto 3× → bloqueio 30min" | o bloqueio é do provedor; não sabemos *por que* a autorização falhou |
| 4.1 Cen.5 (`PRD.md:589`) | "token/smart card não conectado" | não existe token no fluxo de certificado em nuvem |

**Retomar o épico exige reescrever esses critérios no PRD**, não apenas implementá-los.

---

## O que fazer quando as respostas chegarem

### Passo 1 — Registrar as respostas

Colar em `respostas-cliente.md`, preservando a numeração (A1, A2, …). Anotar quem
respondeu e quando — a resposta de **F1** (LGPD) e a de **A5** precisam de nome
identificado, porque viram decisão registrada do controlador.

### Passo 2 — Ler as três respostas que definem o tamanho do projeto

```
A1 — os documentos assinados serão apresentados a alguém de fora da SETES?
C1 — as pessoas que vão assinar têm celular com aplicativo?
F1 — documentos assinados ficam fora da anonimização LGPD?
```

### Passo 3 — Derivar o caminho

```
A1 = "praticamente nunca"  +  A2 = "sem obrigação legal"
        │
        └──▶ CAMINHO AVANÇADO (Lei 14.063 art. 4º II)
             1 ou 2 changes · sem procurement · sem custo recorrente
             reaproveita a trilha de auditoria que já existe
             ⚠️ exige 2º fator no ato de assinar + termo de aceite no primeiro-acesso

A1 = "alguns"  →  A4 = "modelo misto aceito"
        │
        └──▶ CAMINHO HÍBRIDO  ← recomendação do estudo neste cenário
             avançado por padrão + qualificado para uma classe marcada
             cai de graça no modelo de dados (DocumentoAssinatura.nivel)

A1 = "com frequência"  ou  A2 = "existe obrigação"  ou  A3 = "sim"
        │
        └──▶ CAMINHO QUALIFICADO (ICP-Brasil)
             4 a 6 changes · certificado por pessoa · certificado SSL da SETES
             ⚠️ C1 pode inviabilizar na prática · D4 tem semanas de lead time
```

### Passo 4 — Mapa resposta → change

| Respostas | Change que viabilizam |
|---|---|
| A1, A2, A4, A5 | **decide se o projeto é 1 change ou 6** |
| G3, E2 | `assinatura-verificacao-fundacao` — fatia de custo zero, sem procurement |
| A4, B1, B2, B7, H4 | `assinatura-avancada` — 2º fator + termo de aceite |
| C1, D1–D4 | `assinatura-qualificada-psc` — **D4 é o item de prazo mais longo** |
| E1 | `assinatura-carimbo-tempo` — ou retirada da US 4.2 Cen.3 do escopo |
| B3 | `assinatura-coassinatura` — entra agora ou depois |
| F1, F2, F3 | regime de retenção + decisão LGPD registrada com nome |
| G1, G2 | escopo de exibição: consulta pública, Auditor, perfil |
| B1 | escopo de formato (só PDF gerado por modelo, ou também anexos) |

### Passo 5 — Ordem recomendada, independente do caminho

```
0. change de RETOMADA DO ÉPICO (os 3 arquivos do Portão 1
   + reescrita dos critérios de aceite do Portão 2)
        ▼
1. assinatura-verificacao-fundacao   ← começar aqui em qualquer cenário
   Verifica assinaturas de PDFs assinados FORA do sistema.
   Valor imediato · custo zero · zero procurement
   💡 derrisca o pedaço técnico mais difícil (validar cadeia ICP-Brasil)
      ANTES de a SETES comprar qualquer coisa
        ▼
2. assinatura-avancada  (ou  assinatura-qualificada-psc, conforme A1/A2)
        ▼
3. assinatura-carimbo-tempo    → se E1 = sim
4. assinatura-coassinatura     → se B3 = comum
5. assinatura-perfil-assinados → preenche o placeholder da US 1.5
```

### Passo 6 — Regras vinculantes que valem para qualquer uma dessas changes

De `openspec/config.yaml`, seção `rules` — nenhuma é opcional:

- **Teste automatizado** obrigatório: toca dados pessoais (CPF do signatário) e
  histórico de tramitação.
- **Teste E2E Playwright** obrigatório: documentos é fluxo crítico.
- **`pnpm gen:types` + commit de `packages/api-types`**: o CI falha no job de drift.
- **`docs/manual/**` atualizado + `mkdocs build --strict`**: tela nova e texto novo
  exibido ao usuário disparam a regra.
- **Cenário de "acesso negado" explícito** para toda regra de visibilidade.
- **Histórico imutável**: modelar como INSERT de novo evento, nunca UPDATE.
- **Migration Alembic** com revision sequencial escrita à mão (`NNNN_<slug>`), nunca
  `--autogenerate`.
- **Tratamento LGPD declarado** na proposal (CPF do signatário — ver `estudo-tecnico.md` §3).

---

## Linha do tempo

| Data | Evento |
|---|---|
| 2026-07-27 | Épico 4 movido para a Fase 2 — plano de contingência acionado |
| 2026-10-08 | Estudo técnico realizado; questionário enviado à SETES |
| — | ⬜ Respostas do cliente |
| — | ⬜ Decisão de retomada do épico |
| — | ⬜ Primeira change |
