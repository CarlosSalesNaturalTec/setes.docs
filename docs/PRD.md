# Product Requirements Document (PRD) — SETES.DOCS

## 1. Visão Geral e Problema

Órgãos da administração pública sofrem com a falta de visibilidade e controle sobre o ciclo de vida de processos administrativos. Atualmente, os processos tramitam de forma manual ou semiaparelhada (papel, e-mail, planilhas), gerando: (a) incapacidade de identificar gargalos antes que causem prejuízo; (b) ausência de métricas consolidadas sobre tempo de tramitação e produtividade por unidade; (c) dificuldade de auditoria e transparência, tanto interna quanto para o cidadão.

O **SETES.DOCS** é um sistema de gestão de processos administrativos com workflow roteirizado, assinatura digital com validade jurídica e consulta pública. Seu objetivo é digitalizar, automatizar e dar transparência ao trâmite de processos entre unidades administrativas, eliminando o papel, reduzindo o tempo de tramitação e fornecendo métricas de eficiência operacional para gestores.

## 2. Personas

* **Servidor Operacional:** Servidor de uma unidade administrativa (ex.: COFIN, AJUR). É o executor do dia a dia: cria novos processos, despacha para a próxima unidade conforme o roteiro predefinido, anexa documentos, assina documentos com certificado digital e consulta o histórico de processos em que atuou. Sua principal dor é a falta de visibilidade do que chegou para ele e a incerteza sobre o caminho correto de tramitação. Ele só vê e movimenta processos da sua própria unidade.
* **Gestor:** Responsável por uma ou mais unidades administrativas. Visualiza dashboards de desempenho, analisa gargalos, gera relatórios de produtividade e toma decisões a partir dos KPIs. Pode ver todos os processos das unidades que gerencia e cadastrar novos usuários na sua unidade. Sua principal dor é não saber onde os processos estão travados nem quem está sobrecarregado.
* **Administrador do Sistema (Super Admin):** Pessoa da equipe central de TI ou administração dedicada. Cadastra unidades, tipos de processo, perfis de acesso, roteiros de tramitação e usuários. É o guardião da configuração estrutural do sistema. Sua principal dor é a sobrecarga operacional se não houver delegação de cadastros básicos aos chefes de unidade.
* **Cidadão / Parte Interessada Externa:** Pessoa sem autenticação no sistema. Acessa o portal de consulta pública para verificar o andamento de processos de seu interesse, pesquisando por número, assunto, tipo ou data. Sua principal dor é a falta de transparência e a necessidade de se deslocar ou telefonar para obter informação sobre um processo.
* **Auditor / Controlador Interno:** Pessoa que precisa extrair dados para fiscalização e prestação de contas. Possui acesso a relatórios consolidados e, quando autorizado, pode visualizar processos de qualquer unidade, inclusive restritos ou sigilosos. Sua principal dor é a dificuldade de rastrear a cadeia completa de tramitação e decisões de um processo.

## 3. Escopo do MVP

* **Dentro do Escopo:**
  * Autenticação própria do SETES.DOCS com login e senha
  * Cadastro e gestão de usuários, unidades, tipos de processo e roteiros de tramitação
  * Controle de acesso baseado em perfis (Administrador, Gestor, Servidor) com visibilidade restrita por unidade
  * Criação de processos com metadados (número, assunto, tipo, data, prazo, unidade de origem, interessados)
  * Workflow roteirizado: tramitação de processos entre unidades conforme caminho predefinido por tipo de processo
  * Quadro Kanban com colunas (Aberto, Em Tramitação, Concluído, Arquivado) e transições automáticas de status
  * Upload e anexação de documentos (PDF, Word, imagens) aos processos, com armazenamento no próprio sistema
  * ~~**Condicional ao Discovery Técnico:** Assinatura digital com certificado ICP-Brasil (e-CPF/e-CNPJ) com validade jurídica plena.~~ **REMOVIDO DO MVP — movido para a Fase 2** (decisão formalizada em 2026-07-27). O plano de contingência previsto neste item foi acionado: o MVP foi lançado sem assinatura digital, a interface não exibe o botão "Assinar" e os documentos tramitam sem assinatura. Critérios de aceite preservados no Épico 4 como backlog da Fase 2.
  * Notificações internas (ícone no sistema) e por e-mail para eventos relevantes (novo processo recebido, processo concluído, prazo próximo)
  * Dashboard de KPIs para gestores: processos ativos, tempo médio de tramitação, processos parados, produtividade por unidade
  * Consulta pública de processos por número, assunto, tipo de processo ou data, sem necessidade de autenticação
  * Arquivamento automático de processos concluídos após tempo configurável (padrão: 30 dias)
  * Perfil do usuário com lista de processos em que atuou e documentos assinados

* **Fora de Escopo:**
  * Notificações por WhatsApp, SMS ou push notification mobile (apenas e-mail e notificação interna no MVP)
  * Integração com sistemas externos de autenticação (gov.br, Active Directory, SSO corporativo) — o MVP usará login próprio
  * Automação de SLA com escalonamento automático, reabertura de processos ou sanções por atraso — o MVP exibirá prazos e listas de atrasados
  * Relatórios avançados com exportação em múltiplos formatos (Excel, CSV, PDF) — o MVP terá dashboard visual e consulta em tela. Relatórios de auditoria serão visualizados na própria interface, sem exportação
  * Versionamento de documentos anexados — o MVP tratará anexos como arquivos simples
  * Aplicativo mobile nativo — o MVP será responsivo para navegador, sem app dedicado
  * Integração com sistemas legados de organograma ou protocolo — cadastros serão manuais no MVP
  * Bloqueio de concorrência (dois usuários editando simultaneamente) — melhoria futura
  * Tramitação livre (tipo e-mail) entre unidades — o MVP implementa apenas o modelo roteirizado
  * Roteiros de tramitação condicionais (bifurcações baseadas em regras de negócio, ex.: "se valor > X, vá para unidade A; senão, vá para unidade B") — o MVP implementa apenas roteiros lineares sequenciais

## 4. Histórias de Usuário e Critérios de Aceitação

### Épico 1: Autenticação e Controle de Acesso

* **US 1.1:** Como Administrador, eu quero cadastrar novos usuários no sistema para que apenas pessoas autorizadas tenham acesso.
  * **Critérios de Aceitação:**
    * *Cenário 1: Cadastro de servidor com sucesso*
      * **Dado** que estou autenticado como Administrador
      * **Quando** preencho nome, e-mail, unidade, perfil (Servidor/Gestor/Administrador) e confirmo o cadastro
      * **Então** o novo usuário é criado com status "Ativo — pendente de primeiro acesso"
    * *Cenário 1a: Envio de credenciais ao novo usuário*
      * **Dado** que um usuário foi cadastrado com sucesso
      * **Quando** o cadastro é concluído
      * **Então** um e-mail é enviado ao endereço cadastrado contendo link de primeiro acesso com validade de 48 horas
    * *Cenário 2: E-mail duplicado*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento cadastrar um usuário com um e-mail que já está em uso
      * **Então** o sistema rejeita o cadastro e exibe a mensagem "E-mail já cadastrado no sistema"
    * *Cenário 3: E-mail com formato inválido*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento cadastrar um usuário com e-mail em formato inválido (ex.: "joao", "@sem-nome.com", "sem arroba")
      * **Então** o sistema rejeita o cadastro e exibe "Formato de e-mail inválido — informe um endereço de e-mail válido"
    * *Cenário 4: Nome vazio ou apenas com espaços*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento cadastrar um usuário com o campo nome vazio ou contendo apenas espaços em branco
      * **Então** o sistema rejeita o cadastro e exibe "Nome é obrigatório"
    * *Cenário 5: Unidade inexistente*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento cadastrar um usuário vinculado a uma unidade que não existe ou foi desativada
      * **Então** o sistema rejeita o cadastro e exibe "Unidade inválida ou inativa — selecione uma unidade ativa"

* **US 1.2:** Como Gestor, eu quero cadastrar usuários da minha própria unidade para que eu não dependa da TI central para incluir novos membros da minha equipe.
  * **Critérios de Aceitação:**
    * *Cenário 1: Cadastro de usuário na unidade gerenciada*
      * **Dado** que estou autenticado como Gestor da COFIN
      * **Quando** cadastro um novo usuário vinculado à unidade COFIN com perfil de Servidor (único perfil que posso atribuir)
      * **Então** o cadastro é realizado com sucesso e o novo usuário passa a ter acesso apenas aos processos da COFIN
    * *Cenário 2: Tentativa de cadastro em unidade não gerenciada*
      * **Dado** que estou autenticado como Gestor da COFIN
      * **Quando** tento cadastrar um usuário vinculado à unidade COGEP
      * **Então** o sistema rejeita a operação e exibe a mensagem "Você não tem permissão para cadastrar usuários nesta unidade"
    * *Cenário 3: Tentativa de cadastro com perfil privilegiado*
      * **Dado** que estou autenticado como Gestor da COFIN
      * **Quando** tento cadastrar um usuário com perfil de Gestor ou Administrador
      * **Então** o sistema rejeita a operação e exibe "Você não tem permissão para atribuir este perfil. Apenas o Administrador pode cadastrar Gestores e Administradores."

* **US 1.3:** Como Usuário, eu quero fazer login no sistema com minhas credenciais para acessar minhas funcionalidades conforme meu perfil.
  * **Critérios de Aceitação:**
    * *Cenário 1: Login com credenciais válidas*
      * **Dado** que possuo login e senha ativos no SETES.DOCS
      * **Quando** informo minhas credenciais corretas na tela de login
      * **Então** sou autenticado e direcionado ao painel principal correspondente ao meu perfil
    * *Cenário 2: Senha incorreta*
      * **Dado** que possuo login ativo no sistema
      * **Quando** informo senha incorreta três vezes consecutivas
      * **Então** minha conta é bloqueada temporariamente por 30 minutos e recebo um e-mail de alerta de tentativas suspeitas

    * *Cenário 2b: Tentativa de login com senha correta durante bloqueio*
      * **Dado** que minha conta está bloqueada temporariamente (menos de 30 minutos desde o bloqueio) após 3 tentativas incorretas
      * **Quando** tento fazer login com a senha correta durante o período de bloqueio
      * **Então** o sistema rejeita a autenticação e exibe "Conta bloqueada temporariamente. Tente novamente em X minutos.", onde X é o tempo restante de bloqueio. O contador de tentativas não é alterado, e o tempo de bloqueio não é reiniciado.
    * *Cenário 2c: Recuperação de senha durante bloqueio temporário*
      * **Dado** que minha conta está bloqueada temporariamente após 3 tentativas incorretas
      * **Quando** solicito recuperação de senha informando meu e-mail cadastrado
      * **Então** recebo o link de redefinição normalmente. Ao redefinir a senha com sucesso (seguindo os mesmos critérios do Cenário 3), a conta é automaticamente desbloqueada, o contador de tentativas é resetado para zero, e sou redirecionado à tela de login. Caso o link expire (2 horas) sem ser utilizado, a conta permanece bloqueada até o fim do período de 30 minutos.
    * *Cenário 3: Recuperação de senha*
      * **Dado** que esqueci minha senha
      * **Quando** solicito recuperação informando meu e-mail cadastrado
      * **Então** recebo um link de redefinição de senha com validade de 2 horas. Ao acessar o link, sou direcionado para tela de criação de nova senha, que deve ter no mínimo 8 caracteres, contendo pelo menos 1 letra maiúscula, 1 letra minúscula e 1 número
    * *Cenário 4: Desbloqueio após tempo de penalidade*
      * **Dado** que minha conta foi bloqueada por 3 tentativas incorretas há mais de 30 minutos
      * **Quando** tento fazer login com a senha correta
      * **Então** sou autenticado com sucesso e o contador de tentativas é resetado para zero
    * *Cenário 5: Recuperação com e-mail não cadastrado*
      * **Dado** que informei um e-mail que não está na base do sistema
      * **Quando** solicito recuperação de senha
      * **Então** o sistema exibe a mensagem genérica "Se o e-mail informado estiver cadastrado, um link de redefinição será enviado" (para não expor informações de cadastro) e NENHUM e-mail é enviado
    * *Cenário 6: Login com conta desativada*
      * **Dado** que minha conta foi desativada por um Administrador
      * **Quando** tento fazer login com minhas credenciais corretas
      * **Então** o sistema rejeita a autenticação e exibe "Conta desativada. Entre em contato com o Administrador do sistema." NENHUM e-mail de alerta é enviado (pois a desativação é uma ação administrativa legítima, não uma tentativa de invasão).

* **US 1.4:** Como Servidor, eu quero ver os processos da minha unidade e acompanhar os que protocolei mesmo depois de tramitados para que eu não visualizo indevidamente processos de outras unidades, mas não perco o acompanhamento do que a minha unidade originou.
  * **Critérios de Aceitação:**
    * *Cenário 1: Acesso pela unidade atual e acompanhamento pela unidade de origem (revisado — change visibilidade-processos-origem)*
      * **Dado** que estou autenticado como Servidor vinculado à unidade COFIN
      * **Quando** acesso a listagem de processos ou realizo qualquer busca
      * **Então** vejo os processos atualmente na unidade COFIN (colunas Aberto, Em Tramitação, Concluído e Arquivado do Kanban da COFIN, integralmente acionáveis) e, em modo **somente leitura** (card acinzentado, sem Despachar/Devolver/sigilo/anexar-remover documentos), os processos **cuja unidade de origem é a COFIN** e que já tramitaram para outra unidade. Processo sigiloso que está em outra unidade **não aparece** no acompanhamento por origem — o sigilo prevalece. Concluído/Arquivado só aparecem quando o checkbox "Exibir concluídos e arquivados" está marcado (default desmarcado)
    * *Cenário 2: Tentativa de acesso direto por URL a processo de outra unidade*
      * **Dado** que estou autenticado como Servidor da unidade COFIN e conheço o ID de um processo que nunca passou pela COFIN
      * **Quando** tento acessar diretamente a URL desse processo de outra unidade
      * **Então** o sistema exibe "Acesso negado — você não tem permissão para visualizar este processo" e registra a tentativa de acesso indevido em log de segurança
    * *Cenário 3: Servidor transferido de unidade*
      * **Dado** que eu era Servidor da unidade COFIN e fui transferido para a unidade AJUR
      * **Quando** acesso meu histórico de atuação (Meu Perfil)
      * **Então** visualizo os processos em que atuei quando estava na COFIN (histórico permanece), mas não tenho mais acesso ao Kanban ou aos detalhes atuais dos processos que estão na COFIN, exceto se o processo também tiver tramitado pela AJUR

* **US 1.5:** Como Usuário, eu quero acessar meu perfil para visualizar meu histórico de atuação no sistema.
  * **Critérios de Aceitação:**
    * *Cenário 1: Visualização do perfil com histórico*
      * **Dado** que estou autenticado no sistema
      * **Quando** acesso a tela "Meu Perfil"
      * **Então** visualizo meus dados cadastrais, a lista de processos em que atuei (com número, assunto, data da ação e tipo de ação realizada) e a lista de documentos que assinei digitalmente (com nome do documento, processo vinculado e data da assinatura)
    * *Cenário 2: Perfil de usuário recém-cadastrado sem histórico*
      * **Dado** que sou um usuário recém-cadastrado que nunca atuou em nenhum processo
      * **Quando** acesso a tela "Meu Perfil"
      * **Então** visualizo meus dados cadastrais e as seções de histórico exibem a mensagem "Nenhum processo registrado" e "Nenhum documento assinado"

* **US 1.6:** Como Usuário recém-cadastrado, eu quero realizar o primeiro acesso e criar minha senha para ativar minha conta no sistema.
  * **Critérios de Aceitação:**
    * *Cenário 1: Primeiro acesso com link válido e senha forte*
      * **Dado** que sou um usuário recém-cadastrado com status "pendente de primeiro acesso"
      * **Quando** acesso o link de primeiro acesso recebido por e-mail dentro do prazo de 48 horas e defino uma senha com no mínimo 8 caracteres, contendo pelo menos 1 letra maiúscula, 1 letra minúscula e 1 número
      * **Então** a senha é aceita, sou autenticado e meu status passa para "Ativo"

	    * *Cenário 1b: Tentativa de senha fraca no primeiro acesso*
	      * **Dado** que estou na tela de criação de senha do primeiro acesso
	      * **Quando** defino uma senha que não atende aos critérios (menos de 8 caracteres, ou sem maiúscula, ou sem minúscula, ou sem número)
	      * **Então** o sistema rejeita a senha e exibe "A senha deve ter no mínimo 8 caracteres, incluindo letras maiúsculas, minúsculas e números"
    * *Cenário 2: Link de primeiro acesso expirado*
      * **Dado** que sou um usuário recém-cadastrado e meu link de primeiro acesso expirou (mais de 48 horas)
      * **Quando** tento acessar o link expirado
      * **Então** o sistema exibe "Link expirado. Solicite um novo link de acesso ao Administrador." e meu status permanece "pendente de primeiro acesso"

    * *Cenário 3: Link de primeiro acesso já utilizado*
      * **Dado** que sou um usuário que já realizou o primeiro acesso com sucesso (status "Ativo")
      * **Quando** tento acessar novamente o link de primeiro acesso que já foi utilizado
      * **Então** o sistema exibe "Link já utilizado. Se você já definiu sua senha, faça login normalmente. Caso tenha esquecido sua senha, utilize a opção 'Esqueci minha senha'." e meu status não é alterado

* **US 1.7:** Como Usuário autenticado, eu quero alterar minha senha para manter a segurança da minha conta.
  * **Critérios de Aceitação:**
    * *Cenário 1: Troca com senha atual correta e nova senha válida*
      * **Dado** que estou autenticado no sistema
      * **Quando** informo minha senha atual correta e uma nova senha válida (mínimo 8 caracteres, contendo pelo menos 1 letra maiúscula, 1 letra minúscula, 1 número, e diferente da senha atual)
      * **Então** a senha é alterada com sucesso e recebo confirmação visual da troca
    * *Cenário 2: Senha atual incorreta*
      * **Dado** que estou autenticado no sistema
      * **Quando** informo minha senha atual incorreta ao tentar alterar a senha
      * **Então** o sistema rejeita a operação e exibe "Senha atual incorreta"
    * *Cenário 3: Nova senha igual à anterior (histórico)*
      * **Dado** que estou autenticado no sistema
      * **Quando** informo uma nova senha idêntica à senha atual ou a qualquer uma das últimas 6 senhas utilizadas
      * **Então** o sistema rejeita a operação e exibe "A nova senha não pode ser igual à senha atual ou às 6 senhas anteriores"

	    * *Cenário 4: Nova senha não atende aos critérios de complexidade*
	      * **Dado** que estou autenticado no sistema
	      * **Quando** informo a senha atual correta e uma nova senha que não atende aos critérios de complexidade (menos de 8 caracteres, ou sem maiúscula, ou sem minúscula, ou sem número)
	      * **Então** o sistema rejeita a operação e exibe "A senha deve ter no mínimo 8 caracteres, incluindo letras maiúsculas, minúsculas e números"

* **US 1.8:** Como Usuário autenticado, eu quero encerrar minha sessão com segurança e que o sistema encerre sessões inativas automaticamente.
  * **Critérios de Aceitação:**
    * *Cenário 1: Logout manual*
      * **Dado** que estou autenticado no sistema
      * **Quando** aciono a opção "Sair" / "Logout"
      * **Então** minha sessão é encerrada e sou redirecionado à tela de login
    * *Cenário 2: Expiração por inatividade*
      * **Dado** que estou autenticado no sistema
      * **Quando** permaneço inativo por 30 minutos
      * **Então** minha sessão é expirada automaticamente e, ao tentar qualquer ação, sou redirecionado à tela de login com a mensagem "Sessão expirada por inatividade"
    * *Cenário 2b: Aviso prévio de expiração de sessão*
      * **Dado** que estou autenticado no sistema e estou inativo há 28 minutos (2 minutos antes do timeout de 30 minutos)
      * **Quando** o sistema detecta a proximidade da expiração
      * **Então** exibo um modal com a mensagem "Sua sessão expirará em 2 minutos por inatividade. Deseja continuar?" com as opções "Continuar Sessão" (mantém a sessão ativa e reseta o contador) e "Sair" (encerra a sessão imediatamente). Se o usuário não responder em 2 minutos, a sessão é expirada conforme Cenário 2.

* **US 1.9:** Como Usuário, eu quero que o sistema gerencie sessões concorrentes de forma previsível para proteger minha conta contra uso indevido.
  * **Critérios de Aceitação:**
    * *Cenário 1: Login em segundo dispositivo (comportamento padrão)*
      * **Dado** que estou autenticado no sistema no Dispositivo A
      * **Quando** realizo login com as mesmas credenciais no Dispositivo B
      * **Então** ambas as sessões permanecem ativas (sessões independentes). O sistema não invalida a sessão anterior. Cada sessão expira independentemente por inatividade conforme US 1.8, Cenário 2.

* **US 1.10:** Como Administrador, eu quero resetar a senha de um usuário para restaurar o acesso em casos de conta comprometida ou impossibilidade de auto-recuperação.
  * **Critérios de Aceitação:**
    * *Cenário 1: Reset de senha de usuário ativo*
      * **Dado** que estou autenticado como Administrador e acesso um usuário com status "Ativo"
      * **Quando** aciono "Resetar Senha" e confirmo a operação
      * **Então** a senha atual do usuário é invalidada, um link de redefinição com validade de 2 horas é enviado ao e-mail cadastrado, e o evento é registrado em log de auditoria com data, hora e Administrador responsável
    * *Cenário 2: Reset de senha de usuário inativo*
      * **Dado** que estou autenticado como Administrador e acesso um usuário com status "Inativo"
      * **Quando** aciono "Resetar Senha"
      * **Então** o sistema exibe "Não é possível resetar a senha de um usuário inativo. Reative o usuário antes de prosseguir."

### Épico 2: Gestão de Processos e Workflow

* **US 2.1:** Como Servidor, eu quero criar um novo processo administrativo para dar início à tramitação formal.
  * **Critérios de Aceitação:**
    * *Cenário 1: Criação de processo com dados obrigatórios*
      * **Dado** que estou autenticado como Servidor da unidade COFIN
      * **Quando** preencho todos os campos obrigatórios (assunto, tipo de processo, interessados, prazo em dias corridos) e confirmo a criação
      * **Então** o processo é criado com status "Aberto", recebe um número único gerado automaticamente no formato AAAA/NNNNNN (ano com 4 dígitos + sequencial com 6 dígitos, reiniciado a cada ano, ex.: 2026/000001). Caso o sequencial anual atinja o limite de 999.999, o sistema deve expandir automaticamente para 7 dígitos (AAAA/NNNNNNN), registrando o evento em log de sistema. Caso o sequencial de 7 dígitos atinja o limite de 9.999.999, o sistema deve expandir para 8 dígitos (AAAA/NNNNNNNN), registrando o evento em log de sistema. O formato segue o padrão AAAA/N..., sem limite superior de dígitos. Atingir 10 milhões de processos em um ano implica alerta administrativo automático ao Administrador para avaliação da capacidade do sistema e aparece no quadro Kanban da minha unidade
    * *Cenário 2: Criação sem campos obrigatórios*
      * **Dado** que estou autenticado como Servidor
      * **Quando** tento criar um processo sem preencher o campo "assunto" ou "tipo de processo"
      * **Então** o sistema rejeita a criação e destaca os campos obrigatórios pendentes
    * *Cenário 3: Interessado com CPF inválido*
      * **Dado** que estou criando um processo
      * **Quando** preencho um CPF com dígito verificador inválido no campo de interessado
      * **Então** o sistema exibe "CPF inválido — verifique o número informado" e não permite prosseguir
    * *Cenário 3b: Interessado com CNPJ inválido*
      * **Dado** que estou criando um processo e seleciono tipo de interessado "Pessoa Jurídica"
      * **Quando** preencho um CNPJ com dígito verificador inválido no campo de interessado
      * **Então** o sistema exibe "CNPJ inválido — verifique o número informado" e não permite prosseguir

      * *Cenário 3c: Tipo de processo sem roteiro definido*
        * **Dado** que estou autenticado como Servidor da unidade COFIN
        * **Quando** tento criar um processo selecionando um tipo de processo cujo roteiro de tramitação está vazio (sem unidades definidas)
        * **Então** o sistema exibe "Este tipo de processo não possui roteiro de tramitação configurado. Entre em contato com o Administrador." e não permite a criação
  * **Definição do campo "Interessados":** O campo "interessados" aceita um ou mais nomes de pessoas físicas ou jurídicas, com os seguintes subcampos: nome completo (obrigatório, texto livre), CPF ou CNPJ (opcional, validado por algoritmo de dígito verificador) e tipo de participação (opcional, seleção entre: Requerente, Representado, Terceiro).

* **US 2.2:** Como Servidor, eu quero despachar um processo para a próxima unidade conforme o roteiro predefinido para que ele siga o fluxo correto de tramitação.
  * **Critérios de Aceitação:**
    * *Cenário 1: Despacho para a próxima unidade do roteiro*
      * **Dado** que um processo do tipo "Licitação" está na unidade COFIN com status "Aberto" e seu roteiro define o caminho COFIN → AJUR → DIRAD
      * **Quando** eu, servidor da COFIN, seleciono o processo e aciono a ação "Despachar"
      * **Então** o sistema move o processo para a unidade AJUR, altera seu status para "Em Tramitação" e registra a data/hora e o responsável pelo envio no histórico
    * *Cenário 2: Processo na última unidade do roteiro*
      * **Dado** que um processo está na última unidade prevista no roteiro
      * **Quando** o servidor da unidade aciona "Despachar"
      * **Então** o sistema exibe a confirmação "Este é o destino final do roteiro. Deseja concluir o processo?" e, ao confirmar, altera o status para "Concluído"
    * *Cenário 3: Cancelamento da conclusão na última unidade*
      * **Dado** que um processo está na última unidade prevista no roteiro
      * **Quando** o servidor da unidade aciona "Despachar" e, na confirmação modal, clica em "Cancelar"
      * **Então** o processo permanece na unidade atual com o mesmo status, sem alteração no histórico, e o servidor retorna à tela de detalhes do processo
    * *Cenário 4: Roteiro com unidade única*
      * **Dado** que um tipo de processo possui roteiro com apenas uma unidade e um processo desse tipo foi criado nessa mesma unidade (status "Aberto")
      * **Quando** o servidor da unidade aciona "Despachar"
      * **Então** o sistema exibe a mensagem "Esta é a unidade de origem e destino final do roteiro. Deseja concluir o processo?" (equivalente ao Cenário 2). Ao confirmar, o status é alterado para "Concluído".

* **US 2.2b:** Como Servidor, eu quero devolver um processo para a unidade anterior para solicitar correções ou diligências antes de prosseguir com a tramitação.
  * **Critérios de Aceitação:**
    * *Cenário 1: Devolução para a unidade anterior*
      * **Dado** que um processo está na minha unidade e veio da unidade COFIN
      * **Quando** aciono a ação "Devolver", seleciono um motivo (opções predefinidas: "Documentação insuficiente", "Correção de dados", "Diligência complementar") e, opcionalmente, adiciono uma justificativa em texto livre
      * **Então** o processo retorna para a unidade COFIN com status "Em Tramitação", a devolução é registrada no histórico com data/hora, responsável, motivo e justificativa, e os servidores da COFIN recebem notificação de devolução
    * *Cenário 2: Tentativa de devolução na primeira unidade do roteiro*
      * **Dado** que um processo está na primeira unidade do roteiro
      * **Quando** o servidor tenta acionar "Devolver"
      * **Então** o sistema exibe "Não é possível devolver um processo que está na unidade de origem do roteiro" e a ação não é concluída
    * *Cenário 3: Devolução sem seleção de motivo*
      * **Dado** que estou devolvendo um processo
      * **Quando** tento confirmar a devolução sem selecionar um motivo
      * **Então** o sistema exibe "Selecione um motivo para a devolução" e não conclui a ação

* **US 2.3:** Como Servidor, eu quero visualizar o quadro Kanban dos processos da minha unidade para acompanhar o status de cada um de forma intuitiva.
  * **Critérios de Aceitação:**
    * *Cenário 1: Exibição do Kanban por colunas de status*
      * **Dado** que estou autenticado como Servidor da unidade COFIN
      * **Quando** acesso a tela de Processos
      * **Então** visualizo um quadro com colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", cada uma contendo os cards dos processos correspondentes, com número, assunto, prazo e dias restantes visíveis em cada card. O Kanban é um quadro de **visualização**, não de manipulação direta. As transições de status ocorrem exclusivamente por meio de ações explícitas: o botão "Despachar" move o card de "Aberto" para "Em Tramitação" (ou para fora da unidade, se despachado para a próxima); o botão "Concluir" na última unidade move para "Concluído"; a rotina automática move de "Concluído" para "Arquivado". Os cards **NÃO são arrastáveis** entre colunas no MVP.
    * *Cenário 2: Atualização automática após despacho*
      * **Dado** que um processo foi despachado para minha unidade por outra unidade
      * **Quando** eu estiver visualizando o Kanban e um novo processo for despachado para minha unidade
      * **Então** o indicador de notificações no menu superior é incrementado, e o novo processo aparece na coluna "Aberto" após eu realizar as ações de: clicar no ícone de notificações OU acionar o botão "Atualizar" do Kanban OU navegar para outra tela e retornar
    * *Cenário 3: Kanban vazio*
      * **Dado** que estou autenticado como Servidor de uma unidade recém-criada
      * **Quando** acesso a tela de Processos e não há nenhum processo na unidade
      * **Então** visualizo as colunas do Kanban vazias com a mensagem "Nenhum processo encontrado nesta unidade"
    * *Cenário 4: Ordenação dos cards*
      * **Dado** que minha unidade possui múltiplos processos em uma mesma coluna
      * **Quando** visualizo o Kanban
      * **Então** os cards são ordenados por prazo (mais próximo do vencimento primeiro), e processos com prazo vencido aparecem no topo com os seguintes indicadores visuais: (a) o número de dias vencidos é exibido em cor vermelha com um ícone de relógio/calendário; (b) o texto do prazo no card utiliza peso de fonte bold; (c) a borda esquerda do card recebe uma barra vermelha de 4px de espessura

* **US 2.4:** Como Servidor, eu quero ver o histórico completo de tramitação de um processo para saber por quais unidades ele passou e quanto tempo permaneceu em cada uma.
  * **Critérios de Aceitação:**
    * *Cenário 1: Visualização do histórico*
      * **Dado** que um processo já passou por três unidades (COFIN → AJUR → DIRAD)
      * **Quando** acesso a tela de detalhes do processo e clico em "Histórico"
      * **Então** visualizo uma linha do tempo com cada movimentação, contendo: unidade de origem, unidade de destino, servidor responsável pelo envio, data/hora e status do processo naquele momento

      * *Cenário 2: Histórico de processo recém-criado sem movimentações*
        * **Dado** que um processo foi criado mas ainda não foi despachado para nenhuma unidade
        * **Quando** acesso a tela de detalhes do processo e clico em "Histórico"
        * **Então** visualizo a mensagem "Nenhuma movimentação registrada" e a data de criação do processo como informação complementar

* **US 2.5:** Como Sistema, eu devo arquivar automaticamente processos concluídos após o prazo configurado para manter o quadro Kanban focado nos processos ativos.
  * **Critérios de Aceitação:**
    * *Cenário 1: Arquivamento automático por tempo*
      * **Dado** que um processo foi concluído há 30 dias e o prazo de arquivamento configurado é de 30 dias
      * **Quando** a rotina automática de arquivamento é executada
      * **Então** o processo é movido da coluna "Concluído" para a coluna "Arquivado" e o evento é registrado no histórico do processo
    * *Cenário 2: Alteração do prazo de arquivamento com processos já concluídos*
      * **Dado** que existem 10 processos concluídos há 25 dias e o Administrador altera o prazo de arquivamento de 30 para 15 dias
      * **Quando** a rotina automática de arquivamento é executada
      * **Então** nenhum dos 10 processos é arquivado nesta execução, pois todos ainda estão dentro do prazo de 30 dias vigente no momento de suas conclusões. A alteração para 15 dias aplica-se apenas a processos concluídos a partir desta data, e não retroativamente aos processos já concluídos. Os 10 processos serão arquivados somente quando completarem 30 dias cada um.
    * *Cenário 3: Execução da rotina de arquivamento*
      * **Dado** que a rotina automática de arquivamento está configurada
      * **Quando** a rotina diária de arquivamento é executada
      * **Então** todos os processos concluídos cujo prazo de arquivamento (contado a partir da data de conclusão) já expirou são movidos para a coluna "Arquivado" em lote, e cada movimentação é registrada individualmente no histórico do respectivo processo
    * *Cenário 4: Recuperação de execução perdida por indisponibilidade*
      * **Dado** que a rotina de arquivamento não pôde ser executada em um ou mais dias por indisponibilidade do sistema
      * **Quando** o sistema retorna à operação normal e a rotina é executada
      * **Então** todos os processos cujo prazo de arquivamento expirou durante o período de indisponibilidade são arquivados nesta execução, sem perda de eventos de arquivamento

* **US 2.6:** Como Servidor, Gestor ou Administrador, eu quero marcar um processo como sigiloso para restringir sua visibilidade na consulta pública.
  * **Critérios de Aceitação:**
    * *Cenário 1: Marcação de processo como sigiloso*
      * **Dado** que estou autenticado como Servidor ou Gestor da unidade atual do processo, ou como Administrador do sistema
      * **Quando** acesso um processo e aciono "Marcar como Sigiloso"
      * **Então** o processo é marcado como sigiloso, a ação é registrada no histórico de tramitação e o processo deixa de aparecer nos resultados da consulta pública
    * *Cenário 1b: Marcação de sigilo por Administrador em processo de qualquer unidade*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso um processo de qualquer unidade e aciono "Marcar como Sigiloso" ou "Remover Sigilo"
      * **Então** a operação é concluída com sucesso, independentemente da unidade em que o processo se encontra, e a ação é registrada no histórico de tramitação
    * *Cenário 2: Desmarcação de sigilo*
      * **Dado** que um processo está marcado como sigiloso
      * **Quando** um usuário com permissão (Servidor ou Gestor da unidade atual, ou Administrador do sistema) aciona "Remover Sigilo"
      * **Então** a marcação de sigilo é removida, a ação é registrada no histórico e o processo volta a aparecer na consulta pública
    * *Cenário 3: Processo sigiloso visível internamente*
      * **Dado** que um processo está marcado como sigiloso
      * **Quando** um servidor da unidade atual do processo acessa o sistema
      * **Então** o processo aparece normalmente no Kanban da unidade, com um indicador visual de "Sigiloso" (ícone de cadeado ou tarja)

* **US 2.7:** Como Servidor, eu quero buscar e filtrar processos da minha unidade por número, assunto ou período para localizar rapidamente um processo específico.
  * **Critérios de Aceitação:**
    * *Cenário 1: Busca por número exato*
      * **Dado** que estou autenticado como Servidor da unidade COFIN
      * **Quando** informo um número de processo existente na busca interna
      * **Então** o sistema retorna o processo correspondente
    * *Cenário 2: Busca por termo no assunto*
      * **Dado** que estou autenticado como Servidor
      * **Quando** informo um termo de busca no campo "assunto"
      * **Então** o sistema retorna a lista de processos da minha unidade cujo assunto contém o termo informado
    * *Cenário 3: Filtro por período*
      * **Dado** que estou autenticado como Servidor
      * **Quando** informo um intervalo de datas (data inicial e data final)
      * **Então** o sistema retorna os processos da minha unidade criados no período informado
    * *Cenário 4: Busca sem resultados*
      * **Dado** que estou autenticado como Servidor
      * **Quando** informo qualquer combinação de filtros que não retorna resultados
      * **Então** o sistema exibe "Nenhum processo encontrado para os filtros informados"

* **US 2.8:** Como Gestor, eu quero visualizar o quadro Kanban consolidado de todas as unidades que gerencio para ter visão tática completa dos processos sob minha responsabilidade.
  * **Critérios de Aceitação:**
    * *Cenário 1: Kanban multi-unidade*
      * **Dado** que estou autenticado como Gestor das unidades COFIN, AJUR e DIRAD
      * **Quando** acesso a tela de Processos
      * **Então** visualizo um quadro Kanban consolidado com colunas "Aberto", "Em Tramitação", "Concluído" e "Arquivado", contendo os cards de processos de todas as unidades que gerencio. Cada card exibe: número do processo, assunto, unidade atual, prazo e dias restantes. O card também exibe o nome da unidade atual para identificação rápida.
    * *Cenário 2: Filtro por unidade no Kanban do Gestor*
      * **Dado** que estou visualizando o Kanban consolidado com processos de três unidades
      * **Quando** seleciono uma unidade específica no filtro de unidades
      * **Então** o Kanban é filtrado para exibir apenas os processos da unidade selecionada
    * *Cenário 3: Kanban consolidado vazio*
      * **Dado** que estou autenticado como Gestor de unidades que ainda não possuem processos
      * **Quando** acesso a tela de Processos
      * **Então** visualizo as colunas do Kanban vazias com a mensagem "Nenhum processo encontrado nas unidades gerenciadas"


### Épico 3: Gestão Documental

* **US 3.1:** Como Servidor, eu quero anexar documentos a um processo para que todas as informações relevantes fiquem centralizadas.
  * **Critérios de Aceitação:**
    * *Cenário 1: Upload de documento individual*
      * **Dado** que estou visualizando um processo da minha unidade
      * **Quando** seleciono a opção "Anexar Documento" e faço upload de um arquivo nos formatos aceitos (PDF, DOC, DOCX, JPG, PNG) com tamanho de até 20 MB
      * **Então** o arquivo é armazenado no sistema, vinculado ao processo, e aparece na lista de documentos do processo com nome, tipo, tamanho e data de anexação
    * *Cenário 2: Arquivo com formato ou tamanho não aceito*
      * **Dado** que estou anexando documentos a um processo
      * **Quando** tento fazer upload de um arquivo executável (.exe) ou de tamanho superior a 20 MB
      * **Então** o sistema rejeita o upload e exibe a mensagem "Formato de arquivo não permitido" ou "Arquivo excede o tamanho máximo de 20 MB"
    * *Cenário 2b: Upload de arquivo vazio (0 byte)*
      * **Dado** que estou anexando documentos a um processo
      * **Quando** tento fazer upload de um arquivo com tamanho de 0 byte (arquivo vazio ou corrompido)
      * **Então** o sistema rejeita o upload e exibe a mensagem "Não é possível anexar arquivo vazio. Selecione um arquivo com conteúdo."
    * *Cenário 3: Exclusão de documento anexado por engano*
      * **Dado** que anexei um documento a um processo da minha unidade e o processo ainda não foi despachado
      * **Quando** aciono a opção "Remover" / "Excluir" sobre o documento
      * **Então** o sistema exibe confirmação "Tem certeza que deseja remover este documento?" e, ao confirmar, o documento é removido da lista de anexos visíveis do processo, o arquivo é preservado em área de retenção (soft delete) por 30 dias, e a exclusão lógica é registrada no histórico do processo com data, hora e responsável. Durante o período de retenção, o Administrador pode restaurar o documento conforme US 8.7. Após 30 dias, o arquivo físico é excluído permanentemente de forma automática
    * *Cenário 4: Tentativa de exclusão de documento após despacho*
      * **Dado** que um documento foi anexado a um processo que já foi despachado para a próxima unidade
      * **Quando** tento acionar "Remover" sobre o documento
      * **Então** o sistema exibe "Não é possível remover documentos de um processo que já foi despachado" e a exclusão não é concluída
    * *Cenário 4b: Exclusão de documento após devolução do processo*
      * **Dado** que um processo da minha unidade foi despachado, devolvido pela unidade seguinte (US 2.2b) e agora está novamente na minha unidade
      * **Quando** aciono a opção "Remover" sobre um documento (independentemente de ter sido anexado antes do despacho original ou após a devolução)
      * **Então** o sistema exibe confirmação "Tem certeza que deseja remover este documento?" e, ao confirmar, o documento é removido da lista de anexos visíveis do processo, o arquivo é preservado em área de retenção (soft delete) por 30 dias, e a exclusão lógica é registrada no histórico do processo com data, hora e responsável. Durante o período de retenção, o Administrador pode restaurar o documento conforme US 8.7. Após 30 dias, o arquivo físico é excluído permanentemente de forma automática. Esta regra aplica-se a QUALQUER documento, tenha ele sido anexado antes do despacho original ou durante o período de correção pós-devolução. O processo permanece na unidade atual com o mesmo status ("Em Tramitação").
    * *Cenário 4c: Tentativa de exclusão de documento após o processo ser despachado novamente pós-correção*
      * **Dado** que um processo foi devolvido para minha unidade, corrigi a pendência e despachei novamente para a unidade seguinte
      * **Quando** tento remover qualquer documento do processo
      * **Então** o sistema exibe "Não é possível remover documentos de um processo que já foi despachado" (mesma regra do Cenário 4)
	    * *Cenário 5: Upload de arquivo com nome duplicado*
	      * **Dado** que um processo já possui um documento anexado chamado "parecer.pdf"
	      * **Quando** tento anexar outro arquivo com o mesmo nome "parecer.pdf"
	      * **Então** o sistema aceita o upload e renomeia automaticamente o novo arquivo para "parecer (1).pdf". O documento original não é sobrescrito. Ambos os arquivos aparecem na lista de documentos do processo, preservando a integridade de cada um.

* **US 3.2:** Como Servidor, eu quero visualizar ou baixar documentos anexados a um processo para analisar o conteúdo.
  * **Critérios de Aceitação:**
    * *Cenário 1: Visualização inline de documento*
      * **Dado** que um processo possui documentos anexados
      * **Quando** clico sobre o nome de um documento PDF ou imagem
      * **Então** consigo visualizar o conteúdo do documento na própria tela do processo
    * *Cenário 2: Download de documento*
      * **Dado** que um processo possui documentos anexados
      * **Quando** clico na opção "Baixar" de um documento
      * **Então** o arquivo é baixado para meu dispositivo mantendo seu formato e nome originais
    * *Cenário 3: Visualização de documento em formato DOC/DOCX*
      * **Dado** que um processo possui documento anexado nos formatos DOC ou DOCX
      * **Quando** clico sobre o nome do documento
      * **Então** o download do arquivo é iniciado automaticamente, e o sistema exibe a mensagem "Formato não permite visualização inline — o download será iniciado"

### Épico 4: Assinatura Digital — FASE 2 (fora do MVP)

> **Status: movido para a Fase 2 — decisão formalizada em 2026-07-27.** O plano de
> contingência abaixo foi acionado: o MVP foi lançado sem assinatura digital, a interface
> não exibe o botão "Assinar" e os documentos tramitam sem assinatura. **Nada deste épico
> está implementado** — não há capability correspondente em `openspec/specs/`, não há spec
> Playwright, e `documentos_assinados` no perfil (US 1.5) é campo placeholder que retorna
> vazio. As US 4.1 e 4.2 abaixo permanecem válidas como backlog da Fase 2; os requisitos
> funcionais 16, 17, 18 e 41 e as exigências de MP 2.200-2/2001 e ICP-Brasil nos requisitos
> não funcionais só passam a valer quando o épico for retomado.

**Premissa de Produto:** O usuário deve conseguir assinar documentos utilizando seu certificado digital ICP-Brasil (e-CPF/e-CNPJ), diretamente pelo navegador, sem necessidade de instalar software adicional no computador. **Decisão de produto:** O Épico 4 (Assinatura Digital) está condicionado à confirmação, durante a fase de Discovery Técnico, de que os certificados em uso pelo cliente são compatíveis com as APIs de assinatura disponíveis nos navegadores-alvo (Chrome, Firefox, Edge — versões estáveis mais recentes). **Plano de contingência:** Caso o Discovery Técnico identifique restrições impeditivas, o Épico 4 será movido para a Fase 2 do produto, e o MVP será lançado sem assinatura digital. Neste cenário, a interface não exibirá o botão "Assinar", e os documentos tramitarão sem assinatura digital até a Fase 2.

* **US 4.1:** Como Servidor, eu quero assinar digitalmente documentos de um processo usando meu certificado ICP-Brasil para conferir validade jurídica à minha manifestação.
  * **Critérios de Aceitação:**
    * *Cenário 1: Assinatura com certificado digital válido*
      * **Dado** que um processo da minha unidade possui documentos pendentes de assinatura, eu possuo um certificado digital ICP-Brasil (e-CPF) válido e acessível ao navegador
      * **Quando** seleciono um documento e aciono "Assinar", o sistema detecta o certificado digital disponível, insiro o PIN do certificado e confirmo
      * **Então** o sistema aplica a assinatura digital ao documento, registra data/hora da assinatura, vincula ao meu usuário, e o documento aparece na seção "Documentos Assinados" do meu perfil e do processo
    * *Cenário 2: Certificado expirado ou inválido*
      * **Dado** que estou tentando assinar um documento
      * **Quando** utilizo um certificado digital expirado ou revogado
      * **Então** o sistema rejeita a assinatura e exibe "Certificado digital inválido ou expirado. Utilize um certificado ICP-Brasil válido."
    * *Cenário 3: PIN incorreto*
      * **Dado** que estou tentando assinar um documento com certificado digital válido
      * **Quando** insiro o PIN incorreto três vezes consecutivas
      * **Então** a operação de assinatura é bloqueada por 30 minutos e recebo um e-mail de alerta de tentativas suspeitas
    * *Cenário 4: Documento já assinado*
      * **Dado** que um documento já possui assinatura digital
      * **Quando** outro usuário tenta assinar o mesmo documento
      * **Então** o sistema aplica a assinatura adicional (coassinatura), mantendo o histórico de todas as assinaturas aplicadas
      * *Cenário 5: Certificado digital não detectado*
      * **Dado** que estou tentando assinar um documento
      * **Quando** aciono "Assinar" e não há token/smart card conectado ao computador ou o navegador não detecta o certificado digital
      * **Então** o sistema exibe "Certificado digital não detectado. Conecte o token/smart card ao computador e certifique-se de que o driver está instalado corretamente." e a operação de assinatura não é concluída

* **US 4.2:** Como Usuário, eu quero verificar a validade de um documento assinado digitalmente para confirmar que seu conteúdo não foi alterado.
  * **Critérios de Aceitação:**
    * *Cenário 1: Verificação de integridade do documento assinado*
      * **Dado** que um documento possui assinatura digital ICP-Brasil
      * **Quando** acesso o documento e aciono "Verificar Assinatura"
      * **Então** o sistema exibe: nome do signatário, CPF, data/hora da assinatura, autoridade certificadora e status "Assinatura válida — documento íntegro"
    * *Cenário 2: Documento adulterado ou assinatura inválida*
      * **Dado** que um documento possui assinatura digital ICP-Brasil, mas o arquivo foi alterado após a assinatura OU o certificado do signatário foi revogado
      * **Quando** acesso o documento e aciono "Verificar Assinatura"
      * **Então** o sistema exibe: nome do signatário, CPF, data/hora da assinatura, autoridade certificadora e status "Assinatura INVÁLIDA — o documento foi adulterado ou o certificado foi revogado", com destaque visual de alerta (ícone ou cor de advertência)
    * *Cenário 3: Certificado expirado no momento da verificação*
      * **Dado** que um documento foi assinado com certificado válido à época, mas o certificado expirou desde então
      * **Quando** verifico a assinatura
      * **Então** o sistema exibe "Assinatura válida — documento íntegro. Certificado expirado em [data], mas válido na data da assinatura."

### Épico 5: Notificações e Alertas

* **US 5.1:** Como Servidor, eu quero receber notificações internas quando um processo novo chega à minha unidade para agir rapidamente.
  * **Critérios de Aceitação:**
    * *Cenário 1: Notificação de novo processo recebido*
      * **Dado** que um processo foi despachado para minha unidade
      * **Quando** o despacho é concluído pela unidade de origem
      * **Então** eu, como servidor da unidade destino, vejo um indicador de notificação no ícone de sininho do menu superior com a quantidade de novos processos, e ao clicar vejo a lista com número do processo, assunto e unidade de origem
    * *Cenário 2: Abertura do painel sem zerar contador*
      * **Dado** que tenho 3 notificações não lidas
      * **Quando** clico no ícone do sino para abrir o painel de notificações
      * **Então** visualizo a lista de notificações, o contador permanece em 3, e cada notificação exibe um indicador visual de "não lida" (bola azul ou destaque). O contador só é decrementado e a notificação marcada como lida quando EU clicar sobre uma notificação específica OU quando eu clicar no botão "Marcar todas como lidas" disponível no topo do painel. Notificações lidas permanecem acessíveis no histórico por 30 dias
    * *Cenário 3: Persistência entre sessões*
      * **Dado** que eu tinha 2 notificações não lidas quando fiz logout
      * **Quando** faço login novamente
      * **Então** o contador ainda exibe 2 notificações pendentes
    * *Cenário 4: Expurgo de notificações lidas antigas*
      * **Dado** que eu li uma notificação há mais de 30 dias
      * **Quando** acesso o histórico de notificações
      * **Então** esta notificação não aparece mais na listagem, sendo removida automaticamente pelo sistema
    * *Cenário 4b: Notificações não lidas não são expurgadas*
      * **Dado** que uma notificação foi gerada há mais de 30 dias e eu ainda NÃO a li
      * **Quando** acesso a lista de notificações
      * **Então** esta notificação permanece visível NORMALMENTE como "não lida" (com indicador visual de não lida). O expurgo automático NÃO remove notificações não lidas. Notificações não lidas só são removidas após serem lidas E decorridos 30 dias da leitura. O contador do sino continua refletindo esta notificação não lida.

* **US 5.2:** Como Servidor, eu quero receber alertas por e-mail sobre eventos importantes para não perder prazos mesmo quando não estou logado no sistema.
  * **Critérios de Aceitação:**
    * *Cenário 1: E-mail de novo processo recebido*
      * **Dado** que um processo foi despachado para minha unidade
      * **Quando** o despacho é concluído
      * **Então** recebo um e-mail com o assunto "Novo processo recebido — [Número do Processo]" contendo número do processo, assunto, unidade de origem e link direto para acessá-lo
    * *Cenário 2: E-mail de prazo próximo ao vencimento*
      * **Dado** que um processo da minha unidade tem prazo (dias corridos) a vencer dentro do limite configurado pelo Administrador para alerta de prazo (parâmetro 'Dias de antecedência para alerta de prazo', valor padrão: 2 dias corridos — US 8.5)
      * **Quando** a rotina diária de verificação de prazos é executada
      * **Então** todos os servidores da unidade atual do processo recebem um e-mail de alerta com assunto "Prazo próximo — [Número do Processo]" contendo número do processo, prazo e dias restantes

    * *Cenário 3: Falha na entrega do e-mail de notificação*
      * **Dado** que um processo foi despachado para minha unidade e meu e-mail cadastrado está incorreto ou inacessível (caixa cheia, servidor rejeita)
      * **Quando** o sistema tenta enviar o e-mail de notificação e a entrega falha
      * **Então** o sistema registra a falha de entrega em log interno (acessível ao Administrador na tela de "Logs do Sistema") com data, hora, destinatário e motivo da falha. A notificação interna (ícone de sininho) NÃO é afetada — o usuário ainda recebe a notificação no sistema normalmente. O sistema NÃO realiza novas tentativas automáticas de envio para o mesmo evento.

* **US 5.3:** Como Servidor, eu quero receber notificação interna quando um processo da minha unidade é concluído para acompanhar o desfecho das tramitações.
  * **Critérios de Aceitação:**
    * *Cenário 1: Notificação de processo concluído*
      * **Dado** que um processo da minha unidade foi concluído (status alterado para "Concluído")
      * **Quando** a conclusão é registrada
      * **Então** todos os servidores da unidade em que o processo foi concluído veem um indicador de notificação no ícone de sininho do menu superior com a quantidade de novos eventos, e ao clicar visualizam a notificação com número do processo, assunto e data de conclusão

* **US 5.4:** Como Servidor, eu quero receber notificações internas de alerta de prazo para não perder prazos de processos da minha unidade mesmo quando não acesso o e-mail.
  * **Critérios de Aceitação:**
    * *Cenário 1: Alerta interno de prazo próximo*
      * **Dado** que um processo da minha unidade tem prazo (dias corridos) a vencer dentro do limite configurado pelo Administrador para alerta de prazo (parâmetro 'Dias de antecedência para alerta de prazo', valor padrão: 2 dias corridos — US 8.5)
      * **Quando** a rotina diária de verificação de prazos é executada
      * **Então** todos os servidores da unidade atual do processo veem um indicador de notificação no ícone de sininho do menu superior, e ao clicar visualizam a notificação com número do processo, assunto, prazo e dias restantes


### Épico 6: Dashboard e Métricas

* **US 6.1:** Como Gestor, eu quero visualizar um dashboard de KPIs para monitorar a eficiência operacional das minhas unidades.
  * **Critérios de Aceitação:**
    * *Cenário 1: Exibição do dashboard com indicadores*
      * **Dado** que estou autenticado como Gestor de ao menos uma unidade que possui processos
      * **Quando** acesso o Dashboard
      * **Então** visualizo: total de processos ativos, tempo médio de tramitação (em dias corridos, medido da data de criação do processo até a data de conclusão, considerando apenas processos concluídos nos últimos 12 meses), quantidade de processos parados (sem movimentação há mais de 7 dias corridos), produtividade por unidade (processos concluídos no mês) e lista dos processos com prazo vencido ou próximo do vencimento
    * *Cenário 2: Dashboard sem dados (gestor recém-cadastrado)*
      * **Dado** que estou autenticado como Gestor de unidades que ainda não possuem processos
      * **Quando** acesso o Dashboard
      * **Então** visualizo os cards de KPI com valor zero e a mensagem "Nenhum dado disponível para o período" em cada seção
    * *Cenário 3: Filtro por unidade gerenciada*
      * **Dado** que estou autenticado como Gestor de três unidades (COFIN, AJUR, DIRAD)
      * **Quando** seleciono apenas a unidade COFIN no filtro do Dashboard
      * **Então** todos os KPIs e listas são recalculados considerando apenas os processos da COFIN
    * *Cenário 4: Drill-down a partir de KPI*
      * **Dado** que o KPI "Processos Parados" exibe o valor 7
      * **Quando** clico sobre o número 7 no card de KPI
      * **Então** sou direcionado para a listagem filtrada dos 7 processos que estão sem movimentação há mais de 7 dias corridos, com número, assunto, unidade atual e dias parados de cada um
    * *Cenário 5: Drill-down a partir do KPI "Processos Ativos"*
      * **Dado** que o KPI "Total de Processos Ativos" exibe o valor 42
      * **Quando** clico sobre o número 42 no card de KPI
      * **Então** sou direcionado para a listagem filtrada dos 42 processos ativos (Aberto + Em Tramitação), com número, assunto, unidade atual e dias restantes de cada um
    * *Cenário 6: KPIs sem drill-down*
      * **Dado** que estou visualizando o dashboard
      * **Quando** clico sobre os cards de KPI "Tempo Médio de Tramitação" ou "Produtividade por Unidade"
      * **Então** nenhuma ação de drill-down é disparada. Estes KPIs são apenas indicadores numéricos informativos, não clicáveis. Apenas "Processos Ativos" e "Processos Parados" possuem drill-down para lista detalhada.

### Épico 7: Consulta Pública

* **US 7.1:** Como Cidadão, eu quero consultar o andamento de um processo sem precisar de login para ter transparência sobre o que me diz respeito.
  * **Critérios de Aceitação:**
    * *Cenário 1: Consulta por número do processo*
      * **Dado** que estou na página de Consulta Pública, sem autenticação
      * **Quando** informo um número de processo válido e clico em "Consultar"
      * **Então** visualizo: número do processo, assunto, tipo de processo, status atual (Aberto/Em Tramitação/Concluído/Arquivado), unidade atual, data de criação e histórico simplificado de movimentações (datas e unidades percorridas, sem expor nomes de servidores)
    * *Cenário 2: Número de processo inexistente*
      * **Dado** que estou na página de Consulta Pública
      * **Quando** informo um número que não corresponde a nenhum processo
      * **Então** o sistema exibe "Nenhum processo encontrado com o número informado"
    * *Cenário 3: Ocultação de dados pessoais na consulta pública*
      * **Dado** que estou na página de Consulta Pública e um processo existe com interessados cadastrados (nome e CPF/CNPJ)
      * **Quando** consulto o processo pelo número
      * **Então** visualizo o nome do interessado, mas CPF e CNPJ NÃO aparecem em nenhum campo da tela de resultado. Apenas o nome do interessado é exibido. O dado completo (CPF/CNPJ) permanece acessível apenas internamente no sistema, por usuários autenticados e autorizados.

    * *Cenário 4: Consulta de processo marcado como sigiloso*
      * **Dado** que um processo está marcado como sigiloso (US 2.6) e estou na página de Consulta Pública, sem autenticação
      * **Quando** informo o número exato desse processo e clico em "Consultar"
      * **Então** o sistema exibe "Nenhum processo encontrado com o número informado" (mesma mensagem do Cenário 2, para não revelar a existência de processos sigilosos)

* **US 7.2:** Como Cidadão, eu quero pesquisar processos por assunto, tipo ou período para localizar processos de meu interesse quando não sei o número exato.
  * **Critérios de Aceitação:**
    * *Cenário 1: Pesquisa por assunto*
      * **Dado** que estou na página de Consulta Pública
      * **Quando** preencho o campo "assunto" com um termo e clico em "Pesquisar"
      * **Então** visualizo a lista de processos cujo assunto contém o termo informado, respeitando processos cujo tipo é público (processos sigilosos não devem aparecer nos resultados)
    * *Cenário 2: Pesquisa combinada com múltiplos filtros*
      * **Dado** que estou na página de Consulta Pública
      * **Quando** preencho o tipo de processo "Licitação" e o período de "01/01/2026 a 31/03/2026" e clico em "Pesquisar"
      * **Então** visualizo a lista de processos do tipo Licitação criados no período informado, excluídos os processos marcados como sigilosos
    * *Cenário 3: Pesquisa sem resultados*
      * **Dado** que estou na página de Consulta Pública
      * **Quando** preencho qualquer combinação de filtros que não retorna resultados
      * **Então** o sistema exibe a mensagem "Nenhum processo encontrado para os filtros informados"

### Épico 8: Administração do Sistema

* **US 8.0:** Como operador responsável pela implantação, eu quero executar a inicialização do sistema para criar a estrutura administrativa mínima e o primeiro Administrador.
  * **Critérios de Aceitação:**
    * *Cenário 1: Inicialização do sistema vazio*
      * **Dado** que o sistema foi instalado e nunca foi inicializado
      * **Quando** acesso a funcionalidade de inicialização do sistema (disponível apenas enquanto o sistema não tiver nenhum Administrador cadastrado) e preencho os dados do Administrador root (nome, e-mail, senha) e a primeira unidade administrativa (nome, sigla)
      * **Então** o Administrador é criado com perfil "Administrador" e status "Ativo", a unidade é criada como ativa, e a funcionalidade de inicialização é desabilitada permanentemente. O Administrador recebe e-mail de confirmação e pode fazer login imediatamente.
    * *Cenário 2: Tentativa de acessar inicialização após concluída*
      * **Dado** que o sistema já foi inicializado
      * **Quando** qualquer pessoa tenta acessar a funcionalidade de inicialização do sistema após a conclusão do setup
      * **Então** o sistema exibe "Sistema já inicializado. Faça login para continuar." e redireciona para a tela de login.

* **US 8.1:** Como Administrador, eu quero cadastrar e gerenciar unidades administrativas para refletir a estrutura organizacional no sistema.
  * **Critérios de Aceitação:**
    * *Cenário 1: Cadastro de unidade*
      * **Dado** que estou autenticado como Administrador
      * **Quando** cadastro uma nova unidade com nome (ex.: COFIN), sigla e gestor responsável
      * **Então** a unidade fica disponível para vinculação de usuários e para ser incluída em roteiros de tramitação
    * *Cenário 2: Edição de unidade existente*
      * **Dado** que estou autenticado como Administrador e a unidade COFIN já existe
      * **Quando** altero o nome, sigla ou gestor responsável da unidade COFIN
      * **Então** as alterações são salvas e passam a valer imediatamente para todas as telas e relatórios do sistema, sem afetar processos já concluídos ou em andamento
    * *Cenário 3: Desativação de unidade com processos pendentes*
      * **Dado** que estou autenticado como Administrador e a unidade COFIN ainda possui processos em andamento
      * **Quando** tento desativar a unidade COFIN
      * **Então** o sistema exibe a mensagem "Esta unidade possui X processo(s) em andamento. Para desativá-la, primeiro redistribua ou conclua todos os processos pendentes." e a desativação não é concluída
    * *Cenário 4: Desativação de unidade sem processos pendentes*
      * **Dado** que estou autenticado como Administrador e a unidade COFIN não possui processos em andamento
      * **Quando** desativo a unidade COFIN
      * **Então** a unidade é marcada como inativa, seus usuários vinculados são automaticamente desvinculados (perdendo acesso ao sistema até serem realocados por um Administrador), e a unidade deixa de aparecer como opção em novos roteiros de tramitação, mas permanece no histórico de processos já tramitados

* **US 8.2:** Como Administrador, eu quero cadastrar tipos de processo e definir seus roteiros de tramitação para que o sistema conduza cada processo pelo caminho correto.
  * **Critérios de Aceitação:**
    * *Cenário 1: Definição de roteiro de tramitação*
      * **Dado** que estou autenticado como Administrador
      * **Quando** crio ou edito um tipo de processo (ex.: "Licitação") e defino a sequência de unidades: COFIN → AJUR → DIRAD
      * **Então** todos os processos criados com esse tipo seguirão esse roteiro obrigatório, e as unidades de destino aparecerão como opções durante o despacho
    * *Cenário 2: Alteração de roteiro já em uso*
      * **Dado** que existem processos em andamento do tipo "Licitação"
      * **Quando** altero o roteiro do tipo "Licitação"
      * **Então** o novo roteiro se aplica apenas a novos processos criados após a alteração; processos em andamento mantêm o roteiro vigente no momento de sua criação
    * *Cenário 3: Tipo de processo com roteiro vazio*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento criar um tipo de processo sem adicionar nenhuma unidade ao roteiro de tramitação
      * **Então** o sistema exibe "O roteiro deve conter ao menos uma unidade" e não conclui a criação
    * *Cenário 4: Tipo de processo com nome duplicado*
      * **Dado** que já existe um tipo de processo chamado "Licitação"
      * **Quando** tento criar outro tipo de processo com o mesmo nome "Licitação"
      * **Então** o sistema exibe "Já existe um tipo de processo com este nome" e não conclui a criação

* **US 8.3:** Como Administrador, eu quero conceder e revogar permissão de auditoria a usuários específicos para que auditores autorizados possam acessar processos sigilosos conforme as regras de auditoria.
  * **Critérios de Aceitação:**
    * *Cenário 1: Concessão de permissão de auditoria*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso um usuário existente e aciono "Conceder Permissão de Auditoria"
      * **Então** o usuário passa a ter o perfil de Auditor associado à sua conta, podendo visualizar qualquer processo do sistema (inclusive sigilosos) e gerar relatórios consolidados
    * *Cenário 2: Revogação de permissão de auditoria*
      * **Dado** que um usuário possui permissão de auditoria ativa
      * **Quando** eu, Administrador, aciono "Revogar Permissão de Auditoria" sobre esse usuário
      * **Então** a permissão de auditoria é removida, o usuário perde o acesso a processos sigilosos e à geração de relatórios consolidados, e a revogação é registrada em log de auditoria do sistema

* **US 8.4:** Como Administrador, eu quero desativar usuários para revogar acesso ao sistema quando necessário.
  * **Critérios de Aceitação:**
    * *Cenário 1: Desativação de usuário sem processos pendentes*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso um usuário ativo que não possui processos sob sua responsabilidade e aciono "Desativar Usuário"
      * **Então** o usuário é marcado como inativo, não consegue mais fazer login, e seu status é registrado no sistema
    * *Cenário 2: Desativação de usuário com processos pendentes*
      * **Dado** que estou autenticado como Administrador
      * **Quando** tento desativar um usuário que possui processos em andamento sob sua responsabilidade
      * **Então** o sistema exibe "Este usuário possui X processo(s) em andamento. Reatribua os processos antes de desativar." e a desativação não é concluída

* **US 8.5:** Como Administrador, eu quero configurar os parâmetros operacionais do sistema para adequá-lo às políticas do órgão.
  * **Critérios de Aceitação:**
    * *Cenário 1: Configuração do prazo de arquivamento*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso "Configurações do Sistema" e altero o prazo de arquivamento de 30 para 60 dias
      * **Então** o novo prazo se aplica apenas a processos concluídos a partir desta data; processos já concluídos mantêm o prazo vigente no momento da conclusão. O sistema exibe mensagem de confirmação: "Novo prazo de arquivamento configurado: 60 dias. Este prazo se aplica apenas a processos concluídos a partir de hoje."
    * *Cenário 2: Configuração do timeout de sessão*
      * **Dado** que estou autenticado como Administrador
      * **Quando** altero o tempo de inatividade de 30 para 60 minutos
      * **Então** a nova configuração passa a valer imediatamente para todas as novas sessões. Sessões já ativas mantêm o timeout original até o próximo login.
    * *Cenário 3: Valor inválido*
      * **Dado** que estou na tela de configurações
      * **Quando** informo um valor negativo ou zero para qualquer parâmetro
      * **Então** o sistema exibe "O valor deve ser um número inteiro positivo" e não salva a configuração.
    * *Cenário 4: Configuração de thresholds operacionais adicionais*
      * **Dado** que estou autenticado como Administrador e acesso "Configurações do Sistema"
      * **Quando** altero qualquer um dos parâmetros operacionais listados abaixo
      * **Então** o sistema valida o valor informado (deve ser um número inteiro positivo), salva a configuração, exibe mensagem de confirmação e aplica o novo valor a novos eventos a partir da data da alteração (não retroativo, exceto quando explicitamente especificado o contrário na US correspondente)
  * **Parâmetros configuráveis via interface de administração:**
    * Prazo de arquivamento de processos concluídos (padrão: 30 dias) — afeta US 2.5
    * Timeout de sessão por inatividade (padrão: 30 minutos) — afeta US 1.8
    * Prazo para considerar processo "parado" (padrão: 7 dias corridos) — afeta US 6.1
    * Validade do link de primeiro acesso (padrão: 48 horas) — afeta US 1.6
    * Validade do link de recuperação de senha (padrão: 2 horas) — afeta US 1.3
    * Período de retenção de notificações lidas (padrão: 30 dias) — afeta US 5.1
    * Profundidade do histórico de senhas (padrão: 6 últimas senhas) — afeta US 1.7
    * Número máximo de tentativas de login antes do bloqueio (padrão: 3 tentativas) — afeta US 1.3
    * Duração do bloqueio temporário por tentativas excedidas (padrão: 30 minutos) — afeta US 1.3 e US 4.1
    * Dias de antecedência para alerta de prazo (padrão: 2 dias corridos) — afeta US 5.2 e US 5.4

    * *Cenário 5: Configuração de tentativas de login com valor zero*
      * **Dado** que estou na tela de configurações do sistema
      * **Quando** configuro o "Número máximo de tentativas de login antes do bloqueio" com valor 0 (zero)
      * **Então** o sistema exibe "O número máximo de tentativas deve ser no mínimo 1 e no máximo 10" e não salva a configuração
    * *Cenário 6: Configuração de timeout de sessão com valor extremamente baixo*
      * **Dado** que estou na tela de configurações do sistema
      * **Quando** configuro o "Timeout de sessão por inatividade" com valor inferior a 5 minutos
      * **Então** o sistema exibe "O timeout de sessão deve ser no mínimo 5 minutos" e não salva a configuração
    * *Cenário 7: Configuração de profundidade do histórico de senhas com valor excessivo*
      * **Dado** que estou na tela de configurações do sistema
      * **Quando** configuro a "Profundidade do histórico de senhas" com valor 0 (zero)
      * **Então** o sistema exibe "A profundidade do histórico de senhas deve ser no mínimo 3 e no máximo 24" e não salva a configuração. O valor 0 permitiria que o usuário reutilizasse a mesma senha indefinidamente, o que viola a política de segurança.

* **US 8.6:** Como Administrador, eu quero gerenciar o vínculo de servidores às suas unidades para que cada servidor esteja alocado a exatamente uma unidade por vez.
  * **Critérios de Aceitação:**
    * *Cenário 1: Transferência de servidor entre unidades*
      * **Dado** que estou autenticado como Administrador e o servidor João está vinculado à unidade COFIN
      * **Quando** altero a unidade do servidor João de COFIN para AJUR
      * **Então** o vínculo anterior com COFIN é removido, o novo vínculo com AJUR é estabelecido, e o servidor João passa a enxergar apenas processos da unidade AJUR (mantendo seu histórico de atuação na COFIN conforme US 1.4, Cenário 3)
    * *Cenário 2: Tentativa de vínculo duplo como Servidor*
      * **Dado** que o servidor João já está vinculado à unidade COFIN
      * **Quando** tento adicioná-lo também à unidade AJUR mantendo o perfil de Servidor
      * **Então** o sistema rejeita a operação e exibe "Servidores só podem estar vinculados a uma unidade por vez. Para transferir o servidor, altere a unidade atual."

* **US 8.6b:** Como Administrador, eu quero definir quais unidades um Gestor gerencia para que ele tenha visibilidade adequada à sua responsabilidade.
  * **Critérios de Aceitação:**
    * *Cenário 1: Vinculação de Gestor a múltiplas unidades*
      * **Dado** que estou autenticado como Administrador e o usuário Maria possui perfil de Gestor
      * **Quando** acesso os dados de Maria e seleciono as unidades COFIN, AJUR e DIRAD como unidades gerenciadas
      * **Então** Maria passa a visualizar o Kanban consolidado (US 2.8) e o Dashboard (US 6.1) com dados das três unidades, e pode cadastrar usuários (US 1.2) em qualquer uma delas
    * *Cenário 2: Gestor com apenas uma unidade*
      * **Dado** que estou autenticado como Administrador
      * **Quando** cadastro ou edito um usuário com perfil de Gestor e seleciono apenas uma unidade gerenciada
      * **Então** o sistema aceita a configuração (um Gestor pode gerenciar uma ou mais unidades)

* **US 8.7:** Como Administrador, eu quero restaurar documentos que foram removidos por engano (soft delete) para recuperar informações excluídas indevidamente.
  * **Critérios de Aceitação:**
    * *Cenário 1: Restauração de documento dentro do período de retenção*
      * **Dado** que um documento foi removido (soft delete) de um processo há menos de 30 dias e estou autenticado como Administrador
      * **Quando** acesso a área de "Documentos Removidos" no menu de administração, localizo o documento e aciono "Restaurar"
      * **Então** o documento volta a aparecer na lista de anexos do processo de origem, a restauração é registrada no histórico do processo com data, hora e Administrador responsável, e o documento é removido da área de retenção
    * *Cenário 2: Tentativa de restauração após expiração do prazo de retenção*
      * **Dado** que um documento foi removido (soft delete) há mais de 30 dias
      * **Quando** acesso a área de "Documentos Removidos"
      * **Então** o documento não aparece mais na listagem (foi excluído permanentemente), e o sistema exibe no rodapé da tela: "Documentos removidos há mais de 30 dias são excluídos permanentemente e não podem ser restaurados"
    * *Cenário 3: Área de retenção vazia*
      * **Dado** que estou autenticado como Administrador e não há documentos em período de retenção
      * **Quando** acesso a área de "Documentos Removidos"
      * **Então** visualizo a mensagem "Nenhum documento em período de retenção"

### Épico 9: Auditoria e Relatórios Avançados

* **US 9.1:** Como Auditor, eu quero visualizar qualquer processo do sistema mediante autorização para rastrear a cadeia completa de tramitação e decisões.
  * **Critérios de Aceitação:**
    * *Cenário 1: Acesso autorizado a processo de qualquer unidade*
      * **Dado** que sou Auditor autenticado com permissão de auditoria concedida pelo Administrador
      * **Quando** acesso um processo de qualquer unidade, inclusive restritos ou sigilosos
      * **Então** visualizo o processo completo, incluindo histórico de tramitação, todos os documentos anexados e respectivas assinaturas digitais
    * *Cenário 2: Acesso negado por falta de permissão*
      * **Dado** que sou Auditor autenticado sem permissão explícita de auditoria
      * **Quando** tento acessar um processo sigiloso
      * **Então** o sistema exibe a mensagem "Acesso restrito — solicite autorização ao Administrador"

* **US 9.2:** Como Auditor, eu quero extrair relatórios consolidados de tramitação para subsidiar fiscalizações e prestações de contas.
  * **Critérios de Aceitação:**
    * *Cenário 1: Geração de relatório com filtros*
      * **Dado** que sou Auditor autenticado com permissão de auditoria
      * **Quando** solicito um relatório filtrando por período, unidade ou tipo de processo
      * **Então** o sistema exibe em tela um relatório consolidado contendo: total de processos no período, tempo médio de tramitação, lista de processos com status atual e unidade atual. O relatório é visualizado na própria interface. A exportação em PDF estará disponível em versão futura.
    * *Cenário 2: Relatório sem dados para os filtros informados*
      * **Dado** que sou Auditor autenticado
      * **Quando** solicito um relatório com filtros que não retornam resultados
      * **Então** o sistema exibe a mensagem "Nenhum dado encontrado para os filtros informados"

### Épico 10: Conformidade LGPD e Privacidade

* **US 10.1:** Como Cidadão / Titular de Dados, eu quero solicitar a exclusão ou anonimização dos meus dados pessoais dos processos para exercer meus direitos previstos na LGPD.
  * **Critérios de Aceitação:**
    * *Cenário 1: Solicitação de exclusão com dados válidos*
      * **Dado** que sou um titular de dados pessoais (ou meu representante legal) e possuo o número do processo e meus dados de identificação
      * **Quando** acesso o canal de solicitação (página pública, sem autenticação) e preencho: número do processo, meu nome completo, CPF, e-mail para resposta, tipo de solicitação ("Exclusão de dados" ou "Anonimização de dados") e anexo documento de identificação com foto
      * **Então** o sistema registra a solicitação com um número de protocolo, exibe "Solicitação registrada com sucesso. Protocolo: XXXX. Você receberá a resposta no e-mail informado em até 15 dias." e envia um e-mail de confirmação ao solicitante com o número de protocolo
    * *Cenário 2: Campos obrigatórios não preenchidos*
      * **Dado** que estou preenchendo o formulário de solicitação LGPD
      * **Quando** tento enviar sem preencher nome, CPF, número do processo ou e-mail
      * **Então** o sistema destaca os campos obrigatórios e exibe "Preencha todos os campos obrigatórios"
    * *Cenário 3: Documento de identificação com formato inválido*
      * **Dado** que estou preenchendo o formulário de solicitação LGPD
      * **Quando** anexo um arquivo que não é PDF, JPG ou PNG
      * **Então** o sistema exibe "Formato de arquivo não permitido. Anexe documento de identificação nos formatos PDF, JPG ou PNG."
    * *Cenário 4: Número de processo inexistente*
      * **Dado** que estou preenchendo o formulário
      * **Quando** informo um número de processo que não existe na base
      * **Então** o sistema exibe "Nenhum processo encontrado com o número informado. Verifique o número e tente novamente."

* **US 10.2:** Como Administrador, eu quero gerenciar as solicitações LGPD recebidas para processar os pedidos dos titulares de dados.
  * **Critérios de Aceitação:**
    * *Cenário 1: Visualização da fila de solicitações*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso "Solicitações LGPD" no menu de administração
      * **Então** visualizo a lista de solicitações com: número do protocolo, data, nome do solicitante, número do processo, tipo de solicitação e status (Pendente / Em análise / Atendida / Rejeitada)
    * *Cenário 2: Processamento de solicitação de exclusão*
      * **Dado** que uma solicitação LGPD está com status "Pendente" e o tipo é "Exclusão de dados"
      * **Quando** valido a identidade do solicitante e aciono "Atender Solicitação"
      * **Então** o sistema anonimiza os dados pessoais do titular no processo indicado (substitui CPF/CNPJ por identificador anonimizado irreversível, sem possibilidade de reversão ao dado original, e nome do interessado por "Titular Anonimizado") e envia e-mail automático ao solicitante informando a conclusão
    * *Cenário 3: Rejeição de solicitação*
      * **Dado** que uma solicitação LGPD está em análise e o Administrador identifica que o solicitante não é o titular dos dados
      * **Quando** aciono "Rejeitar Solicitação" e preencho a justificativa
      * **Então** o status muda para "Rejeitada" e um e-mail é enviado ao solicitante informando a decisão com a justificativa

* **US 10.3:** Como Sistema, eu devo anonimizar automaticamente dados pessoais de processos arquivados após o prazo legal para garantir conformidade contínua com a LGPD.
  * **Critérios de Aceitação:**
    * *Cenário 1: Anonimização automática após prazo legal*
      * **Dado** que um processo está arquivado há 5 anos (prazo legal configurado para o tipo de processo)
      * **Quando** a rotina trimestral de anonimização é executada
      * **Então** todos os dados pessoais de interessados (nome completo, CPF, CNPJ, endereço) são substituídos por identificadores anonimizados, sem possibilidade técnica de recuperação do dado original, mantendo-se o número do processo, datas, unidades, status e histórico de tramitação íntegros. O evento é registrado em log de conformidade.
    * *Cenário 2: Configuração do prazo de anonimização por tipo de processo*
      * **Dado** que estou autenticado como Administrador
      * **Quando** acesso as configurações de um tipo de processo e defino o prazo de anonimização LGPD em 5 anos
      * **Então** o sistema registra a configuração e exibe "Prazo de anonimização configurado: 5 anos. A partir desta data, processos deste tipo serão anonimizados após 5 anos de arquivamento."

## 5. Requisitos Funcionais

1. O sistema deve permitir autenticação por login e senha próprios do SETES.DOCS
2. O sistema deve suportar três perfis de acesso: Administrador, Gestor e Servidor
3. Cada Servidor deve pertencer a exatamente uma unidade administrativa. Gestores e Administradores podem estar vinculados a uma ou mais unidades
4. Servidores só podem visualizar e movimentar processos de suas próprias unidades
5. Gestores podem visualizar processos de todas as unidades que gerenciam e cadastrar usuários em suas unidades
6. Administradores têm acesso irrestrito a todos os processos, unidades e configurações do sistema
7. O sistema deve gerar automaticamente um número único sequencial para cada processo criado
8. Cada tipo de processo deve ter um roteiro de tramitação predefinido (sequência ordenada de unidades)
9. O envio de um processo para a próxima unidade do roteiro deve ser feito pelo servidor da unidade atual por meio da ação "Despachar"
10. O sistema deve alterar automaticamente o status do processo conforme seu avanço: "Aberto" ao ser criado, "Em Tramitação" ao ser despachado pela primeira vez, "Concluído" ao chegar à última unidade do roteiro e ser despachado
11. O quadro Kanban deve exibir os processos agrupados por status (Aberto, Em Tramitação, Concluído, Arquivado)
12. Processos concluídos devem ser arquivados automaticamente após um número configurável de dias (padrão: 30)
13. O sistema deve permitir upload de documentos nos formatos PDF, DOC, DOCX, JPG e PNG com tamanho máximo de 20 MB por arquivo
14. Documentos anexados devem ser armazenados no próprio sistema e vinculados ao processo
15. O sistema deve permitir visualização inline (no navegador) de documentos PDF e imagens
16. *(FASE 2 — Épico 4, fora do MVP)* O sistema deve permitir assinatura digital de documentos utilizando certificado ICP-Brasil (e-CPF/e-CNPJ)
17. *(FASE 2 — Épico 4, fora do MVP)* O sistema deve verificar a validade do certificado digital (data de expiração, revogação) antes de aplicar a assinatura
18. *(FASE 2 — Épico 4, fora do MVP)* O sistema deve permitir múltiplas assinaturas (coassinatura) no mesmo documento
19. O sistema deve gerar notificações internas (ícone no menu) para eventos como recebimento de novo processo
20. O sistema deve enviar e-mails de notificação para novo processo recebido e alerta de prazo próximo ao vencimento
21. O dashboard de gestão deve exibir: total de processos ativos, tempo médio de tramitação, processos parados e produtividade por unidade
22. A consulta pública deve permitir pesquisa de processos por número, assunto, tipo de processo e período, sem exigir autenticação
23. Processos marcados como sigilosos não devem aparecer nos resultados da consulta pública
24. O perfil do usuário deve exibir a relação de processos em que atuou e documentos assinados
25. Toda movimentação de processo deve ser registrada em histórico imutável com: data, hora, unidade de origem, unidade de destino, servidor responsável e ação realizada
26. O sistema deve permitir ao Administrador cadastrar, editar e desativar unidades e tipos de processo
27. O sistema deve permitir que usuários com perfil de Auditor visualizem qualquer processo do sistema, inclusive restritos ou sigilosos, mediante autorização do Administrador
28. O sistema deve permitir que usuários com perfil de Auditor gerem relatórios consolidados de tramitação filtrando por período, unidade ou tipo de processo
29. O sistema deve exigir que usuários recém-cadastrados criem sua própria senha no primeiro acesso, por meio de link enviado ao e-mail cadastrado com validade de 48 horas
30. O sistema deve permitir que usuários autenticados alterem sua própria senha a qualquer momento
31. O sistema deve encerrar automaticamente sessões após 30 minutos de inatividade do usuário
32. O sistema deve permitir busca e filtro interno de processos por número, assunto e período para usuários autenticados
33. O sistema deve permitir ao Administrador desativar usuários, impedindo seu acesso ao sistema
34. O sistema deve permitir ao servidor da unidade atual devolver um processo para a unidade anterior do roteiro, mediante seleção de motivo predefinido e justificativa opcional
35. O sistema deve permitir ao Administrador configurar parâmetros operacionais (prazo de arquivamento, timeout de sessão) via interface de administração, sem necessidade de intervenção no código-fonte
36. Dados pessoais de interessados (CPF/CNPJ) não devem ser exibidos na consulta pública; apenas o nome do interessado será visível ao cidadão
37. O sistema deve disponibilizar canal de solicitação para que titulares de dados pessoais requeiram a exclusão ou anonimização de seus dados, em conformidade com a LGPD
38. Dados pessoais de processos arquivados devem ser mantidos pelo prazo legal aplicável; após esse prazo, o sistema deve anonimizar ou excluir os dados pessoais automaticamente
39. O sistema deve permitir que um mesmo usuário mantenha múltiplas sessões ativas simultaneamente em dispositivos diferentes, com expiração independente por inatividade (US 1.9)
40. O sistema deve permitir ao Gestor visualizar um quadro Kanban consolidado com os processos de todas as unidades que gerencia, com filtro por unidade (US 2.8)
41. *(FASE 2 — Épico 4, fora do MVP)* O sistema deve permitir a verificação de integridade e validade de documentos assinados digitalmente, exibindo signatário, data, autoridade certificadora e status da assinatura (US 4.2)
42. O sistema deve gerar notificação interna quando um processo da unidade do usuário é concluído (US 5.3)
43. O sistema deve gerar notificação interna de alerta quando um processo da unidade do usuário está com prazo a vencer em 2 dias corridos ou menos (US 5.4)
44. O sistema deve permitir ao Administrador gerenciar solicitações LGPD recebidas, processando pedidos de exclusão ou anonimização de dados pessoais (US 10.2)

## 6. Requisitos Não Funcionais

* **Segurança:** Todas as senhas devem ser armazenadas com hash criptográfico e nunca em texto plano. A comunicação entre o navegador e o servidor deve ser criptografada (HTTPS). *(FASE 2 — Épico 4, fora do MVP)* As assinaturas digitais devem seguir os padrões e algoritmos criptográficos vigentes da ICP-Brasil (MP 2.200-2/2001 e normas correlatas). O histórico de tramitação deve ser imutável e à prova de adulteração. **Proteção contra Abuso:** A consulta pública deve implementar limite de requisições por endereço IP de no máximo 60 consultas por minuto. Ao exceder o limite, o sistema deve retornar a mensagem "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente." e liberar o acesso automaticamente após 60 segundos. Este mecanismo visa prevenir scraping massivo sem prejudicar o uso legítimo do cidadão.
* **Disponibilidade:** O sistema deve estar disponível 24 horas por dia, 7 dias por semana, com tolerância a janelas de manutenção programada de até 2 horas mensais fora do horário comercial.
* **Performance:** O quadro Kanban deve carregar em até 3 segundos para unidades com até 500 processos ativos. Para unidades com mais de 500 processos ativos, o sistema deve implementar paginação automática (50 cards por página) mantendo o tempo de carregamento abaixo de 3 segundos. A consulta pública deve retornar resultados paginados (20 resultados por página) em até 5 segundos. O upload de documentos de até 20 MB deve ser concluído em até 30 segundos em conexões de banda larga padrão.
* **Usabilidade:** A interface deve ser responsiva, permitindo o uso por navegadores de desktop e dispositivos móveis. O sistema deve seguir os padrões visuais definidos pelo cliente nas telas de referência. As ações mais frequentes (despachar processo, anexar documento) devem ser acessíveis em no máximo dois cliques a partir da tela principal.
* **Conformidade Legal:** O sistema deve estar em conformidade com a Lei Geral de Proteção de Dados (LGPD) no tratamento de dados pessoais de servidores, interessados e cidadãos. *(FASE 2 — Épico 4, fora do MVP)* As assinaturas digitais devem atender aos requisitos da MP 2.200-2/2001 e normas da ICP-Brasil. Os registros de tramitação devem atender aos requisitos de auditoria para órgãos públicos.
* **Escalabilidade:** A arquitetura deve suportar o crescimento gradual de usuários e processos sem degradação significativa, comportando no MVP até 500 usuários ativos e 10.000 processos simultâneos.
* **Manutenibilidade:** A configuração de unidades, tipos de processo, roteiros e prazos de arquivamento deve ser dinâmica (via interface de administração), sem necessidade de intervenção no código-fonte.

## 7. Métricas de Sucesso

As seguintes métricas serão acompanhadas após o lançamento do MVP para avaliar se o SETES.DOCS está entregando valor ao negócio:

* **Adoção do Sistema:** 80% dos servidores das unidades cadastradas utilizando o sistema ativamente (realizando ao menos uma ação por semana) em até 3 meses após o lançamento
* **Redução do Tempo de Tramitação:** Redução de pelo menos 30% no tempo médio entre a criação e a conclusão de um processo, comparado ao método anterior (papel/e-mail), medido após 6 meses de operação
* **Eliminação de Processos Perdidos:** Zero processos com status desconhecido ou localização ignorada após a implantação — todo processo deve estar localizável via consulta pública ou interna a qualquer momento
* **Eficiência Operacional:** Redução de 50% no volume de consultas presenciais ou telefônicas sobre andamento de processos, uma vez que a consulta pública supre essa demanda
* **Integridade Documental:** 100% dos documentos tramitados devem manter sua integridade comprovável por meio de assinatura digital, com zero incidentes de extravio ou adulteração documental
