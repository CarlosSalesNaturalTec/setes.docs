# inicializacao-sistema

## Purpose

Funcionalidade de inicialização (setup) que cria o Administrador root e a primeira unidade administrativa numa única operação, disponível apenas uma vez na vida do sistema.

## Requirements

### Requirement: Inicialização única do sistema
O sistema SHALL disponibilizar uma funcionalidade de inicialização (setup) que cria o Administrador root e a primeira unidade administrativa numa única operação, e que SHALL ficar permanentemente indisponível após a primeira execução bem-sucedida. Ver PRD US 8.0.

#### Scenario: Setup do sistema vazio
- **DADO** que o sistema foi instalado e nunca foi inicializado (nenhum usuário com perfil Administrador existe)
- **QUANDO** o operador acessa a funcionalidade de inicialização e preenche os dados do Administrador root (nome, e-mail, senha) e da primeira unidade administrativa (nome, sigla)
- **ENTÃO** o Administrador é criado com perfil "Administrador" e status "Ativo", a unidade é criada como ativa, a inicialização é marcada como concluída de forma permanente, e um e-mail de confirmação é enviado ao Administrador (PRD US 8.0 Cen.1)

#### Scenario: Tentativa de acesso à inicialização após conclusão
- **DADO** que o sistema já foi inicializado
- **QUANDO** qualquer pessoa tenta acessar a funcionalidade de inicialização
- **ENTÃO** o sistema rejeita a operação, exibe "Sistema já inicializado. Faça login para continuar." e redireciona para a tela de login, sem criar nenhum registro (PRD US 8.0 Cen.2)

#### Scenario: Duas requisições de inicialização simultâneas
- **DADO** que o sistema nunca foi inicializado
- **QUANDO** duas requisições de setup chegam concorrentemente
- **ENTÃO** exatamente uma delas cria o Administrador root e a unidade; a outra é rejeitada com "Sistema já inicializado", sem produzir Administrador ou unidade duplicados
