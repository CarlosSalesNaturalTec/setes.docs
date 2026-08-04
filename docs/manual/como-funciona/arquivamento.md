# Como funciona o arquivamento automático

O arquivamento **acontece sozinho, sem ação de ninguém** — não existe botão
"Arquivar". Esta página explica quando ele dispara e o que ele muda.

## O único caminho para "Arquivado"

Um processo só chega ao status **Arquivado** por uma rotina diária que roda
sozinha (o job de manutenção diária, disparado pelo Cloud Scheduler). Não há
como um usuário arquivar um processo manualmente — o botão não existe em
nenhuma tela, por nenhum perfil.

A cada execução, a rotina seleciona os processos com status **"Concluído"**
cujo prazo de arquivamento já expirou, e transiciona cada um deles para
**"Arquivado"**, registrando um evento imutável de arquivamento no histórico
de cada processo (o mesmo evento que aparece na aba
[Histórico](../servidor/historico.md)).

## O prazo é congelado no momento da conclusão

Quando um Servidor [conclui um processo](../servidor/concluir.md), o sistema
grava, naquele instante, a data a partir da qual ele poderá ser arquivado —
`data de conclusão + prazo de arquivamento vigente` (padrão: **30 dias**, veja
[Parâmetros operacionais](../administrador/parametros.md)). Esse valor fica
**congelado** no processo.

Isso tem uma consequência direta: se o Administrador alterar o prazo de
arquivamento depois, processos **já concluídos** continuam usando o prazo que
estava vigente quando cada um foi concluído. A mudança só vale para conclusões
**futuras** — nunca retroage.

## A rotina é diária e idempotente

"Idempotente" aqui quer dizer: rodar a rotina uma vez, dez vezes, ou retomar
depois de dias sem executar produz **o mesmo resultado final**, sem duplicar
nada. Isso acontece porque a rotina não pergunta "o que venceu desde a última
vez que rodei" — ela pergunta "o que está vencido **agora**":

- Um processo já "Arquivado" não satisfaz mais o critério de seleção, então
  nunca é reprocessado nem gera um segundo evento no histórico.
- Se a rotina ficar dias sem conseguir rodar (indisponibilidade do sistema),
  a próxima execução arquiva **todos** os processos que venceram nesse
  intervalo — nenhum fica para trás.
- Cada processo é confirmado individualmente no banco: se algo falhar no meio
  de um lote grande, o progresso já feito não se perde na próxima tentativa.

## Arquivar não apaga

Este é o ponto que mais gera confusão: **arquivar não é excluir**. Um processo
arquivado:

- continua existindo, com número, dados, interessados, documentos e
  **histórico completo** intactos;
- continua acessível a quem tem acesso à unidade (e continua elegível à
  [consulta pública](consulta-publica.md), se não for sigiloso);
- apenas **some do quadro Kanban por padrão** — reaparece assim que alguém
  marca o checkbox **"Exibir Arquivados"** na tela de Processos.

Nada é fisicamente removido pelo arquivamento; ele só muda o status e a
visibilidade padrão no quadro.
