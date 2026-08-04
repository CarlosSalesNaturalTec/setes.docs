# modelos-documento

## Purpose

Catálogo de **Modelos de documento** — textos pré-formatados com lacunas,
mantidos pelo Administrador — que o servidor escolhe e completa na abertura de
um processo, em vez de redigir cada requerimento, ofício ou memorando do
início. O documento resultante é gerado em PDF e anexado ao processo pelo
mesmo pipeline dos anexos enviados por upload (ver capability
`gestao-documental`), registrando o modelo que o originou (Épico 2, US 2.1;
Épico 3).

## Requirements

### Requirement: Catálogo de modelos de documento
O sistema SHALL manter um catálogo de **Modelos de documento**, cada um com **nome**, **categoria** (texto livre), **tipo** (um entre: requerimento, ofício, memorando, despacho, parecer, nota técnica, relatório, ata, contrato, outro), **descrição** opcional, **conteúdo formatado** e situação (ativo/inativo). O cadastro, a edição e a desativação SHALL ser restritos ao perfil Administrador; a **leitura** do catálogo SHALL ser disponível a Servidor e Gestor, que precisam escolher modelos na abertura de processo. Modelos NÃO SHALL ser excluídos fisicamente, apenas desativados — documentos já gerados mantêm referência ao modelo que os originou.

#### Scenario: Cadastro de modelo
- **DADO** que estou autenticado como Administrador
- **QUANDO** cadastro um modelo com nome "Requerimento padrão", categoria "Pessoal", tipo "requerimento", descrição e conteúdo formatado
- **ENTÃO** o modelo é criado como ativo e passa a constar no catálogo disponível para escolha

#### Scenario: Modelo desativado sai do catálogo de escolha
- **DADO** que o modelo "Requerimento padrão" está ativo e foi usado em processos anteriores
- **QUANDO** o desativo
- **ENTÃO** ele deixa de aparecer entre os modelos selecionáveis na abertura de processo, e os documentos já gerados a partir dele permanecem intactos e acessíveis

#### Scenario: Modelo não pode ser excluído
- **DADO** que existe um modelo cadastrado
- **QUANDO** consulto as ações disponíveis na interface e na API
- **ENTÃO** não há nenhuma ação de exclusão — apenas editar, desativar e reativar

#### Scenario: Leitura do catálogo por Servidor
- **DADO** que estou autenticado como Servidor
- **QUANDO** consulto o catálogo de modelos ativos
- **ENTÃO** a listagem é retornada, permitindo escolher um modelo na abertura de processo

#### Scenario: Escrita no catálogo por não-Administrador — acesso negado
- **DADO** que estou autenticado como Servidor ou como Gestor
- **QUANDO** tento criar, editar, desativar ou reativar um modelo
- **ENTÃO** o sistema rejeita a operação com "Acesso negado — você não tem permissão para esta operação", nenhum modelo é alterado, e a tentativa é registrada em log de segurança

### Requirement: Conteúdo formatado do modelo com sanitização
O sistema SHALL permitir que o conteúdo do modelo seja texto **formatado**, limitado a **negrito, itálico, sublinhado, alinhamento e listas**. O conteúdo SHALL ser **sanitizado no backend** contra uma whitelist estrita de marcação, descartando qualquer outra tag ou atributo, tanto na gravação do modelo quanto na geração de documento. A restrição aplicada pelo editor da interface é conveniência de uso e NÃO SHALL ser tratada como fronteira de segurança. Modelos NÃO SHALL conter dados pessoais reais — apenas marcações de lacuna a serem preenchidas no momento do uso.

#### Scenario: Formatação permitida é preservada
- **DADO** que redijo um modelo com trechos em negrito, um parágrafo centralizado e uma lista
- **QUANDO** salvo o modelo e o reabro
- **ENTÃO** negrito, alinhamento e lista são preservados exatamente como redigidos

#### Scenario: Marcação maliciosa é descartada
- **DADO** que um conteúdo de modelo contendo `<script>`, atributos de evento ou tags fora da whitelist é enviado diretamente à API
- **QUANDO** o modelo é salvo
- **ENTÃO** a marcação não permitida é removida silenciosamente, e o conteúdo persistido contém apenas as tags da whitelist

#### Scenario: Modelo aberto por outro usuário não executa script
- **DADO** que um modelo foi gravado por meio de requisição direta contendo marcação maliciosa
- **QUANDO** outro servidor abre esse modelo no editor
- **ENTÃO** nenhum script é executado — o conteúdo armazenado já está sanitizado

### Requirement: Lacunas preenchidas manualmente pelo servidor
O sistema SHALL tratar as **lacunas** dos modelos como convenção textual — marcações visuais escritas no próprio conteúdo — e NÃO SHALL implementar campos estruturados, variáveis substituíveis ou formulário gerado a partir do modelo. O servidor SHALL editar o texto livremente para substituir as lacunas pelas informações reais do caso. O sistema NÃO SHALL bloquear a geração de um documento cujas lacunas não tenham sido preenchidas, mas SHALL destacá-las visualmente no editor enquanto existirem, como lembrete.

#### Scenario: Edição livre do texto do modelo
- **DADO** que escolhi um modelo cujo conteúdo contém a lacuna "[NOME DO SOLICITANTE]"
- **QUANDO** substituo essa marcação pelo nome real do interessado e complemento outros trechos do texto
- **ENTÃO** o texto editado é aceito integralmente, sem qualquer validação de estrutura ou de campos obrigatórios do modelo

#### Scenario: Lacuna pendente é destacada mas não bloqueia
- **DADO** que editei o texto do modelo mas deixei uma lacuna sem preencher
- **QUANDO** salvo o documento
- **ENTÃO** o editor destacou a lacuna como lembrete, e a geração é concluída normalmente — o texto é gravado tal como está

### Requirement: Geração de documento de processo a partir de modelo
O sistema SHALL permitir que, na abertura de um processo, o servidor escolha um modelo **ativo**, edite seu texto e o salve como **documento do processo**. O texto editado SHALL ser sanitizado e **renderizado em PDF**, e o arquivo resultante SHALL ser anexado ao processo pelo mesmo pipeline dos anexos enviados por upload — mesma validação de formato, mesma verificação de assinatura binária, mesmo armazenamento, mesmo cálculo de integridade. O documento gerado SHALL registrar o **modelo que o originou**. A criação de processo **sem** modelo SHALL permanecer disponível e inalterada. A geração SHALL respeitar a autorização por unidade já existente para anexar documentos.

#### Scenario: Documento gerado a partir de modelo
- **DADO** que estou criando um processo e escolhi o modelo "Requerimento padrão"
- **QUANDO** substituo as lacunas e salvo
- **ENTÃO** um documento em PDF é gerado e anexado ao processo, aparecendo na lista de anexos com nome de exibição próprio e disponível para download

#### Scenario: Criação de processo sem modelo continua disponível
- **DADO** que estou criando um processo
- **QUANDO** opto por digitar apenas o assunto, sem escolher modelo algum
- **ENTÃO** o processo é criado normalmente, sem nenhum documento gerado — o uso de modelo é opcional

#### Scenario: Proveniência do modelo é registrada
- **DADO** que um documento foi gerado a partir do modelo "Requerimento padrão"
- **QUANDO** consulto a proveniência desse documento
- **ENTÃO** o modelo de origem está registrado, permitindo auditar quais modelos estão em uso

#### Scenario: Modelo inativo não pode originar documento
- **DADO** que o modelo "Requerimento padrão" foi desativado
- **QUANDO** tento gerar um documento a partir dele por requisição direta
- **ENTÃO** o sistema rejeita a operação informando que o modelo não está disponível

#### Scenario: Geração em processo de outra unidade — acesso negado
- **DADO** que estou autenticado como Servidor da unidade COFIN
- **QUANDO** tento gerar um documento em um processo que está na unidade DIRAD
- **ENTÃO** o sistema rejeita a operação com "Acesso negado — você não tem permissão para visualizar este processo", nenhum documento é criado, e a tentativa é registrada em log de segurança

### Requirement: Administração do catálogo de modelos organizada em abas

A tela de administração do catálogo de modelos de documento SHALL ser organizada em
duas abas: **"Novo modelo"**, contendo a ficha de cadastro, e **"Modelos
cadastrados"**, contendo os filtros e a listagem do catálogo. A aba ativa SHALL ser
refletida na URL, de modo que a recarga da página e o compartilhamento do endereço
preservem a aba escolhida; um valor ausente ou inválido SHALL recair na aba padrão,
sem mensagem de erro. A navegação entre abas SHALL ser acessível por teclado.

Após o cadastro bem-sucedido de um modelo, o sistema SHALL alternar para a aba
"Modelos cadastrados", de modo que o modelo recém-criado seja visível na listagem —
o resultado da ação SHALL ser observável sem que o usuário precise navegar
manualmente.

A reorganização é **exclusivamente de apresentação**: os campos da ficha, as regras
de validação, os filtros disponíveis, as ações por modelo (editar, desativar,
reativar) e a restrição de acesso ao perfil Administrador permanecem inalterados.

#### Scenario: Navegação entre as abas

- **DADO** que estou autenticado como Administrador e acesso a tela de modelos de
  documento
- **QUANDO** a tela é carregada
- **ENTÃO** vejo as duas abas com a aba padrão ativa; ao selecionar a outra aba, o
  conteúdo correspondente é exibido sem que a página seja recarregada

#### Scenario: Aba ativa preservada na recarga

- **DADO** que selecionei a aba "Modelos cadastrados"
- **QUANDO** recarrego a página ou abro novamente o mesmo endereço
- **ENTÃO** a aba "Modelos cadastrados" continua ativa

#### Scenario: Endereço inválido recai na aba padrão

- **DADO** que acesso a tela de modelos com um identificador de aba desconhecido no
  endereço
- **QUANDO** a página é carregada
- **ENTÃO** a aba padrão é exibida, sem mensagem de erro

#### Scenario: Cadastro bem-sucedido leva à listagem

- **DADO** que estou na aba "Novo modelo" com a ficha preenchida validamente
- **QUANDO** confirmo o cadastro e ele é aceito
- **ENTÃO** a aba "Modelos cadastrados" passa a ser a ativa e o modelo recém-criado
  consta na listagem
- **E** a ficha de cadastro é reiniciada, sem reter o conteúdo enviado

#### Scenario: Cadastro rejeitado permanece na ficha

- **DADO** que estou na aba "Novo modelo" e o cadastro é rejeitado pelo backend
- **QUANDO** o erro é retornado
- **ENTÃO** permaneço na aba "Novo modelo" com os dados preenchidos preservados e a
  mensagem de erro visível, sem alternância de aba

#### Scenario: Filtros continuam operando na aba de listagem

- **DADO** que estou na aba "Modelos cadastrados"
- **QUANDO** aplico os filtros de tipo e de situação
- **ENTÃO** a listagem é filtrada exatamente como antes da reorganização em abas

#### Scenario: Navegação por teclado entre abas

- **DADO** que o foco está sobre a lista de abas
- **QUANDO** navego com as setas esquerda e direita e ativo uma aba com Enter ou
  Espaço
- **ENTÃO** a aba correspondente é ativada, o foco permanece visível e não fica preso
  em nenhum elemento

#### Scenario: Acesso por não-Administrador continua negado

- **DADO** que estou autenticado como Servidor ou como Gestor
- **QUANDO** acesso a rota de administração de modelos
- **ENTÃO** o acesso é negado exatamente como antes da reorganização, sem que
  nenhuma das abas seja renderizada
