## 1. Ponto único da URL e ícone

- [ ] 1.1 Criar `apps/web/lib/manual.ts` exportando `URL_MANUAL` com a URL do
      site MkDocs publicado (`https://carlossalesnaturaltec.github.io/setes.docs/`),
      seguindo o padrão de `lib/marca.ts` (design.md D3). Critério de aceite:
      nenhum outro arquivo do frontend contém essa URL como literal.
- [ ] 1.2 Adicionar `IconManual` em `apps/web/components/icons.tsx`, seguindo
      a assinatura `IconProps` e o padrão de SVG monocromático dos demais
      ícones de menu (design.md D4). Critério de aceite: `pnpm --filter @setes/web typecheck` passa.

## 2. Item de navegação externo no shell

- [ ] 2.1 Estender o tipo `ItemMenu` em `components/protected-shell.tsx` com
      `hrefExterno?: string` (design.md D1), sem alterar o significado de
      `href` para os itens existentes.
- [ ] 2.2 Adicionar o item "Manual" a `ITENS_MENU`, com `Icon: IconManual`,
      `hrefExterno: URL_MANUAL` e `visivel: () => true` (design.md D2).
- [ ] 2.3 Atualizar a renderização do `<nav>` para, quando `hrefExterno`
      estiver presente, renderizar `<a href={hrefExterno} target="_blank"
      rel="noopener noreferrer">` em vez de `<Link href={href}>`, e não
      calcular estado ativo para esse item (`itemAtivo` não é chamado, ou é
      chamado e o resultado é descartado — o item nunca recebe a classe/estado
      de ativo). Critério de aceite: nenhum item interno muda de
      comportamento — `itemAtivo(pathname, href)` continua sendo usado
      exatamente como antes para os demais itens.

## 3. Testes

- [ ] 3.1 Atualizar `components/protected-shell.test.tsx`: o item "Manual"
      aparece para os três perfis (servidor, gestor, administrador); o link
      renderizado usa `target="_blank"` e `rel="noopener noreferrer"` e
      aponta para `URL_MANUAL`; nenhum item restrito por perfil passa a
      aparecer para quem não deveria vê-lo (regressão de RBAC) — cobre os
      cenários "Servidor vê apenas os itens do seu perfil", "Item restrito
      continua oculto para perfil sem acesso" e "Administrador vê os itens
      administrativos" do spec delta.
- [ ] 3.2 Adicionar caso ao mesmo arquivo cobrindo que o item "Manual" nunca
      recebe o destaque de item ativo, independentemente da rota corrente
      (cenário "Item externo não é elegível ao destaque de item ativo").
      Critério de aceite: `pnpm --filter @setes/web test` passa.

## 4. Documentação do manual

- [ ] 4.1 Adicionar a linha `| Manual | Todos |` à tabela de
      `docs/manual/comum/menu-lateral.md` e uma frase indicando que o item
      abre o manual em nova aba. Critério de aceite: `mkdocs build --strict`
      roda sem erro localmente.
