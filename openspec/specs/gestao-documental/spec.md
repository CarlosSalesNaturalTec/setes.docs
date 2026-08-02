# gestao-documental

## Purpose

Gestão documental do processo: anexação, visualização, download e remoção
(soft-delete) de documentos vinculados a um processo, armazenamento no Cloud
Storage com residência e confidencialidade, purga física após retenção, e
restauração administrativa de documentos removidos dentro do período de
retenção (Épico 3, US 3.1, US 3.2, US 8.7).

## Requirements

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
O sistema SHALL, por meio da rotina diária de manutenção (`job-manutencao-diaria`), excluir fisicamente do Cloud Storage e do banco os documentos cujo `purgar_em` já expirou (soft-deleted há mais de 30 dias), de forma **irreversível**. A seleção SHALL ser função do estado atual (`removido_em IS NOT NULL AND purgar_em <= agora`), de modo que reexecução e retomada após indisponibilidade não dupliquem efeito nem percam documentos vencidos (reusa o contrato de idempotência de `rotinas-agendadas`). Documentos ainda dentro dos 30 dias NÃO são purgados (permanecem restauráveis pela US 8.7). Ver PRD US 3.1 (Cen.3) e RNF de LGPD.

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

### Requirement: Restaurar documento removido dentro da retenção
O sistema SHALL permitir que um Administrador restaure um documento removido por soft-delete **enquanto estiver em período de retenção** (`removido_em IS NOT NULL AND purgar_em > agora`), independentemente da unidade do processo. Ao restaurar, o sistema SHALL: limpar `removido_em`, `removido_por_id` e `purgar_em` (o documento volta a ser visível na lista de anexos do processo de origem); registrar a restauração como evento imutável no histórico do processo (evento `restaurar_documento`, com o Administrador responsável e data/hora); e retirar o documento da área de retenção. A restauração NÃO depende do status do processo nem da regra de custódia de remoção (é ação administrativa, não de custódia). Ver PRD US 8.7 (Cen.1).

#### Scenario: Restauração dentro do período de retenção
- **DADO** que um documento foi removido (soft-delete) há menos de 30 dias e estou autenticado como Administrador
- **QUANDO** acesso "Documentos Removidos", localizo o documento e aciono "Restaurar"
- **ENTÃO** o documento volta a aparecer na lista de anexos do processo de origem, a restauração é registrada no histórico com data, hora e Administrador responsável, e o documento é removido da área de retenção (PRD US 8.7 Cen.1)

#### Scenario: Nome de exibição re-resolvido em caso de colisão na restauração
- **DADO** que um documento removido chamava-se "parecer.pdf" e, durante sua ausência, outro documento visível "parecer.pdf" passou a existir no mesmo processo
- **QUANDO** o Administrador restaura o documento removido
- **ENTÃO** o sistema re-resolve o nome de exibição do documento restaurado com sufixo `(n)` (ex.: "parecer (1).pdf"), preservando ambos sem sobrescrita

### Requirement: Acesso negado à restauração por não-Administrador
O sistema SHALL restringir a área "Documentos Removidos" e a ação de restauração ao perfil Administrador, negando o acesso a Servidor, Gestor ou Auditor. Ver PRD US 8.7 e o perfil Administrador (acesso irrestrito à configuração).

#### Scenario: Servidor ou Gestor tenta acessar a área de restauração
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento acessar "Documentos Removidos" ou acionar a restauração de um documento
- **ENTÃO** o sistema retorna "acesso negado" e a operação não é concluída

### Requirement: Listagem da área de documentos removidos
O sistema SHALL exibir ao Administrador a lista de documentos em período de retenção (soft-deleted e ainda não purgados: `removido_em IS NOT NULL AND purgar_em > agora`), de qualquer unidade, com dados que permitam identificá-los (nome, processo de origem, data de remoção, responsável pela remoção). Documentos já purgados fisicamente (`purgar_em <= agora`) NÃO aparecem. Ver PRD US 8.7 (Cen.2, Cen.3).

#### Scenario: Documento já purgado não aparece e não é restaurável
- **DADO** que um documento foi removido há mais de 30 dias (já purgado pelo job diário)
- **QUANDO** o Administrador acessa "Documentos Removidos"
- **ENTÃO** o documento não aparece na listagem, uma tentativa direta de restaurá-lo retorna "não encontrado", e a tela exibe no rodapé "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados" (PRD US 8.7 Cen.2)

#### Scenario: Área de retenção vazia
- **DADO** que estou autenticado como Administrador e não há documentos em período de retenção
- **QUANDO** acesso "Documentos Removidos"
- **ENTÃO** visualizo a mensagem "Nenhum documento em período de retenção" (PRD US 8.7 Cen.3)

### Requirement: Documentos gerados pelo sistema a partir de modelo
O sistema SHALL tratar os documentos **gerados a partir de modelo** como documentos de pleno direito do acervo, sujeitos **exatamente** às mesmas regras dos anexos enviados por upload: validação de formato contra a whitelist vigente, verificação da assinatura binária do arquivo, armazenamento no bucket de documentos com chave opaca, cálculo de integridade, listagem, download, remoção por soft-delete, bloqueio de remoção após a saída do processo da unidade, retenção, restauração pelo Administrador e purga física ao fim da retenção. NENHUMA exceção SHALL ser criada para documentos gerados, e a whitelist de formatos NÃO SHALL ser ampliada por causa deles.

Documentos gerados SHALL ser **imutáveis após salvos**, como qualquer anexo — não há edição posterior nem versionamento. A correção de um documento gerado SHALL se dar pela remoção (soft-delete, reversível pelo Administrador dentro da retenção) seguida de nova geração.

#### Scenario: Documento gerado é indistinguível de um anexo enviado
- **DADO** que um processo possui um anexo enviado por upload e um documento gerado a partir de modelo
- **QUANDO** listo os documentos do processo
- **ENTÃO** ambos aparecem na mesma lista, com os mesmos controles de visualização, download e remoção

#### Scenario: Whitelist de formatos não é ampliada
- **DADO** que o documento gerado é produzido pelo sistema
- **QUANDO** ele é submetido ao pipeline de anexos
- **ENTÃO** passa pela mesma validação de formato e verificação de assinatura binária aplicada a qualquer upload, sem qualquer caminho alternativo que dispense esses controles

#### Scenario: Documento gerado não é editável
- **DADO** que um documento foi gerado a partir de modelo e salvo no processo
- **QUANDO** procuro uma forma de editar seu conteúdo
- **ENTÃO** não existe ação de edição — a correção se dá removendo o documento e gerando um novo

#### Scenario: Soft-delete e restauração aplicam-se ao documento gerado
- **DADO** que um documento gerado foi removido pelo servidor
- **QUANDO** o Administrador acessa a área de documentos removidos dentro do período de retenção
- **ENTÃO** o documento gerado consta na listagem e pode ser restaurado, como qualquer anexo

#### Scenario: Purga física alcança o documento gerado
- **DADO** que um documento gerado foi removido e o período de retenção se esgotou
- **QUANDO** a rotina de purga é executada
- **ENTÃO** o objeto correspondente é apagado do bucket e o registro é purgado, sem tratamento distinto do aplicado aos anexos enviados

#### Scenario: Bloqueio de remoção após a saída do processo vale para o gerado
- **DADO** que um documento gerado está em um processo que já foi enviado para outra unidade
- **QUANDO** tento removê-lo
- **ENTÃO** o sistema bloqueia a remoção pela mesma regra aplicada aos anexos enviados, e a tentativa é registrada em log de segurança

#### Scenario: Dados pessoais no documento gerado não vazam para a consulta pública
- **DADO** que um documento gerado contém nome e CPF de um interessado
- **QUANDO** um cidadão consulta o processo pela consulta pública
- **ENTÃO** o conteúdo do documento não é exibido nem disponibilizado para download, exatamente como ocorre com os anexos enviados
