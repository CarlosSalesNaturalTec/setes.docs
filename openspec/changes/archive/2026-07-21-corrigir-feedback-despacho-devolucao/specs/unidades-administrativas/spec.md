## ADDED Requirements

### Requirement: Leitura do catálogo de unidades por qualquer usuário autenticado

O sistema SHALL permitir que qualquer usuário autenticado (Servidor, Gestor ou
Administrador) liste o catálogo de unidades administrativas (nome, sigla,
situação ativa/inativa) via `GET /unidades`. Este é um dado não sensível,
necessário para o Servidor resolver o nome de uma unidade (ex.: ao exibir a
unidade de destino de um despacho/devolução, ver capability `workflow-tramitacao`).
Cadastro, edição, desativação e reativação de unidade permanecem restritos ao
Administrador (Requirement "Gestão de unidades restrita ao Administrador").

#### Scenario: Servidor comum lista o catálogo de unidades
- **DADO** que sou Servidor, sem permissão de auditoria
- **QUANDO** solicito o catálogo de unidades
- **ENTÃO** recebo a lista de unidades (nome, sigla, ativo) com sucesso

#### Scenario: Servidor tenta cadastrar unidade a partir do catálogo — acesso negado
- **DADO** que sou Servidor e tenho acesso de leitura ao catálogo de unidades
- **QUANDO** tento cadastrar, editar, desativar ou reativar uma unidade administrativa
- **ENTÃO** o sistema rejeita a operação exibindo "Acesso negado — apenas o Administrador pode gerenciar unidades" e registra a tentativa em log de segurança (Requirement "Gestão de unidades restrita ao Administrador")
