# Como funciona a consulta pública

A [consulta pública](../cidadao/consulta-publica.md) é um canal **sem login**,
aberto a qualquer pessoa. Esta página detalha exatamente o que ela mostra, o
que nunca mostra, e por que processo sigiloso e número inexistente respondem
de forma idêntica.

## O que é exibido

- **Por número exato:** número, assunto, tipo de processo, situação, unidade
  atual, data de criação, os **nomes** dos interessados, e o histórico de
  movimentações — cada item com data, unidade de origem, unidade de destino e
  a situação resultante.
- **Por pesquisa** (assunto, tipo, período, combináveis): uma lista paginada
  com número, assunto, tipo, situação e unidade atual de cada processo.

O histórico exibido cobre apenas os eventos de **movimentação de fato**:
Envio, Devolução, Conclusão e arquivamento automático. Eventos de
**Reatribuição** e de marcação/remoção de **Sigilo** não aparecem no histórico
público — não são movimentações do ponto de vista de quem acompanha de fora,
e reatribuição em particular revelaria uma correção interna de responsável que
não diz respeito a quem consulta de fora.

## O que nunca é revelado

Três categorias de dado nunca aparecem na consulta pública, em nenhuma
circunstância:

- **CPF ou CNPJ** dos interessados — só o nome é exibido;
- **Nomes de servidores** responsáveis por qualquer movimentação;
- **Documentos anexados** ao processo.

Essa supressão acontece na camada que monta a resposta da consulta pública, e
não é uma questão de esconder na tela: um processo sigiloso ou um dado restrito
simplesmente nunca entra na resposta construída pelo servidor.

## Sigiloso e inexistente: a mesma resposta, de propósito

Consultar um processo sigiloso pelo número exato e consultar um número que não
existe produzem **exatamente a mesma resposta**: "nenhum processo encontrado".

Isso é **intencional, não uma falha de busca**. A consulta filtra processos
não sigilosos diretamente na consulta ao banco — nunca chega a carregar um
processo sigiloso para só depois decidir escondê-lo. Se o sistema tratasse os
dois casos de forma diferente (por exemplo, "processo existe mas é sigiloso"
vs. "processo não existe"), qualquer pessoa poderia usar a consulta pública
para **descobrir que um processo sigiloso existe**, mesmo sem ver o conteúdo
dele — o que já seria uma informação sensível por si só (ex.: confirmar que
há um processo sigiloso associado a um determinado assunto ou período). A
indistinguibilidade protege a própria **existência** do processo sigiloso, não
apenas seu conteúdo.

## Proteção contra abuso

Os endpoints públicos de consulta são limitados a **60 requisições por minuto
por endereço IP**. Ao exceder, a consulta é recusada com a mensagem "Muitas
consultas realizadas. Aguarde alguns instantes e tente novamente.", e o acesso
volta a ser liberado automaticamente após 60 segundos — sem prejudicar o uso
normal de um cidadão consultando alguns processos.
