# verificacao-assinatura Specification

## Purpose
Verificação, sob demanda, das assinaturas digitais embutidas em documentos PDF de um
processo (Épico 4, US 4.2): integridade, cadeia ICP-Brasil, revogação e data da
assinatura, com veredito honesto sobre o que o sistema consegue e não consegue
afirmar. Nesta fatia cobre PDFs assinados fora do sistema (G3); as assinaturas
aplicadas pelo próprio sistema reutilizarão esta capability.

## Requirements

### Requirement: Verificar assinaturas de um documento PDF
O sistema SHALL oferecer a ação "Verificar Assinatura" em todo documento PDF visível de um processo — anexado por upload ou gerado por modelo — e, ao acioná-la, SHALL exibir, para cada assinatura encontrada: nome do signatário, CPF (quando presente no certificado), data/hora da assinatura, autoridade certificadora emissora e o veredito. Ver PRD US 4.2 Cen.1.

#### Scenario: Assinatura ICP-Brasil válida e documento íntegro
- **DADO** que um processo que posso ler possui um PDF assinado com certificado ICP-Brasil não revogado, válido na data da verificação, e o arquivo não foi alterado após a assinatura
- **QUANDO** aciono "Verificar Assinatura" nesse documento
- **ENTÃO** o sistema exibe nome do signatário, CPF, data/hora da assinatura, autoridade certificadora e o status "Assinatura válida — documento íntegro" (PRD US 4.2 Cen.1)

#### Scenario: Data/hora sem carimbo de tempo é identificada como declarada
- **DADO** que a assinatura verificada não contém carimbo de tempo
- **QUANDO** o resultado é exibido
- **ENTÃO** a data/hora aparece identificada como "declarada pelo signatário (sem carimbo de tempo)", nunca como data comprovada

#### Scenario: Data/hora com carimbo de tempo válido
- **DADO** que a assinatura verificada contém carimbo de tempo cuja própria assinatura e cadeia são válidas
- **QUANDO** o resultado é exibido
- **ENTÃO** a data/hora exibida é a do carimbo, identificada como "comprovada por carimbo de tempo", com o nome da Autoridade de Carimbo do Tempo

#### Scenario: Certificado sem CPF
- **DADO** que o certificado do signatário não traz CPF em campo reconhecível
- **QUANDO** o resultado é exibido
- **ENTÃO** o campo CPF mostra "não informado no certificado" e os demais dados continuam exibidos

### Requirement: Assinatura inválida é exibida com alerta
O sistema SHALL exibir o veredito de assinatura inválida, com destaque visual de alerta, quando a verificação criptográfica da assinatura falhar (o conteúdo assinado foi alterado) ou quando o certificado do signatário, ou um certificado da sua cadeia, estiver revogado. Ver PRD US 4.2 Cen.2.

#### Scenario: Documento adulterado após a assinatura
- **DADO** que um PDF possui assinatura digital, mas os bytes cobertos pela assinatura foram alterados
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe os dados disponíveis do signatário e o status "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado", com ícone e cor de advertência (PRD US 4.2 Cen.2)

#### Scenario: Certificado revogado
- **DADO** que um PDF possui assinatura ICP-Brasil íntegra, mas a LCR ou o OCSP da AC emissora informa o certificado do signatário como revogado antes do momento da assinatura comprovado (ou sem carimbo de tempo)
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe o status "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado", com destaque de alerta (PRD US 4.2 Cen.2)

### Requirement: Certificado expirado só é aceito com prova de data
O sistema SHALL afirmar que uma assinatura com certificado hoje expirado era válida na data da assinatura **somente** quando o PDF contiver carimbo de tempo válido anterior à expiração. Sem carimbo, a data é auto-declarada e o veredito SHALL ser inconclusivo. Ver PRD US 4.2 Cen.3.

#### Scenario: Certificado expirado com carimbo de tempo anterior à expiração
- **DADO** que um PDF foi assinado com certificado ICP-Brasil que expirou depois, e a assinatura contém carimbo de tempo válido anterior à expiração
- **QUANDO** verifico a assinatura
- **ENTÃO** o sistema exibe "Assinatura válida — documento íntegro. Certificado expirado em [data], mas válido na data da assinatura." (PRD US 4.2 Cen.3)

#### Scenario: Certificado expirado sem carimbo de tempo
- **DADO** que um PDF foi assinado com certificado ICP-Brasil hoje expirado e a assinatura não contém carimbo de tempo válido
- **QUANDO** verifico a assinatura
- **ENTÃO** o sistema exibe "Verificação inconclusiva — o certificado expirou em [data] e o documento não tem carimbo de tempo que comprove a data da assinatura." e não exibe o status de assinatura válida

### Requirement: Verificação inconclusiva nunca é exibida como válida
O sistema SHALL exibir veredito inconclusivo quando não conseguir determinar a situação de revogação do certificado (LCR/OCSP indisponível, expirada ou ilegível) ou quando o conjunto de âncoras de confiança não puder ser carregado íntegro. Em nenhum desses casos SHALL exibir "Assinatura válida".

#### Scenario: Serviço de revogação indisponível
- **DADO** que um PDF possui assinatura ICP-Brasil íntegra e a LCR e o OCSP da AC emissora não respondem ou estão vencidos
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe "Verificação inconclusiva — não foi possível confirmar agora a situação do certificado. Tente novamente mais tarde ou confira no verificador oficial do ITI.", sem destaque de assinatura válida

#### Scenario: Âncoras de confiança corrompidas
- **DADO** que o conjunto de âncoras ICP-Brasil instalado não confere com os hashes fixados
- **QUANDO** qualquer usuário aciona "Verificar Assinatura"
- **ENTÃO** nenhuma assinatura é declarada válida, o veredito exibido é inconclusivo, e a falha é registrada no log de erro da aplicação para a equipe técnica

### Requirement: Assinatura fora da ICP-Brasil é identificada como tal
O sistema SHALL distinguir a assinatura cuja integridade criptográfica confere, mas cuja cadeia não termina em âncora da ICP-Brasil (ex.: assinatura gov.br, plataformas privadas), exibindo veredito próprio que não a declara qualificada nem inválida.

#### Scenario: PDF assinado com certificado fora da ICP-Brasil
- **DADO** que um PDF possui assinatura íntegra feita com certificado cuja cadeia não pertence à ICP-Brasil
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil — não é uma assinatura qualificada.", com o nome do signatário e a autoridade emissora como constam no certificado

### Requirement: Alteração posterior à assinatura é sinalizada
O sistema SHALL sinalizar quando uma assinatura íntegra não cobrir o arquivo inteiro — isto é, quando o PDF recebeu acréscimos depois de assinado — sem declará-la inválida, mas deixando claro que o conteúdo acrescentado não está coberto por ela.

#### Scenario: PDF com acréscimo após a última assinatura
- **DADO** que um PDF possui assinatura ICP-Brasil válida e, depois dela, recebeu uma revisão incremental (anotação, campo preenchido, página)
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe "Assinatura válida, mas o documento recebeu alterações depois de assinado. As alterações posteriores não estão cobertas pela assinatura.", com destaque de atenção

### Requirement: Documento com várias assinaturas
O sistema SHALL listar todas as assinaturas de um PDF, na ordem em que foram aplicadas, cada uma com seu próprio veredito, e SHALL exibir um resumo do documento igual ao veredito mais grave entre elas (inválida > inconclusiva > fora da ICP-Brasil > alteração posterior > válida).

#### Scenario: Uma assinatura válida e outra inválida
- **DADO** que um PDF possui duas assinaturas, a primeira válida e a segunda com certificado revogado
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema lista as duas assinaturas com seus vereditos individuais e o resumo do documento é "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado"

### Requirement: PDF sem assinatura ou ilegível
O sistema SHALL responder de forma explícita quando o PDF não contiver assinatura digital ou quando não for possível ler sua estrutura de assinaturas, sem confundir os dois casos.

#### Scenario: PDF sem assinatura
- **DADO** que um processo possui um PDF sem nenhuma assinatura digital
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe "Este documento não contém assinatura digital."

#### Scenario: PDF corrompido ou protegido por senha
- **DADO** que um processo possui um PDF corrompido ou criptografado
- **QUANDO** aciono "Verificar Assinatura"
- **ENTÃO** o sistema exibe "Não foi possível ler as assinaturas deste documento. O arquivo pode estar corrompido ou protegido por senha." e nenhum veredito de assinatura é exibido

### Requirement: Verificação restrita a documentos PDF
O sistema SHALL oferecer a verificação apenas para documentos com tipo de conteúdo PDF; para os demais formatos aceitos (DOC, DOCX, JPG, PNG) a ação não SHALL ser exibida e a requisição direta SHALL ser rejeitada.

#### Scenario: Documento DOCX
- **DADO** que um processo possui um documento DOCX
- **QUANDO** visualizo a lista de documentos
- **ENTÃO** a ação "Verificar Assinatura" não é exibida para esse documento

#### Scenario: Requisição direta para documento não PDF
- **DADO** que um documento do processo é uma imagem PNG
- **QUANDO** a verificação desse documento é solicitada diretamente à API
- **ENTÃO** o sistema rejeita com "A verificação de assinatura está disponível apenas para documentos PDF." e nenhum conteúdo é lido do armazenamento

### Requirement: Acesso à verificação segue a leitura do processo
O sistema SHALL permitir a verificação a quem pode ler o documento no processo (G2: qualquer funcionário com acesso ao processo — unidade atual, unidade de origem quando não sigiloso, ou permissão de auditoria, nas mesmas condições da visualização do documento), e SHALL negar a todos os demais, registrando a negativa em `log_seguranca`.

#### Scenario: Servidor sem acesso ao processo tenta verificar
- **DADO** que estou autenticado como Servidor de uma unidade que não é a atual nem a de origem do processo, e não tenho permissão de auditoria
- **QUANDO** solicito a verificação de assinatura de um documento desse processo
- **ENTÃO** o sistema responde acesso negado, não lê o documento do armazenamento, e registra `acesso_negado` em `log_seguranca`

#### Scenario: Processo sigiloso acompanhado pela unidade de origem
- **DADO** que sou da unidade de origem de um processo que hoje está sigiloso em outra unidade
- **QUANDO** solicito a verificação de assinatura de um documento dele
- **ENTÃO** o sistema responde acesso negado e registra `acesso_negado` em `log_seguranca` (sigilo prevalece sobre o acompanhamento)

#### Scenario: Auditor verifica documento de processo de outra unidade
- **DADO** que tenho permissão de auditoria e não tenho acesso à unidade do processo
- **QUANDO** solicito a verificação de assinatura de um documento dele
- **ENTÃO** o sistema executa a verificação e registra `acesso_auditoria` em `log_seguranca`, como na leitura do documento

#### Scenario: Documento removido
- **DADO** que um documento do processo foi removido (soft-delete)
- **QUANDO** sua verificação é solicitada
- **ENTÃO** o sistema responde documento não encontrado, como na visualização

#### Scenario: Usuário não autenticado
- **DADO** que não estou autenticado
- **QUANDO** solicito a verificação de assinatura de qualquer documento
- **ENTÃO** o sistema responde não autenticado e não lê o documento

### Requirement: Limites do veredito local e veredito oficial
O sistema SHALL exibir, junto a todo resultado de verificação que contenha ao menos uma assinatura, o aviso de que a conferência local não valida a política de assinatura ICP-Brasil e um link para o verificador oficial do ITI (`https://validar.iti.gov.br`), aberto em nova aba, sem enviar o documento a terceiros.

#### Scenario: Resultado com assinatura exibe o caminho oficial
- **DADO** que verifiquei um PDF com ao menos uma assinatura, em qualquer veredito
- **QUANDO** o resultado é exibido
- **ENTÃO** a tela mostra "Esta conferência é feita pelo Despapelize e não substitui o verificador oficial. Para o veredito oficial, envie o arquivo ao Verificador de Conformidade do ITI." com link para `https://validar.iti.gov.br` em nova aba, e o sistema não transmite o arquivo ao ITI

### Requirement: Verificação não persiste dados do signatário
O sistema SHALL tratar a verificação como leitura transitória: o resultado — incluindo nome e CPF extraídos do certificado — SHALL ser devolvido apenas na resposta e NÃO SHALL ser gravado em banco, cache persistente, log ou histórico de tramitação. A verificação NÃO SHALL criar evento de tramitação nem alterar o documento.

#### Scenario: Verificar não deixa rastro do signatário
- **DADO** que verifiquei um PDF assinado por um terceiro
- **QUANDO** consulto o histórico de tramitação do processo, o banco e os logs da aplicação
- **ENTÃO** não existe evento de tramitação da verificação, nem registro com o nome ou CPF do signatário, e o documento (bytes, hash e metadados) permanece inalterado

### Requirement: Âncora de teste só em ambiente de desenvolvimento
O sistema SHALL confiar, em produção, exclusivamente nas âncoras ICP-Brasil versionadas com hash fixado. Uma âncora adicional de teste SHALL ser aceita somente com a flag de desenvolvimento/E2E habilitada; sem a flag, qualquer âncora extra configurada SHALL ser ignorada.

#### Scenario: Âncora de teste sem a flag
- **DADO** que a flag de desenvolvimento de âncora de teste não está habilitada e há uma âncora extra configurada
- **QUANDO** verifico um PDF assinado por um certificado emitido por essa âncora de teste
- **ENTÃO** o veredito é "Assinatura íntegra, mas o certificado não pertence à ICP-Brasil — não é uma assinatura qualificada."

### Requirement: Consulta pública não expõe assinaturas
O sistema NÃO SHALL oferecer verificação de assinatura, nem exibir qualquer informação de assinatura, na consulta pública (G1).

#### Scenario: Cidadão na consulta pública
- **DADO** que sou um cidadão na consulta pública, consultando um processo que possui PDF assinado
- **QUANDO** visualizo o resultado da consulta
- **ENTÃO** não há menção a documentos, assinaturas ou ação de verificação, e não existe rota pública de verificação
