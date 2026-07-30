## ADDED Requirements

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
