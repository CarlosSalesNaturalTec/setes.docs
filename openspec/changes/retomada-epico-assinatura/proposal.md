## Why

Em 2026-10-13 a SETES respondeu as 33 perguntas de
`docs/fase2-assinatura/questionario-cliente.md`. As respostas estão transcritas em
`docs/fase2-assinatura/respostas-cliente.md` e **determinam o caminho da Fase 2**:
assinatura **qualificada (ICP-Brasil)**, por força de A1 ("os documentos saem da
instituição com frequência") e A3 ("há atos da PJ que vão a registro público") —
cada uma suficiente sozinha, segundo a árvore de decisão do
`docs/fase2-assinatura/README.md`.

Isso **não** autoriza implementar. Dois portões descritos naquele README continuam
fechados, e nenhum deles cai por decisão do cliente:

**Portão 1 — a proibição está em vigor.** `openspec/config.yaml:33` diz
textualmente *"Não proponha changes de assinatura sem decisão explícita de retomada
do épico"*. `CLAUDE.md:39` repete. Enquanto esses textos existirem como estão,
qualquer agente que leia o repositório é obrigado a recusar as changes de
assinatura — inclusive as que as respostas acabaram de viabilizar.

**Portão 2 — o PRD descreve um produto impossível.** O Épico 4 foi escrito sobre uma
premissa que o Discovery Técnico derrubou em definitivo:

> "assinar documentos utilizando seu certificado digital ICP-Brasil (e-CPF/e-CNPJ),
> **diretamente pelo navegador**" — `docs/PRD.md:569`

Nenhum navegador do mercado dá acesso a token ou smart card, e isso não é limitação
transitória (`docs/fase2-assinatura/estudo-tecnico.md` §1). Dessa premissa falsa
descendem três critérios de aceite que **não podem ser implementados como escritos**
— não por dificuldade, mas porque descrevem atos que a norma ICP-Brasil proíbe a
aplicação praticar:

| Critério | O que pede | Por que não fecha |
|---|---|---|
| US 4.1 Cen.1 (`PRD.md:575`) | "insiro o PIN do certificado" | DOC-ICP-17.01 proíbe a aplicação coletar fatores de autenticação |
| US 4.1 Cen.3 (`PRD.md:582`) | "PIN incorreto 3× → bloqueio 30min" | o bloqueio é do provedor; não sabemos *por que* a autorização falhou |
| US 4.1 Cen.5 (`PRD.md:589`) | "token/smart card não conectado" | não existe token no fluxo de certificado em nuvem |

Se o Portão 1 cair sem o Portão 2 cair junto, a próxima change de assinatura vai
implementar critérios de aceite impossíveis, descobrir isso no meio do caminho, e
reabrir uma discussão que já está resolvida.

Além dos dois portões, as respostas **reduziram o escopo** do épico em cinco pontos
(B1, B5, B6, G1, H3). Esses recortes precisam estar no PRD *antes* da primeira
change de implementação, senão ela será desenhada sobre escopo que o cliente já
descartou.

Este change é, portanto, a condição de possibilidade de todas as demais: ele torna o
PRD verdadeiro e troca uma proibição absoluta por uma condicional.

**Este change não implementa assinatura.** Não há código, migration, endpoint, tela
nem capability nova. Ele altera três arquivos de documentação e regras.

## What Changes

### Portão 1 — a proibição vira condicional, não desaparece (D1)

- **`openspec/config.yaml`**, bloco `context`, parágrafo de assinatura: a proibição
  absoluta ("não proponha changes de assinatura") é substituída pelo registro da
  retomada **e por uma lista nomeada de pendências que continuam bloqueando**. O
  guard-rail não é removido — passa a apontar para condições verificáveis.
- **`CLAUDE.md`**, seção "Assinatura digital ICP-Brasil ... está FORA DE ESCOPO":
  reescrita para refletir que o épico foi retomado, com o caminho determinado
  (qualificado), o escopo recortado e os bloqueios remanescentes.
- **`docs/PRD.md:560-568`**, bloco de status do Épico 4: deixa de dizer "movido para
  a Fase 2 / nada implementado" e passa a registrar a retomada, com data, origem
  (respostas de 2026-10-13) e o que continua pendente.

### Portão 2 — a premissa e os três critérios impossíveis são reescritos (D2, D3)

- **Premissa de Produto do Épico 4 (`PRD.md:569`)**: a frase "diretamente pelo
  navegador, sem necessidade de instalar software adicional" é marcada como
  superada — pelo mesmo padrão de tachado + nota já usado em `PRD.md:27` — e
  substituída pela premissa correta: **certificado em nuvem, com autorização pelo
  aplicativo do PSC no celular**. O "Plano de contingência" do mesmo parágrafo é
  marcado como **acionado e encerrado**, já que descreve um futuro que virou passado.
- **US 4.1 Cenário 1** reescrito: a autorização acontece no aplicativo do PSC; o
  sistema nunca vê PIN, senha ou biometria.
- **US 4.1 Cenário 3** reescrito: a falha de autorização é tratada como **opaca** —
  o sistema informa que a autorização não foi concedida, sem afirmar o motivo nem
  aplicar bloqueio próprio por tentativas (o bloqueio é do provedor).
- **US 4.1 Cenário 5** reescrito: deixa de falar em token/smart card não conectado e
  passa a cobrir o caso real — **não há certificado em nuvem vinculado ao CPF do
  usuário no provedor**.
- **US 4.2 Cenário 3 fica intacto**, marcado como **condicional** à decisão pendente
  sobre carimbo de tempo (D4). Não se reescreve critério cuja decisão de negócio
  ainda não existe.

### Escopo: registrar o que o cliente recortou (D5)

Notas de decisão, com data e origem, junto aos critérios afetados — seguindo o
padrão `**Nota (change ...)**` já usado em `PRD.md:177-178`:

| Recorte | Resposta |
|---|---|
| Assináveis apenas os documentos gerados pelo sistema a partir de `ModeloDocumento` (PDF); DOC/DOCX/JPG/PNG fora | **B1** |
| Assinatura é sempre de pessoa física; sem assinatura institucional por e-CNPJ | **B5** |
| Só se assina enquanto o processo estiver com o servidor | **B6** |
| Consulta pública permanece sem exibir documentos ou assinaturas | **G1** |
| Sem assinatura retroativa de documentos existentes | **H3** |

### O que este change deliberadamente NÃO faz

- **Não** propõe nem desenha `assinatura-verificacao-fundacao`,
  `assinatura-qualificada-psc` ou qualquer outra change de implementação.
- **Não** decide o carimbo de tempo (conflito D5 × E1, aberto).
- **Não** planeja `assinatura-avancada` (D6) — com B4 = até 5 pessoas, o modelo
  misto de A4 não economiza certificados e custaria um caminho de código paralelo.
  Fica registrado como recomendação de abandono, pendente de confirmação.
- **Não** cria capability em `openspec/specs/` (D7).

## Impact

- **Changes anteriores:** nenhuma dependência de implementação. Depende apenas de
  `docs/fase2-assinatura/` existir consolidado (commits `d91502b`, `e5f8d0d`,
  `8931bd3`) e das respostas transcritas em `respostas-cliente.md`.
- **Tabelas PostgreSQL:** nenhuma criada ou afetada. Sem migration.
- **Secret Manager / Cloud Storage:** nenhum segredo novo, nenhum bucket novo.
  (A change de implementação exigirá `psc-client-secret`, `psc-mtls-cert` e o bucket
  `documentos-assinados` — ver `estudo-tecnico.md` §7c e §7d. **Não aqui.**)
- **Dados pessoais / LGPD:** este change **não trata dados pessoais**. Ele registra
  que a SETES decidiu (F1) manter documentos assinados fora da anonimização, com
  nome e CPF do signatário preservados — mas o tratamento em si só existirá na
  change de implementação, que deverá declará-lo integralmente. ⚠️ A resposta F1
  ainda **carece de ratificação do DPO** (ver tarefa 1.2).
- **Contrato OpenAPI / `packages/api-types`:** inalterado. Nenhuma rota ou schema.
  Sem `pnpm gen:types`.
- **`docs/manual/**`:** não se aplica. Nenhuma tela, fluxo de usuário final ou texto
  exibido ao usuário muda — a regra de `rules.tasks` não dispara (justificativa
  explícita na tarefa 5.1).
- **Testes:** sem teste automatizado ou E2E. Nenhum código executável é alterado.
- **Efeito sobre agentes futuros:** este é o efeito principal. Após o apply, um
  agente que leia `config.yaml` e `CLAUDE.md` deixa de ser obrigado a recusar
  changes de assinatura, e passa a verificar as pendências nomeadas em D1.

## ⛔ Condição de apply

**Este change pode ser proposto e revisado agora, mas NÃO deve ser aplicado enquanto
a resposta A5 estiver sem nome.**

A5 pergunta quem aprova formalmente a decisão jurídica. O campo *Nome* voltou em
branco; o campo *Cargo* traz "Diretoria Executiva ou o Jurídico" — uma alternativa,
não uma determinação. `docs/fase2-assinatura/README.md` (Passo 1) exige nome
identificado porque a decisão "fica registrada na documentação do sistema como
decisão do cliente".

Aplicar este change sem esse nome gravaria no `config.yaml`, no `CLAUDE.md` e no PRD
uma retomada de épico atribuída a ninguém. O conteúdo do change está pronto; falta
o responsável. Ver `tasks.md`, seção 1.
