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

- Seus dados de cadastro;
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

### 7. Sair e sessão automática

Use **"Sair"** para encerrar sua sessão com segurança. Por proteção, o sistema
também **encerra sozinho sessões inativas** após um tempo — quando isso
acontece, basta entrar de novo.

---

## Perfil Servidor

O Servidor é o **executor do dia a dia**. Ao entrar, você chega ao seu
**quadro de processos (Kanban) da sua unidade**.

> **Regra de visibilidade:** você enxerga **apenas os processos que estão na sua
> unidade**. Processos que já seguiram para outra unidade saem do seu quadro,
> mas continuam no seu histórico pessoal ("Meu Perfil") e nas buscas restritas à
> sua unidade. Tentar abrir um processo de outra unidade resulta em **"Acesso
> negado"**.

### O quadro de processos (Kanban)

O quadro organiza os processos da sua unidade em colunas por situação:
**Aberto**, **Em Tramitação**, **Concluído** e **Arquivado**. Ele dá uma visão
rápida de onde cada processo está. As colunas mudam sozinhas conforme você
movimenta os processos (não é preciso arrastar manualmente para trocar de
situação).

### Criar um novo processo

Para dar início a uma tramitação formal:

1. Escolha **"Novo processo"**.
2. Preencha os dados: assunto, tipo de processo, data, prazo, unidade de origem
   e os interessados.
3. Confirme. O sistema gera o **número do processo** e ele passa a aparecer no
   seu quadro.

O **tipo de processo** escolhido já define o **roteiro** — ou seja, o caminho de
unidades por onde o processo vai passar.

### Despachar para a próxima unidade

Quando sua parte terminar, **despache** o processo para dar sequência:

1. Abra o processo e escolha **"Despachar"**.
2. O sistema indica a **próxima unidade conforme o roteiro** do tipo de
   processo.
3. Confirme. O processo sai do seu quadro e chega à próxima unidade, que é
   notificada.

O caminho é **predefinido e sequencial** — você não precisa adivinhar para onde
enviar.

### Devolver para a unidade anterior

Se algo precisa de correção ou diligência antes de seguir adiante, use
**"Devolver"** para mandar o processo de volta à **unidade anterior**,
registrando o motivo. É o caminho correto quando o processo veio incompleto.

### Acompanhar o histórico de tramitação

Cada processo tem um **histórico completo e imutável**: por quais unidades
passou, quando, quem atuou e **quanto tempo ficou em cada uma**. Esse histórico
serve para entender toda a trajetória do processo.

### Buscar e filtrar processos

Você pode **localizar processos da sua unidade** por número, assunto ou período.
A busca sempre respeita a regra de visibilidade — só retorna processos da sua
unidade.

### Anexar e consultar documentos

- **Anexar:** adicione documentos ao processo (arquivos de texto, PDF ou
  imagens) para centralizar tudo em um só lugar.
- **Consultar / baixar:** abra ou baixe os documentos já anexados para analisar
  o conteúdo.

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
consulta pública** — a tramitação interna continua normalmente. *(Gestores e
Administradores também podem marcar sigilo.)*

---

## Perfil Gestor

O Gestor tem a **visão tática** das unidades que gerencia. Ao entrar, você chega
ao **Painel de Indicadores**.

> **Regra de visibilidade:** você enxerga os processos de **todas as unidades
> que você gerencia** — não apenas uma. Quais unidades você gerencia é definido
> pelo Administrador.

### Painel de Indicadores (KPIs)

O painel reúne os números que ajudam a monitorar a eficiência das suas
unidades, como:

- **Processos ativos** no momento;
- **Tempo médio de tramitação**;
- **Processos parados** (onde pode haver gargalo);
- **Produtividade por unidade**.

Use esses indicadores para identificar **onde os processos estão travando** e
**quem está sobrecarregado**, e assim tomar decisões.

### Quadro consolidado das suas unidades

Além dos números, você vê um **quadro de processos consolidado** reunindo, em
um só lugar, os processos de **todas as unidades que você gerencia** — uma visão
completa do que está sob sua responsabilidade.

### Cadastrar usuários da sua unidade

Para não depender da equipe central a cada nova pessoa na sua equipe, você pode
**cadastrar novos usuários na sua própria unidade**:

1. Informe nome, e-mail e a unidade (que precisa ser uma que você gerencia).
2. O único perfil que você pode atribuir é **Servidor**.
3. Confirme. A pessoa recebe o e-mail de primeiro acesso e passa a enxergar
   apenas os processos daquela unidade.

**Limites importantes:**

- Você **não pode** cadastrar usuários em unidades que não gerencia.
- Você **não pode** atribuir os perfis Gestor ou Administrador — isso é
  exclusivo do Administrador.

### Marcar sigilo

Assim como o Servidor, o Gestor também pode **marcar e remover o sigilo** de um
processo quando a confidencialidade for necessária.

---

## Perfil Administrador

O Administrador é o **guardião da configuração** do sistema. Ao entrar, você
chega à área de **Cadastros (Unidades)**. É aqui que se define a estrutura que
todos os demais perfis usam no dia a dia.

### Gerenciar usuários

- **Cadastrar usuários** de qualquer perfil (Servidor, Gestor ou
  Administrador), informando nome, e-mail, unidade e perfil. A pessoa recebe o
  link de primeiro acesso (válido por 48 horas).
- **Resetar a senha** de um usuário quando ele não conseguir se recuperar
  sozinho ou em caso de conta comprometida.
- **Desativar usuários** para revogar o acesso quando necessário. Quem está
  desativado não consegue entrar.

O sistema recusa cadastros com **e-mail já usado**, **e-mail em formato
inválido**, **nome em branco** ou **unidade inexistente/inativa**, sempre
explicando o motivo.

### Cadastrar unidades administrativas

**Cadastre e gerencie as unidades** (por exemplo, setores e coordenadorias)
para refletir a estrutura organizacional do órgão. As unidades são a base do
controle de acesso e do roteiro dos processos.

### Cadastrar tipos de processo e desenhar roteiros

Para cada **tipo de processo**, você define o **roteiro de tramitação** — a
sequência de unidades por onde processos daquele tipo devem passar. É esse
roteiro que orienta os Servidores ao despachar, garantindo que cada processo
siga o caminho correto. No sistema, os roteiros são **lineares e sequenciais**.

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

- **Vincular servidor à unidade:** garanta que cada servidor esteja alocado a
  **exatamente uma unidade por vez**. Ao transferir alguém, o histórico anterior
  é preservado, mas ele deixa de ver o quadro da unidade antiga.
- **Definir as unidades de um Gestor:** determine **quais unidades** cada Gestor
  gerencia, para dar a ele a visibilidade adequada à sua responsabilidade.

### Restaurar documentos removidos

Se um documento foi **removido por engano**, você pode **restaurá-lo** para
recuperar a informação excluída indevidamente.

### Tratar solicitações de privacidade (LGPD)

Cidadãos podem pedir a **exclusão ou anonimização dos seus dados pessoais**. Cabe
ao Administrador **gerenciar essas solicitações** recebidas e dar o
encaminhamento a cada pedido, em conformidade com a legislação.

### Marcar sigilo

O Administrador também pode **marcar e remover o sigilo** de processos.

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

> **Sobre a Consulta Pública:** qualquer cidadão, **sem precisar de login**, pode
> pesquisar o andamento de processos por número, assunto, tipo ou período no
> portal de consulta pública. Processos marcados como **sigilosos** não aparecem
> nessa consulta.

---

## Glossário

| Termo | O que significa |
|-------|-----------------|
| **Processo** | O documento/assunto administrativo que tramita no sistema, com número, tipo, prazo e interessados. |
| **Unidade** | Setor ou coordenadoria do órgão (ex.: uma coordenadoria financeira). Base do acesso e do roteiro. |
| **Tipo de processo** | Categoria do processo que define qual roteiro ele seguirá. |
| **Roteiro** | O caminho predefinido de unidades por onde um tipo de processo passa, na ordem. |
| **Tramitação** | O andamento do processo de uma unidade para outra ao longo do roteiro. |
| **Despachar** | Enviar o processo para a **próxima** unidade do roteiro. |
| **Devolver** | Mandar o processo de volta para a unidade **anterior**, para correção ou diligência. |
| **Quadro Kanban** | Painel visual que organiza os processos em colunas por situação (Aberto, Em Tramitação, Concluído, Arquivado). |
| **Situação do processo** | Estágio atual: Aberto, Em Tramitação, Concluído ou Arquivado. |
| **Arquivamento automático** | O sistema arquiva sozinho processos concluídos após o prazo configurado (padrão: 30 dias). |
| **Sigilo** | Marcação que restringe a aparição do processo na consulta pública; não afeta a tramitação interna. |
| **Assinatura digital** | Assinatura de um documento com validade jurídica, feita com certificado digital. *(Sujeito a confirmação do certificado digital a ser utilizado.)* |
| **Consulta pública** | Pesquisa de processos aberta ao cidadão, sem login. |
| **Auditoria** | Permissão concedida pelo Administrador que dá acesso amplo a processos e relatórios para fiscalização. |
| **LGPD** | Lei de proteção de dados pessoais; embasa os pedidos de exclusão/anonimização feitos por cidadãos. |

---

*Este manual descreve como **operar** o SETES.DOCS conforme cada perfil de
acesso. As regras de negócio detalhadas (cenários de aceite e casos de borda)
estão no documento mestre `docs/PRD.md`.*
