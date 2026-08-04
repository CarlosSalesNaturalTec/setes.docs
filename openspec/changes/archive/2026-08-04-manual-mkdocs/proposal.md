## Why

O manual do usuário existe hoje como um único arquivo de ~780 linhas
(`docs/manual-usuario.md`), navegável apenas por rolagem e por um sumário de
âncoras. O cliente pediu que ele seja publicado como **site de documentação com
MkDocs**, com navegação por perfil, busca e endereço estável para compartilhar com
os usuários finais.

Além do formato, o conteúdo tem lacunas: três mecanismos que operam **sozinhos, sem
ação do usuário** — arquivamento automático, consulta pública e LGPD — são os que
mais geram dúvida justamente por não terem tela onde se explicar. O manual atual os
menciona de passagem, sem descrever quando disparam, o que preservam e o que nunca
revelam.

## What Changes

- **Site MkDocs publicado no GitHub Pages**, com o manual do usuário fatiado em
  páginas por perfil, navegação lateral e busca.
- **O manual passa a ter uma única fonte**: `docs/manual-usuario.md` é **removido** e
  seu conteúdo passa a viver, fatiado, em `docs/manual/`. Não há cópia paralela para
  divergir.
- **O `docs_dir` do MkDocs aponta para `docs/manual/`, não para `docs/`.** Essa é uma
  decisão de segurança, não de organização: o MkDocs constrói **todo** arquivo dentro
  do `docs_dir`, esteja ou não declarado no `nav` — ficar fora do `nav` apenas silencia
  um aviso, a página continua sendo gerada e acessível por URL direta. E um site do
  GitHub Pages é **público**, inclusive quando servido a partir de repositório privado
  (salvo em planos Enterprise). Com o `docs_dir` restrito ao manual, os documentos
  internos hoje em `docs/` — PRD, guia de primeiro acesso em produção com URLs do
  ambiente, configuração de provedor de e-mail, decisões de arquitetura e o histórico
  em `docs/history/` — ficam fora do site **por construção**, sem depender de nenhum
  denylist que alguém possa esquecer de atualizar ao adicionar um documento novo.
- **Três seções novas de conteúdo**, escritas a partir do comportamento real do código:
  - **Arquivamento automático** — o único caminho para o estado `Arquivado`; o prazo
    congelado no momento da conclusão; a idempotência do job diário; e o fato de que
    arquivar não apaga nada, apenas oculta o processo do quadro por padrão.
  - **Consulta pública** — as duas formas de consulta; o que é exibido; e, sobretudo,
    o que **nunca** é revelado (CPF/CNPJ, nomes de servidores, documentos anexados,
    reatribuições) e por que processo sigiloso e número inexistente produzem resposta
    idêntica.
  - **LGPD** — os dois gatilhos (solicitação do titular e rotina automática) e o
    efeito único e irreversível que ambos produzem: o que é anonimizado e o que é
    preservado para fins de auditoria do processo administrativo.
- **Dependências Python em `requirements-docs.txt`** na raiz, separado do `uv` de
  `apps/api` — MkDocs é ferramenta de documentação, não dependência da API.
- **Workflow de publicação** em `.github/workflows/`, disparado por push em `main`
  com filtro de caminho sobre `docs/manual/**` e o `mkdocs.yml`, seguindo o padrão de
  path filtering já usado pelo CI do repositório.

## Capabilities

### New Capabilities

<!-- Nenhuma. Nenhum comportamento do sistema muda: este change produz documentação
e a infraestrutura para publicá-la. O change declara `skip_specs: true`. -->

### Modified Capabilities

<!-- Nenhuma. As três seções novas descrevem comportamento já especificado em
`arquivamento-automatico`, `rotinas-agendadas`, `consulta-publica`, `sigilo-processo`,
`anonimizacao-lgpd` e `solicitacao-lgpd` — o manual documenta esses requisitos, não os
altera. Se ao redigir surgir divergência entre o manual e uma spec, isso é um defeito
a reportar, não uma alteração a fazer por este change. -->

## Impact

- **Dependências**: **requer `renomear-sistema-despapelize` concluído** — o manual
  deve nascer com o nome definitivo do produto em vez de ser reescrito em seguida.
  **Requer `ajustes-ui-admin` concluído** — as telas de modelos e de tipos de processo
  mudam de layout, e as instruções passo a passo descrevem a versão nova.
- **Tabelas PostgreSQL**: **nenhuma** tabela nova ou alterada.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: nenhum novo segredo no Secret Manager, nenhum bucket novo no
  Cloud Storage. A publicação no GitHub Pages usa o `GITHUB_TOKEN` do próprio workflow
  — nenhuma credencial nova é criada ou armazenada.
- **Backend / Frontend**: **nenhuma alteração de código de aplicação**. Nenhum
  endpoint, componente, contrato ou tipo é tocado.
- **Contrato**: nenhuma regeneração de tipos.
- **Novos arquivos**: `mkdocs.yml`, `requirements-docs.txt`, `docs/manual/**`,
  workflow de publicação. **Removido**: `docs/manual-usuario.md`.
- **Repositório GitHub**: exige habilitar GitHub Pages com origem em GitHub Actions —
  ação de configuração no repositório, fora do que o código pode fazer sozinho.
- **LGPD**: o manual **descreve** o tratamento de dados pessoais sem conter nenhum
  dado pessoal real. Todos os exemplos usam dados fictícios; nenhum número de processo,
  nome de interessado, CPF/CNPJ ou captura de tela com dado real entra no site. A
  escolha do `docs_dir` acima é o controle que impede publicação inadvertida de
  documento interno.
- **PRD**: nenhuma alteração. O manual é derivado do PRD, não o contrário.

> **Observação fora do escopo deste change**: `docs/emailConfig.md` mantém, versionada
> no repositório, a identificação de conta do provedor de e-mail. O `docs_dir`
> restrito impede que ela seja publicada no site, mas não a remove do histórico do
> Git. Tratar isso é decisão de segurança à parte, não coberta aqui.
