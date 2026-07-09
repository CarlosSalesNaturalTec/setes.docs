# SETES.DOCS

## Apreentação

O **SETES.DOCS** é um **Sistema Eletrônico de Gestão de Processos** desenhado para centralizar, monitorar e otimizar o fluxo de documentos e tarefas dentro de uma organização.

Abaixo, apresento um resumo executivo das suas funcionalidades, estruturado conforme o levantamento técnico realizado:

---

### 1. Visão Geral do Sistema

O sistema atua como uma plataforma de *workflow* administrativo. Seu objetivo central é garantir visibilidade sobre o ciclo de vida de cada processo — desde a sua abertura até o arquivamento — permitindo que gestores e usuários acompanhem prazos, responsáveis e gargalos operacionais em tempo real.

### 2. Funcionalidades Principais

* **Painel de Controle (Dashboard):** A "central de comando" do sistema. Oferece uma visão macro através de indicadores (KPIs) de performance, gráficos de produtividade por unidade e usuário, além de um alerta crítico para "Processos Parados", facilitando a tomada de decisão rápida.
* **Gestão de Processos (Fluxo de Trabalho):** Interface robusta para a criação e movimentação de processos. Suporta classificação por tipos (ex: Licitação, Administrativo) e níveis de acesso, garantindo controle sobre a informação.
* **Consulta Pública:** Transparência operacional. Permite que cidadãos ou partes interessadas consultem o status e detalhes de processos públicos sem a necessidade de autenticação no sistema.
* **Relatórios e Inteligência de Dados:** Ferramenta analítica que permite extrair métricas detalhadas (tempo médio, gargalos, volume por setor), essencial para a auditoria e melhoria contínua dos processos internos.
* **Gestão de Perfil:** Área dedicada à transparência individual, onde o usuário logado pode auditar suas próprias ações, documentos assinados e histórico de produtividade.

### 3. Pilares Estratégicos

* **Monitoramento e Alerta:** Identificação automática de processos inativos (atrasos), permitindo intervenções tempestivas.
* **Organização e Padronização:** Estrutura de dados que facilita a organização por unidades, tipos e níveis, mantendo a padronização necessária para o serviço público/corporativo.
* **Interface Centrada no Usuário:** O sistema utiliza uma arquitetura visual limpa e intuitiva, com foco em *UX (User Experience)* para reduzir a curva de aprendizado dos colaboradores.


### 4. Estrutura de Layout (Layout Base)

* **Cabeçalho (Header):**
* **Logo/Título:** "SETES.DOCS - SISTEMA ELETRÔNICO" à esquerda.
* **Navegação:** Menu horizontal com os itens: `[Painel]`, `[Processos]`, `[Novo Processo]`, `[Consulta Pública]`, `[Relatórios]`,  `[Meu Perfil]`.
* **Ação de Saída:** Botão `[Sair]` à direita.
* **Identificação do Usuário:** Nome do usuário logado: Exemplo: "Carlos Sales".


* **Corpo da Página:** Container principal centralizado, com cards organizados em grade (grid).
---

## Painel de Controle
Uma ferramenta de gestão eletrônica de processos. As principais funcionalidades são:

### Gestão e Monitoramento de Processos

* **Visão Geral:** O painel apresenta indicadores quantitativos sobre o status dos processos, como total de processos, abertos, em tramitação e concluídos.
* **Análise de Desempenho:** Permite visualizar o tempo médio de conclusão de processos e identificar gargalos ativos na tramitação.
* **Monitoramento de Atrasos:** Identifica especificamente "Processos Parados" (aqueles sem movimentação há mais de 5 dias), exibindo o número do processo, o assunto e o tempo de inatividade.

### Relatórios e Filtros

O sistema permite visualizar dados consolidados através de gráficos e métricas divididas por:

* **Unidade:** Processos por setor (ex: Diretoria Administrativa, Coordenação de Gestão de Pessoas).
* **Tipo de Processo:** Classificação por natureza (ex: Contratação, Administrativo, Pessoal, Licitação).
* **Usuário:** Atividade por colaborador (ex: Ricardo Pita).
* **Tramitação:** Relatório geral sobre a movimentação entre unidades.

### 2. Componentes e Funcionalidades (Painel)

#### A. Cards de Indicadores (KPIs)

Uma linha com 4 cards de destaque (estilo *Stat Cards*):

* **Título:** "Total de Processos", "Abertos", "Em Tramitação", "Concluídos".
* **Valor:** Exibição numérica em destaque (fonte grande/negrito).
* **Dados Adicionais:** Abaixo de cada card, exibir métricas secundárias: "Total de Processos" (ex: 4), "Concluídos" (ex: 2), "Tempo Médio Conclusão" (ex: 0h).

#### B. Seção "Relatório de Tramitação"

Container contendo:

* **Resumo Geral:** 3 cards horizontais:
* `# Total de Tramitações` (valor: 4).
* `⏱️ Tempo Médio Geral` (valor: 0min).
* `⚠️ Gargalos Ativos` (valor: 2).


* **Detalhamento de Fluxos:**
* Lista ou tabela simples mostrando "Tempo entre Unidades" (ex: "COFIN → AJUR", 1 tramitação, 0min).


* **Tempo Médio por Unidade:** Lista com o nome da unidade e o tempo médio (ex: "COFIN" - "0min").

#### C. Lista de "Processos Parados"

Tabela ou lista de alertas (estilo *Warning List*):

* **Título:** "Processos Parados (5+ dias sem movimentação)".
* **Colunas:** Número do processo, Descrição do assunto, Tempo de inatividade (ex: 14 dias).
* **Identificação Visual:** Ícone de relógio e destaque em vermelho suave para indicar alerta de atraso.

---

### 3. Especificações Visuais e UX

* **Paleta de Cores:**
* **Primária:** Tom de azul institucional para cabeçalho e ícones de navegação.
* **Alerta/Aviso:** Vermelho (para processos parados e gargalos) e Laranja/Amarelo (para métricas de tempo).
* **Sucesso:** Verde (para tempos de tramitação dentro da normalidade).


* **Estilo:** Design limpo (*Clean UI*), utilizando sombras leves (*box-shadow*) nos cards para criar hierarquia visual e espaçamentos generosos (padding/margin).
* **Interatividade:**
* Links de navegação devem possuir estado *hover*.
* Botões de ação ("Ver todos") devem levar para a página de processos filtrada.


* **Responsividade:** O layout deve utilizar CSS Grid ou Flexbox para garantir que os cards se organizem verticalmente em telas menores (tablets/celulares).

---

### 4. Requisitos de Dados (Backend)

O desenvolvedor precisará de endpoints de API para:

1. `GET /dashboard/stats`: Retornar os totais numéricos (KPIs).
2. `GET /dashboard/tramitacao`: Retornar o relatório de fluxos e tempos médios.
3. `GET /processos/atrasados`: Retornar a lista filtrada de processos com inatividade > 5 dias.

----

## Processos

### 1. Estrutura de Layout (Grid e Componentes)

* **Cabeçalho da Página:** Título "Processos" em destaque (H1).
* **Controles de Exibição:** * À direita do título: Toggle/Switcher para alternar entre visualização de **Lista** (ícone de colunas) e **Kanban/Cards** (ícone de grid).
* Botão de ação principal: `[+ Novo Processo]` (azul escuro, com preenchimento).


* **Barra de Filtros (Filtro Composto):**
* Container cinza claro com bordas arredondadas.
* Input de busca textual (placeholder: "Buscar por protocolo, assunto ou...").
* Selects (dropdowns): `[Todos os Status]`, `[Todos os Níveis]`.
* Botão fixo: `[Documentos]`.
* Botão/Filtro avançado: `[Filtro] Avançados` (ícone de funil).

### 2. Composição do Dashboard (Canvas Kanban)

A página utiliza um layout estilo **Kanban** com quatro colunas verticais principais. Cada coluna é um container (Card Group):

* **Colunas:** "Aberto", "Em Tramitação", "Concluído", "Arquivado".
* **Indicadores:** Cada cabeçalho de coluna possui um "badge" circular no canto superior direito contendo o total de itens (ex: "2").
* **Cards de Processo (Componentes individuais):**
* **Identificador:** Número do processo (ex: `000142.2026/06`) com link.
* **Descrição:** Assunto do processo (ex: "Aquisição de equipamentos...").
* **Tags:** Labels coloridas para Tipo e Nível (ex: "Administrativo" - cinza, "Público" - verde, "Restrito" - laranja).
* **Metadados:** Localização atual (ex: "Coordenação Financeira") e Data (ex: "21/06").


### 3. Especificações Visuais e UX

* **Estilo:** Minimalista. Espaçamento interno (*padding*) confortável entre os elementos.
* **Tipografia:** Fonte sem serifa, legível (padrão *Inter* ou *Roboto*).
* **Cores de Estado:**
* **Aberto:** Fundo de cabeçalho azul claro.
* **Em Tramitação:** Fundo de cabeçalho amarelo/creme.
* **Concluído:** Fundo de cabeçalho verde claro.
* **Arquivado:** Fundo de cabeçalho cinza.


* **Feedback Visual:**
* Quando não há itens (como em "Aberto"), exibir um ícone de pasta vazia (Ghost Icon) e o texto centralizado "Vazio".


### 4. Requisitos de Funcionalidade para o Desenvolvedor

* **Componente de Busca:** Deve realizar a filtragem *real-time* ou via clique no botão de busca.
* **Interatividade (Drag & Drop):** Se a intenção for um Kanban real, as colunas devem permitir arrastar processos entre os status.
* **State Management:** O sistema deve manter o estado dos filtros ativos e da visualização escolhida (Lista vs. Grid) no estado da aplicação.
* **Endpoints Necessários:**
* `GET /api/processos?status={status}`: Para carregar os dados de cada coluna.
* `POST /api/processos/novo`: Disparado pelo botão principal.
* `GET /api/processos/search?query={texto}`: Endpoint para a barra de busca.

---

## Novo Processo

### 1. Estrutura de Layout (Formulário)

* **Cabeçalho:** Título "Novo Processo" (H2) com subtítulo instrutivo "Preencha os dados para iniciar um novo processo".
* **Container:** O formulário deve estar centralizado em um card com bordas arredondadas e um fundo branco limpo, destacando-se sobre o fundo da página.
* **Seção "Dados do Processo":**
* Título da seção em negrito, servindo como divisor visual (usar uma linha horizontal sutil abaixo).


### 2. Campos do Formulário (Inputs)

Abaixo, os campos necessários e seus respectivos tipos de entrada:

| Campo | Tipo | Observações |
| --- | --- | --- |
| **Tipo do Processo** | Dropdown (Select) | Obrigatório. Valores: Administrativo, Contratação, etc. |
| **Nível de Acesso** | Dropdown (Select) | Obrigatório. Padrão: "Público". |
| **Assunto** | Text Input | Obrigatório. Placeholder: "Descreva o assunto do processo". |
| **Descrição** | Textarea | Campo multi-linha para detalhes adicionais. |
| **Unidade de Origem** | Dropdown (Select) | Lista das unidades (ex: COGEP, DIRAD, COFIN). |
| **Interessados** | Text Input | Campo para nome dos interessados. |
| **Prazo Limite** | Date/Time Picker | Campo com máscara de data e hora (`dd/mm/aaaa --:--`). |
| **Observações** | Textarea | Campo para notas complementares. |

---

### 3. Ações e Botões (Footer do Card)

* **Botão [Cancelar]:** Estilo transparente ou com bordas (*outline*), alinhado à esquerda do rodapé.
* **Botão [Criar Processo]:** Estilo sólido (cor principal do sistema), alinhado à direita. Deve ser desabilitado se os campos obrigatórios (*) não estiverem preenchidos (validação de formulário).

---

### 4. Especificações Técnicas e UX

* **Validação (Validation Rules):**
* Implementar validação *client-side* para campos obrigatórios (*Tipo do Processo*, *Nível de Acesso*, *Assunto*).
* Feedback visual (borda vermelha) caso o usuário tente enviar o formulário sem preencher os campos obrigatórios.


* **Responsividade:**
* Em dispositivos móveis, os campos devem ocupar 100% da largura do container em uma única coluna vertical.


* **UX (User Experience):**
* Adicionar um pequeno ícone de ajuda (tooltip) caso haja necessidade de explicar a diferença entre os níveis de acesso (Público, Restrito, Sigiloso).



---

### 5. Requisitos de Backend

* **Endpoint:** `POST /api/processos/criar`
* **Payload Esperado (JSON):**

```json
{
  "tipo": "string",
  "nivel_acesso": "string",
  "assunto": "string",
  "descricao": "string",
  "unidade_origem": "string",
  "interessados": "string",
  "prazo_limite": "datetime",
  "observacoes": "string"
}

```

---

## Consulta Pública

1. Estrutura de Layout
Cabeçalho: Centralizado, com um ícone representativo (um globo dentro de um quadrado com bordas arredondadas) acima do título "Consulta Pública".

Subtítulo: Texto instrucional abaixo do título: "Busque processos públicos por número, assunto, tipo ou data".

Container de Busca (Search Card): Um card branco, com sombra suave, ocupando a largura central da tela, contendo todos os campos de entrada e o botão de ação.

2. Elementos do Formulário (Form Components)
O formulário é composto por uma grade (grid) de duas linhas:

Linha 1:

Número do protocolo: Input de texto com ícone de lupa à esquerda. Placeholder: "Número do protocolo".

Assunto ou tema: Input de texto simples. Placeholder: "Assunto ou tema".

Linha 2:

Tipo de processo: Dropdown (Select) com ícone de seta. Valores (conforme definido no sistema): Ofício, Memorando, Despacho, Parecer, Portaria, Nota Técnica, Relatório, Ata, Contrato, Requerimento, Outro.

Data Início: Input de data (dd/mm/aaaa) com ícone de calendário.

Data Fim: Input de data (dd/mm/aaaa) com ícone de calendário.

Botão de Ação: Botão "Buscar" de largura total, com fundo azul escuro, ocupando a parte inferior do card.

3. Especificações Técnicas e UX
Design: Clean UI. O uso de whitespace (espaçamento) generoso entre os campos do formulário é essencial para a clareza.

Interatividade:

Os campos devem possuir estados de foco (borda azul sutil ao clicar).

Os ícones de calendário nos campos de data devem abrir um date picker nativo ou customizado.

Responsividade: Em telas menores, o layout de grade (2 colunas) deve colapsar para uma única coluna (1 input por linha).

4. Requisitos de Backend
Endpoint: GET /api/public/processos/search

Parâmetros de Query (Query Strings):

protocolo: string

assunto: string

tipo: enum (lista dos tipos pré-definidos)

data_inicio: ISO date

data_fim: ISO date

Dica para o Desenvolvedor
Como esta página é aberta a consultas públicas (geralmente fora do escopo de autenticação do usuário logado), certifique-se de que o endpoint de busca não exponha metadados sensíveis ou documentos internos, filtrando estritamente para que apenas processos marcados como "Público" retornem nos resultados da consulta.

===============

## Relatórios e Gráficos

### 1. Estrutura de Layout

* **Cabeçalho da Página:** Título "Relatórios e Gráficos" (H1) com o subtítulo "Análise detalhada de processos com filtros avançados".
* **Ação Principal:** Botão `[Gerar Relatório]` alinhado à direita, com ícone de gráfico.
* **Seção de Filtros (Collapsible/Container):**
* Um card centralizado com bordas arredondadas e sombra suave.
* Título "Filtros" com ícone de funil.
* **Grid de Filtros:** Layout de 2 colunas para os campos de entrada.

### 2. Componentes e Inputs

* **Campos de Filtro:**
* **Data Inicial e Data Final:** Inputs de data (`dd/mm/aaaa`) com seletor de calendário (ícone à direita).
* **Selects (Dropdowns):**
* "Status" (Opções: Todos, etc.)
* "Tipo de Processo" (Opções: Todos, etc.)
* "Unidade" (Opções: Todas, etc.)
* "Nível de Acesso" (Opções: Todos, etc.)
* "Usuário" (Opções: Todos, etc.)

* **Ação de Limpeza:** Botão `[Limpar Filtros]` alinhado à direita, abaixo dos campos de seleção.

### 3. Visualização de Dados (Dashboard)

Abaixo dos filtros, a página exibe uma área de métricas e gráficos (que atualmente exibe estado de "vazio" ou "sem dados"):

* **Cards de Resumo (Linha superior):** 4 blocos destacando valores numéricos:
* "Total de Processos"
* "Concluídos"
* "Atrasados"
* "Status Utilizados"


* **Área de Gráficos (Grid inferior):**
* **Distribuição por Status** (Gráfico de pizza/rosca).
* **Distribuição por Nível de Acesso** (Gráfico de pizza/rosca).
* **Top 10 (Tipos, Unidades, Usuários):** Gráficos de barras horizontais.
* **Timeline de Criação:** Gráfico de linha para série temporal.
* **Tempo de Conclusão (Top 20):** Lista ou gráfico de barras.


### 4. Especificações Técnicas para Desenvolvimento

* **UX/UI:** O design deve manter o espaçamento (padding) generoso e o estilo limpo adotado nas outras telas (card branco, fundo de página cinza muito claro).
* **Responsividade:**
* A grade de filtros deve se ajustar de 2 colunas para 1 coluna em dispositivos móveis.
* Os gráficos devem ser responsivos, adaptando-se à largura da tela.


* **Bibliotecas Recomendadas:**
* **Gráficos:** *Chart.js* ou *Recharts* para renderização dinâmica dos dados.
* **Componentes:** *Tailwind CSS* para o grid e estilização dos cards.
* **Formulários:** *React Hook Form* (se for React) para gerenciar o estado dos filtros.


### 5. Requisitos de Backend

* **Endpoint de Busca:** `GET /api/relatorios/filtrar?data_inicio=...&data_fim=...&status=...&tipo=...&unidade=...&nivel=...&usuario=...`
* **Resposta (JSON):** Deve retornar um objeto contendo os totais numéricos (KPIs) e os datasets para cada gráfico (ex: `labels` e `values`).

---

## Meu Perfil

### 1. Estrutura de Layout

* **Cabeçalho da Página:** Título "Meu Perfil" (H1) e um subtítulo descritivo: "Histórico de ações e produtividade individual".
* **Card de Identificação (Header do Perfil):** Um card horizontal que agrupa:
* **Avatar:** Ícone de perfil (à esquerda).
* **Dados do Usuário:** Nome ("Carlos Sales"), e-mail ("naturalbahia@gmail.com") e o tipo de conta ("Usuário").
* **Métricas de Performance:** Dois blocos de contadores em destaque: "Ações" e "Assinaturas" (valores numéricos grandes e negrito).


* **Navegação Interna (Tabs):** Um componente de abas para alternar entre:
* `[Histórico de Ações]` (Ativo/Selecionado)
* `[Documentos Assinados]`



### 2. Seção de Conteúdo Dinâmico

Logo abaixo das abas, um grande container com bordas arredondadas e sombra sutil, servindo como área de exibição para a aba ativa:

* **Estado Vazio:** Quando não há dados, exibir um ícone centralizado de "relógio/histórico" e a mensagem: "Nenhuma ação registrada ainda".
* **Interatividade:** Ao clicar em "Documentos Assinados", a lista ou o estado de vazio deve ser atualizado via *fetch* assíncrono.

### 3. Especificações Técnicas para o Desenvolvedor

* **Design UI:**
* **Estilo:** *Clean* e minimalista.
* **Sombras:** `shadow-sm` ou `box-shadow` moderada para destacar os cards do fundo da página.
* **Paleta:** Fundo da página cinza claro (`bg-gray-50`), cards brancos (`bg-white`).


* **Responsividade:**
* O card de identificação deve empilhar os elementos (ícone, dados, métricas) em telas de dispositivos móveis.


* **Endpoints de API Sugeridos:**
* `GET /api/usuario/me`: Retorna os dados do perfil (nome, email, contadores).
* `GET /api/usuario/historico`: Retorna a lista de ações realizadas.
* `GET /api/usuario/assinaturas`: Retorna a lista de documentos assinados.