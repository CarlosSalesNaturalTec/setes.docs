# consulta-publica

## Purpose

Canal público de consulta a processos administrativos, sem autenticação, que permite a
qualquer cidadão acompanhar o andamento de um processo pelo número exato ou pesquisar por
assunto, tipo e período — sempre respeitando sigilo processual e LGPD (sem CPF/CNPJ, sem
nomes de servidores) e protegido por rate limiting contra abuso. Ver PRD Épico 7.

## Requirements

### Requirement: Consulta pública de processo por número

O sistema SHALL disponibilizar um endpoint **público, sem autenticação**, que retorna,
a partir do número exato de um processo **não sigiloso**, os dados de andamento:
número, assunto, tipo de processo, status atual (máquina de estados `Aberto → Em
Tramitação → Concluído → Arquivado`), unidade atual, data de criação e histórico
simplificado de movimentações (datas e unidades percorridas). Processos marcados como
`sigiloso` SHALL ser tratados como inexistentes nesta consulta, retornando a mesma
mensagem de "não encontrado", para **não revelar sua existência**. Ver PRD US 7.1.

#### Scenario: Consulta por número de processo não sigiloso
- **DADO** que estou na página de Consulta Pública, sem autenticação
- **QUANDO** informo o número exato de um processo existente e não sigiloso e aciono "Consultar"
- **ENTÃO** visualizo número, assunto, tipo de processo, status atual, unidade atual, data de criação e o histórico simplificado de movimentações (datas e unidades percorridas) (PRD US 7.1 Cen.1)

#### Scenario: Número de processo inexistente
- **DADO** que estou na página de Consulta Pública
- **QUANDO** informo um número que não corresponde a nenhum processo
- **ENTÃO** o sistema exibe "Nenhum processo encontrado com o número informado" (PRD US 7.1 Cen.2)

#### Scenario: Consulta de processo sigiloso pelo número exato — existência não revelada
- **DADO** que um processo está marcado como `sigiloso` (US 2.6) e estou na Consulta Pública, sem autenticação
- **QUANDO** informo o número exato desse processo e aciono "Consultar"
- **ENTÃO** o sistema exibe "Nenhum processo encontrado com o número informado" — mensagem idêntica à de número inexistente, sem qualquer sinal de que o processo existe (PRD US 7.1 Cen.4)

### Requirement: Pesquisa pública por assunto, tipo e período

O sistema SHALL disponibilizar um endpoint **público, sem autenticação**, que pesquisa
processos por assunto (correspondência parcial), tipo de processo e período de criação
(data inicial e final), combináveis, retornando resultados **paginados em 20 por
página**. Processos marcados como `sigiloso` SHALL ser **excluídos de todos os
resultados**. Ver PRD US 7.2.

#### Scenario: Pesquisa por termo no assunto
- **DADO** que estou na página de Consulta Pública
- **QUANDO** preencho o campo "assunto" com um termo e aciono "Pesquisar"
- **ENTÃO** visualizo a lista de processos **não sigilosos** cujo assunto contém o termo informado (PRD US 7.2 Cen.1)

#### Scenario: Pesquisa combinada por tipo e período
- **DADO** que estou na página de Consulta Pública
- **QUANDO** preencho o tipo de processo e um período (data inicial e final) e aciono "Pesquisar"
- **ENTÃO** visualizo a lista de processos **não sigilosos** daquele tipo criados no período informado (PRD US 7.2 Cen.2)

#### Scenario: Pesquisa sem resultados
- **DADO** que estou na página de Consulta Pública
- **QUANDO** informo qualquer combinação de filtros que não retorna resultados
- **ENTÃO** o sistema exibe "Nenhum processo encontrado para os filtros informados" (PRD US 7.2 Cen.3)

#### Scenario: Processos sigilosos são excluídos da pesquisa
- **DADO** que existe um processo sigiloso cujo assunto casaria com o termo pesquisado
- **QUANDO** realizo a pesquisa por esse termo
- **ENTÃO** o processo sigiloso NÃO aparece entre os resultados (PRD US 7.2 Cen.1, US 2.6)

#### Scenario: Resultados paginados
- **DADO** que há mais de 20 processos não sigilosos correspondentes aos filtros
- **QUANDO** realizo a pesquisa
- **ENTÃO** o sistema retorna no máximo 20 resultados por página, com metadados de paginação (página atual e total), atendendo ao RNF de Performance

### Requirement: Ocultação de dados pessoais e de identificação interna na consulta pública

O sistema SHALL garantir que a resposta pública **nunca** serialize CPF ou CNPJ de
interessados nem nomes de servidores responsáveis por movimentações. A supressão SHALL
ocorrer na camada de schema/serialização do backend, não apenas na interface — o dado
completo permanece acessível somente a usuários autenticados e autorizados. Apenas o
nome do interessado é exibido, por ser informação de andamento processual. Ver PRD
US 7.1 (Cen.3) e RF 36.

#### Scenario: CPF/CNPJ do interessado não são expostos
- **DADO** que um processo não sigiloso possui interessado com nome e CPF/CNPJ cadastrados
- **QUANDO** consulto o processo pela Consulta Pública
- **ENTÃO** a resposta contém o nome do interessado, mas NÃO contém CPF nem CNPJ em nenhum campo (PRD US 7.1 Cen.3, RF 36)

#### Scenario: Histórico simplificado não expõe nomes de servidores
- **DADO** que um processo não sigiloso já passou por várias unidades
- **QUANDO** consulto seu histórico pela Consulta Pública
- **ENTÃO** cada movimentação exibe data, unidade de origem, unidade de destino e status, mas NÃO exibe o nome do servidor responsável, e eventos internos de marcação/remoção de sigilo NÃO aparecem (PRD US 7.1 Cen.1)

### Requirement: Rate limiting da consulta pública

O sistema SHALL limitar os endpoints públicos de consulta a no máximo **60 requisições
por minuto por endereço IP**, retornando, ao exceder, a mensagem "Muitas consultas
realizadas. Aguarde alguns instantes e tente novamente." e liberando o acesso
automaticamente após 60 segundos, sem prejudicar o uso legítimo do cidadão. Ver PRD
RNF de Segurança (Proteção contra Abuso).

#### Scenario: Requisições dentro do limite
- **DADO** que um cidadão realiza consultas em ritmo normal a partir de um IP
- **QUANDO** o número de requisições no minuto está em 60 ou menos
- **ENTÃO** as consultas são atendidas normalmente

#### Scenario: Acesso negado por excesso de requisições (abuso)
- **DADO** que um mesmo IP excedeu 60 requisições em um minuto
- **QUANDO** realiza uma requisição adicional dentro da mesma janela
- **ENTÃO** o sistema recusa com status HTTP 429 e a mensagem "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente.", e volta a atender o mesmo IP automaticamente após 60 segundos
