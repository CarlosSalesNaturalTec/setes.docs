## ADDED Requirements

### Requirement: Quadro Kanban consolidado read-only (Administrador)
O sistema SHALL conceder ao Administrador acesso **read-only** ao Kanban
consolidado de todas as unidades: ele visualiza os processos como qualquer
observador autorizado, mas NÃO dispõe de controles de ação sobre processos —
criar, despachar, devolver e alternar sigilo permanecem exclusivos do Servidor
da unidade. A interface NÃO SHALL exibir ao Administrador controles de ação que
ele não pode executar; o backend já rejeita essas ações para perfis não-Servidor.
Ver PRD US 2.3/2.8.

#### Scenario: Administrador visualiza o Kanban de todas as unidades
- **DADO** que estou autenticado como Administrador
- **QUANDO** acesso a tela de Processos
- **ENTÃO** vejo o Kanban consolidado com os processos de todas as unidades, organizados por coluna de status

#### Scenario: Administrador não vê controles de ação de processo
- **DADO** que estou autenticado como Administrador na tela de Processos ou no detalhe de um processo
- **QUANDO** a tela é renderizada
- **ENTÃO** os controles "Novo processo", "Despachar", "Devolver" e alternar sigilo não são exibidos para o meu perfil

#### Scenario: Ação de processo por Administrador é rejeitada pelo backend
- **DADO** que estou autenticado como Administrador
- **QUANDO** uma requisição de criar, despachar, devolver ou alternar sigilo de processo chega ao backend
- **ENTÃO** a operação é rejeitada por ser exclusiva do perfil Servidor, registrando a tentativa em log de segurança
