# gestao-documental

## ADDED Requirements

### Requirement: Anexar documento a um processo
O sistema SHALL permitir que um usuário com acesso à unidade atual do processo anexe um documento nos formatos `PDF`, `DOC`, `DOCX`, `JPG` ou `PNG`, com tamanho de 1 byte até 20 MB. O conteúdo binário SHALL ser armazenado no Cloud Storage e os metadados (nome original, nome de exibição, tipo de conteúdo, tamanho, hash SHA-256, autor, data) SHALL ser persistidos como uma linha em `documento`, vinculada ao processo. Ver PRD US 3.1 (Cen.1).

#### Scenario: Upload de documento individual
- **DADO** que estou visualizando um processo da minha unidade
- **QUANDO** seleciono "Anexar Documento" e faço upload de um arquivo em formato aceito com tamanho de até 20 MB
- **ENTÃO** o arquivo é armazenado no sistema, vinculado ao processo, e aparece na lista de documentos com nome, tipo, tamanho e data de anexação (PRD US 3.1 Cen.1)

#### Scenario: Formato ou tamanho não aceito
- **DADO** que estou anexando um documento a um processo
- **QUANDO** faço upload de um arquivo com extensão/MIME não permitido (ex.: `.exe`) ou de tamanho superior a 20 MB
- **ENTÃO** o sistema rejeita o upload e exibe "Formato de arquivo não permitido" ou "Arquivo excede o tamanho máximo de 20 MB", e nada é gravado no bucket nem no banco (PRD US 3.1 Cen.2)

#### Scenario: Upload de arquivo vazio (0 byte)
- **DADO** que estou anexando um documento a um processo
- **QUANDO** faço upload de um arquivo com tamanho de 0 byte
- **ENTÃO** o sistema rejeita o upload e exibe "Não é possível anexar arquivo vazio. Selecione um arquivo com conteúdo.", e nada é gravado (PRD US 3.1 Cen.2b)

#### Scenario: Nome duplicado é renomeado, não sobrescreve
- **DADO** que um processo já possui um documento anexado chamado "parecer.pdf"
- **QUANDO** anexo outro arquivo com o mesmo nome "parecer.pdf"
- **ENTÃO** o sistema aceita o upload e renomeia o nome de exibição do novo arquivo para "parecer (1).pdf"; o documento original não é sobrescrito e ambos aparecem na lista, cada um com sua chave única no bucket (PRD US 3.1 Cen.5)

### Requirement: Acesso negado ao anexar em processo de outra unidade
O sistema SHALL negar a anexação de documento por usuário sem acesso à unidade atual do processo (Servidor de outra unidade, Gestor de unidade não gerida), retornando "acesso negado" e registrando a tentativa em `log_seguranca` (linha imutável). Ver o invariante de visibilidade por unidade (PRD US 1.4 Cen.2).

#### Scenario: Servidor de outra unidade tenta anexar
- **DADO** que estou autenticado como Servidor da unidade COFIN e o processo está atualmente em outra unidade
- **QUANDO** tento anexar um documento a esse processo
- **ENTÃO** o sistema exibe "Acesso negado — você não tem permissão para visualizar este processo", a operação não é concluída e a tentativa é registrada em `log_seguranca`

### Requirement: Remover documento por soft-delete com bloqueio pós-despacho
O sistema SHALL permitir a remoção lógica (soft-delete) de um documento **apenas enquanto o processo está sob custódia da unidade atual e ainda não foi despachado a partir dessa custódia** — isto é, quando o processo está em status `Aberto`, ou quando retornou por devolução e ainda não foi redespachado. Ao remover, o sistema SHALL: exigir confirmação; retirar o documento da lista de anexos visíveis; preservar o arquivo em retenção por 30 dias (congelando `purgar_em = removido_em + 30 dias`); e registrar a exclusão lógica como evento imutável no histórico do processo (evento `remover_documento`, com responsável e data/hora). A remoção SHALL ser negada quando o processo já foi despachado (`Em Tramitação` por despacho, `Concluído` ou `Arquivado`). Ver PRD US 3.1 (Cen.3, Cen.4, Cen.4b, Cen.4c).

#### Scenario: Remoção com processo ainda não despachado
- **DADO** que anexei um documento a um processo `Aberto` da minha unidade que ainda não foi despachado
- **QUANDO** aciono "Remover" e confirmo
- **ENTÃO** o documento sai da lista de anexos visíveis, o arquivo é preservado em retenção (soft-delete) por 30 dias, e a exclusão lógica é registrada no histórico com data, hora e responsável (PRD US 3.1 Cen.3)

#### Scenario: Tentativa de remoção após despacho — bloqueada
- **DADO** que um documento foi anexado a um processo que já foi despachado para a próxima unidade
- **QUANDO** tento acionar "Remover" sobre o documento
- **ENTÃO** o sistema exibe "Não é possível remover documentos de um processo que já foi despachado" e a exclusão não é concluída (PRD US 3.1 Cen.4)

#### Scenario: Remoção permitida após devolução do processo
- **DADO** que um processo da minha unidade foi despachado, devolvido pela unidade seguinte (US 2.2b) e agora está novamente na minha unidade com status "Em Tramitação"
- **QUANDO** aciono "Remover" sobre qualquer documento (anexado antes do despacho original ou após a devolução) e confirmo
- **ENTÃO** o documento sai da lista, o arquivo entra em retenção de 30 dias e a exclusão é registrada no histórico; o processo permanece na unidade atual com o mesmo status (PRD US 3.1 Cen.4b)

#### Scenario: Tentativa de remoção após redespacho pós-correção — bloqueada
- **DADO** que um processo foi devolvido para minha unidade, corrigi a pendência e despachei novamente para a unidade seguinte
- **QUANDO** tento remover qualquer documento do processo
- **ENTÃO** o sistema exibe "Não é possível remover documentos de um processo que já foi despachado" (PRD US 3.1 Cen.4c)

### Requirement: Visualizar e baixar documentos
O sistema SHALL permitir que um usuário com acesso à unidade atual do processo visualize inline documentos `PDF` e imagens (`JPG`/`PNG`) e baixe qualquer documento mantendo formato e nome originais. Documentos `DOC`/`DOCX` não têm visualização inline: o acionamento SHALL iniciar o download automático com aviso. Todo acesso ao conteúdo SHALL passar pela API autenticada e autorizada por unidade/perfil; o conteúdo nunca é servido por URL pública permanente. Ver PRD US 3.2 (Cen.1, Cen.2, Cen.3).

#### Scenario: Visualização inline de PDF ou imagem
- **DADO** que um processo possui documentos anexados
- **QUANDO** clico sobre o nome de um documento PDF ou imagem
- **ENTÃO** visualizo o conteúdo do documento na própria tela do processo (PRD US 3.2 Cen.1)

#### Scenario: Download de documento
- **DADO** que um processo possui documentos anexados
- **QUANDO** clico em "Baixar" de um documento
- **ENTÃO** o arquivo é baixado mantendo seu formato e nome originais (PRD US 3.2 Cen.2)

#### Scenario: DOC/DOCX inicia download automático
- **DADO** que um processo possui documento anexado em formato DOC ou DOCX
- **QUANDO** clico sobre o nome do documento
- **ENTÃO** o download é iniciado automaticamente e o sistema exibe "Formato não permite visualização inline — o download será iniciado" (PRD US 3.2 Cen.3)

#### Scenario: Acesso negado ao conteúdo por unidade
- **DADO** que estou autenticado como Servidor da unidade COFIN e conheço o ID de um documento de um processo que nunca passou pela COFIN
- **QUANDO** tento acessar diretamente o conteúdo ou o download desse documento
- **ENTÃO** o sistema retorna "acesso negado", não serve o conteúdo e registra a tentativa em `log_seguranca`

### Requirement: Armazenamento no Cloud Storage com residência e confidencialidade
O sistema SHALL armazenar o conteúdo dos documentos no bucket regional de documentos (residência no Brasil), com `public_access_prevention` habilitado, sem qualquer leitura pública. O acesso ao conteúdo SHALL ser mediado pela aplicação — via URL assinada de TTL curto ou streaming autenticado — de modo que apenas usuários autenticados e autorizados por unidade obtenham o binário. O sistema SHALL calcular e persistir o hash SHA-256 de cada documento anexado (preparação de integridade para a assinatura digital do Épico 4). Ver PRD Épico 3 e RNF de Segurança/LGPD.

#### Scenario: Conteúdo não é exposto publicamente
- **DADO** um documento armazenado no bucket
- **QUANDO** alguém tenta acessar o objeto diretamente por URL do bucket sem passar pela API
- **ENTÃO** o acesso é negado pela política do bucket (`public_access_prevention`), e a única via de acesso é a API autenticada e autorizada

#### Scenario: Hash de integridade é registrado na anexação
- **DADO** que anexo um documento a um processo
- **QUANDO** o upload é concluído
- **ENTÃO** o sistema persiste o hash SHA-256 do conteúdo junto aos metadados do documento

### Requirement: Purga física de documentos após o período de retenção
O sistema SHALL, por meio da rotina diária de manutenção (`job-manutencao-diaria`), excluir fisicamente do Cloud Storage e do banco os documentos cujo `purgar_em` já expirou (soft-deleted há mais de 30 dias), de forma **irreversível**. A seleção SHALL ser função do estado atual (`removido_em IS NOT NULL AND purgar_em <= agora`), de modo que reexecução e retomada após indisponibilidade não dupliquem efeito nem percam documentos vencidos (reusa o contrato de idempotência de `rotinas-agendadas`). Documentos ainda dentro dos 30 dias NÃO são purgados (permanecem restauráveis pela US 8.7, change futuro). Ver PRD US 3.1 (Cen.3) e RNF de LGPD.

#### Scenario: Purga de documento vencido
- **DADO** que um documento foi removido (soft-delete) há mais de 30 dias
- **QUANDO** a rotina diária de manutenção é executada
- **ENTÃO** o objeto é excluído fisicamente do bucket e a linha correspondente é removida do banco, de forma irreversível

#### Scenario: Documento dentro do prazo não é purgado
- **DADO** que um documento foi removido (soft-delete) há menos de 30 dias
- **QUANDO** a rotina diária de manutenção é executada
- **ENTÃO** o documento permanece em retenção, sem exclusão física, disponível para futura restauração (US 8.7)

#### Scenario: Retomada da purga após indisponibilidade sem duplicar efeito
- **DADO** que a rotina de manutenção não pôde ser executada por um ou mais dias
- **QUANDO** o sistema retorna à operação e a rotina é executada
- **ENTÃO** todos os documentos cujo `purgar_em` expirou durante a indisponibilidade são purgados nesta execução, e uma reexecução imediata não remove nada além do já purgado (idempotência por estado atual)
