# Análise Preliminar de Discovery — SETES.DOCS

## 1. Desconstrução do Problema

* **Dor Real do Negócio:** O cliente sofre com a falta de visibilidade e controle sobre o ciclo de vida de processos administrativos. Hoje, provavelmente, os processos tramitam de forma manual ou semiaparelhada (papel, e-mail, planilhas), gerando: (a) incapacidade de identificar gargalos e processos parados antes que causem prejuízo; (b) ausência de métricas consolidadas sobre tempo de tramitação e produtividade por unidade/servidor; (c) dificuldade de auditoria e transparência, tanto interna quanto para o cidadão. A dor central é **gestão da ineficiência operacional**: o cliente não sabe onde os processos estão travados, quem está sobrecarregado e quanto tempo se perde entre as unidades.
* **Solução Assumida pelo Cliente:** O cliente já tem uma visão bastante clara e detalhada do produto desejado — um sistema de workflow administrativo com dashboard de KPIs, quadro Kanban, consulta pública e relatórios. No entanto, o documento é quase inteiramente focado em **UI/UX e especificações visuais**, deixando lacunas profundas na modelagem do negócio. O cliente "desenhou as telas" mas não modelou o que acontece entre elas: as regras de tramitação, os papéis dos atores e o motor do fluxo de trabalho. Ou seja, a solução assumida está **visualmente madura, mas funcionalmente incompleta** — as telas existem, mas o "motor" que as move ainda não foi definido.

## 2. Mapeamento de Personas Ocultas

O documento cita explicitamente apenas "usuário logado" (ex.: Carlos Sales) e "cidadão/partes interessadas" (consulta pública). Entretanto, as seguintes personas estão implícitas e precisam ser formalizadas:

* **Servidor/Colaborador Operacional:** Quem cria processos, movimenta entre status, anexa documentos. É o executor do dia a dia. Implícito nas telas de Processos e Novo Processo.
* **Gestor/Chefe de Unidade:** Quem visualiza o dashboard, analisa gargalos, gera relatórios e toma decisões a partir dos KPIs. Precisa de visão macro, possivelmente restrita à sua unidade ou a todas.
* **Administrador do Sistema (Super Admin):** Não mencionado, mas inevitável. Alguém precisa cadastrar unidades, tipos de processo, níveis de acesso, usuários e gerir permissões.
* **Cidadão/Parte Interessada Externa:** Já mencionado na Consulta Pública. Pessoa sem autenticação que consulta processos públicos por número, assunto, tipo ou data.
* **Auditor/Controlador Interno:** Implícito na ênfase em relatórios e transparência. Pessoa que precisa extrair dados para fiscalização e prestação de contas, possivelmente com acesso a todos os processos, inclusive restritos/sigilosos.

## 3. Avaliação de Maturidade e Lacunas Críticas

O documento é **alto em maturidade visual (telas, componentes, estilo)** e **baixo em maturidade funcional (regras de negócio, fluxos, papéis)**. As lacunas críticas são:

| # | Lacuna | Risco |
|---|--------|-------|
| 1 | **Motor de Tramitação:** O cliente descreve o Kanban e fala em "movimentação entre unidades", mas não define COMO um processo se move. É arrastar e soltar livre? Há um fluxo predefinido (ex.: COFIN → AJUR → DIRAD)? Quem define o destinatário? Existe validação/se conferência entre etapas? | **CRÍTICO.** Sem isso, o sistema vira um quadro de recados glorificado, não um workflow. |
| 2 | **Perfis de Usuário e Permissões (RBAC):** Não há menção a papéis. Todos os usuários logados veem e fazem as mesmas coisas? Um servidor pode mover qualquer processo de qualquer unidade? Um gestor pode editar processos concluídos? | **CRÍTICO.** A segurança e a integridade dos processos dependem de um modelo de permissões claro. |
| 3 | **Ciclo de Vida do Processo:** As colunas do Kanban (Aberto → Em Tramitação → Concluído → Arquivado) estão definidas, mas as regras de transição não. Todo processo começa "Aberto"? O que dispara a transição para "Em Tramitação"? Pode-se pular status? Pode-se reabrir um processo concluído? | **ALTO.** A integridade do fluxo depende de regras de transição claras. |
| 4 | **Gestão de Documentos e Anexos:** O botão "Documentos" aparece na tela de Processos, e "Documentos Assinados" na aba de Perfil, mas não há absolutamente nenhuma descrição de como documentos são anexados, armazenados, versionados ou visualizados. | **ALTO.** Se o sistema se chama SETES.**DOCS**, a gestão documental é central e está completamente omitida. |
| 5 | **Assinatura Eletrônica:** O Perfil menciona "Documentos Assinados" e contador de "Assinaturas". Que tipo de assinatura? É um check box de "ciente"? É assinatura digital com certificado ICP-Brasil? É integração com algum portal de assinatura externo? | **ALTO.** Assinatura eletrônica tem implicações legais, de segurança e de arquitetura profundamente diferentes conforme a modalidade. |
| 6 | **Notificações e Alertas:** O Dashboard mostra "Processos Parados", mas como o usuário sabe que um processo novo chegou para ele? O sistema envia e-mail? Notificação interna (sininho)? SMS/WhatsApp? | **MÉDIO.** A adoção do sistema depende de os usuários saberem que têm tarefas pendentes. |
| 7 | **Autenticação e Onboarding:** Como o usuário faz login? É integrado a um sistema existente (AD/LDAP, SSO, gov.br)? Há cadastro próprio? Recuperação de senha? | **MÉDIO.** Impacta arquitetura de segurança e experiência de primeiro uso. |
| 8 | **Gestão de Usuários e Unidades:** Quem cria usuários? Como se vinculam a unidades? As unidades mudam com frequência? Há algum sistema de organograma já existente para integrar? | **MÉDIO.** Sem isso, o Administrador pode virar um gargalo operacional. |
| 9 | **Regras de Arquivamento:** A coluna "Arquivado" existe, mas nenhuma regra é descrita. É manual? Automático por tempo? Processos concluídos viram automaticamente arquivados? | **MÉDIO.** Impacta a integridade dos dados históricos e a performance da base. |
| 10 | **Concorrência e Integridade:** Dois usuários podem mover o mesmo processo ao mesmo tempo? O que acontece se ambos editarem? Há bloqueio otimista/pessimista? | **BAIXO (para MVP).** Importante para escala, mas pode ser tratado como melhoria futura. |

## 4. Estratégia de Mitigação de Riscos (MVP)

Para evitar desperdício de escopo, as seguintes premissas precisam ser validadas **antes** do início do desenvolvimento:

1. **Validar o modelo de tramitação primeiro.** Antes de codificar uma linha do Kanban, definir em workshop com o cliente: o fluxo é livre (qualquer um manda para qualquer unidade) ou roteirizado (workflow predefinido)? A resposta muda completamente a arquitetura do backend.
2. **Definir a matriz de perfis x permissões.** Construir uma tabela simples com o cliente: Administrador, Gestor, Servidor, Cidadão — o que cada um vê e faz. Isso evita retrabalho em segurança e autorização.
3. **Esclarecer o escopo de "documentos".** O MVP inclui upload e anexo de arquivos? Com visualização inline? A resposta define necessidades de storage, antivírus e preview.
4. **Confirmar a modalidade de assinatura.** Se for assinatura digital com ICP-Brasil, o escopo do MVP se expande enormemente (integração com autoridade certificadora, custo, complexidade jurídica). Se for "ciente/de acordo" interno, é trivial.
5. **Validar se há integrações legadas.** O cliente menciona estruturas organizacionais (COFIN, COGEP, DIRAD). Essas unidades já existem em algum sistema? O SETES.DOCS precisa se integrar a algo já em uso? Isso impacta a estratégia de migração e adoção.
6. **Começar o MVP sem automação de prazos.** Os campos de prazo existem, mas regras de SLA (escalonamento, alertas automáticos, reabertura) podem ficar para a Fase 2 — o essencial é exibir o prazo e listar os atrasados.
