# Glossário

| Termo | O que significa |
|-------|-----------------|
| **Processo** | O documento/assunto administrativo que tramita no sistema, com número no formato `AAAA/NNNNNN`, tipo, prazo e interessados. Nasce atribuído ao servidor que o criou. |
| **Unidade** | Área administrativa da instituição (ex.: uma coordenadoria financeira). Base do controle de acesso. |
| **Setor** | Subdivisão de uma unidade (ex.: o gabinete da coordenadoria financeira). Organiza as pessoas e é escolhido a cada tramitação; **não** altera quem enxerga o quê — isso continua sendo por unidade. |
| **Tipo de processo** | Categoria do processo, usada em filtros do quadro/dashboard e no prazo de anonimização LGPD — não define um caminho de tramitação. |
| **Modelo de documento** | Texto pré-formatado com lacunas, cadastrado pelo Administrador, que o Servidor pode escolher e completar ao abrir um processo; gera um PDF anexado ao processo, tratado como qualquer outro documento. |
| **Tramitação** | O conjunto de ações (Envio, Devolução, Reatribuição, Conclusão) que movem um processo entre servidores, setores e unidades. |
| **Enviar** | Encaminhar o processo a um servidor de destino escolhido explicitamente (unidade, setor, servidor), com mensagem. |
| **Devolver** | Mandar o processo de volta a quem o enviou por último (resolvido automaticamente pelo sistema), com motivo e justificativa opcional. |
| **Reatribuir** | Corrigir a pessoa responsável dentro da **mesma unidade**, quando a atribuição foi indevida; não altera status nem prazo. |
| **Concluir** | Encerrar o tratamento do processo, ação própria disponível a qualquer momento para quem está com ele. |
| **Ação necessária** | Selo do card que indica que **você** é o responsável atual — a próxima ação é sua. |
| **Quadro Kanban** | Painel visual que organiza os processos em colunas por situação (Aberto, Em Tramitação, Concluído, Arquivado). |
| **Situação do processo** | Estágio atual: Aberto, Em Tramitação, Concluído ou Arquivado. |
| **Arquivamento automático** | O sistema arquiva sozinho processos concluídos após o prazo configurado (padrão: 30 dias). |
| **Sigilo** | Marcação que oculta o processo da consulta pública e de quem está fora da unidade onde ele se encontra; não afeta a tramitação interna. |
| **Consulta pública** | Pesquisa de processos aberta a qualquer pessoa, sem login. |
| **Auditoria** | Permissão concedida pelo Administrador que dá acesso amplo a processos e relatórios para fiscalização. |
| **LGPD** | Lei de proteção de dados pessoais (Lei 13.709/2018); embasa os pedidos de exclusão/anonimização. |
| **Protocolo LGPD** | Número gerado ao registrar uma solicitação LGPD; identifica o pedido até a resposta. |
| **Anonimização** | Substituição irreversível dos dados pessoais do titular no processo (nome e CPF/CNPJ), preservando número, datas e histórico. |

---

*Este manual descreve como **operar** o Despapelize conforme cada perfil de
acesso. As regras de negócio detalhadas (cenários de aceite e casos de borda)
estão no documento mestre `docs/PRD.md`.*
