## Context

`services/processo_consulta.py` monta o quadro a partir de
`unidades_visiveis(usuario)` e do filtro
`unidade_atual ∈ escopo OR (unidade_origem ∈ escopo AND NOT sigiloso)`. Os
atributos contextuais do card (`somente_leitura`, `devolvido`) já são calculados
por usuário em `atributos_contextuais()`, em consulta única em lote.

Depois do change `tramitacao-manual` existem `processo.servidor_atual_id` e, em
`tramitacao`, `servidor_origem_id`/`servidor_destino_id`. Esses campos são a
base do novo escopo.

Fatos que enquadram o design:

- `atributos_contextuais()` já é o ponto de extensão natural: devolve flags por
  processo, calculadas em lote, sem N+1. `acao_requerida` entra ali.
- O checkbox "Exibir concluídos e arquivados" já existe, com o param
  `incluir_finalizados` e persistência em `localStorage` — o desdobramento
  reaproveita a mecânica.
- A busca (`buscar`) e o quadro (`listar_kanban`) compartilham escopo
  deliberadamente (`visibilidade-processos-origem` D1) — a regra "quadro e busca
  nunca divergem" precisa ser revista aqui, e é revista conscientemente (D6).
- Autorização não muda: `tem_acesso_a_unidade` e `require_acesso_unidade`
  continuam por unidade.

## Goals / Non-Goals

**Goals:**

- Quadro pessoal do Servidor: responsável ∪ criador ∪ participante histórico.
- Distinção visual e de contrato entre ação requerida e acompanhamento.
- Arquivados ocultos por padrão, concluídos visíveis.
- Filtros por tipo, assunto parcial e data, combináveis.
- Gestor inalterado no escopo (unidades geridas), incluindo arquivados.
- Cinco cards de contagem no dashboard.

**Non-Goals:**

- **Nenhuma mudança em autorização.** Abrir um processo continua governado por
  unidade. O quadro estreita a *visão*, não a *permissão* — decisão explícita do
  cliente.
- Nenhuma mudança em sigilo: a regra "sigiloso fora da unidade atual não
  aparece" permanece exatamente como está.
- Nenhuma mudança em tramitação, notificações, documentos ou LGPD.
- Sem drag-and-drop no quadro (segue sendo visualização).
- Sem paginação nova; mantém a página única de até 50 cards.

## Decisions

### D1 — Escopo pessoal do Servidor em três ramos

```sql
WHERE  servidor_atual_id = :eu                    -- responsável atual
   OR  criado_por_id     = :eu                    -- criei
   OR  EXISTS (SELECT 1 FROM tramitacao t         -- já detive
               WHERE t.processo_id = p.id
                 AND :eu IN (t.servidor_origem_id, t.servidor_destino_id))
```

O terceiro ramo usa **detentores**, não `responsavel_id` (design D6 de
`tramitacao-manual`): o Gestor que reatribuiu um processo agiu sobre ele mas
nunca o deteve, e não deve carregá-lo no quadro pessoal — ele já o vê pelo
escopo de unidade.

Alternativa rejeitada: tabela `processo_participante` denormalizada. Duplicaria
informação que `tramitacao` já carrega, criando duas fontes de verdade passíveis
de divergir se algum caminho de escrita esquecer o INSERT. A regra do OpenSpec é
explícita: o histórico imutável é a fonte da verdade. Custo aceito: um semi-join
por montagem de quadro, sustentado pelos índices do D7.

### D2 — `acao_requerida` como terceiro atributo contextual do card

```
acao_requerida    servidor_atual_id == eu           →  "está comigo"
somente_leitura   unidade atual fora do escopo      →  (inalterado)
devolvido         último evento é DEVOLUCAO         →  (inalterado)
```

Os três eixos são **independentes** e podem coexistir. Em particular,
`acao_requerida` e `somente_leitura` não se excluem: se eu sou o responsável, a
unidade atual é a minha por construção, então `somente_leitura` será falso —
mas a independência é mantida no cálculo, sem atalho, para que a mudança de
qualquer uma das regras não corrompa a outra.

Para o **Gestor**, `acao_requerida` é verdadeiro apenas quando o processo estiver
pessoalmente atribuído a ele — o normal é ver o quadro inteiro como
acompanhamento.

### D3 — Sigilo permanece filtrado por unidade

O ramo de sigilo não muda: processo sigiloso fora da unidade atual do usuário
continua fora do quadro, **inclusive** para quem foi participante histórico. Um
servidor que deteve o processo antes de ele ser marcado como sigiloso em outra
unidade deixa de vê-lo — comportamento idêntico ao já decidido em
`visibilidade-processos-origem` (sigilo prevalece sobre acompanhamento).

### D4 — Desdobramento do checkbox: concluídos entram, arquivados saem

O comportamento anterior (`incluir_finalizados`, um checkbox para
Concluído + Arquivado, default desmarcado) é substituído:

```
Concluídos   →  SEMPRE exibidos (o cliente os quer no quadro pessoal)
Arquivados   →  ocultos por padrão; checkbox "Exibir Arquivados" os traz
```

O param passa a ser `incluir_arquivados: bool = false`, e a chave de
`localStorage` muda para `setes:processos:exibir-arquivados`. Trocar a chave
(em vez de reaproveitar a antiga) evita que uma preferência salva com a
semântica anterior seja reinterpretada com a nova. Filtrar no servidor mantém o
contador do cabeçalho correto, como já era.

### D5 — Filtros de tipo, assunto e data no servidor

Três query params novos em `GET /processos/kanban`, todos opcionais e
combináveis entre si e com `incluir_arquivados`:

```
tipo_processo_id : uuid   →  Processo.tipo_processo_id == valor
assunto          : str    →  Processo.assunto ILIKE %valor%
data_inicial     : date   →  Processo.criado_em >= valor
data_final       : date   →  Processo.criado_em <= fim do dia
```

Reaproveitam exatamente a semântica já implementada em `buscar()` — inclusive o
tratamento do dia final inteiro — para que quadro e busca não divirjam na
interpretação de um mesmo filtro. Nenhum filtro amplia escopo: são aplicados
**depois** do recorte de autorização.

### D6 — Busca mantém o escopo de unidade; o quadro estreita

Decisão consciente de divergir do que `visibilidade-processos-origem` (D1)
estabeleceu. O quadro é **pessoal** — é a área de trabalho do servidor. A busca
(US 2.7) é **investigativa**: serve para localizar um processo específico dentro
da unidade, e estreitá-la ao conjunto pessoal a tornaria inútil para o trabalho
cotidiano (localizar o processo que um colega está tratando). Como a autorização
não muda, a busca continuar por unidade não expõe nada que o usuário já não
pudesse abrir por URL direta.

A divergência é registrada aqui e refletida nas specs para não parecer omissão.

### D7 — Migration `0025`: índices para o ramo de participação

Única migration do change (schema antes de endpoint), sem mudança de dado:

- `ix_tramitacao_servidor_destino` em `(servidor_destino_id, processo_id)`
- `ix_tramitacao_servidor_origem` em `(servidor_origem_id, processo_id)`

Índices compostos, nessa ordem de colunas, porque o `EXISTS` do D1 filtra por
servidor e correlaciona por processo — a segunda coluna torna o índice
*covering* para a subconsulta. `down_revision = "0024_remover_roteiro"`.

### D8 — Cards de contagem do dashboard

Cinco contagens sobre o escopo de unidades do Gestor já resolvido por
`resolver_escopo_gestor`:

```
Total  =  Abertos + Em Tramitação + Concluídos + Arquivados
```

O Total é a soma das quatro parcelas, calculado a partir de uma **única**
consulta com `GROUP BY status` — não cinco consultas. Isso garante que o total
nunca discorde das parcelas por efeito de concorrência entre queries.

### Fluxo principal

```
Servidor B                 web (/processos)                  api
     │  abre a tela            │                              │
     │─────────────────────────▶ GET /processos/kanban        │
     │                         │   ?incluir_arquivados=false  │
     │                         │   &tipo_processo_id=…        │
     │                         │   &assunto=…&data_inicial=…  │
     │                         │──────────────────────────────▶
     │                         │   D1: servidor_atual = eu
     │                         │     ∪ criado_por = eu
     │                         │     ∪ EXISTS(detentor em tramitacao)
     │                         │   D3: sigiloso fora da unidade → excluído
     │                         │   D4: arquivados fora
     │                         │   D5: filtros aplicados após o escopo
     │                         │   D2: acao_requerida/somente_leitura/
     │                         │        devolvido em lote (sem N+1)
     │                         │◀──────────────────────────────
     │  ┏━━ card sólido ━━┓    │   (acao_requerida = true)
     │  ┌╌ card discreto ╌┐    │   (acompanhamento + nome do detentor)
```

## Risks / Trade-offs

- [O `EXISTS` sobre `tramitacao` roda a cada montagem do quadro] → sustentado
  pelos índices compostos do D7, que tornam a subconsulta *covering*. O volume
  de eventos por processo é pequeno (dezenas), e a página é de 50 cards. Se
  medições futuras mostrarem custo, a materialização em tabela de participantes
  fica como evolução — mas não se antecipa sem medida.
- [Servidor perde de vista processos da unidade que nunca tocou] → é exatamente o
  pedido do cliente. Mitigações preservadas: a **busca** continua por unidade
  (D6), o Gestor mantém a visão consolidada, e a autorização não muda — o
  processo continua acessível por link.
- [Divergência consciente entre escopo do quadro e escopo da busca] → registrada
  em D6 e explicitada nas specs com cenários próprios, para que uma leitura
  futura não a trate como bug.
- [Trocar a semântica do checkbox pode confundir quem já usava o sistema] → a
  chave de `localStorage` é trocada (D4), forçando o default novo para todos; o
  rótulo passa a ser "Exibir Arquivados", inequívoco quanto ao que controla.
- [Processo sigiloso em outra unidade some do quadro de quem já o deteve, sem
  aviso] → comportamento herdado e coerente com a decisão anterior de que sigilo
  prevalece sobre acompanhamento; cenário explícito na spec.
- [Cards de contagem podem discordar do quadro do Gestor se calculados em
  consultas separadas] → uma única consulta com `GROUP BY status` (D8).
