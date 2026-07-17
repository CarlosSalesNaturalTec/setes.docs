# solicitacao-lgpd

## Purpose

Canal público de solicitação LGPD (exclusão/anonimização de dados pessoais) e fila
administrativa de atendimento pelo Administrador, incluindo o fluxo de rejeição
justificada. Ver PRD Épico 10 (US 10.1, US 10.2).

## Requirements

### Requirement: Canal público de solicitação LGPD
O sistema SHALL disponibilizar um endpoint **público, sem autenticação**, sob rate
limiting, onde um titular de dados pessoais (ou seu representante legal) registra uma
solicitação de exclusão ou anonimização de dados informando: número do processo, nome
completo, CPF, e-mail para resposta, tipo de solicitação ("Exclusão de dados" ou
"Anonimização de dados") e documento de identificação com foto (PDF, JPG ou PNG). A
solicitação SHALL receber um número de protocolo único e o solicitante SHALL receber
confirmação em tela e por e-mail. Ver PRD US 10.1.

#### Scenario: Solicitação registrada com sucesso
- **DADO** que sou titular de dados pessoais e possuo o número do processo e meus dados de identificação
- **QUANDO** acesso o canal de solicitação e preencho número do processo, nome completo, CPF, e-mail, tipo de solicitação e anexo documento de identificação válido
- **ENTÃO** o sistema registra a solicitação com um número de protocolo, exibe "Solicitação registrada com sucesso. Protocolo: XXXX. Você receberá a resposta no e-mail informado em até 15 dias." e envia e-mail de confirmação com o protocolo (PRD US 10.1 Cen.1)

#### Scenario: Campos obrigatórios não preenchidos
- **DADO** que estou preenchendo o formulário de solicitação LGPD
- **QUANDO** tento enviar sem preencher nome, CPF, número do processo ou e-mail
- **ENTÃO** o sistema destaca os campos obrigatórios e exibe "Preencha todos os campos obrigatórios" (PRD US 10.1 Cen.2)

#### Scenario: Documento de identificação com formato inválido
- **DADO** que estou preenchendo o formulário de solicitação LGPD
- **QUANDO** anexo um arquivo que não é PDF, JPG ou PNG
- **ENTÃO** o sistema exibe "Formato de arquivo não permitido. Anexe documento de identificação nos formatos PDF, JPG ou PNG." (PRD US 10.1 Cen.3)

#### Scenario: Documento de identificação vazio
- **DADO** que estou preenchendo o formulário de solicitação LGPD
- **QUANDO** anexo um arquivo de identificação com 0 byte
- **ENTÃO** o sistema rejeita o upload e não permite concluir a solicitação sem um documento de identificação válido

#### Scenario: Número de processo inexistente
- **DADO** que estou preenchendo o formulário de solicitação LGPD
- **QUANDO** informo um número de processo que não existe na base
- **ENTÃO** o sistema exibe "Nenhum processo encontrado com o número informado. Verifique o número e tente novamente." (PRD US 10.1 Cen.4)

#### Scenario: Rate limiting do canal público de solicitação
- **DADO** que estou na página pública de solicitação LGPD
- **QUANDO** excedo o limite de requisições por minuto configurado para endpoints públicos a partir do mesmo endereço IP
- **ENTÃO** o sistema rejeita a requisição e libera o acesso automaticamente após a janela de limitação, sem revelar dados de outras solicitações

### Requirement: Fila administrativa de solicitações LGPD
O sistema SHALL permitir que o Administrador visualize todas as solicitações LGPD
recebidas, com protocolo, data, nome do solicitante, número do processo, tipo de
solicitação e status (Pendente / Em análise / Atendida / Rejeitada). Ver PRD US 10.2.

#### Scenario: Visualização da fila de solicitações
- **DADO** que estou autenticado como Administrador
- **QUANDO** acesso "Solicitações LGPD" no menu de administração
- **ENTÃO** visualizo a lista de solicitações com protocolo, data, nome do solicitante, número do processo, tipo de solicitação e status (PRD US 10.2 Cen.1)

#### Scenario: Acesso negado — perfil não-Administrador
- **DADO** que estou autenticado como Servidor, Gestor ou Auditor
- **QUANDO** tento acessar a fila de solicitações LGPD ou qualquer ação de atendimento/rejeição
- **ENTÃO** o sistema rejeita a operação com acesso negado e registra a tentativa em log de segurança

### Requirement: Atendimento de solicitação LGPD (anonimização sob demanda)
O sistema SHALL permitir que o Administrador atenda uma solicitação LGPD pendente ou em
análise, disparando a anonimização irreversível dos dados pessoais dos interessados do
processo indicado (nome completo substituído por "Titular Anonimizado", CPF/CNPJ
substituído por identificador anonimizado irreversível, sem possibilidade de reversão) e
notificando o solicitante por e-mail sobre a conclusão. A operação SHALL usar o mesmo
serviço de anonimização consumido pela rotina automática trimestral (capability
`anonimizacao-lgpd`), preservando número do processo, datas, unidades, status e histórico
de tramitação íntegros. Ver PRD US 10.2.

#### Scenario: Processamento de solicitação de exclusão
- **DADO** que uma solicitação LGPD está com status "Pendente" e o tipo é "Exclusão de dados"
- **QUANDO** o Administrador valida a identidade do solicitante e aciona "Atender Solicitação"
- **ENTÃO** o sistema anonimiza os dados pessoais do titular no processo indicado, muda o status da solicitação para "Atendida" e envia e-mail automático ao solicitante informando a conclusão (PRD US 10.2 Cen.2)

#### Scenario: Atendimento de solicitação já atendida ou rejeitada
- **DADO** que uma solicitação LGPD já está com status "Atendida" ou "Rejeitada"
- **QUANDO** o Administrador tenta acionar "Atender Solicitação" ou "Rejeitar Solicitação" novamente
- **ENTÃO** o sistema rejeita a operação, pois o status é terminal e não permite nova transição

### Requirement: Rejeição de solicitação LGPD
O sistema SHALL permitir que o Administrador rejeite uma solicitação LGPD em análise,
mediante justificativa obrigatória, notificando o solicitante por e-mail sobre a decisão.
Ver PRD US 10.2.

#### Scenario: Rejeição de solicitação
- **DADO** que uma solicitação LGPD está em análise e o Administrador identifica que o solicitante não é o titular dos dados
- **QUANDO** aciona "Rejeitar Solicitação" e preenche a justificativa
- **ENTÃO** o status muda para "Rejeitada" e um e-mail é enviado ao solicitante informando a decisão com a justificativa (PRD US 10.2 Cen.3)

#### Scenario: Rejeição sem justificativa
- **DADO** que o Administrador está rejeitando uma solicitação LGPD
- **QUANDO** tenta confirmar a rejeição sem preencher a justificativa
- **ENTÃO** o sistema rejeita a ação e exige o preenchimento da justificativa antes de concluir
