# processos

## Purpose

Criação de processo com metadados e interessados, geração do número `AAAA/NNNNNN`, snapshot do roteiro na criação e busca interna por unidade (US 2.1, 2.7).

## Requirements

### Requirement: Criação de processo com número único
O sistema SHALL permitir que um Servidor crie um processo administrativo informando assunto, tipo de processo, interessados e prazo (dias corridos), gerando um número único no formato `AAAA/NNNNNN` (ano com 4 dígitos + sequencial de 6 dígitos, reiniciado a cada ano), atribuindo status inicial "Aberto" e definindo a unidade atual como a unidade do Servidor criador. Ver PRD US 2.1.

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

#### Scenario: Tipo de processo sem roteiro definido
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** tento criar um processo selecionando um tipo cujo roteiro de tramitação está vazio (sem unidades definidas)
- **ENTÃO** o sistema exibe "Este tipo de processo não possui roteiro de tramitação configurado. Entre em contato com o Administrador." e não permite a criação (PRD US 2.1 Cen.3c)

### Requirement: Snapshot do roteiro na criação
O sistema SHALL, na criação de cada processo, fixar (snapshot) o roteiro de tramitação vigente do tipo de processo naquele momento, de modo que alterações posteriores no roteiro do tipo não afetem processos já criados. Consome o versionamento de `tipos-processo-e-roteiros`. Ver PRD US 2.1 e US 8.2.

#### Scenario: Processo mantém o roteiro vigente na criação
- **DADO** que um processo do tipo "Licitação" foi criado com o roteiro COFIN → AJUR → DIRAD
- **QUANDO** o Administrador posteriormente altera o roteiro do tipo "Licitação"
- **ENTÃO** o processo já criado continua tramitando pelo roteiro COFIN → AJUR → DIRAD vigente no momento de sua criação, sem ser afetado pela alteração (PRD US 8.2 Cen.2)

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
