# Manual do Usuário — SETES.DOCS

Guia prático de operação do sistema, organizado por tipo de perfil. Cada
pessoa recebe um perfil ao ser cadastrada, e é o perfil que determina o que
ela vê e pode fazer. Os três perfis são:

- **Servidor** — executa o dia a dia dos processos da sua unidade.
- **Gestor** — acompanha o desempenho e a equipe das unidades que gerencia.
- **Administrador** — configura a estrutura do sistema para toda a instituição.

> **Como usar este manual:** comece pela seção **"Para todos os perfis"**
> (primeiro acesso, login, senha, sair). Depois vá direto para a seção do seu
> perfil. Ao final há um **glossário** dos termos usados no dia a dia.

---

## Sumário

- [Para todos os perfis](#para-todos-os-perfis)
- [Perfil Servidor](#perfil-servidor)
- [Perfil Gestor](#perfil-gestor)
- [Perfil Administrador](#perfil-administrador)
- [Nota: permissão de Auditoria](#nota-permissão-de-auditoria)
- [Para o cidadão (sem login)](#para-o-cidadão-sem-login)
- [Fora do escopo desta versão](#fora-do-escopo-desta-versão)
- [Glossário](#glossário)

---

## Para todos os perfis

Estas ações valem para qualquer pessoa com acesso ao sistema,
independentemente do perfil.

### 1. Primeiro acesso (ativar sua conta)

Quando alguém cadastra você no sistema, você recebe um **e-mail com um link de
primeiro acesso**.

1. Abra o e-mail e clique no link **dentro de 48 horas**.
2. Crie sua senha. Ela precisa ter, no mínimo, **8 caracteres**, com pelo menos
   **1 letra maiúscula, 1 letra minúscula e 1 número**.
3. Pronto: sua conta fica ativa e você já entra no sistema.

- Se passar de 48 horas, o link expira. Peça um novo link ao Administrador.
- Se o link já tiver sido usado, faça login normalmente; caso tenha esquecido a
  senha, use "Esqueci minha senha".

### 2. Entrar no sistema (login)

Informe seu **e-mail e senha** na tela de login. Você será levado
automaticamente à tela inicial do seu perfil:

| Perfil | Tela inicial |
|--------|--------------|
| Servidor | Processos (quadro pessoal) |
| Gestor | Dashboard |
| Administrador | Unidades administrativas |
| Qualquer perfil **com permissão de Auditoria** | Relatório de Auditoria |

- **Errou a senha 3 vezes seguidas?** Sua conta fica **bloqueada por 30
  minutos** por segurança, e você recebe um e-mail avisando das tentativas.
  Aguarde o tempo indicado ou redefina a senha para desbloquear na hora.
- **Conta desativada?** O sistema informa que a conta foi desativada e orienta
  procurar o Administrador.

### 3. Esqueci minha senha

1. Na tela de login, escolha **"Esqueci minha senha"** e informe seu e-mail.
2. Você recebe um **link de redefinição válido por 2 horas**.
3. Crie uma nova senha seguindo as mesmas regras de complexidade.

Por segurança, a mensagem exibida é sempre a mesma, exista ou não o e-mail na
base — assim o sistema não revela quem tem cadastro.

### 4. Trocar a senha (quando já está logado)

Na aba **"Trocar senha"** de "Meu Perfil", você pode alterar a senha
informando a **senha atual** e uma **nova senha**. A nova senha precisa
atender às regras de complexidade e **não pode repetir** a senha atual nem as
**6 últimas** que você já usou.

### 5. Menu lateral

O menu à esquerda mostra apenas o que o seu perfil pode acessar (em telas
estreitas ele vira uma gaveta, aberta pelo botão de menu no topo):

| Item | Quem vê |
|------|---------|
| Dashboard | Gestor |
| Processos | Todos |
| Documentos Removidos | Administrador |
| Solicitações LGPD | Administrador |
| Unidades | Administrador |
| Tipos de Processo | Administrador |
| Modelos de Documento | Administrador |
| Usuários | Administrador e Gestor |
| Relatório de Auditoria | Quem tem permissão de Auditoria |
| Meu Perfil | Todos |

No alto da tela ficam o **sino de notificações**, seu nome com o perfil e o
botão **"Sair"**.

### 6. Meu Perfil

A tela **"Meu Perfil"** é organizada em quatro abas, navegáveis também pelo
teclado (setas esquerda/direita):

- **Meu perfil** — seus dados de cadastro: nome, e-mail, perfil, situação e,
  quando preenchidos, **unidade, setor, cargo, telefone e chefia direta**
  (campos em branco simplesmente não aparecem). É aqui também que você edita
  o seu nome;
- **Trocar senha** — o formulário de troca de senha descrito acima;
- **Processos em que atuei** — a lista de processos em que você atuou
  (número, assunto, data e tipo da sua última ação). Ela acompanha você mesmo
  depois de uma transferência de unidade. Se você acabou de ser cadastrado e
  ainda não atuou em nada, a lista aparece vazia com um aviso — é o esperado;
- **Documentos assinados** — mostra um aviso de que a assinatura digital de
  documentos será disponibilizada em uma fase futura do produto e orienta a
  solicitar desde já seu Certificado Digital ICP-Brasil junto a uma
  Autoridade Certificadora, como preparação **fora do sistema**; por enquanto
  não há nenhuma ação de assinatura disponível na tela (veja
  [Fora do escopo desta versão](#fora-do-escopo-desta-versão)).

A aba escolhida fica registrada no endereço da página: recarregar ou
compartilhar o link mantém a mesma aba aberta.

### 7. Notificações

O sistema avisa você sobre eventos importantes de duas formas: por um **sino de
notificações dentro do sistema** e por **e-mail** (para você não perder prazos
mesmo sem estar logado).

Os avisos do sino são:

| Aviso | Quando acontece | Quem recebe |
|-------|-----------------|-------------|
| Novo processo recebido | Alguém **envia** um processo a você | O servidor de destino (também por e-mail) |
| Processo concluído | O processo que você criou é concluído por outra pessoa | Quem criou o processo |
| Prazo próximo | O prazo do processo está a poucos dias de vencer | Os servidores da unidade (também por e-mail) |
| Reatribuído para você | Alguém corrige a atribuição e o processo passa a ser seu | O novo responsável |
| Destino da tramitação corrigido | O processo que você enviou foi reatribuído a outra pessoa | Quem havia enviado |

- A **devolução não gera notificação no sino** — o processo simplesmente
  reaparece no quadro de quem o enviou, com o selo **"↩ Devolvido"**.
- O número no sino indica quantas notificações **não lidas** você tem. Abrir o
  painel **não zera o contador** — uma notificação só é considerada lida quando
  você **clica nela** ou usa **"Marcar todas como lidas"**.
- Notificações já lidas são mantidas por **30 dias** e depois removidas
  automaticamente.

### 8. Sair e sessão automática

Use **"Sair"** para encerrar sua sessão com segurança. Por proteção, o sistema
também **encerra sozinho sessões inativas após 30 minutos**. Dois minutos antes
disso aparece um aviso com as opções **"Continuar Sessão"** (que renova o
tempo) e **"Sair"**. Qualquer ação no sistema também renova a sessão — o
relógio só corre enquanto você está parado.

---

## Perfil Servidor

O Servidor é o **executor do dia a dia**. Ao entrar, você chega ao seu
**quadro de processos (Kanban) pessoal**.

> **Regra de visibilidade:** o seu quadro é **pessoal** — mostra
> exclusivamente os processos em que você é o **responsável atual**, os que
> você **criou** e aqueles pelos quais você **já passou** (foi responsável em
> algum momento do histórico). Não é "todos os processos da sua unidade": um
> processo de um colega da sua unidade que você nunca tocou não aparece no seu
> quadro. Um processo sigiloso fora da sua unidade atual **não aparece**,
> mesmo que você já tenha sido responsável por ele — o sigilo prevalece. Isso
> muda apenas a **composição do quadro**, não o acesso: você continua podendo
> abrir por link direto qualquer processo que esteja na sua unidade ou tenha
> sido protocolado por ela. Tentar abrir um processo fora do seu escopo por
> unidade resulta em **"Acesso negado"**.

### A tela de Processos (Kanban e Lista)

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

### Filtrar o quadro

Logo abaixo do cabeçalho há uma **barra de filtros** que refina o quadro por:

- **Tipo de processo** (lista dos tipos cadastrados);
- **Assunto** (texto parcial — o quadro atualiza sozinho enquanto você digita);
- **Período de criação** (data inicial "De" e final "Até").

Os filtros são combináveis entre si e com "Exibir Arquivados", e **nunca
mostram processos fora do seu quadro pessoal** — eles recortam o que você já
via, não ampliam o acesso. Um botão **"Limpar filtros"** aparece quando há
algum filtro ativo e restaura a visão completa.

> Não há uma tela separada de busca por número: para localizar um processo
> específico, use o filtro por assunto ou o período de criação. O número
> completo pode ser consultado por qualquer pessoa na
> [consulta pública](#consulta-pública-de-processos).

### Criar um novo processo

Para dar início a uma tramitação formal:

1. Escolha **"Novo processo"** (o botão aparece só para o perfil Servidor).
2. Preencha o **assunto**, o **tipo de processo** e o **prazo em dias
   corridos** — os três são obrigatórios.
3. Adicione os **interessados**, se houver: para cada um, o nome completo, o
   tipo de documento (**CPF** ou **CNPJ**) com o número, e o tipo de
   participação (**Requerente**, **Representado** ou **Terceiro**). O número é
   formatado enquanto você digita e **validado** ao salvar — um CPF ou CNPJ
   inválido impede a criação, com aviso explicando o motivo.
4. Confirme. O sistema gera o **número do processo** no formato
   `AAAA/NNNNNN`, e ele nasce **atribuído a você** — aparece imediatamente no
   seu quadro, como responsável, mesmo antes de qualquer tramitação.

Para criar um processo você precisa estar vinculado a uma **unidade** e a um
**setor** dela; se seu cadastro não tiver setor, o sistema avisa e recusa a
criação — peça ao Administrador ou ao seu Gestor para completar o cadastro.

### Abrir um processo a partir de um modelo (opcional)

Para evitar redigitar do zero requerimentos, ofícios, memorandos e outros
textos repetitivos, você pode **escolher um modelo** do catálogo ao criar um
processo:

1. No formulário de "Novo processo", em **"Modelo de documento (opcional)"**,
   escolha um modelo ativo do catálogo. O texto do modelo aparece no editor.
   Deixando **"Nenhum — começar do zero"**, o processo é criado sem documento.
2. **Edite o texto livremente**, substituindo as lacunas (trechos como
   "[NOME DO SOLICITANTE]" ou "____________") pelas informações reais do caso.
   O editor conta quantas lacunas ainda não foram preenchidas e exibe o aviso
   logo abaixo, como lembrete — isso **não impede** você de salvar o processo
   mesmo assim.
3. Use a barra de formatação para **negrito, itálico, sublinhado, alinhamento
   (esquerda, centro, direita, justificado) e listas** (com marcadores ou
   numeradas).
4. Ao confirmar a criação do processo, o texto é convertido em **PDF** e
   aparece automaticamente na aba "Documentos" do processo — como qualquer
   outro anexo: pode ser visualizado, baixado, e removido/restaurado pelas
   mesmas regras da seção adiante. Uma vez salvo, o documento gerado **não pode
   ser editado**; para corrigir um erro de digitação, remova-o e gere outro a
   partir do modelo.
5. Se por algum motivo o documento não puder ser gerado, o **processo mesmo
   assim é criado** e o sistema avisa que só a geração falhou.

Escolher um modelo é **opcional** — criar um processo digitando só o assunto
continua funcionando normalmente.

### A tela de um processo

Ao abrir um processo, o cabeçalho traz o número, o cadeado 🔒 se for sigiloso,
o assunto e os botões de ação disponíveis. Abaixo, três abas:

- **Detalhes** — situação, unidade atual, prazo e a lista de interessados;
- **Documentos** — os anexos do processo (veja adiante);
- **Histórico** — a trajetória completa do processo (veja adiante).

Quando o processo está em uma unidade que não é a sua (acompanhamento por ter
sido protocolado pela sua unidade), a tela exibe o aviso **"Acompanhamento em
modo leitura — este processo está atualmente em outra unidade"** e nenhuma ação
fica disponível.

### Tramitar um processo: Enviar, Devolver ou Reatribuir

Não existe um "caminho predefinido" por tipo de processo — você escolhe
explicitamente **para quem** o processo vai a cada tramitação, pelo botão
**"Tramitar"**, que abre um único formulário com três tipos de ação.

**Enviar** — para mandar o processo adiante, a quem deve tratá-lo:

1. Abra o processo, clique em **"Tramitar"** e deixe selecionado o tipo de
   ação **"Envio"**.
2. Escolha a **unidade de destino**, depois o **setor** dessa unidade e, por
   fim, o **servidor** — os campos aparecem em cascata, um habilitando o
   seguinte. Só unidades e setores ativos são oferecidos, e só servidores
   ativos daquele setor.
3. Escreva uma **mensagem** explicando o que precisa ser feito e confirme. O
   processo sai do seu quadro e chega ao servidor escolhido, que é notificado
   no sino e por e-mail; o quadro volta a aparecer com a confirmação
   "Processo enviado para \<unidade\>".

Você não pode enviar um processo para si mesmo — o destino tem que ser outro
servidor.

**Devolver** — para mandar o processo de volta a quem te enviou, quando algo
precisa de correção antes de seguir adiante:

1. Abra o processo, clique em **"Tramitar"** e mude o tipo de ação para
   **"Devolução"**.
2. O destino **não é escolhido por você** — o sistema já sabe para quem
   devolver (quem enviou o processo a você da última vez) e informa isso na
   própria tela.
3. Selecione um **motivo** (Documentação insuficiente, Correção de dados ou
   Diligência complementar) e, se quiser, uma **justificativa** (opcional), e
   confirme.

Se o processo nunca foi enviado a ninguém (ainda está com quem o criou), não
há devolução possível — o sistema avisa que não há remetente anterior.

**Reatribuir** — para corrigir quando o processo chegou à unidade certa, mas
com a **pessoa errada**:

1. Abra o processo, clique em **"Tramitar"** e mude o tipo de ação para
   **"Reatribuir"**.
2. A **unidade fica travada** (aparece preenchida e não editável) — você só
   escolhe o **setor** e o **servidor** corretos dentro da mesma unidade.
3. Escreva a **justificativa** (obrigatória) e confirme. O processo permanece
   na tela, com a confirmação "Processo reatribuído. O prazo foi mantido."

A reatribuição **não altera o status do processo nem o prazo** — é só uma
correção de responsável. Podem reatribuir: quem está com o processo agora,
quem o enviou por engano da última vez, ou o Gestor da unidade. Se você
enviou o processo para a pessoa errada e ela reatribuir para a pessoa certa,
você recebe o aviso "Destino da tramitação corrigido".

> **Quando usar qual:** unidade errada → **Devolver**; setor ou pessoa errados
> dentro da unidade certa → **Reatribuir**; processo pronto para seguir →
> **Enviar**.

### Concluir um processo

Quando o tratamento do processo estiver encerrado, use o botão **"Concluir"**
— disponível a qualquer momento, sem precisar enviar o processo a mais
ninguém antes. Após confirmar na janela de confirmação, o processo passa para
"Concluído" e o prazo de arquivamento é contado a partir desse instante. Quem
criou o processo é notificado da conclusão.

Processos já concluídos ou arquivados não exibem mais os botões "Tramitar" e
"Concluir".

### Acompanhar o histórico de tramitação

Na aba **Histórico** de cada processo você vê o registro **completo e
imutável** da trajetória: cada evento (Envio, Devolução, Reatribuição,
Conclusão, arquivamento automático, marcação e remoção de sigilo, remoção e
restauração de documento), com a unidade de origem e destino, a data e hora, a
situação resultante e a mensagem, o motivo ou a justificativa daquela ação.

Nenhum evento pode ser editado ou apagado — o histórico só cresce.

### Anexar, consultar e remover documentos

Na aba **Documentos** do processo:

- **Anexar:** o botão **"Anexar Documento"** aceita **PDF, DOC, DOCX, JPG ou
  PNG**, com até **20 MB** por arquivo. Arquivos vazios, em outros formatos ou
  com conteúdo incompatível com a extensão são recusados. Se você anexar um
  arquivo com nome repetido, o sistema o renomeia automaticamente (ex.:
  "parecer (1).pdf") — nada é sobrescrito.
- **Visualizar:** clicar no nome do documento abre **PDF e imagens** em uma
  janela dentro do sistema. **DOC e DOCX** não têm visualização embutida: o
  sistema avisa e inicia o download automaticamente.
- **Baixar:** o botão **"Baixar"** salva o arquivo no seu computador.
- **Remover:** um documento pode ser removido **apenas enquanto o processo
  ainda está com a sua unidade e não foi enviado** (processo recém-criado ou
  recém-devolvido). Depois do envio, o botão de remoção não aparece. A remoção
  pede confirmação, fica registrada no histórico do processo (com autor e
  data/hora) e o arquivo é preservado por **30 dias** — nesse período, o
  Administrador consegue restaurá-lo se a remoção tiver sido um engano.
- **Documentos gerados a partir de modelo:** o PDF gerado ao abrir um
  processo com um modelo aparece na mesma lista dos anexos enviados por
  upload, com os mesmos controles de visualização, download, remoção,
  retenção e restauração — não há distinção nenhuma no tratamento.

### Marcar sigilo

Quando um processo exige confidencialidade, você pode **marcá-lo como
sigiloso** pelo botão **"Marcar como Sigiloso"** (e desfazer depois em
**"Remover Sigilo"**). O sigilo **restringe a aparição do processo na
consulta pública** e o esconde de quem está fora da unidade onde ele se
encontra — a tramitação interna continua normalmente. Marcar e remover sigilo
é uma ação do **Servidor da unidade onde o processo está**; nas demais
unidades, um processo sigiloso simplesmente não aparece (só quem tem permissão
de Auditoria consegue vê-lo).

---

## Perfil Gestor

O Gestor tem a **visão tática** das unidades que gerencia. Ao entrar, você chega
ao **Painel de Indicadores (Dashboard)**.

> **Regra de visibilidade:** você enxerga os processos **atualmente em
> qualquer unidade que você gerencia** — não apenas uma — e também acompanha,
> em modo somente leitura (card acinzentado), os processos **originados em
> uma unidade sua** que já tramitaram para uma unidade que você não gerencia
> (exceto sigilosos). Diferente do Servidor, o seu quadro **não é estreitado
> para o pessoal** — você continua vendo tudo das unidades geridas,
> independentemente de ter criado, detido ou estar responsável pelo
> processo. A maioria dos cards aparece como acompanhamento (mostrando o
> servidor responsável de cada um); só os atribuídos pessoalmente a você têm
> o destaque de "Ação necessária". Quais unidades você gerencia é definido
> pelo Administrador.

### Painel de Indicadores (KPIs)

No topo do painel, um **filtro por unidade** ("Todas as unidades" por padrão)
recorta tudo o que é exibido abaixo.

Em seguida, cinco **cards de contagem por status** dão o panorama geral:
**Total**, **Abertos**, **Em Tramitação**, **Concluídos** e **Arquivados** —
o Total é sempre a soma dos outros quatro.

Abaixo, quatro indicadores de eficiência:

- **Total de Processos Ativos** — clicável: abre a lista dos processos ativos
  com o número, o assunto, a unidade e os dias restantes de cada um;
- **Tempo Médio de Tramitação**, em dias;
- **Processos Parados** — clicável: abre a lista dos processos sem
  movimentação, com há quantos dias cada um está parado;
- **Produtividade por Unidade** — quantidade por unidade gerida.

Logo abaixo, **Prazos em Risco** lista os processos cujo prazo se aproxima ou
já venceu, destacando em vermelho os vencidos ("vencido há N dias") e em
cinza os que ainda têm dias restantes.

Por fim, três **gráficos de distribuição** mostram como os processos
**ativos** (Aberto e Em Tramitação) se dividem:

- **Processos por Unidade**;
- **Processos por Tipo**;
- **Processos por Usuário** (quem criou cada processo).

Onde não houver dados, o painel exibe "Nenhum dado disponível para o período"
em vez de um número enganoso.

Use esses indicadores para identificar **onde os processos estão travando** e
**quem está sobrecarregado**, e assim tomar decisões.

### Quadro consolidado das suas unidades

Além dos números, o item **Processos** do menu traz um **quadro consolidado**
reunindo, em um só lugar, os processos de **todas as unidades que você
gerencia** — uma visão completa do que está sob sua responsabilidade. Um
**filtro por unidade** permite focar em uma unidade de cada vez, combinável com
os filtros de tipo, assunto e período e com o checkbox "Exibir Arquivados"
(mesma mecânica do Servidor, veja "A tela de Processos"), e a alternância
**Kanban / Lista** funciona igual à do Servidor.

### Cadastrar usuários da sua unidade

Para não depender da equipe central a cada nova pessoa na sua equipe, você pode
**cadastrar novos usuários nas unidades que gerencia**:

1. Em **Usuários**, acione **"Novo usuário"** — o cadastro abre em uma janela
   sobre a listagem.
2. Informe nome, e-mail e a unidade (que precisa ser uma que você gerencia).
3. Escolha o **setor** dentro dessa unidade. Para o perfil Servidor o setor é
   **obrigatório**, e a lista só oferece setores ativos da unidade escolhida —
   trocar a unidade limpa o setor.
4. Se quiser, preencha **telefone, cargo e chefia direta** (a chefia é texto
   livre: pode ser alguém sem conta no sistema).
5. O único perfil que você pode atribuir é **Servidor** — os demais nem são
   oferecidos na lista.
6. Confirme. A pessoa recebe o e-mail de primeiro acesso e passa a enxergar
   apenas os processos daquela unidade.

**Limites importantes:**

- Você **não pode** cadastrar usuários em unidades que não gerencia.
- Você **não pode** atribuir os perfis Gestor ou Administrador — isso é
  exclusivo do Administrador.
- As ações da listagem de usuários (transferir de unidade, resetar senha,
  conceder auditoria, desativar) são **exclusivas do Administrador** — você vê
  a lista, mas não esses botões.

> **Nota:** o Gestor **acompanha** os processos das suas unidades. Criar,
> enviar, devolver e marcar sigilo são ações exclusivas dos **Servidores** de
> cada unidade. O Gestor da unidade também pode **Reatribuir** e **Concluir**
> um processo — os botões aparecem na tela do processo assim que ele acessa
> um processo de uma unidade sob sua gestão.

---

## Perfil Administrador

O Administrador é o **guardião da configuração** do sistema. Ao entrar, você
chega à área de **Unidades administrativas**. É aqui que se define a estrutura
que todos os demais perfis usam no dia a dia.

### Gerenciar usuários

Na tela **Usuários**:

- **Cadastrar usuários** de qualquer perfil (Servidor, Gestor ou
  Administrador) pelo botão **"Novo usuário"**, que abre o formulário em uma
  janela sobre a listagem. Informe nome, e-mail, perfil, unidade e **setor**, e
  opcionalmente **telefone, cargo e chefia direta**. A pessoa recebe o link de
  primeiro acesso (válido por 48 horas).
- **Filtrar a listagem por nome:** o campo de busca no alto da tela filtra
  enquanto você digita, por parte do nome e sem diferenciar maiúsculas de
  minúsculas. Limpe o campo para ver todos de novo.
- **Transferir de unidade** (ícone na linha de um Servidor): escolha a nova
  unidade e, obrigatoriamente, um **setor dela**.
- **Definir as unidades geridas** (ícone na linha de um Gestor): marque as
  unidades que ele acompanha.
- **Resetar a senha** de um usuário quando ele não conseguir se recuperar
  sozinho ou em caso de conta comprometida.
- **Conceder ou revogar a permissão de Auditoria** (veja a seção adiante).
- **Desativar usuários** para revogar o acesso quando necessário. Quem está
  desativado não consegue entrar.

O sistema recusa cadastros com **e-mail já usado**, **e-mail em formato
inválido**, **nome em branco**, **unidade inexistente/inativa**, **Servidor sem
setor** ou **setor que não pertence à unidade escolhida**, sempre explicando o
motivo. Usuários com perfil Servidor que ainda estejam sem setor aparecem
marcados na listagem com a etiqueta **"sem setor"**, para você regularizar o
cadastro — sem setor, a pessoa não consegue criar processos.

### Cadastrar unidades administrativas

**Cadastre e gerencie as unidades** (as áreas administrativas da instituição —
coordenadorias, diretorias, departamentos) para refletir a estrutura
organizacional. Cada unidade tem **nome** e **sigla**, e pode ser editada,
desativada e reativada — nunca excluída. As unidades são a base do controle
de acesso e do destino das tramitações.

### Cadastrar setores de uma unidade

Cada unidade se divide em **setores** — o segundo nível da estrutura
organizacional. Na tela de unidades, acione o ícone **"Setores"** na linha da
unidade para abrir a lista dela logo abaixo da tabela e cadastrar, editar,
desativar ou reativar setores.

- A **sigla é única dentro da unidade**, mas pode se repetir entre unidades
  diferentes (duas unidades podem ter um "GAB").
- **Setor nunca é excluído**, apenas desativado — o histórico de tramitação
  precisa continuar referenciando setores antigos.
- Não é possível desativar um setor enquanto houver **servidor ativo vinculado**
  a ele; o sistema informa quantos estão impedindo a operação.
- **Desativar a unidade desativa todos os seus setores.** A confirmação avisa
  quantos serão afetados antes de aplicar. Ao reativar a unidade, os setores
  **permanecem inativos**: cada um precisa ser reativado individualmente.

> **Atenção:** o setor organiza as pessoas e é escolhido a cada tramitação, mas
> **não altera quem enxerga o quê** — o controle de acesso continua sendo por
> unidade.

### Cadastrar tipos de processo

Cadastre os **tipos de processo** (ex.: "Licitação", "Requerimento") usados na
criação de processos e nos filtros do quadro e do dashboard. O nome é único.
O tipo de processo **não define um caminho fixo de tramitação** — cada envio,
devolução ou reatribuição tem seu destino escolhido explicitamente pelo
Servidor no momento da ação.

Os tipos já cadastrados aparecem em uma **tabela**, uma linha por tipo, com o
nome e o **prazo de anonimização LGPD** (em anos). O prazo é editado
diretamente na linha — altere o valor e acione **"Salvar"**; erro e
salvamento afetam só aquela linha, sem alterar as demais. A alteração **não é
retroativa**: vale a partir da próxima avaliação da rotina automática de
anonimização. O formulário de cadastro de novo tipo fica acima da tabela.

### Cadastrar modelos de documento

Em **"Modelos de Documento"**, mantenha o catálogo de modelos que o Servidor
pode escolher ao abrir um processo (veja "Abrir um processo a partir de um
modelo"). A tela é organizada em duas abas — **"Novo modelo"**, com a ficha
de cadastro, e **"Modelos cadastrados"**, com os filtros e a listagem, aberta
por padrão. Ao cadastrar um modelo com sucesso, a tela alterna
automaticamente para "Modelos cadastrados", onde o modelo recém-criado já
aparece na lista.

- **Cadastrar/editar:** na aba "Novo modelo", informe nome, categoria (texto
  livre), tipo (Requerimento, Ofício, Memorando, Despacho, Parecer, Nota
  técnica, Relatório, Ata, Contrato ou Outro), descrição opcional e o
  conteúdo, escrito no editor com a barra de formatação restrita a
  **negrito, itálico, sublinhado, alinhamento e listas**. Use marcações de
  lacuna no texto (ex.: "[NOME DO SOLICITANTE]", "____________") para indicar
  onde o servidor deve substituir pelas informações reais.
- **Não inclua dados pessoais reais no modelo** — nome, CPF, endereço ou
  qualquer dado de uma pessoa específica não devem aparecer no modelo, só
  marcações de lacuna. A tela adverte sobre isso a cada cadastro.
- **Desativar/reativar:** na aba "Modelos cadastrados", um modelo desativado
  some da lista de escolha do Servidor, mas os documentos já gerados a partir
  dele **permanecem intactos** na lista de anexos dos respectivos processos.
  **Não existe exclusão** de modelo — apenas desativação, como acontece
  também com unidades e setores.
- Use os filtros por **tipo** e por **situação** (Todos / Ativos / Inativos),
  na aba "Modelos cadastrados", para localizar um modelo no catálogo.

### Conceder permissão de Auditoria

Na listagem de usuários, o ícone de escudo **concede e revoga a permissão de
Auditoria** a usuários específicos. Quem recebe essa permissão passa a poder
acessar processos de qualquer unidade — inclusive sigilosos — para fins de
fiscalização. Veja a [nota sobre auditoria](#nota-permissão-de-auditoria) mais
abaixo.

### Acompanhar processos (somente leitura)

O Administrador tem acesso à tela de **Processos de todas as unidades**, em
modo **somente leitura**: você visualiza o quadro (Kanban ou Lista), usa os
mesmos filtros e abre o detalhe de qualquer processo, mas **não vê botões de
ação** — criar processo, tramitar (Enviar/Devolver/Reatribuir), concluir e
marcar sigilo são ações do Servidor da unidade onde o processo está. Use essa
visão para acompanhar o andamento geral sem interferir.

### Restaurar documentos removidos

Em **"Documentos Removidos"** ficam os anexos em período de retenção, com o
nome do documento, o processo a que pertencem, quando e por quem foram
removidos. O botão **"Restaurar"** devolve o documento à lista de anexos do
processo, após confirmação.

A restauração só é possível dentro do período de retenção de **30 dias** após
a remoção — depois disso o arquivo é apagado definitivamente, e a tela avisa
caso você tente restaurar um documento que acabou de ser purgado.

### Tratar solicitações de privacidade (LGPD)

Cidadãos podem pedir a **exclusão ou anonimização dos seus dados pessoais**
pelo canal público (ver [Para o cidadão](#para-o-cidadão-sem-login)). Em
**"Solicitações LGPD"**, você vê a fila de pedidos com protocolo, data,
solicitante, processo, tipo e status (**Pendente / Em análise / Atendida /
Rejeitada**) e, para os que ainda estão pendentes ou em análise:

- **Atender:** após validar a identidade do solicitante, o atendimento
  **anonimiza de forma irreversível** os dados pessoais do titular no processo
  (o número, as datas e o histórico de tramitação são preservados) e envia
  e-mail automático ao solicitante informando a conclusão.
- **Rejeitar:** exige uma **justificativa obrigatória** (por exemplo, quando o
  solicitante não é o titular dos dados), enviada por e-mail ao solicitante.

"Atendida" e "Rejeitada" são status finais — a solicitação não pode ser
reprocessada depois, e os botões de ação deixam de aparecer.

### Parâmetros operacionais do sistema

Três parâmetros governam as rotinas automáticas:

| Parâmetro | Padrão | Para que serve |
|-----------|--------|----------------|
| Prazo de arquivamento | 30 dias | Quanto tempo um processo concluído espera antes de ser arquivado automaticamente |
| Antecedência do alerta de prazo | 2 dias | Com quantos dias de antecedência o alerta de prazo é disparado |
| Limiar de "processo parado" | 7 dias | A partir de quantos dias sem movimentação um processo entra no KPI "Processos Parados" |

> **Ainda não há tela para editá-los.** Os valores estão disponíveis no sistema
> e podem ser alterados pela equipe técnica; a tela de configuração para o
> Administrador está prevista para uma etapa seguinte.

---

## Nota: permissão de Auditoria

**Auditoria não é um perfil**, e sim uma **permissão** que o Administrador
concede por cima de um perfil existente (Servidor, Gestor ou Administrador).
Quem recebe a permissão de Auditoria pode:

- **Visualizar qualquer processo do sistema**, de qualquer unidade — inclusive
  os sigilosos — para rastrear a cadeia completa de tramitação e decisões;
- **Consultar relatórios consolidados** de tramitação para subsidiar
  fiscalizações e prestações de contas.

Ao entrar, um usuário com permissão de Auditoria é levado diretamente à área de
**Relatório de Auditoria**, onde escolhe um **período** (início e fim), uma
**unidade** e um **tipo de processo** — todos opcionais — e aciona **"Gerar
relatório"**. O resultado traz o **total de processos no período**, o **tempo
médio de tramitação** e a listagem dos processos com número, assunto, unidade,
tipo e situação. Quando nada corresponde aos filtros, o relatório informa isso
em vez de exibir uma lista vazia.

---

## Para o cidadão (sem login)

Duas áreas do sistema são abertas ao público, **sem necessidade de cadastro ou
senha**.

### Consulta pública de processos

Qualquer pessoa pode acompanhar o andamento de processos de duas formas:

- **Consultar por número** — informando o número no formato `AAAA/NNNNNN`.
  O resultado traz o número, o assunto, o tipo, a situação, a unidade atual, a
  data de criação, os **nomes dos interessados** e o **histórico de
  movimentações** (data, unidade de origem, unidade de destino e situação
  resultante).
- **Pesquisar por assunto, tipo ou período** — com resultados paginados
  mostrando número, assunto, tipo, situação e unidade atual de cada processo.

O que a consulta pública **nunca** revela: **CPF ou CNPJ** dos interessados,
os **nomes dos servidores** que atuaram nas movimentações, e os **documentos
anexados**. Processos marcados como **sigilosos** não aparecem de forma alguma
— nem por número, nem na pesquisa.

### Solicitação de privacidade (LGPD)

Quem é titular de dados pessoais citados em um processo (ou seu representante
legal) pode pedir a **exclusão** ou a **anonimização** desses dados pelo canal
público de solicitação LGPD:

1. Informe o **número do processo**, seu **nome completo**, **CPF** e um
   **e-mail para resposta**.
2. Escolha o tipo de solicitação: **"Exclusão de dados"** ou **"Anonimização de
   dados"**.
3. Anexe um **documento de identificação com foto** (PDF, JPG ou PNG).
4. Envie. Você recebe um **número de protocolo** em tela e por e-mail.

A resposta é enviada ao e-mail informado em **até 15 dias**. Guarde o número de
protocolo — é por ele que a solicitação é identificada.

---

## Fora do escopo desta versão

Para evitar expectativa equivocada, estes itens **não existem** no sistema hoje:

- **Assinatura digital de documentos (ICP-Brasil).** Foi movida para uma fase
  seguinte do produto. A aba "Documentos assinados" de "Meu Perfil" apenas
  informa isso, e não há nenhuma ação de assinar ou verificar assinatura em
  processos ou documentos.
- **Roteiro ou tramitação automática por tipo de processo.** O destino de cada
  movimentação é sempre escolhido pelo servidor no momento da ação.
- **Tela de configuração dos parâmetros operacionais** (veja
  "Parâmetros operacionais do sistema").
- **Tela de busca de processos por número dentro do sistema.** Os filtros do
  quadro cobrem tipo, assunto e período.

---

## Glossário

| Termo | O que significa |
|-------|-----------------|
| **Processo** | O documento/assunto administrativo que tramita no sistema, com número no formato `AAAA/NNNNNN`, tipo, prazo e interessados. Nasce atribuído ao servidor que o criou. |
| **Unidade** | Área administrativa da instituição (ex.: uma coordenadoria financeira). Base do controle de acesso. |
| **Setor** | Subdivisão de uma unidade (ex.: o gabinete da coordenadoria financeira). Organiza as pessoas e é escolhido a cada tramitação; **não** altera quem enxerga o quê — isso continua sendo por unidade. |
| **Tipo de processo** | Categoria do processo, usada em filtros do quadro/dashboard e no prazo de anonimização LGPD — não define um caminho de tramitação. |
| **Modelo de documento** | Texto pré-formatado com lacunas, cadastrado pelo Administrador, que o Servidor pode escolher e completar ao abrir um processo; gera um PDF anexado ao processo, tratado como qualquer outro documento. |
| **Tramitação** | O conjunto de ações (Envio, Devolução, Reatribuição, Conclusão) que movem um processo entre servidores, setores e unidades. |
| **Enviar** | Encaminhar o processo a um servidor de destino escolhido explicitamente (unidade, setor, servidor), com mensagem. |
| **Devolver** | Mandar o processo de volta a quem o enviou por último (resolvido automaticamente pelo sistema), com motivo e justificativa opcional. |
| **Reatribuir** | Corrigir a pessoa responsável dentro da **mesma unidade**, quando a atribuição foi indevida; não altera status nem prazo. |
| **Concluir** | Encerrar o tratamento do processo, ação própria disponível a qualquer momento para quem está com ele. |
| **Ação necessária** | Selo do card que indica que **você** é o responsável atual — a próxima ação é sua. |
| **Quadro Kanban** | Painel visual que organiza os processos em colunas por situação (Aberto, Em Tramitação, Concluído, Arquivado). |
| **Situação do processo** | Estágio atual: Aberto, Em Tramitação, Concluído ou Arquivado. |
| **Arquivamento automático** | O sistema arquiva sozinho processos concluídos após o prazo configurado (padrão: 30 dias). |
| **Sigilo** | Marcação que oculta o processo da consulta pública e de quem está fora da unidade onde ele se encontra; não afeta a tramitação interna. |
| **Consulta pública** | Pesquisa de processos aberta a qualquer pessoa, sem login. |
| **Auditoria** | Permissão concedida pelo Administrador que dá acesso amplo a processos e relatórios para fiscalização. |
| **LGPD** | Lei de proteção de dados pessoais (Lei 13.709/2018); embasa os pedidos de exclusão/anonimização. |
| **Protocolo LGPD** | Número gerado ao registrar uma solicitação LGPD; identifica o pedido até a resposta. |
| **Anonimização** | Substituição irreversível dos dados pessoais do titular no processo (nome e CPF/CNPJ), preservando número, datas e histórico. |

---

*Este manual descreve como **operar** o SETES.DOCS conforme cada perfil de
acesso. As regras de negócio detalhadas (cenários de aceite e casos de borda)
estão no documento mestre `docs/PRD.md`.*
