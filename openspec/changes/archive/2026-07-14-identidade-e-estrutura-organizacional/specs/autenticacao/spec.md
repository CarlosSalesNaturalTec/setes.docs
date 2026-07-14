## ADDED Requirements

### Requirement: Login com credenciais
O sistema SHALL autenticar usuários por e-mail e senha, emitindo uma sessão (JWT + registro server-side) válida para o perfil do usuário, e SHALL bloquear temporariamente a conta após 3 tentativas incorretas consecutivas. Ver PRD US 1.3.

#### Scenario: Login com credenciais válidas
- **DADO** que possuo login e senha ativos no SETES.DOCS
- **QUANDO** informo minhas credenciais corretas na tela de login
- **ENTÃO** sou autenticado, uma sessão é criada e sou direcionado ao painel correspondente ao meu perfil (PRD US 1.3 Cen.1)

#### Scenario: Bloqueio após tentativas incorretas
- **DADO** que possuo login ativo no sistema
- **QUANDO** informo senha incorreta três vezes consecutivas
- **ENTÃO** minha conta é bloqueada temporariamente por 30 minutos e recebo e-mail de alerta de tentativas suspeitas (PRD US 1.3 Cen.2)

#### Scenario: Tentativa de login com senha correta durante bloqueio
- **DADO** que minha conta está bloqueada temporariamente há menos de 30 minutos
- **QUANDO** tento fazer login com a senha correta durante o bloqueio
- **ENTÃO** o sistema rejeita a autenticação exibindo o tempo restante, sem alterar o contador de tentativas nem reiniciar o bloqueio (PRD US 1.3 Cen.2b)

#### Scenario: Desbloqueio automático após o período de penalidade
- **DADO** que minha conta foi bloqueada há mais de 30 minutos
- **QUANDO** tento fazer login com a senha correta
- **ENTÃO** sou autenticado com sucesso e o contador de tentativas é resetado para zero (PRD US 1.3 Cen.4)

#### Scenario: Login com conta desativada — acesso negado
- **DADO** que minha conta foi desativada por um Administrador
- **QUANDO** tento fazer login com minhas credenciais corretas
- **ENTÃO** o sistema rejeita a autenticação exibindo "Conta desativada. Entre em contato com o Administrador do sistema." e nenhum e-mail de alerta é enviado (PRD US 1.3 Cen.6)

### Requirement: Recuperação de senha
O sistema SHALL permitir a recuperação de senha via link enviado por e-mail, válido por 2 horas, sem revelar se um e-mail está ou não cadastrado. Ver PRD US 1.3.

#### Scenario: Solicitação de recuperação com e-mail cadastrado
- **DADO** que esqueci minha senha
- **QUANDO** solicito recuperação informando meu e-mail cadastrado
- **ENTÃO** recebo um link de redefinição com validade de 2 horas, que leva à criação de nova senha conforme critérios de complexidade (PRD US 1.3 Cen.3)

#### Scenario: Solicitação com e-mail não cadastrado
- **DADO** que informo um e-mail que não está na base do sistema
- **QUANDO** solicito recuperação de senha
- **ENTÃO** o sistema exibe a mensagem genérica "Se o e-mail informado estiver cadastrado, um link de redefinição será enviado" e nenhum e-mail é enviado (PRD US 1.3 Cen.5)

#### Scenario: Recuperação de senha durante bloqueio temporário
- **DADO** que minha conta está bloqueada temporariamente após 3 tentativas incorretas
- **QUANDO** solicito e concluo a recuperação de senha com sucesso dentro da validade do link
- **ENTÃO** a conta é automaticamente desbloqueada e o contador de tentativas é resetado para zero (PRD US 1.3 Cen.2c)

### Requirement: Primeiro acesso
O sistema SHALL exigir que usuários recém-cadastrados criem sua própria senha através de um link de primeiro acesso válido por 48 horas, de uso único. Ver PRD US 1.6.

#### Scenario: Ativação com link válido e senha forte
- **DADO** que sou um usuário recém-cadastrado com status "pendente de primeiro acesso"
- **QUANDO** acesso o link de primeiro acesso dentro do prazo de 48 horas e defino uma senha que atende aos critérios de complexidade
- **ENTÃO** a senha é aceita, sou autenticado e meu status passa para "Ativo" (PRD US 1.6 Cen.1)

#### Scenario: Senha fraca rejeitada no primeiro acesso
- **DADO** que estou na tela de criação de senha do primeiro acesso
- **QUANDO** defino uma senha que não atende aos critérios de complexidade
- **ENTÃO** o sistema rejeita a senha e exibe a mensagem de critérios exigidos (PRD US 1.6 Cen.1b)

#### Scenario: Link de primeiro acesso expirado
- **DADO** que meu link de primeiro acesso expirou (mais de 48 horas)
- **QUANDO** tento acessá-lo
- **ENTÃO** o sistema exibe "Link expirado. Solicite um novo link de acesso ao Administrador." e meu status permanece "pendente de primeiro acesso" (PRD US 1.6 Cen.2)

#### Scenario: Link de primeiro acesso já utilizado
- **DADO** que já realizei o primeiro acesso com sucesso
- **QUANDO** tento acessar novamente o mesmo link
- **ENTÃO** o sistema exibe que o link já foi utilizado e orienta a fazer login ou usar "Esqueci minha senha", sem alterar meu status (PRD US 1.6 Cen.3)

### Requirement: Troca de senha autenticada
O sistema SHALL permitir que um usuário autenticado altere sua própria senha, exigindo a senha atual correta e impedindo reuso das últimas 6 senhas. Ver PRD US 1.7.

#### Scenario: Troca com sucesso
- **DADO** que estou autenticado no sistema
- **QUANDO** informo minha senha atual correta e uma nova senha válida e diferente da atual
- **ENTÃO** a senha é alterada com sucesso e recebo confirmação visual (PRD US 1.7 Cen.1)

#### Scenario: Senha atual incorreta — operação negada
- **DADO** que estou autenticado no sistema
- **QUANDO** informo minha senha atual incorreta ao tentar alterar a senha
- **ENTÃO** o sistema rejeita a operação exibindo "Senha atual incorreta" (PRD US 1.7 Cen.2)

#### Scenario: Nova senha reaproveitada do histórico
- **DADO** que estou autenticado no sistema
- **QUANDO** informo uma nova senha idêntica à atual ou a qualquer uma das últimas 6 senhas utilizadas
- **ENTÃO** o sistema rejeita a operação exibindo a mensagem correspondente (PRD US 1.7 Cen.3)

### Requirement: Sessão e encerramento
O sistema SHALL encerrar sessões por ação manual do usuário ou automaticamente após 30 minutos de inatividade, exibindo aviso prévio 2 minutos antes da expiração, e SHALL permitir múltiplas sessões concorrentes independentes por usuário. Ver PRD US 1.8, US 1.9.

#### Scenario: Logout manual
- **DADO** que estou autenticado no sistema
- **QUANDO** aciono a opção "Sair"
- **ENTÃO** minha sessão é encerrada imediatamente e sou redirecionado à tela de login (PRD US 1.8 Cen.1)

#### Scenario: Expiração por inatividade
- **DADO** que estou autenticado no sistema
- **QUANDO** permaneço inativo por 30 minutos
- **ENTÃO** minha sessão expira automaticamente e, ao tentar qualquer ação, sou redirecionado à tela de login com "Sessão expirada por inatividade" (PRD US 1.8 Cen.2)

#### Scenario: Aviso prévio de expiração
- **DADO** que estou inativo há 28 minutos (2 minutos antes do timeout)
- **QUANDO** o sistema detecta a proximidade da expiração
- **ENTÃO** exibo um modal de aviso com as opções "Continuar Sessão" (reseta o contador de inatividade) e "Sair" (encerra a sessão imediatamente) (PRD US 1.8 Cen.2b)

#### Scenario: Sessões concorrentes independentes
- **DADO** que estou autenticado no sistema no Dispositivo A
- **QUANDO** realizo login com as mesmas credenciais no Dispositivo B
- **ENTÃO** ambas as sessões permanecem ativas de forma independente, sem invalidação cruzada, cada uma expirando por sua própria inatividade (PRD US 1.9 Cen.1)

### Requirement: Reset de senha por Administrador
O sistema SHALL permitir que um Administrador force a redefinição de senha de um usuário ativo, invalidando a senha atual e registrando a ação em log de auditoria. Ver PRD US 1.10.

#### Scenario: Reset de senha de usuário ativo
- **DADO** que estou autenticado como Administrador e acesso um usuário com status "Ativo"
- **QUANDO** aciono "Resetar Senha" e confirmo
- **ENTÃO** a senha atual é invalidada, um link de redefinição válido por 2 horas é enviado, e o evento é registrado em log de auditoria com data, hora e Administrador responsável (PRD US 1.10 Cen.1)

#### Scenario: Reset de senha de usuário inativo — operação negada
- **DADO** que estou autenticado como Administrador e acesso um usuário com status "Inativo"
- **QUANDO** aciono "Resetar Senha"
- **ENTÃO** o sistema rejeita a operação exibindo "Não é possível resetar a senha de um usuário inativo. Reative o usuário antes de prosseguir." (PRD US 1.10 Cen.2)
