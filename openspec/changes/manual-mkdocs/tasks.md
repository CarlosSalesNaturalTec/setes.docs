## 1. Pré-requisitos

- [ ] 1.1 Confirmar que `renomear-sistema-despapelize` e `ajustes-ui-admin` estão
  concluídos e arquivados. **Aceite**: ambos aparecem em `openspec/changes/archive/`.
  Sem isso o manual nasce descrevendo o nome e as telas antigos.
- [ ] 1.2 Habilitar GitHub Pages no repositório com origem **"GitHub Actions"**
  (Settings › Pages). **Aceite**: a origem está configurada. É clique na interface do
  GitHub — não automatizável pelo código, e o workflow falha com erro explícito até que
  seja feito.

## 2. Infraestrutura de documentação

- [ ] 2.1 Criar `requirements-docs.txt` na raiz com MkDocs, o tema e os plugins
  necessários, **versões fixadas com `==`** (D4). **Aceite**: o arquivo está na raiz,
  fora do `pyproject.toml` de `apps/api`; `uv sync --extra dev` na API não baixa nada
  de documentação.
- [ ] 2.2 Criar `mkdocs.yml` com `docs_dir: docs/manual` (D1), `nav` declarado
  explicitamente (D2), busca habilitada e idioma pt-BR. **Aceite**: `docs_dir` aponta
  para `docs/manual`, nunca para `docs`.
- [ ] 2.3 Incluir no `mkdocs.yml` comentário explicando **por que** o `docs_dir` é
  restrito, com o inventário do que vive em `docs/` e não deve ser publicado (D1,
  mitigação do risco principal). **Aceite**: quem for editar o `docs_dir` no futuro lê
  a justificativa no próprio arquivo.
- [ ] 2.4 Criar o workflow de publicação em `.github/workflows/`, disparado por push
  em `main` com path filter sobre `docs/manual/**`, `mkdocs.yml` e
  `requirements-docs.txt`, usando as ações oficiais de Pages e permissões mínimas
  (`pages: write`, `id-token: write`) — sem `gh-deploy` nem branch `gh-pages` (D5).
  **Aceite**: um push que só toca `apps/api` não dispara o workflow; nenhuma branch
  nova é criada.

## 3. Fatiamento do manual

- [ ] 3.1 Criar `docs/manual/index.md` a partir da abertura do manual atual —
  apresentação, os três perfis e como usar o manual. **Aceite**: a página abre o site
  e orienta o leitor ao seu perfil.
- [ ] 3.2 Fatiar as seções §1-8 ("Para todos os perfis") em `docs/manual/comum/`.
  **Aceite**: primeiro acesso, login, esqueci a senha, trocar senha, menu lateral, meu
  perfil, notificações e sair viram páginas próprias.
- [ ] 3.3 Fatiar a seção do Servidor em `docs/manual/servidor/` — Kanban e lista,
  filtros, criar processo, abrir a partir de modelo, tela do processo, tramitar,
  concluir, histórico, documentos e sigilo. **Aceite**: uma página por tarefa.
- [ ] 3.4 Fatiar a seção do Gestor em `docs/manual/gestor/` — KPIs, quadro consolidado
  e cadastro de usuários da unidade. **Aceite**: uma página por tarefa.
- [ ] 3.5 Fatiar a seção do Administrador em `docs/manual/administrador/`, incluindo a
  nota sobre a permissão de Auditoria. **Aceite**: uma página por tarefa; as páginas
  de modelos e de tipos de processo descrevem o layout **novo** (abas e tabela).
- [ ] 3.6 Fatiar a seção do cidadão em `docs/manual/cidadao/` — consulta pública e
  solicitação de privacidade. **Aceite**: as duas páginas deixam claro que são áreas
  abertas, sem login.
- [ ] 3.7 Migrar "Fora do escopo desta versão" e o glossário. **Aceite**: o glossário
  vira `docs/manual/glossario.md`, último item do `nav`.
- [ ] 3.8 Converter as âncoras internas do manual (`#primeiro-acesso`, …) em links
  entre páginas. **Aceite**: `mkdocs build --strict` não reporta link quebrado — é
  onde as âncoras órfãs do fatiamento aparecem.
- [ ] 3.9 **Remover `docs/manual-usuario.md`** no mesmo commit do fatiamento (D6).
  **Aceite**: o arquivo não existe mais; o Git registra a operação como movimentação e
  preserva o histórico do texto.

## 4. Seção "Como funciona"

- [ ] 4.1 Escrever `docs/manual/como-funciona/arquivamento.md` a partir de
  `apps/api/app/services/arquivamento.py` e `app/jobs/`: que é o **único** caminho
  para o estado Arquivado, que o prazo é congelado no momento da conclusão, que o job
  é diário e idempotente (reexecução não duplica evento), e que **arquivar não apaga**
  — o processo continua consultável, apenas some do quadro por padrão. **Aceite**:
  cada afirmação verificável corresponde ao código lido.
- [ ] 4.2 Escrever `docs/manual/como-funciona/consulta-publica.md` a partir de
  `app/services/consulta_publica.py` e `app/routers/consulta_publica.py`: as duas
  formas de consulta, o que é exibido, e o que **nunca** é revelado — CPF/CNPJ, nomes
  de servidores, documentos anexados e reatribuições (que não constam do histórico
  público). **Aceite**: a lista de eventos visíveis corresponde a
  `EVENTOS_MOVIMENTACAO`.
- [ ] 4.3 Explicar, na mesma página, por que processo sigiloso e número inexistente
  produzem resposta idêntica — e que isso é intencional, não falha de busca.
  **Aceite**: o texto deixa claro que a indistinguibilidade protege a própria
  existência do processo sigiloso.
- [ ] 4.4 Escrever `docs/manual/como-funciona/lgpd.md` a partir de
  `app/services/lgpd.py`, `app/services/anonimizacao_lgpd.py` e
  `app/services/solicitacao_lgpd.py`: os dois gatilhos (solicitação do titular e
  rotina automática trimestral), o prazo configurável por tipo de processo, e o efeito
  único que ambos produzem. **Aceite**: o manual não sugere que os dois caminhos
  produzam resultados diferentes.
- [ ] 4.5 Deixar explícito na página de LGPD **o que é preservado**: número do
  processo, datas, unidades, status e histórico de tramitação permanecem íntegros —
  anonimização não é exclusão do processo. **Aceite**: a distinção entre anonimizar o
  titular e apagar o processo é inequívoca.
- [ ] 4.6 Conferir as três páginas contra as specs consolidadas correspondentes
  (`arquivamento-automatico`, `rotinas-agendadas`, `consulta-publica`,
  `sigilo-processo`, `anonimizacao-lgpd`, `solicitacao-lgpd`). **Aceite**: nenhuma
  divergência; divergência encontrada entre código e spec é **relatada como defeito**,
  não conciliada no texto do manual.
- [ ] 4.7 Confirmar que nenhuma das páginas contém dado pessoal real — número de
  processo, nome de interessado ou CPF/CNPJ verdadeiros. **Aceite**: todos os exemplos
  são fictícios.

## 5. Validação e publicação

- [ ] 5.1 Rodar `mkdocs build --strict` localmente. **Aceite**: build sem erro nem
  aviso — `--strict` é o portão que pega link quebrado e página fora do `nav`.
- [ ] 5.2 **Verificação de vazamento**: inspecionar o `site/` gerado e confirmar que
  não contém nenhuma página derivada de `docs/PRD.md`, `docs/emailConfig.md`,
  `docs/primeiro-acesso-producao.md`, `docs/history/**` ou dos documentos de decisão.
  **Aceite**: nenhuma dessas páginas existe no build. É a verificação central do
  change.
- [ ] 5.3 Revisar a navegação com `mkdocs serve`: ordem pedagógica (comum → perfil →
  glossário), busca funcionando e nenhuma página órfã. **Aceite**: um usuário chega ao
  seu perfil a partir da página inicial em no máximo dois cliques.
- [ ] 5.4 Após o merge, confirmar que o workflow publicou e que o site responde no
  endereço do Pages. **Aceite**: o site está no ar com a navegação esperada.

## 6. Referências cruzadas

- [ ] 6.1 Atualizar as referências ao caminho antigo `docs/manual-usuario.md` em
  `CLAUDE.md`, `README.md` e `docs/PRD.md`, se existirem, apontando para o site ou
  para `docs/manual/`. **Aceite**: nenhum link aponta para o arquivo removido.
- [ ] 6.2 **Não** editar `openspec/changes/archive/**` nem `docs/history/**` que
  citem o caminho antigo (D6). **Aceite**: `git diff --stat` não lista nenhum arquivo
  sob esses caminhos.
