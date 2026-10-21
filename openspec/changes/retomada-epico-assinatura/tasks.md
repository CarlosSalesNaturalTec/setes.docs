## 1. Pré-requisitos — ⛔ bloqueiam o apply

- [ ] 1.1 **Obter nome e cargo do aprovador da decisão jurídica (resposta A5).**
  O PDF devolvido em 2026-10-13 traz o campo *Nome* em branco e o campo *Cargo*
  como "Diretoria Executiva ou o Jurídico" — alternativa, não determinação.
  **Aceite**: `docs/fase2-assinatura/respostas-cliente.md`, linha A5, contém um nome
  próprio e um cargo único. Enquanto houver "⚠️ NOME EM BRANCO" naquela célula,
  **nenhuma tarefa da seção 2 em diante deve ser executada** — ver `proposal.md`,
  "Condição de apply". A solicitação está redigida em
  `docs/fase2-assinatura/devolutiva-cliente.md`, Parte 2, Pergunta 1.

- [ ] 1.2 **Registrar o estado de ratificação da resposta F1 (LGPD).**
  F1 (documentos assinados fora da anonimização) foi respondida por Serviços
  Compartilhados; o bloco roteava para Jurídico / DPO. **Aceite**: ou existe
  ratificação do DPO transcrita em `respostas-cliente.md`, ou a ausência está
  explicitada ali — já está, na nota do Bloco F. Esta tarefa **não bloqueia o
  apply**; bloqueia a change `assinatura-qualificada-psc`, e seu resultado precisa
  estar refletido na linha correspondente do `config.yaml` (tarefa 3.2).

- [ ] 1.3 **Confirmar que o dossiê está consolidado e consistente.**
  **Aceite**: `docs/fase2-assinatura/` contém `README.md`, `estudo-tecnico.md`,
  `questionario-cliente.md`, `questionario-fornecedores.md`, `respostas-cliente.md`
  (transcrito) e `devolutiva-cliente.md`. As 33 respostas estão transcritas. Sem
  isso, os textos das seções 2 e 3 não têm fonte citável.

## 2. `docs/PRD.md` — Portão 2 e escopo (D2, D3, D5)

> Primeiro arquivo a mudar, por D2/"Ordem de aplicação" do `design.md`: o documento
> mestre passa a ser verdadeiro antes de as regras liberarem a retomada.

- [ ] 2.1 **Reescrever o bloco de status do Épico 4** (`PRD.md:560-568`).
  Substituir "movido para a Fase 2 / nada deste épico está implementado" pelo
  registro da retomada: data (2026-10-13), origem (respostas da SETES, transcritas
  em `docs/fase2-assinatura/respostas-cliente.md`), caminho determinado
  (**qualificado — ICP-Brasil**, por A1 e A3) e aprovador (nome obtido em 1.1).
  **Aceite**: o bloco cita o arquivo de respostas e o aprovador nominalmente; não
  afirma que alguma coisa está implementada — nada está.

- [ ] 2.2 **Acrescentar ao mesmo bloco os recortes de escopo G1 e H3** (D5).
  **Aceite**: o bloco registra que a consulta pública permanece sem exibir
  documentos ou assinaturas (**G1**) e que não haverá assinatura retroativa
  (**H3**), cada um com a resposta de origem e a data.

- [ ] 2.3 **Reescrever a Premissa de Produto do Épico 4** (`PRD.md:569`), conforme
  D2. Texto original em `~~tachado~~`, seguido de "PREMISSA SUPERADA" com a
  justificativa e a referência a `estudo-tecnico.md` §1, e de "PREMISSA VIGENTE" com
  o fluxo de certificado em nuvem.
  **Aceite**: a frase "diretamente pelo navegador, sem necessidade de instalar
  software adicional" **não** aparece mais como afirmação vigente; aparece tachada.
  O padrão visual é o mesmo de `PRD.md:27`.

- [ ] 2.4 **Marcar o "Plano de contingência" do mesmo parágrafo como acionado e
  encerrado** (D2), com as duas datas: acionado em 2026-07-27, encerrado em
  2026-10-13. **Aceite**: o texto não descreve mais um futuro condicional ("caso o
  Discovery identifique…"); descreve um fato consumado.

- [ ] 2.5 **Substituir US 4.1 Cenário 1** (`PRD.md:573-576`) pelo texto normativo de
  D3. **Aceite**: o cenário não contém a palavra "PIN"; contém a cláusula explícita
  de que o sistema nunca solicita, recebe, transporta ou armazena PIN, senha ou
  biometria, com a referência a DOC-ICP-17.01.

- [ ] 2.6 **Substituir US 4.1 Cenário 3** (`PRD.md:581-584`) pelo texto normativo de
  D3 ("Autorização não concedida pelo provedor"). **Aceite**: não há bloqueio de 30
  minutos nem contagem de tentativas por parte do Despapelize; a mensagem ao usuário
  não afirma o motivo da recusa; há registro em `log_seguranca`.

- [ ] 2.7 **Substituir US 4.1 Cenário 5** (`PRD.md:589-592`) pelo texto normativo de
  D3 ("Nenhum certificado vinculado ao usuário"). **Aceite**: as palavras "token",
  "smart card" e "driver" não aparecem mais no Épico 4 como instrução ao usuário.

- [ ] 2.8 **Acrescentar notas de recorte B1, B5 e B6 na US 4.1** (D5).
  **Aceite**: três notas no padrão `**Nota (change retomada-epico-assinatura,
  2026-10-21):**`, cada uma citando a resposta de origem — B1 (só documentos gerados
  por `ModeloDocumento`, em PDF; DOC/DOCX/JPG/PNG fora), B5 (sem assinatura
  institucional por e-CNPJ), B6 (só assina enquanto o processo estiver com o
  servidor).

- [ ] 2.9 **Acrescentar a nota de condicionalidade em US 4.2 Cenário 3**
  (`PRD.md:604-607`), conforme D4. **Aceite**: o texto do cenário permanece
  **inalterado**; a nota registra a dependência do carimbo de tempo, a contradição
  D5 × E1 e a consequência caso a decisão venha contra o carimbo.

- [ ] 2.10 **Revisar as menções residuais ao Épico 4 fora do épico.**
  Linhas conhecidas: 27 (escopo do MVP), 176-178 (placeholder do perfil, US 1.5),
  837 (bloqueio por tentativas), 978-980 e 1004 (requisitos funcionais 16/17/18/41),
  1011 e 1015 (requisitos não funcionais).
  **Aceite**: nenhuma delas continua afirmando que o épico está "fora do MVP / Fase
  2" sem qualificação, agora que foi retomado. ⚠️ As linhas 176-178 descrevem o
  **placeholder vazio da aba "Documentos assinados"**, que **continua vazio** — essas
  permanecem válidas como estão e devem ser conferidas, não alteradas. O requisito 18
  (coassinatura) é confirmado por **B3**.

## 3. `openspec/config.yaml` — Portão 1 (D1, D6)

- [ ] 3.1 **Substituir o parágrafo de assinatura no bloco `context`**
  (`config.yaml:30-38`) pelo registro da retomada. **Aceite**: a frase "Não proponha
  changes de assinatura sem decisão explícita de retomada do épico" não existe mais;
  em seu lugar há a data da retomada, o caminho determinado (qualificado) e a
  referência a `docs/fase2-assinatura/respostas-cliente.md`.

- [ ] 3.2 **Acrescentar ao mesmo parágrafo a lista de bloqueios por change** (D1).
  **Aceite**: a lista nomeia, para cada change prevista, o que a bloqueia —
  `assinatura-verificacao-fundacao` **liberada**; `assinatura-qualificada-psc`
  bloqueada por procurement (D4), pelo escopo dos documentos de registro público
  (A2 × A3), pela tabela de prazos (F2) e pela ratificação de F1;
  `assinatura-carimbo-tempo` bloqueada pelo conflito D5 × E1. A lista é verificável:
  cada item aponta para uma pendência de `respostas-cliente.md`.

- [ ] 3.3 **Registrar a recomendação sobre o modelo misto** (D6).
  **Aceite**: o texto registra que A4 aceitou o modelo misto, que B4 = até 5 pessoas
  torna a economia nula, e que `assinatura-avancada` **não está planejada** pendente
  de confirmação de B4 — enunciado como recomendação, não como decisão do cliente.

- [ ] 3.4 **Confirmar que MP 2.200-2/2001 e ICP-Brasil passam a valer.**
  O texto atual diz que essas normas "só voltam a ser conformidade obrigatória nesse
  caso" — e o caso ocorreu. **Aceite**: o `config.yaml` afirma que são conformidade
  obrigatória para changes de assinatura, sem a condicional.

## 4. `CLAUDE.md` — espelho (D1)

- [ ] 4.1 **Reescrever a seção "Assinatura digital ICP-Brasil … está FORA DE
  ESCOPO"** (`CLAUDE.md:39-48`). **Aceite**: o título da seção não contém mais "FORA
  DE ESCOPO"; o corpo registra a retomada, o caminho qualificado, o escopo recortado
  (B1, B5, B6, G1, H3) e remete a `docs/fase2-assinatura/` para as pendências. A
  frase sobre a aba "Documentos assinados" ser **placeholder vazio permanece** — ela
  continua verdadeira.

- [ ] 4.2 **Conferir coerência entre os três arquivos.**
  **Aceite**: `CLAUDE.md`, `openspec/config.yaml` e o bloco de status do Épico 4 em
  `docs/PRD.md` afirmam a mesma coisa sobre (a) o épico estar retomado, (b) o
  caminho ser qualificado, (c) quais changes estão liberadas e quais bloqueadas.
  Divergência entre os três é o defeito que este change existe para não deixar
  acontecer.

## 5. Verificação

- [ ] 5.1 **Registrar a não aplicabilidade das regras de `rules.tasks`.**
  **Aceite**: está escrito no change, com justificativa, que não se aplicam —
  (a) **teste automatizado**: nenhum código executável é alterado; (b) **E2E
  Playwright**: nenhum fluxo de login, tramitação, documentos ou consulta pública
  muda; (c) **`pnpm gen:types`**: nenhuma rota ou schema do FastAPI muda, o job de
  drift do CI não é afetado; (d) **`docs/manual/**`**: nenhuma tela, fluxo de usuário
  final ou texto exibido ao usuário muda — o gatilho da regra não dispara. A
  justificativa já consta em `proposal.md`, "Impact"; esta tarefa confirma que ela
  continua verdadeira depois das edições reais.

- [ ] 5.2 **Verificar que nenhum arquivo de código foi tocado.**
  **Aceite**: `git diff --name-only` lista exclusivamente `docs/PRD.md`,
  `openspec/config.yaml`, `CLAUDE.md` e arquivos sob `openspec/changes/` e
  `docs/fase2-assinatura/`. Qualquer arquivo sob `apps/`, `packages/`, `infra/` ou
  `migrations/` no diff é defeito — este change não implementa assinatura.

- [ ] 5.3 **Validar o change pelo OpenSpec.**
  **Aceite**: `openspec validate retomada-epico-assinatura --strict` passa (ou o
  equivalente de `opsx:verify`), e `openspec list` mostra o change com os três
  artefatos.

- [ ] 5.4 **Teste de leitura em contexto frio** — o critério que importa.
  **Aceite**: um agente (ou pessoa) que leia apenas `CLAUDE.md` +
  `openspec/config.yaml`, sem este change em contexto, consegue responder
  corretamente: *"posso propor `assinatura-qualificada-psc` hoje?"* → **não, e por
  quais pendências nomeadas**; e *"posso propor `assinatura-verificacao-fundacao`
  hoje?"* → **sim**. Se qualquer das duas respostas não sair dali, D1 falhou e o
  texto precisa voltar à tarefa 3.2.

## 6. Encerramento

- [ ] 6.1 **Atualizar a linha do tempo do dossiê.**
  **Aceite**: `docs/fase2-assinatura/README.md`, tabela "Linha do tempo", registra
  as respostas de 2026-10-13 e a decisão de retomada com sua data. As linhas `⬜` de
  "Respostas do cliente" e "Decisão de retomada do épico" deixam de estar vazias.

- [ ] 6.2 **Atualizar o estado dos arquivos no README do dossiê.**
  **Aceite**: a tabela de arquivos do `README.md` marca `respostas-cliente.md` como
  preenchido (hoje diz "⬜ vazio — aguardando"), e inclui `devolutiva-cliente.md`,
  que não existia quando o README foi escrito.

- [ ] 6.3 **Enviar o questionário técnico à Soluti** (pendência 8 de
  `respostas-cliente.md`). **Aceite**: as quatro perguntas de
  `questionario-fornecedores.md` que mudam a arquitetura — 1.1 (modelo de
  autorização), 2.4 (formato de saída), 3.1 (certificado SSL exigido) e 4.1
  (allowlist de IP) — foram enviadas. ⚠️ Esta tarefa **não bloqueia o apply** e pode
  correr em paralelo desde já: D1 identifica a Soluti como fornecedora do e-CNPJ
  atual, D3 não impõe restrição e D4 liberou o início "desde já". É o item de maior
  lead time do projeto.
