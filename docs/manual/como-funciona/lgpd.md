# Como funciona a LGPD no sistema

O sistema anonimiza dados pessoais de interessados por **dois caminhos**
diferentes, que produzem exatamente **o mesmo efeito**. Esta página explica
os dois gatilhos e, principalmente, o que a anonimização muda — e o que não
muda — em um processo.

## Os dois gatilhos

- **Solicitação do titular** — qualquer titular de dados pessoais citados em
  um processo (ou seu representante legal) pode pedir, pelo
  [canal público de solicitação LGPD](../cidadao/solicitacao-lgpd.md), a
  **"Exclusão de dados"** ou a **"Anonimização de dados"**. Depois de validar a
  identidade do solicitante, o Administrador
  [atende a solicitação](../administrador/solicitacoes-lgpd.md) e dispara a
  anonimização.
- **Rotina automática trimestral** — um job agendado (Cloud Scheduler)
  seleciona, a cada execução, os processos **Arquivados** cujo prazo legal de
  anonimização já expirou e que ainda têm algum interessado com dado pessoal
  não anonimizado, anonimizando-os sem intervenção humana.

Note que os dois tipos de solicitação do cidadão — "Exclusão" e
"Anonimização" — **não produzem resultados diferentes**: ambos disparam o
mesmo serviço de anonimização. Não existe, hoje, uma exclusão física de dados
diferente da anonimização; "exclusão de dados pessoais", no sistema, **é**
anonimização.

## O prazo é contado a partir do arquivamento, por tipo de processo

O prazo legal de anonimização é configurável **por tipo de processo** (veja
[Cadastrar tipos de processo](../administrador/tipos-processo.md)), em anos, e
é contado a partir do mesmo instante congelado que o
[arquivamento automático](arquivamento.md) usa como referência — o momento em
que o processo se tornou elegível ao arquivamento (não necessariamente o
momento em que o job de arquivamento efetivamente rodou, se houve atraso). Um
processo com prazo de anonimização de 5 anos, elegível ao arquivamento há 5
anos ou mais, torna-se elegível à anonimização na próxima execução da rotina
trimestral.

## O efeito é único, único caminho técnico

Os dois gatilhos — manual e automático — chamam o **mesmo serviço** interno
de anonimização, com apenas um registro diferente ("origem: manual" ou
"origem: automático") para fins de auditoria. Isso garante que o critério do
que conta como "anonimizado" seja idêntico nos dois casos, sem risco de um
caminho ser mais ou menos rigoroso que o outro.

O efeito, sempre **irreversível**:

- o **nome** do interessado é substituído por "Titular Anonimizado";
- o **CPF/CNPJ** é substituído por um identificador irreversível — não é um
  hash do documento original (o que permitiria testar candidatos de CPF até
  encontrar uma correspondência), e sim derivado de um valor aleatório, sem
  nenhuma forma de reconstituir o documento original a partir dele.

## O que é preservado — anonimizar não é apagar o processo

Este é o ponto mais importante para não errar: **anonimizar o titular não
apaga o processo**. Permanecem intactos e íntegros:

- o **número do processo**;
- todas as **datas** (criação, conclusão, arquivamento);
- as **unidades** por onde o processo passou;
- o **status** do processo;
- o **histórico de tramitação completo**.

Só o nome e o documento (CPF/CNPJ) do interessado são alterados — o resto do
processo continua íntegro e consultável, exatamente pelo motivo que torna a
anonimização aceitável do ponto de vista da LGPD: ela protege o titular sem
apagar o registro administrativo, que segue auditável.

## Idempotência

Assim como o arquivamento, a rotina automática só considera interessados
ainda não anonimizados. Um processo cujos interessados já foram todos
anonimizados — seja pela rotina automática, seja por atendimento manual de
uma solicitação anterior — não é reprocessado nem gera um evento duplicado.
