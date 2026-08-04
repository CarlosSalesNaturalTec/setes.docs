## 1. Modelos de documento — abas

- [x] 1.1 Reorganizar `app/admin/modelos/page.tsx` em duas abas consumindo
  `components/tabs.tsx` **sem alterar o componente** (D1): "Novo modelo"
  (`CadastroModeloForm`) e "Modelos cadastrados" (filtros + lista de `CartaoModelo`).
  **Aceite**: `git diff` não toca `components/tabs.tsx`; as duas abas renderizam o
  conteúdo que hoje está empilhado, sem perda de nenhum elemento.
- [x] 1.2 Refletir a aba ativa na URL por query param, com recaída silenciosa na aba
  padrão para valor ausente ou desconhecido (D2), seguindo o padrão de
  `app/perfil/page.tsx`. **Aceite**: recarregar com a aba de cadastro selecionada a
  preserva; um valor inválido renderiza a aba padrão sem mensagem de erro.
- [x] 1.3 Definir "Modelos cadastrados" como aba padrão (D2). **Aceite**: acessar
  `/admin/modelos` sem query param abre a listagem, não a ficha.
- [x] 1.4 Alternar para a aba de listagem **após** o cadastro ser aceito e a listagem
  recarregada (D3); em caso de erro, permanecer na ficha com os dados preservados.
  **Aceite**: no sucesso, o modelo recém-criado está visível na listagem no momento da
  troca de aba; no erro, o conteúdo do editor formatado não é perdido.
- [x] 1.5 Verificar que os filtros de tipo e de situação continuam operando dentro da
  aba de listagem. **Aceite**: filtrar por tipo e por situação produz o mesmo
  resultado de antes da reorganização.

## 2. Tipos de processo — tabela

- [x] 2.1 Substituir a lista de cards de `app/admin/tipos-processo/page.tsx` por
  tabela com colunas Nome, Prazo de anonimização LGPD (anos) e ação de salvar,
  mantendo o formulário de cadastro acima (D4). **Aceite**: uma linha por tipo; o
  formulário de cadastro permanece funcional e inalterado.
- [x] 2.2 Transpor `PrazoAnonimizacaoLgpd` de card para linha, preservando estado de
  edição, salvamento e erro **isolados por linha** (D4). **Aceite**: salvar o prazo de
  um tipo não altera nem revalida os demais; o erro de uma linha aparece junto dela.
- [x] 2.3 Envolver a tabela em contêiner com rolagem horizontal própria, usando os
  tokens de card de `identidade-visual` (D4). **Aceite**: em viewport estreito a
  tabela rola dentro do próprio contêiner e a página **não** rola horizontalmente.
- [x] 2.4 Exibir indicação explícita quando não houver nenhum tipo cadastrado.
  **Aceite**: com catálogo vazio, aparece a indicação em vez de uma tabela com corpo
  vazio; o formulário de cadastro continua disponível.
- [x] 2.5 Confirmar que nenhuma ação inexistente foi introduzida — sem edição de nome,
  desativação ou exclusão, nem desabilitadas nem ocultas (D4, relayout puro).
  **Aceite**: a única ação por linha é salvar o prazo.

## 3. Mensagem do certificado digital

- [x] 3.1 Substituir o texto de `DocumentosAssinadosAba` em `app/perfil/page.tsx:214`
  pela formulação de D5, mantendo a citação `(change perfil-em-abas, design D3)` do
  comentário acima do componente e acrescentando a referência a este change.
  **Aceite**: o texto novo está no lugar; o comentário continua rastreando a decisão de
  origem.
- [x] 3.2 Confirmar que a aba permanece **sem** qualquer controle — nenhum botão,
  campo, formulário ou link foi acrescentado junto do texto (D5). **Aceite**: a aba
  contém exclusivamente texto.

## 4. Testes

- [x] 4.1 Atualizar `app/perfil/perfil-abas.test.tsx:130`: a regex atual
  (`/assinatura digital.*fase futura/i`) **continua passando** com o texto novo sem
  verificar a parte acrescentada. Estender a asserção para cobrir a orientação sobre o
  Certificado Digital ICP-Brasil. **Aceite**: o teste falha se a orientação for
  removida — hoje não falharia.
- [x] 4.2 Acrescentar asserção de que a aba "Documentos assinados" não contém nenhum
  controle interativo. **Aceite**: o teste falharia se um botão ou link fosse
  introduzido na aba.
- [x] 4.3 Cobrir com Vitest a tela de modelos: aba padrão, alternância após cadastro
  bem-sucedido, permanência na ficha em caso de erro e recaída de query param
  inválido. **Aceite**: os quatro cenários dos deltas de `modelos-documento` têm teste
  correspondente.
- [x] 4.4 Cobrir com Vitest a tabela de tipos de processo: salvamento isolado por
  linha, erro isolado por linha e estado vazio. **Aceite**: os três cenários
  correspondentes do delta de `tipos-processo` têm teste.
- [x] 4.5 Atualizar `e2e/16-modelos-documento.spec.ts` para selecionar a aba "Novo
  modelo" antes de interagir com a ficha (a aba padrão passou a ser a listagem).
  **Aceite**: a spec passa; a navegação por aba está explícita no teste, não
  pressuposta.
- [x] 4.6 Rodar `pnpm --filter @setes/web typecheck`, `pnpm --filter @setes/web test` e
  `cd apps/web && pnpm test:e2e`. **Aceite**: typecheck limpo, Vitest e Playwright
  verdes.

## 5. Documentação

- [x] 5.1 Atualizar `docs/PRD.md`: US 1.5 (texto da aba de documentos assinados) e as
  US de administração de modelos e de tipos de processo, registrando a nova
  organização de tela. **Aceite**: o PRD não descreve mais o layout antigo.
- [x] 5.2 Atualizar `docs/manual-usuario.md` nas seções "Cadastrar modelos de
  documento", "Cadastrar tipos de processo" e "Meu Perfil". **Aceite**: os passos
  descritos correspondem às telas novas — inclusive a necessidade de trocar de aba
  para cadastrar um modelo.

## 6. Fechamento

- [x] 6.1 Confirmar que nenhuma alteração vazou para o backend ou para o contrato.
  **Aceite**: `git diff --stat` não lista nada sob `apps/api/` nem
  `packages/api-types/`; nenhuma execução de `pnpm gen:types` foi necessária.
- [x] 6.2 Confirmar que `components/tabs.tsx` permaneceu intacto (D1). **Aceite**: o
  arquivo não aparece no diff. Se aparecer, avaliar o impacto sobre `app/perfil` antes
  de prosseguir.
