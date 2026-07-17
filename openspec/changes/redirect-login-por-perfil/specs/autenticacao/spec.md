## MODIFIED Requirements

### Requirement: Login com credenciais
O sistema SHALL autenticar usuários por e-mail e senha, emitindo uma sessão (JWT + registro server-side) válida para o perfil do usuário, e SHALL bloquear temporariamente a conta após 3 tentativas incorretas consecutivas. Ver PRD US 1.3.

Após uma autenticação bem-sucedida — e sempre que um usuário já autenticado acessar a raiz `/` — o sistema SHALL redirecioná-lo à sua **rota inicial**, resolvida de forma determinística a partir do perfil e da permissão de auditoria, nesta ordem de precedência:

1. SE `pode_auditar` for verdadeiro, a rota inicial SHALL ser `/auditoria/relatorios`, **sobrepondo o perfil** (independe de o usuário ser Servidor, Gestor ou Administrador);
2. SENÃO, para perfil **Servidor**, a rota inicial SHALL ser `/processos`;
3. SENÃO, para perfil **Gestor**, a rota inicial SHALL ser `/dashboard`;
4. SENÃO, para perfil **Administrador**, a rota inicial SHALL ser `/admin/unidades`.

A rota `/perfil` ("Meu Perfil") SHALL deixar de ser destino automático de login ou da raiz, permanecendo acessível apenas por navegação explícita no menu. A rota inicial resolvida SHALL sempre apontar para uma tela que o usuário tem permissão de acessar, de modo que nenhum redirecionamento pós-login resulte em "acesso negado".

#### Scenario: Login como Servidor é direcionado aos Processos
- **DADO** que possuo login e senha ativos e perfil Servidor, sem permissão de auditoria
- **QUANDO** informo minhas credenciais corretas na tela de login
- **ENTÃO** sou autenticado, uma sessão é criada e sou direcionado a `/processos` (PRD US 1.3 Cen.1)

#### Scenario: Login como Gestor é direcionado ao Dashboard
- **DADO** que possuo login e senha ativos e perfil Gestor, sem permissão de auditoria
- **QUANDO** informo minhas credenciais corretas na tela de login
- **ENTÃO** sou autenticado e sou direcionado a `/dashboard` (PRD US 1.3 Cen.1)

#### Scenario: Login como Administrador é direcionado às Unidades
- **DADO** que possuo login e senha ativos e perfil Administrador, sem permissão de auditoria
- **QUANDO** informo minhas credenciais corretas na tela de login
- **ENTÃO** sou autenticado e sou direcionado a `/admin/unidades` (PRD US 1.3 Cen.1)

#### Scenario: Permissão de auditoria sobrepõe o destino do perfil
- **DADO** que possuo login e senha ativos e a permissão `pode_auditar` habilitada, qualquer que seja meu perfil (Servidor, Gestor ou Administrador)
- **QUANDO** informo minhas credenciais corretas na tela de login
- **ENTÃO** sou autenticado e sou direcionado a `/auditoria/relatorios`, ignorando o destino que meu perfil teria isoladamente

#### Scenario: Usuário já autenticado acessa a raiz
- **DADO** que possuo uma sessão ativa
- **QUANDO** acesso a rota raiz `/`
- **ENTÃO** sou redirecionado à mesma rota inicial que meu perfil e permissão de auditoria determinam no login, e não à tela de login nem a `/perfil`

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
