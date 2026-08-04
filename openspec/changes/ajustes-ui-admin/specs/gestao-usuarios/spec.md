## MODIFIED Requirements

### Requirement: Aba de documentos assinados como marcador de fase futura
O sistema SHALL exibir a aba "Documentos assinados" com uma mensagem informando que a assinatura digital de documentos será disponibilizada em fase futura do produto e orientando o usuário a solicitar seu Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora. A orientação SHALL deixar claro que se trata de providência **externa ao sistema** e preparatória, NÃO de uma ação disponível na tela. A aba NÃO SHALL exibir botão de assinatura, campo de certificado digital, formulário de solicitação, link de emissão nem qualquer elemento que sugira funcionalidade disponível. A assinatura digital (Épico 4) permanece **fora do escopo do MVP**, e este requisito NÃO SHALL ser interpretado como retomada do épico.

#### Scenario: Aba informa fase futura em vez de vazio silencioso
- **DADO** que acesso a aba "Documentos assinados"
- **QUANDO** a aba é exibida
- **ENTÃO** vejo uma mensagem explicando que a assinatura digital de documentos será disponibilizada em fase futura, e nenhuma lista vazia sem explicação

#### Scenario: Aba orienta a obtenção prévia do certificado digital
- **DADO** que estou na aba "Documentos assinados"
- **QUANDO** leio a mensagem exibida
- **ENTÃO** ela me orienta a solicitar o Certificado Digital ICP-Brasil junto a uma Autoridade Certificadora, como preparação para a fase futura
- **E** deixa claro que essa solicitação é feita fora do sistema, não por esta tela

#### Scenario: Nenhum controle de assinatura é oferecido
- **DADO** que estou na aba "Documentos assinados"
- **QUANDO** examino os controles disponíveis
- **ENTÃO** não há botão "Assinar", seleção de certificado digital nem qualquer ação que sugira que a assinatura já esteja implementada

#### Scenario: A orientação não introduz nenhum controle
- **DADO** que a aba passou a orientar a solicitação do certificado digital
- **QUANDO** examino os controles disponíveis
- **ENTÃO** a orientação é apenas texto — não há botão de solicitação, formulário, campo de upload de certificado nem link de emissão dentro do sistema
