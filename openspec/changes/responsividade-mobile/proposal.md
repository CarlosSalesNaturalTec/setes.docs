## Why

A pergunta original era se a aplicação é adaptável a smartphones e tablets. A
resposta levantada no código é **parcialmente — e o que falta é específico e
localizado**, não um redesenho.

O shell de navegação **já é responsivo**. `components/protected-shell.tsx:143-212`
implementa gaveta lateral completa: `md:grid-cols-[240px_1fr]` no desktop,
`fixed inset-y-0` + `translate-x-full` com overlay e botão hambúrguer abaixo de
768 px. Dashboard e Kanban também empilham corretamente
(`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`).

O problema é a **cobertura**: são apenas **23 prefixos responsivos em toda a
aplicação**, distribuídos em 8 arquivos — e 10 deles estão no próprio shell. Fora
dele, telas inteiras nunca receberam tratamento de viewport estreito.

O achado mais concreto são as **tabelas de administração**. Cinco das seis tabelas
do sistema aplicam `overflow-hidden` **na própria `<table>`** — o que serve para
arredondar a borda, e não para permitir rolagem horizontal:

```
apps/web/app/admin/usuarios/page.tsx:378                <table … overflow-hidden>   ⚠
apps/web/app/admin/unidades/page.tsx:360                <table … overflow-hidden>   ⚠
apps/web/app/admin/unidades/page.tsx:413                <table … overflow-hidden>   ⚠
apps/web/app/admin/lgpd/solicitacoes-lgpd-content.tsx:147   <table … overflow-hidden>   ⚠
apps/web/app/admin/documentos-removidos/…:129           <table … overflow-hidden>   ⚠

apps/web/app/admin/tipos-processo/page.tsx:149  <div className="overflow-x-auto">   ✅
                                                  <table className="w-full">
```

Ou seja: **o padrão correto já existe no próprio repositório** — `tipos-processo`
envolve a tabela num contêiner com `overflow-x-auto`. Ele simplesmente não foi
aplicado às outras cinco. Isso torna a correção barata e verificável, em vez de
uma reescrita.

Por fim, nada disso é detectável pela suíte atual: `apps/web/playwright.config.ts:41`
declara `projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }]` —
**nenhum viewport móvel é exercitado**. Uma regressão de layout em telas estreitas
passa hoje sem ser notada.

## What Changes

- **As cinco tabelas de administração passam a usar o padrão já estabelecido em
  `tipos-processo`**: contêiner com `overflow-x-auto` envolvendo a `<table>`, de
  modo que a tabela role horizontalmente dentro da sua própria caixa em vez de
  espremer colunas ou estourar a largura da página. As colunas, os dados e as ações
  por perfil **não mudam**.
- **A tela de detalhe do processo (`app/processos/[id]/page.tsx`) é revisada para
  viewport estreito.** É a tela mais densa do sistema — histórico de tramitação,
  documentos, formulários de envio/devolução/reatribuição — e hoje tem **zero
  prefixos responsivos**.
- **`app/consulta-publica/page.tsx:18` deixa de usar `grid-cols-2` fixo** na lista
  de definições, ganhando comportamento de coluna única em telas estreitas. Esta é
  a única tela do escopo acessível **sem login**, e portanto a mais provável de ser
  aberta em celular.
- **A suíte Playwright ganha um projeto de viewport móvel**, para que o
  comportamento em tela estreita passe a ser verificado automaticamente e não
  regrida em silêncio.
- **Cobertura E2E móvel dos fluxos obrigatórios**: login e tramitação em viewport
  de smartphone, conforme a regra do projeto que exige Playwright para
  login/tramitação/documentos/consulta pública. Como este change altera a
  apresentação desses fluxos em telas estreitas, os testes correspondentes são
  **obrigatórios, não opcionais**.
- **Nenhuma tabela é convertida em cards.** A conversão tabela→card em telas
  estreitas foi considerada e deixada **fora de escopo**: mudaria a densidade de
  informação e a forma de interação de todas as telas administrativas, e o objetivo
  aqui é tornar a aplicação utilizável em dispositivos móveis, não redesenhá-la.

## Capabilities

### New Capabilities

<!-- Nenhuma. -->

### Modified Capabilities

- **`identidade-visual`** — o requisito "Conteúdo das páginas internas herda o
  tema" cobre os contêineres de tabela das telas de administração. Ele ganha a
  exigência de que esses contêineres permaneçam legíveis e roláveis em viewport
  estreito, **sem alterar** o conjunto de dados, as colunas nem as ações por
  perfil, exatamente como o requisito já garante para o restyle.

<!-- As capabilities de comportamento (processos, workflow-tramitacao,
gestao-usuarios, consulta-publica) NÃO são modificadas: nenhuma regra de negócio,
visibilidade ou autorização muda. Este change é de apresentação. -->

## Impact

- **Dependências**: nenhuma. Convém aplicá-lo **depois** de
  `marca-visual-despapelize` se ambos forem trabalhados em paralelo, apenas porque
  os dois tocam o shell e o Login — mas não há dependência técnica real.
- **Tabelas PostgreSQL**: **nenhuma**.
- **Migrations**: **nenhuma**.
- **Segredos / buckets**: **nenhum**.
- **Backend**: **nenhuma alteração**. Nenhum endpoint, schema ou rota é tocado.
- **Contrato**: **nenhuma regeneração de tipos**.
- **Frontend**: cinco telas de administração, `app/processos/[id]/page.tsx`,
  `app/consulta-publica/page.tsx`, `apps/web/playwright.config.ts` e novas specs
  E2E.
- **Testes**: Vitest existente deve continuar passando sem alteração — os testes
  de componente não asseguram classes de layout. O acréscimo real é o projeto
  Playwright móvel e as specs de login e tramitação nesse viewport.
- **LGPD**: **não aplicável** — nenhum dado pessoal novo é coletado, exibido ou
  transmitido. As telas afetadas continuam exibindo exatamente os mesmos campos aos
  mesmos perfis.
- **PRD**: nenhuma alteração.

> **A verificar no design**: se a revisão de `processos/[id]` revelar que a
> densidade da tela exige mais do que ajuste de breakpoints — por exemplo,
> reorganizar histórico e documentos em abas no viewport estreito —, isso amplia o
> escopo e deve ser decidido explicitamente, não absorvido em silêncio.
