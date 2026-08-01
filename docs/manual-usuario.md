# Manual do Usuário — SETES.DOCS

Guia prático de operação do sistema, organizado por tipo de perfil. Cada
pessoa recebe um perfil ao ser cadastrada, e é o perfil que determina o que
ela vê e pode fazer. Os três perfis são:

- **Servidor** — executa o dia a dia dos processos da sua unidade.
- **Gestor** — acompanha o desempenho e a equipe das unidades que gerencia.
- **Administrador** — configura a estrutura do sistema para todo o órgão.

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
automaticamente à tela inicial do seu perfil.

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

Em "Meu Perfil", você pode alterar a senha informando a **senha atual** e uma
**nova senha**. A nova senha precisa atender às regras de complexidade e **não
pode repetir** a senha atual nem as **6 últimas** que você já usou.

### 5. Meu Perfil

A tela **"Meu Perfil"** mostra:

- Seus dados de cadastro — nome, e-mail, perfil, situação e, quando
  preenchidos, **unidade, setor, cargo, telefone e chefia direta** (campos em
  branco simplesmente não aparecem);
- A **lista de processos em que você atuou** (número, assunto, data e tipo de
  ação);
- A **lista de documentos que você assinou** digitalmente.

Se você acabou de ser cadastrado e ainda não atuou em nada, essas listas
aparecem vazias com um aviso — é o esperado.

### 6. Notificações

O sistema avisa você sobre eventos importantes de duas formas: por um **sino de
notificações dentro do sistema** e por **e-mail** (para você não perder prazos
mesmo sem estar logado). Exemplos de aviso: novo processo chegando à sua
unidade, processo concluído e prazo se aproximando.

- O número no sino indica quantas notificações **não lidas** você tem. Abrir o
  painel **não zera o contador** — uma notificação só é considerada lida quando
  você **clica nela** ou usa **"Marcar todas como lidas"**.
- Notificações já lidas são mantidas por **30 dias** e depois removidas
  automaticamente.

### 7. Sair e sessão automática

Use **"Sair"** para encerrar sua sessão com segurança. Por proteção, o sistema
também **encerra sozinho sessões inativas** após um tempo — quando isso
acontece, basta entrar de novo.

---

## Perfil Servidor

O Servidor é o **executor do dia a dia**. Ao entrar, você chega ao seu
**quadro de processos (Kanban) pessoal**.

> **Regra de visibilidade:** o seu quadro é **pessoal** — mostra
> exclusivamente os processos em que você é o **responsável atual**, os que
> você **criou** e aqueles pelos quais você **já passou** (foi responsável em
> algum momento do histórico). Não é mais "todos os processos da sua
> unidade": um colega da sua unidade que você nunca tocou não aparece no seu
> quadro. Um processo sigiloso fora da sua unidade atual **não aparece**,
> mesmo que você já tenha sido responsável por ele — o sigilo prevalece. Isso
> muda apenas a **composição do quadro**, não o acesso: você continua podendo
> abrir qualquer processo da sua unidade por link direto ou pela busca
> interna (que continua por unidade, veja "Buscar e filtrar processos").
> Tentar abrir um processo fora do seu escopo por unidade resulta em
> **"Acesso negado"**.

### A tela de Processos (Kanban e Lista)

A tela de Processos tem **dois modos de visualização**, alternáveis por um
controle no cabeçalho:

- **Kanban** (modo padrão) — colunas por situação: **Aberto** (azul), **Em
  Tramitação** (âmbar), **Concluído** (verde) e **Arquivado** (cinza). As
  colunas mudam sozinhas conforme os processos são movimentados (não é preciso
  arrastar manualmente para trocar de situação).
- **Lista** — os mesmos processos como linhas empilhadas, com a situação
  indicada à direita de cada linha.

Cada card (ou linha) mostra o **número**, o **tipo de processo**, o
**assunto**, a **unidade atual** (nome por extenso), o **servidor
responsável**, a **data de criação**, o **prazo com os dias restantes** e o
cadeado 🔒 quando o processo é sigiloso. Os processos aparecem **ordenados
por prazo**, e o cabeçalho exibe o total de processos visíveis.

- **Cards com destaque sólido** e o selo **"Ação necessária"** são processos
  em que você é o responsável atual — a próxima ação é sua.
- **Cards discretos** (borda tracejada) são processos que você criou ou já
  deteve, mas que estão agora com outro servidor — o nome de quem está com o
  processo aparece no card ("Com: Fulano"). Você pode acompanhá-los, mas não
  agir sobre eles enquanto não voltarem a ser sua responsabilidade.
- **Cards acinzentados** (`somente_leitura`) são processos que a sua unidade
  protocolou e que já tramitaram para uma unidade que não é a sua — eixo
  independente do anterior: um card pode ser discreto (acompanhamento) e
  acinzentado (fora da sua unidade) ao mesmo tempo.
- Um card com o selo **"↩ Devolvido"** e borda âmbar indica que o processo
  acabou de ser devolvido a você e está pronto para uma nova ação; o destaque
  some assim que você enviar novamente.
- O checkbox **"Exibir Arquivados"**, no topo da tela, começa **desmarcado**
  — processos **"Concluído" aparecem sempre**; só os **"Arquivado"** ficam
  ocultos até você marcá-lo. A preferência é lembrada da próxima vez que você
  acessar a tela.
- Uma **barra de filtros** permite refinar o quadro por **tipo de
  processo**, por **assunto** (texto parcial) e por **período de criação**
  (data inicial/final) — combináveis entre si e com "Exibir Arquivados", sem
  nunca mostrar processos fora do seu quadro pessoal. Um botão "Limpar
  filtros" restaura a visão completa.

### Criar um novo processo

Para dar início a uma tramitação formal:

1. Escolha **"Novo processo"**.
2. Preencha os dados: assunto, tipo de processo, prazo e os interessados.
3. Confirme. O sistema gera o **número do processo**, e ele nasce **atribuído
   a você** — aparece imediatamente no seu quadro, como responsável, mesmo
   antes de qualquer tramitação.

Para criar um processo você precisa estar vinculado a um **setor** da sua
unidade; se seu cadastro não tiver setor, peça ao Administrador para
completá-lo antes de tentar criar um processo.

### Tramitar um processo: Enviar, Devolver ou Reatribuir

Não existe mais um "caminho predefinido" por tipo de processo — você escolhe
explicitamente **para quem** o processo vai a cada tramitação, pelo botão
**"Tramitar"**, que abre um único formulário com três tipos de ação:

**Enviar** — para mandar o processo adiante, a quem deve tratá-lo:

1. Abra o processo, clique em **"Tramitar"** e deixe selecionado o tipo de
   ação **"Envio"**.
2. Escolha a **unidade**, depois o **setor** dessa unidade e, por fim, o
   **servidor** — os campos aparecem em cascata, um depois do outro.
3. Escreva uma **mensagem** explicando o que precisa ser feito e confirme. O
   processo sai do seu quadro e chega ao servidor escolhido, que é notificado.

Você não pode enviar um processo para si mesmo — o destino tem que ser outro
servidor.

**Devolver** — para mandar o processo de volta a quem te enviou, quando algo
precisa de correção antes de seguir adiante:

1. Abra o processo, clique em **"Tramitar"** e mude o tipo de ação para
   **"Devolução"**.
2. O destino **não é escolhido por você** — o sistema já sabe para quem
   devolver (quem enviou o processo a você da última vez).
3. Selecione um **motivo** (Documentação insuficiente, Correção de dados ou
   Diligência complementar) e, se quiser, uma justificativa, e confirme.

Se o processo nunca foi enviado a ninguém (ainda está com quem o criou), não
há devolução possível — o sistema avisa que não há remetente anterior.

**Reatribuir** — para corrigir quando o processo chegou à unidade certa, mas
com a **pessoa errada**:

1. Abra o processo, clique em **"Tramitar"** e mude o tipo de ação para
   **"Reatribuir"**.
2. A **unidade fica travada** (não muda) — você só escolhe o **setor** e o
   **servidor** corretos dentro da mesma unidade.
3. Escreva a **justificativa** (obrigatória) e confirme.

A reatribuição **não altera o status do processo nem o prazo** — é só uma
correção de responsável. Podem reatribuir: quem está com o processo agora,
quem o enviou por engano da última vez, ou o Gestor da unidade. Se você
enviou o processo para a pessoa errada e ela reatribuir para a pessoa certa,
você recebe um aviso de que o destino foi corrigido.

> **Quando usar qual:** unidade errada → **Devolver**; setor ou pessoa errados
> dentro da unidade certa → **Reatribuir**; processo pronto para seguir →
> **Enviar**.

### Concluir um processo

Quando o tratamento do processo estiver encerrado, use o botão **"Concluir"**
— disponível a qualquer momento, sem precisar enviar o processo a mais
ninguém antes. Após confirmar, o processo passa para "Concluído" e o prazo de
arquivamento é contado a partir desse instante. Podem concluir: quem está com
o processo agora, ou o Gestor da unidade.

### Acompanhar o histórico de tramitação

Cada processo tem um **histórico completo e imutável**: por quais unidades,
setores e servidores passou, quando, quem atuou em cada ação (Envio,
Devolução, Reatribuição, Conclusão) e a mensagem ou justificativa de cada
uma. Esse histórico serve para entender toda a trajetória do processo.

### Buscar e filtrar processos

Você pode **localizar processos** por número, assunto ou período. Diferente
do seu quadro (que agora é pessoal), a **busca continua por unidade** — ela
retorna os processos atualmente na sua unidade e os que ela protocolou
(origem), sempre excluindo sigilosos fora da sua unidade. É assim de
propósito: o quadro é a sua área de trabalho pessoal, a busca serve para
localizar processos que colegas da sua unidade estão tratando, mesmo que
você nunca os tenha tocado.

### Anexar, consultar e remover documentos

- **Anexar:** adicione documentos ao processo nos formatos **PDF, DOC, DOCX,
  JPG ou PNG**, com até **20 MB** por arquivo. Arquivos vazios ou em outros
  formatos são recusados. Se você anexar um arquivo com nome repetido, o
  sistema o renomeia automaticamente (ex.: "parecer (1).pdf") — nada é
  sobrescrito.
- **Consultar / baixar:** abra ou baixe os documentos já anexados para analisar
  o conteúdo.
- **Remover:** um documento pode ser removido **apenas enquanto o processo
  ainda está com a sua unidade e não foi enviado** (processo recém-criado ou
  recém-devolvido). Depois do envio, a remoção é bloqueada. A remoção pede
  confirmação, fica registrada no histórico do processo (com autor e data/hora)
  e o arquivo é preservado por **30 dias** — nesse período, o Administrador
  consegue restaurá-lo se a remoção tiver sido um engano.

### Assinar documentos digitalmente

> **Sujeito a confirmação do certificado digital a ser utilizado.** Esta
> funcionalidade depende da confirmação de compatibilidade dos certificados
> digitais adotados pelo órgão; até essa confirmação, ela pode não estar
> disponível.

Você pode **assinar digitalmente** documentos de um processo para dar validade
jurídica à sua manifestação, usando seu certificado digital. Qualquer pessoa
pode depois **verificar** um documento assinado para confirmar que o conteúdo
não foi alterado. Os documentos que você assinou ficam registrados no seu
"Meu Perfil".

### Marcar sigilo

Quando um processo exige confidencialidade, você pode **marcá-lo como sigiloso**
(e remover o sigilo depois). O sigilo **restringe a aparição do processo na
consulta pública** — a tramitação interna continua normalmente. Marcar e
remover sigilo é uma ação do **Servidor da unidade onde o processo está**; nas
demais unidades, um processo sigiloso simplesmente não aparece (só quem tem
permissão de Auditoria consegue vê-lo).

---

## Perfil Gestor

O Gestor tem a **visão tática** das unidades que gerencia. Ao entrar, você chega
ao **Painel de Indicadores**.

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

No topo do painel, cinco **cards de contagem por status** dão o panorama
geral das suas unidades: **Total**, **Abertos**, **Em Tramitação**,
**Concluídos** e **Arquivados** — o Total é sempre a soma dos outros quatro.

Abaixo, o painel reúne os números que ajudam a monitorar a eficiência das
suas unidades, como:

- **Processos ativos** no momento;
- **Tempo médio de tramitação**;
- **Processos parados** (onde pode haver gargalo);
- **Produtividade por unidade**.

Abaixo dos KPIs, três **gráficos de distribuição** mostram como os processos
**ativos** (Aberto e Em Tramitação) das suas unidades se dividem:

- **Processos por Unidade**;
- **Processos por Tipo**;
- **Processos por Usuário** (quem criou cada processo).

Use esses indicadores para identificar **onde os processos estão travando** e
**quem está sobrecarregado**, e assim tomar decisões.

### Quadro consolidado das suas unidades

Além dos números, você vê um **quadro de processos consolidado** reunindo, em
um só lugar, os processos de **todas as unidades que você gerencia** — uma visão
completa do que está sob sua responsabilidade. Um **filtro por unidade** permite
focar em uma unidade de cada vez, combinável com os filtros de tipo, assunto e
período e com o checkbox "Exibir Arquivados" (mesma mecânica do Servidor,
veja "A tela de Processos"), e a alternância **Kanban / Lista** funciona
igual à do Servidor.

### Cadastrar usuários da sua unidade

Para não depender da equipe central a cada nova pessoa na sua equipe, você pode
**cadastrar novos usuários na sua própria unidade**:

1. Acione **"Novo usuário"** — o cadastro abre em uma janela sobre a listagem.
2. Informe nome, e-mail e a unidade (que precisa ser uma que você gerencia).
3. Escolha o **setor** dentro dessa unidade. Para o perfil Servidor o setor é
   **obrigatório**, e a lista só oferece setores ativos da unidade escolhida —
   trocar a unidade limpa o setor.
4. Se quiser, preencha **telefone, cargo e chefia direta** (a chefia é texto
   livre: pode ser alguém sem conta no sistema).
5. O único perfil que você pode atribuir é **Servidor**.
6. Confirme. A pessoa recebe o e-mail de primeiro acesso e passa a enxergar
   apenas os processos daquela unidade.

**Limites importantes:**

- Você **não pode** cadastrar usuários em unidades que não gerencia.
- Você **não pode** atribuir os perfis Gestor ou Administrador — isso é
  exclusivo do Administrador.

> **Nota:** o Gestor **acompanha** os processos das suas unidades. Criar,
> enviar, devolver e marcar sigilo são ações exclusivas dos **Servidores** de
> cada unidade; **Reatribuir** e **Concluir** também podem ser feitas pelo
> Gestor da unidade, além do servidor responsável.

---

## Perfil Administrador

O Administrador é o **guardião da configuração** do sistema. Ao entrar, você
chega à área de **Cadastros (Unidades)**. É aqui que se define a estrutura que
todos os demais perfis usam no dia a dia.

### Gerenciar usuários

- **Cadastrar usuários** de qualquer perfil (Servidor, Gestor ou
  Administrador) pelo botão **"Novo usuário"**, que abre o formulário em uma
  janela sobre a listagem. Informe nome, e-mail, perfil, unidade e **setor**, e
  opcionalmente **telefone, cargo e chefia direta**. A pessoa recebe o link de
  primeiro acesso (válido por 48 horas).
- **Filtrar a listagem por nome:** o campo de busca no alto da tela filtra
  enquanto você digita, por parte do nome e sem diferenciar maiúsculas de
  minúsculas. Limpe o campo para ver todos de novo.
- **Resetar a senha** de um usuário quando ele não conseguir se recuperar
  sozinho ou em caso de conta comprometida.
- **Desativar usuários** para revogar o acesso quando necessário. Quem está
  desativado não consegue entrar.

O sistema recusa cadastros com **e-mail já usado**, **e-mail em formato
inválido**, **nome em branco**, **unidade inexistente/inativa**, **Servidor sem
setor** ou **setor que não pertence à unidade escolhida**, sempre explicando o
motivo. Usuários com perfil Servidor que ainda estejam sem setor aparecem
marcados na listagem, para você regularizar o cadastro.

### Cadastrar unidades administrativas

**Cadastre e gerencie as unidades** (as coordenadorias e diretorias do órgão)
para refletir a estrutura organizacional. As unidades são a base do controle
de acesso e do destino das tramitações.

### Cadastrar setores de uma unidade

Cada unidade se divide em **setores** — o segundo nível da estrutura
organizacional. Na tela de unidades, acione **"Setores"** na linha da unidade
para abrir a lista dela e cadastrar, editar, desativar ou reativar setores.

- A **sigla é única dentro da unidade**, mas pode se repetir entre unidades
  diferentes (duas unidades podem ter um "GAB").
- **Setor nunca é excluído**, apenas desativado — o histórico de tramitação
  precisa continuar referenciando setores antigos.
- Não é possível desativar um setor enquanto houver **servidor ativo vinculado**
  a ele; o sistema informa quantos estão impedindo a operação.
- **Desativar a unidade desativa todos os seus setores.** A tela avisa quantos
  serão afetados antes de confirmar. Ao reativar a unidade, os setores
  **permanecem inativos**: cada um precisa ser reativado individualmente.

> **Atenção:** o setor organiza as pessoas e é escolhido a cada tramitação, mas
> **não altera quem enxerga o quê** — o controle de acesso continua sendo por
> unidade.

### Cadastrar tipos de processo

Cadastre os **tipos de processo** (ex.: "Licitação", "Requerimento") usados na
criação de processos e nos filtros do Kanban e do dashboard. Diferente do
modelo anterior, o tipo de processo **não define mais um caminho fixo de
tramitação** — cada envio, devolução ou reatribuição tem seu destino escolhido
explicitamente pelo Servidor no momento da ação. Na tela de cada tipo, você
também configura o **prazo de anonimização LGPD** (em anos).

### Conceder permissão de Auditoria

Você pode **conceder e revogar a permissão de Auditoria** a usuários
específicos. Quem recebe essa permissão passa a poder acessar processos de
qualquer unidade — inclusive sigilosos — para fins de fiscalização. Veja a
[nota sobre auditoria](#nota-permissão-de-auditoria) mais abaixo.

### Configurar parâmetros do sistema

Ajuste os **parâmetros operacionais** para adequar o sistema às políticas do
órgão — por exemplo, o **prazo para arquivamento automático** de processos
concluídos (padrão: 30 dias).

### Organizar pessoas e responsabilidades

- **Vincular servidor à unidade e ao setor:** garanta que cada servidor esteja
  alocado a **exatamente uma unidade por vez** e a um setor dela. Ao transferir
  alguém, escolha também o **setor da nova unidade** — o sistema recusa a
  transferência que deixaria o servidor com um setor da unidade antiga. O
  histórico anterior é preservado, mas ele deixa de ver o quadro da unidade
  antiga.
- **Definir as unidades de um Gestor:** determine **quais unidades** cada Gestor
  gerencia, para dar a ele a visibilidade adequada à sua responsabilidade.

### Acompanhar processos (somente leitura)

O Administrador tem acesso à tela de **Processos de todas as unidades**, em
modo **somente leitura**: você visualiza o quadro (Kanban ou Lista) e o detalhe
de qualquer processo, mas **não vê botões de ação** — criar processo, tramitar
(Enviar/Devolver/Reatribuir), concluir e marcar sigilo são ações exclusivas de
Servidor e Gestor da unidade onde o processo está. Use essa visão para
acompanhar o andamento geral sem interferir.

### Restaurar documentos removidos

Se um documento foi **removido por engano**, você pode **restaurá-lo** para
recuperar a informação excluída indevidamente. A restauração só é possível
dentro do período de retenção de **30 dias** após a remoção — depois disso, o
arquivo é apagado definitivamente.

### Tratar solicitações de privacidade (LGPD)

Cidadãos podem pedir a **exclusão ou anonimização dos seus dados pessoais**
pelo canal público (ver [Para o cidadão](#para-o-cidadão-sem-login)). Em
**"Solicitações LGPD"**, você vê a fila de pedidos com protocolo, data,
solicitante, processo e status (**Pendente / Em análise / Atendida /
Rejeitada**) e, para cada um:

- **Atender:** após validar a identidade do solicitante, o atendimento
  **anonimiza de forma irreversível** os dados pessoais do titular no processo
  (o número, as datas e o histórico de tramitação são preservados) e envia
  e-mail automático ao solicitante informando a conclusão.
- **Rejeitar:** exige uma **justificativa obrigatória** (por exemplo, quando o
  solicitante não é o titular dos dados), enviada por e-mail ao solicitante.

"Atendida" e "Rejeitada" são status finais — a solicitação não pode ser
reprocessada depois.

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
**Relatórios de Auditoria**.

---

## Para o cidadão (sem login)

Duas áreas do sistema são abertas ao público, **sem necessidade de cadastro ou
senha**.

### Consulta pública de processos

Qualquer cidadão pode pesquisar o **andamento de processos** por número,
assunto, tipo de processo ou período, no portal de consulta pública. A consulta
mostra as informações de tramitação do processo, **sem expor dados pessoais**
dos interessados. Processos marcados como **sigilosos** não aparecem nessa
consulta.

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

## Glossário

| Termo | O que significa |
|-------|-----------------|
| **Processo** | O documento/assunto administrativo que tramita no sistema, com número, tipo, prazo e interessados. Nasce atribuído ao servidor que o criou. |
| **Unidade** | Coordenadoria ou diretoria do órgão (ex.: uma coordenadoria financeira). Base do controle de acesso. |
| **Setor** | Subdivisão de uma unidade (ex.: o gabinete da coordenadoria financeira). Organiza as pessoas e é escolhido a cada tramitação; **não** altera quem enxerga o quê — isso continua sendo por unidade. |
| **Tipo de processo** | Categoria do processo, usada em filtros do Kanban/dashboard e no prazo de anonimização LGPD — não define mais um caminho de tramitação. |
| **Tramitação** | O conjunto de ações (Envio, Devolução, Reatribuição, Conclusão) que movem um processo entre servidores, setores e unidades. |
| **Enviar** | Encaminhar o processo a um servidor de destino escolhido explicitamente (unidade, setor, servidor), com mensagem. |
| **Devolver** | Mandar o processo de volta a quem o enviou por último (resolvido automaticamente pelo sistema), com motivo e justificativa. |
| **Reatribuir** | Corrigir a pessoa responsável dentro da **mesma unidade**, quando a atribuição foi indevida; não altera status nem prazo. |
| **Concluir** | Encerrar o tratamento do processo, ação própria disponível a qualquer momento para quem está com ele ou para o Gestor da unidade. |
| **Quadro Kanban** | Painel visual que organiza os processos em colunas por situação (Aberto, Em Tramitação, Concluído, Arquivado). |
| **Situação do processo** | Estágio atual: Aberto, Em Tramitação, Concluído ou Arquivado. |
| **Arquivamento automático** | O sistema arquiva sozinho processos concluídos após o prazo configurado (padrão: 30 dias). |
| **Sigilo** | Marcação que restringe a aparição do processo na consulta pública; não afeta a tramitação interna. |
| **Assinatura digital** | Assinatura de um documento com validade jurídica, feita com certificado digital. *(Sujeito a confirmação do certificado digital a ser utilizado.)* |
| **Consulta pública** | Pesquisa de processos aberta ao cidadão, sem login. |
| **Auditoria** | Permissão concedida pelo Administrador que dá acesso amplo a processos e relatórios para fiscalização. |
| **LGPD** | Lei de proteção de dados pessoais; embasa os pedidos de exclusão/anonimização feitos por cidadãos. |
| **Protocolo LGPD** | Número gerado ao registrar uma solicitação LGPD; identifica o pedido até a resposta. |
| **Anonimização** | Substituição irreversível dos dados pessoais do titular no processo (nome e CPF/CNPJ), preservando número, datas e histórico. |

---

*Este manual descreve como **operar** o SETES.DOCS conforme cada perfil de
acesso. As regras de negócio detalhadas (cenários de aceite e casos de borda)
estão no documento mestre `docs/PRD.md`.*
