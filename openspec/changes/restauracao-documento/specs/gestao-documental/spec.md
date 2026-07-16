# gestao-documental

## ADDED Requirements

### Requirement: Restaurar documento removido dentro da retenção
O sistema SHALL permitir que um Administrador restaure um documento removido por soft-delete **enquanto estiver em período de retenção** (`removido_em IS NOT NULL AND purgar_em > agora`), independentemente da unidade do processo. Ao restaurar, o sistema SHALL: limpar `removido_em`, `removido_por_id` e `purgar_em` (o documento volta a ser visível na lista de anexos do processo de origem); registrar a restauração como evento imutável no histórico do processo (evento `restaurar_documento`, com o Administrador responsável e data/hora); e retirar o documento da área de retenção. A restauração NÃO depende do status do processo nem da regra de custódia de remoção (é ação administrativa, não de custódia). Ver PRD US 8.7 (Cen.1).

#### Scenario: Restauração dentro do período de retenção
- **DADO** que um documento foi removido (soft-delete) há menos de 30 dias e estou autenticado como Administrador
- **QUANDO** acesso "Documentos Removidos", localizo o documento e aciono "Restaurar"
- **ENTÃO** o documento volta a aparecer na lista de anexos do processo de origem, a restauração é registrada no histórico com data, hora e Administrador responsável, e o documento é removido da área de retenção (PRD US 8.7 Cen.1)

#### Scenario: Nome de exibição re-resolvido em caso de colisão na restauração
- **DADO** que um documento removido chamava-se "parecer.pdf" e, durante sua ausência, outro documento visível "parecer.pdf" passou a existir no mesmo processo
- **QUANDO** o Administrador restaura o documento removido
- **ENTÃO** o sistema re-resolve o nome de exibição do documento restaurado com sufixo `(n)` (ex.: "parecer (1).pdf"), preservando ambos sem sobrescrita

### Requirement: Acesso negado à restauração por não-Administrador
O sistema SHALL restringir a área "Documentos Removidos" e a ação de restauração ao perfil Administrador, negando o acesso a Servidor, Gestor ou Auditor. Ver PRD US 8.7 e o perfil Administrador (acesso irrestrito à configuração).

#### Scenario: Servidor ou Gestor tenta acessar a área de restauração
- **DADO** que estou autenticado como Servidor ou Gestor
- **QUANDO** tento acessar "Documentos Removidos" ou acionar a restauração de um documento
- **ENTÃO** o sistema retorna "acesso negado" e a operação não é concluída

### Requirement: Listagem da área de documentos removidos
O sistema SHALL exibir ao Administrador a lista de documentos em período de retenção (soft-deleted e ainda não purgados: `removido_em IS NOT NULL AND purgar_em > agora`), de qualquer unidade, com dados que permitam identificá-los (nome, processo de origem, data de remoção, responsável pela remoção). Documentos já purgados fisicamente (`purgar_em <= agora`) NÃO aparecem. Ver PRD US 8.7 (Cen.2, Cen.3).

#### Scenario: Documento já purgado não aparece e não é restaurável
- **DADO** que um documento foi removido há mais de 30 dias (já purgado pelo job diário)
- **QUANDO** o Administrador acessa "Documentos Removidos"
- **ENTÃO** o documento não aparece na listagem, uma tentativa direta de restaurá-lo retorna "não encontrado", e a tela exibe no rodapé "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados" (PRD US 8.7 Cen.2)

#### Scenario: Área de retenção vazia
- **DADO** que estou autenticado como Administrador e não há documentos em período de retenção
- **QUANDO** acesso "Documentos Removidos"
- **ENTÃO** visualizo a mensagem "Nenhum documento em período de retenção" (PRD US 8.7 Cen.3)
