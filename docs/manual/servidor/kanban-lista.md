# Kanban e lista de processos

O Servidor é o **executor do dia a dia**. Ao entrar, você chega ao seu
**quadro de processos (Kanban) pessoal**.

!!! info "Regra de visibilidade"
    O seu quadro é **pessoal** — mostra exclusivamente os processos em que
    você é o **responsável atual**, os que você **criou** e aqueles pelos
    quais você **já passou** (foi responsável em algum momento do histórico).
    Não é "todos os processos da sua unidade": um processo de um colega da
    sua unidade que você nunca tocou não aparece no seu quadro. Um processo
    sigiloso fora da sua unidade atual **não aparece**, mesmo que você já
    tenha sido responsável por ele — o sigilo prevalece. Isso muda apenas a
    **composição do quadro**, não o acesso: você continua podendo abrir por
    link direto qualquer processo que esteja na sua unidade ou tenha sido
    protocolado por ela. Tentar abrir um processo fora do seu escopo por
    unidade resulta em **"Acesso negado"**.

## A tela de Processos (Kanban e Lista)

A tela de Processos tem **dois modos de visualização**, alternáveis por um
controle no cabeçalho:

- **Kanban** (modo padrão) — colunas por situação: **Aberto**, **Em
  Tramitação**, **Concluído** e **Arquivado**, cada uma com a contagem de
  processos ao lado do título. As colunas mudam sozinhas conforme os processos
  são movimentados (não é preciso arrastar manualmente para trocar de
  situação).
- **Lista** — os mesmos processos como linhas empilhadas, com a situação
  indicada à direita de cada linha.

O modo escolhido fica lembrado para a próxima vez que você acessar a tela.

Cada card (ou linha) mostra o **número**, o **tipo de processo**, o
**assunto**, a **unidade atual**, a **data e hora de criação**, o **prazo** e o
cadeado 🔒 quando o processo é sigiloso. Os processos aparecem **ordenados
por prazo** (o mais urgente primeiro), e o cabeçalho exibe o total de
processos visíveis.

- **Cards com destaque sólido** e o selo **"Ação necessária"** são processos
  em que você é o responsável atual — a próxima ação é sua.
- **Cards discretos** (borda tracejada) são processos que você criou ou já
  deteve, mas que estão agora com outro servidor — o nome de quem está com o
  processo aparece no card ("Com: Fulano"). Você pode acompanhá-los, mas não
  agir sobre eles enquanto não voltarem a ser sua responsabilidade.
- **Cards acinzentados** são processos que a sua unidade protocolou e que já
  tramitaram para uma unidade que não é a sua — eixo independente do anterior:
  um card pode ser discreto (acompanhamento) e acinzentado (fora da sua
  unidade) ao mesmo tempo.
- Um card com o selo **"↩ Devolvido"** e borda âmbar indica que o processo
  acabou de ser devolvido a você e está pronto para uma nova ação; o destaque
  some assim que você enviar novamente.
- **Prazo vencido** aparece em vermelho, com o ícone ⏰ e o texto "Vencido há
  N dias"; no dia do vencimento o card informa "Vence hoje".
- O checkbox **"Exibir Arquivados"**, no topo da tela, começa **desmarcado**
  — processos **"Concluído" aparecem sempre**; só os **"Arquivado"** ficam
  ocultos até você marcá-lo. A preferência é lembrada da próxima vez que você
  acessar a tela.
