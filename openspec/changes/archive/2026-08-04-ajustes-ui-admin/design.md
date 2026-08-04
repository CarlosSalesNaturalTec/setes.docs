## Context

Ver `proposal.md` — Why. Os três ajustes vivem inteiramente no frontend, e o que os
enquadra é o que **já existe** e não precisa ser construído:

- `components/tabs.tsx` é um widget de abas ARIA completo, criado em `perfil-em-abas`
  (D4): `tablist`/`tab`/`tabpanel`, roving tabindex, navegação por setas, sem
  armadilha de foco. É genérico — recebe `abas`, `abaAtiva`, `onSelecionar` — e não
  tem nada de específico da tela de perfil.
- `app/perfil/page.tsx` já estabeleceu o padrão de **aba refletida na URL** por query
  param, com recaída silenciosa na aba padrão quando o valor é desconhecido.
- A tela de modelos já separa `CadastroModeloForm` de `CartaoModelo` e do bloco de
  filtros. A fatia em abas é redistribuição de JSX que já está modularizado, não
  refatoração.

O estado atual das duas telas admin:

```
/admin/modelos                    /admin/tipos-processo
┌────────────────────────┐        ┌──────────────────────────┐
│ CadastroModeloForm     │        │ CadastroTipoProcessoForm │
│  (inclui EditorFormat.)│        ├──────────────────────────┤
├────────────────────────┤        │ <ul> de cards            │
│ filtros (tipo/situação)│        │  └ <h2>nome</h2>         │
├────────────────────────┤        │  └ PrazoAnonimizacaoLgpd │
│ <ul> de CartaoModelo   │        │     (mini-form inline)   │
└────────────────────────┘        └──────────────────────────┘
```

O terceiro ajuste é a substituição de um literal em `app/perfil/page.tsx:214`, dentro
de `DocumentosAssinadosAba`.

## Goals / Non-Goals

**Goals:**

- Reusar `components/tabs.tsx` **sem modificá-lo** — se a tela de modelos exigir
  alteração no componente, isso é sinal de que o componente não era genérico e a
  mudança precisa ser avaliada contra a tela de perfil, que também o consome.
- Manter o padrão de URL de `perfil-em-abas`, para que abas se comportem igual em
  todo o sistema.
- Relayout que não altere nenhuma chamada de API, payload ou regra de validação.

**Non-Goals:**

- **Nenhuma alteração de backend, contrato ou banco.**
- **Nenhuma ação nova em tipos de processo** — sem edição de nome, desativação ou
  exclusão. Relayout puro, por decisão explícita.
- **Nenhuma retomada do Épico 4.** A aba de documentos assinados continua sem
  qualquer controle; muda só o texto.
- **Nenhuma paginação ou busca** nas listas de modelos ou de tipos. Os filtros
  existentes de modelos são preservados como estão.

## Decisions

### D1 — Reuso de `components/tabs.tsx` sem alteração

A tela de modelos consome o componente existente. Nenhuma prop nova, nenhum
comportamento novo no widget.

*Por quê:* o componente já resolve toda a acessibilidade que o requisito de navegação
por teclado exige, e já foi validado em `components/tabs.test.tsx`. Reescrever ou
parametrizar significaria revalidar do zero, e qualquer regressão atingiria também a
tela de perfil.

*Alternativa considerada:* abas nativas do Next via rotas aninhadas
(`/admin/modelos/novo`, `/admin/modelos/lista`). Rejeitada — introduz navegação real,
com remontagem de componente e recarga dos dados a cada troca de aba, para uma tela
onde a lista já está toda em memória. Também divergiria do padrão de "Meu Perfil",
que resolve o mesmo problema por query param.

### D2 — Aba na URL por query param, mesmo padrão de `perfil-em-abas`

A aba ativa é refletida por query param, com recaída na aba padrão quando o valor é
ausente ou desconhecido, **sem** mensagem de erro.

*Por quê:* consistência de comportamento entre telas com abas. Um usuário que aprendeu
que o link de "Meu Perfil" preserva a aba espera o mesmo em modelos.

*A aba padrão é "Modelos cadastrados"*, não "Novo modelo": o uso dominante da tela é
consultar o catálogo, e o motivo declarado na proposta é justamente não obrigar quem
consulta a passar pela ficha de cadastro. Abrir na ficha reproduziria o problema numa
forma nova.

### D3 — Alternância para a listagem só no sucesso confirmado

A troca de aba após o cadastro acontece **depois** de a criação ser aceita pelo
backend e a listagem ser recarregada — não otimisticamente ao submeter.

*Por quê:* o requisito é que o modelo recém-criado **conste na listagem** quando a aba
troca. Alternar antes da recarga exibiria uma lista sem o item, o que é pior que não
alternar: sugere que o cadastro falhou. Em caso de erro, permanece-se na ficha com os
dados preservados — o usuário não perde o conteúdo já digitado no editor formatado,
que é o campo mais caro de repreencher.

### D4 — Tabela de tipos de processo com escopo de edição por linha

Cada linha da tabela mantém o próprio estado de edição de prazo, com salvamento e erro
isolados — o comportamento que `PrazoAnonimizacaoLgpd` já tem hoje, transposto de card
para linha.

*Por quê:* preserva a semântica atual sem introduzir salvamento em lote, que traria a
pergunta "o que acontece se três linhas salvam e a quarta falha?" — pergunta que não
existe hoje e que a proposta não pediu para responder.

*Sobre a coluna de ações:* ela contém apenas a ação de salvar o prazo. A spec proíbe
explicitamente sugerir ações inexistentes — uma coluna "Ações" com um único botão é
correta; o que seria incorreto é adicionar ícones de editar/excluir desabilitados
"para depois".

*Responsividade:* tabelas quebram em telas estreitas, e a sidebar do shell já consome
240px. A tabela precisa de contêiner com rolagem horizontal própria, sem que a página
role horizontalmente — os tokens de card de `identidade-visual` já cobrem o contêiner.

### D5 — Texto do certificado digital: orientação sem controle

O texto passa a ser: *"A assinatura digital de documentos será disponibilizada em uma
fase futura do produto. Para se preparar, solicite seu Certificado Digital ICP-Brasil
junto a uma Autoridade Certificadora."*

*Por quê a formulação longa, e não o literal "Solicite Certificado Digital":* a spec
`gestao-usuarios` proíbe "qualquer elemento que sugira funcionalidade disponível". Um
imperativo isolado numa tela do sistema lê-se como instrução *para aquela tela* — a
pergunta imediata do usuário é "solicito onde, aqui?". A formulação escolhida mantém a
declaração de indisponibilidade como oração principal, e a orientação como preparação
explicitamente externa ("junto a uma Autoridade Certificadora"). Atende ao pedido do
cliente sem violar o requisito.

*Sem link:* nenhuma URL de Autoridade Certificadora é embutida. O ITI credencia
múltiplas ACs, a lista muda, e apontar para uma seria escolha comercial indevida —
além de virar link quebrado sem ninguém perceber. Texto puro, também porque um link
sairia numa tela que a spec exige livre de controles.

## Risks / Trade-offs

- **`e2e/16-modelos-documento.spec.ts` quebra** — a spec navega direto ao formulário,
  que passa a estar atrás de uma aba não-padrão (D2). → O teste precisa selecionar a
  aba "Novo modelo" antes de interagir com a ficha. É quebra esperada e visível, não
  silenciosa.
- **`app/perfil/perfil-abas.test.tsx:130`** afirma o texto antigo por regex
  (`/assinatura digital.*fase futura/i`). O texto novo ainda casa com esse padrão, o
  que significa que o teste **passa sem verificar a parte nova**. → Estender a
  asserção para cobrir a orientação sobre o certificado, senão o requisito novo fica
  sem teste.
- **Mudar a aba padrão para a listagem altera o hábito de quem já usa a tela** — quem
  cadastra em lote passa a precisar de um clique a mais por sessão. → Aceito: a
  proposta declara a consulta como uso dominante, e a URL com a aba de cadastro pode
  ser guardada como favorito por quem cadastra com frequência.
- **A tabela de tipos com muitos registros não tem paginação** — mesma limitação da
  lista de cards atual, que a tabela apenas herda. Não é regressão, mas fica mais
  aparente numa tabela longa. → Fora de escopo; registrar se o volume crescer.
- **Risco de o relayout arrastar mudança de comportamento sem querer** (ex.: um filtro
  que deixa de aplicar, uma validação perdida na transposição). → Os cenários de
  "filtros continuam operando", "prazo salvo individualmente" e "acesso negado" nos
  deltas existem exatamente para travar isso.

## Migration Plan

Não há migration de banco nem de contrato. Deploy padrão do repositório.

**Rollback:** reverter o merge. Nenhum estado persistido muda — nenhuma migration,
nenhum payload novo, nenhum campo novo. Um usuário com URL contendo o query param de
aba, após rollback, cai numa tela que ignora o parâmetro e renderiza normalmente;
sem erro.
