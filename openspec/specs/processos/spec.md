# processos

## Purpose

Criação de processo com metadados e interessados, geração do número `AAAA/NNNNNN`, atribuição ao criador (unidade, setor e servidor) e busca interna por unidade (US 2.1, 2.7).

## Requirements

### Requirement: Criação de processo com número único
O sistema SHALL permitir ao Servidor criar um processo informando tipo de processo, assunto, prazo em dias e interessados, atribuindo um **número único** no formato `AAAA/NNNNNN`. Na criação, o processo SHALL nascer com status "Aberto", com a **unidade, o setor e o servidor do criador** como unidade, setor e servidor atuais — ou seja, **atribuído ao próprio criador** — de modo que passe a constar imediatamente na sua área de trabalho, antes de qualquer tramitação. A unidade de origem SHALL ser registrada e permanecer imutável. A criação NÃO SHALL depender de roteiro nem de qualquer configuração de fluxo do tipo de processo. Ver PRD US 2.1.

#### Scenario: Criação atribui o processo ao criador
- **DADO** que sou Servidor da unidade COFIN, setor "Protocolo"
- **QUANDO** crio um processo informando tipo, assunto, prazo e interessados
- **ENTÃO** o processo é criado com número único no formato `AAAA/NNNNNN`, status "Aberto", unidade atual COFIN, setor atual Protocolo e **eu** como servidor responsável

#### Scenario: Criação de processo com dados obrigatórios
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** preencho assunto, tipo de processo, interessados e prazo em dias corridos e confirmo a criação
- **ENTÃO** o processo é criado com status "Aberto", recebe um número único no formato `AAAA/NNNNNN` (ex.: 2026/000001) reiniciado a cada ano, e passa a aparecer na coluna "Aberto" do Kanban da minha unidade (PRD US 2.1 Cen.1)

#### Scenario: Expansão do sequencial ao atingir o limite anual
- **DADO** que o sequencial anual de processos atingiu o valor 999.999 no ano corrente
- **QUANDO** um novo processo é criado nesse mesmo ano
- **ENTÃO** o sistema expande automaticamente o sequencial para 7 dígitos (`AAAA/NNNNNNN`), registra o evento em log de sistema, e o formato `AAAA/N...` permanece sem limite superior de dígitos (PRD US 2.1 Cen.1)

#### Scenario: Criação sem campos obrigatórios
- **DADO** que estou autenticado como Servidor
- **QUANDO** tento criar um processo sem preencher "assunto" ou "tipo de processo"
- **ENTÃO** o sistema rejeita a criação e destaca os campos obrigatórios pendentes (PRD US 2.1 Cen.2)

#### Scenario: Interessado com CPF inválido
- **DADO** que estou criando um processo
- **QUANDO** preencho um CPF com dígito verificador inválido no campo de interessado
- **ENTÃO** o sistema exibe "CPF inválido — verifique o número informado" e não permite prosseguir (PRD US 2.1 Cen.3)

#### Scenario: Interessado com CNPJ inválido
- **DADO** que estou criando um processo e seleciono tipo de interessado "Pessoa Jurídica"
- **QUANDO** preencho um CNPJ com dígito verificador inválido no campo de interessado
- **ENTÃO** o sistema exibe "CNPJ inválido — verifique o número informado" e não permite prosseguir (PRD US 2.1 Cen.3b)

#### Scenario: Criação não exige roteiro configurado
- **DADO** que o tipo de processo escolhido não possui nenhuma configuração de fluxo
- **QUANDO** crio o processo
- **ENTÃO** a criação é concluída normalmente — nenhuma validação de roteiro é aplicada, porque roteiros não existem mais no sistema

#### Scenario: Criação por usuário sem setor é rejeitada
- **DADO** que sou um Servidor cujo cadastro não possui setor vinculado
- **QUANDO** tento criar um processo
- **ENTÃO** o sistema rejeita a operação informando que é necessário estar vinculado a um setor, e nenhum processo é criado

#### Scenario: Unidade de origem é imutável
- **DADO** que um processo foi criado na unidade COFIN e depois enviado para AJUR e DIRAD
- **QUANDO** consulto o processo
- **ENTÃO** a unidade de origem continua sendo COFIN, independentemente da unidade atual

### Requirement: Responsável atual do processo
O sistema SHALL registrar, em cada processo, o **setor atual** e o **servidor atualmente responsável**, atualizados a cada ação de tramitação (Envio, Devolução, Reatribuição). O servidor responsável SHALL ser sempre um usuário existente — o processo nunca fica sem responsável. Além do responsável corrente, o sistema SHALL preservar de forma permanente o **servidor criador** e, por meio do histórico imutável de tramitação, a **sequência completa de servidores** que detiveram o processo.

#### Scenario: Responsável acompanha a tramitação
- **DADO** que um processo foi criado por A, enviado para B, reatribuído para C e devolvido para A
- **QUANDO** consulto o processo em cada momento
- **ENTÃO** o servidor responsável é, respectivamente, A, B, C e A — sempre exatamente um servidor

#### Scenario: Sequência de detentores recuperável do histórico
- **DADO** que um processo passou pelos servidores A, B e C
- **QUANDO** consulto seu histórico de tramitação
- **ENTÃO** consigo reconstruir a sequência completa de detentores a partir dos servidores de origem e destino dos eventos, somada ao criador registrado no processo

#### Scenario: Criador preservado após a saída do processo
- **DADO** que criei um processo e o enviei para outra unidade há meses
- **QUANDO** consulto o processo
- **ENTÃO** continuo registrado como seu criador, ainda que não seja mais o responsável atual

### Requirement: Interessados do processo
O sistema SHALL registrar um ou mais interessados por processo, cada um com nome completo (obrigatório), CPF ou CNPJ (opcional, validado por dígito verificador) e tipo de participação (opcional: Requerente, Representado, Terceiro). Estes são dados pessoais de terceiros, acessíveis apenas por usuários autenticados e autorizados por unidade. Ver PRD US 2.1 (Definição do campo "Interessados").

#### Scenario: Processo com múltiplos interessados
- **DADO** que estou criando um processo
- **QUANDO** adiciono dois interessados — um Requerente pessoa física com CPF válido e um Terceiro pessoa jurídica com CNPJ válido
- **ENTÃO** ambos os interessados são vinculados ao processo com seus respectivos nome, documento e tipo de participação

#### Scenario: Interessado apenas com nome
- **DADO** que estou criando um processo
- **QUANDO** informo um interessado apenas com nome completo, sem CPF/CNPJ nem tipo de participação
- **ENTÃO** o sistema aceita o interessado, pois apenas o nome é obrigatório

### Requirement: Busca interna de processos por unidade
O sistema SHALL permitir que um usuário autenticado busque e filtre processos **de sua própria unidade** (ou das unidades geridas, no caso do Gestor) por número exato, termo no assunto e intervalo de datas, sem jamais retornar processos fora de seu escopo de unidade. Ver PRD US 2.7.

#### Scenario: Busca por número exato
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** informo um número de processo existente na minha unidade
- **ENTÃO** o sistema retorna o processo correspondente (PRD US 2.7 Cen.1)

#### Scenario: Busca por termo no assunto restrita à unidade
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** informo um termo de busca no campo "assunto"
- **ENTÃO** o sistema retorna apenas os processos da unidade COFIN cujo assunto contém o termo, nunca processos de outras unidades (PRD US 2.7 Cen.2; PRD US 1.4)

#### Scenario: Filtro por período
- **DADO** que estou autenticado como Servidor
- **QUANDO** informo um intervalo de datas (inicial e final)
- **ENTÃO** o sistema retorna os processos da minha unidade criados no período informado (PRD US 2.7 Cen.3)

#### Scenario: Busca sem resultados
- **DADO** que estou autenticado como Servidor
- **QUANDO** informo uma combinação de filtros que não retorna resultados
- **ENTÃO** o sistema exibe "Nenhum processo encontrado para os filtros informados" (PRD US 2.7 Cen.4)
