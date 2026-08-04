## MODIFIED Requirements

### Requirement: Armazenamento no Cloud Storage com confidencialidade
O sistema SHALL armazenar o conteúdo dos documentos no bucket regional de documentos, provisionado na **região única do projeto** (`us-central1`), com `public_access_prevention` habilitado e sem qualquer leitura pública. O bucket NÃO SHALL ser exigido em território brasileiro — a localização acompanha a região única do projeto, escolhida por custo, com a transferência internacional documentada pelo controlador sob a LGPD.

O acesso ao conteúdo SHALL continuar sendo mediado pela aplicação — via URL assinada de TTL curto ou streaming autenticado — de modo que apenas usuários autenticados e autorizados por unidade obtenham o binário. O sistema SHALL continuar calculando e persistindo o hash SHA-256 de cada documento. Todas as garantias de confidencialidade, retenção, soft-delete e purga permanecem **inalteradas**. Ver PRD Épico 3 e RNF de Segurança/LGPD.

#### Scenario: Conteúdo não é exposto publicamente
- **DADO** um documento armazenado no bucket
- **QUANDO** alguém tenta acessar o objeto diretamente por URL do bucket sem passar pela API
- **ENTÃO** o acesso é negado pela política do bucket (`public_access_prevention`), e a única via de acesso é a API autenticada e autorizada

#### Scenario: Hash de integridade é registrado na anexação
- **DADO** que anexo um documento a um processo
- **QUANDO** o upload é concluído
- **ENTÃO** o sistema persiste o hash SHA-256 do conteúdo junto aos metadados do documento

#### Scenario: Bucket acompanha a região única do projeto
- **QUANDO** o bucket de documentos é provisionado
- **ENTÃO** ele é criado na mesma região dos demais recursos regionais, referenciando `var.region`, sem exigência de localização em território brasileiro

#### Scenario: Garantias de acesso preservadas após a mudança de região
- **DADO** que o bucket foi recriado na região nova
- **QUANDO** um usuário sem autorização por unidade tenta obter um documento
- **ENTÃO** o acesso é negado exatamente como antes, e a tentativa é registrada em log de segurança — a mudança de região não flexibiliza nenhum controle de acesso
