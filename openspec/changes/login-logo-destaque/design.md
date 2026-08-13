## Context

Ver `proposal.md — Why` para a motivação. O que segue é só o que molda a
implementação.

**Estado atual** (`apps/web/app/login/page.tsx:47-53`): chip circular navy de 48px
contendo `IconMarca` (28px, `currentColor`, componente compartilhado com a
sidebar/favicon), seguido de `<h1>{NOME_PRODUTO}</h1>` ("Despapelize"),
`SUBTITULO_CLIENTE` ("SETES") e "Acesse sua conta" como texto.

**Restrição herdada** (`identidade-visual`, change `marca-visual-despapelize`,
arquivado há poucos dias): chip circular obrigatório em Login e sidebar, símbolo
monocromático `currentColor` único (`IconMarca`), material de origem
(`docs/images/logo_despapelize.jpeg`) proibido de ser consumido pela aplicação. Este
change abre exceção a essas três regras, **escopada explicitamente ao Login** — a
delta spec já registra isso; aqui documento como a exceção é implementada sem
vazar para sidebar/favicon.

## Goals / Non-Goals

**Goals:**

- Login exibe a arte original do cliente (fundo, árvore, raízes, wordmark) tal como
  fornecida, sem chip, com largura máxima de 260px.
- `<h1>` textual duplicado é removido; a imagem assume o papel de heading acessível
  via `alt="Despapelize"`.
- Sidebar, favicon e `IconMarca` continuam bit-a-bit como estão hoje.

**Non-Goals:**

- Editar a imagem (recorte, remoção de fundo, correção de cor). É a arte como veio
  do cliente.
- Aplicar qualquer tratamento de destaque fora da paleta navy institucional (glow
  neon, gradiente) — cogitado e descartado durante a exploração que precedeu esta
  proposta.
- Alterar o componente `IconMarca`, o favicon ou a marca horizontal
  (`public/marca/despapelize-horizontal.svg`).
- Alterar lógica de autenticação, validação de campos ou mensagens de erro do
  Login.

## Decisions

### D1 — Cópia do material de origem em `public/`, comentário na origem do consumo

`docs/images/logo_despapelize.jpeg` fica fora de `apps/web`, e o Next.js só serve
estático a partir de `apps/web/public/`. Não há como referenciar o arquivo de
`docs/` diretamente de dentro da app sem um passo de build.

A solução é **copiar** o arquivo para `apps/web/public/marca/login-hero.jpg` uma
única vez, sem edição. Como um arquivo JPEG não comporta um comentário legível de
forma prática (EXIF não é o lugar certo para isso), a citação da origem vai no
código que consome o arquivo — o JSX em `login/page.tsx` recebe um comentário
apontando `docs/images/logo_despapelize.jpeg` como fonte, no mesmo espírito da
citação cruzada que `IconMarca`/`app/icon.svg` já usam (D4 do change
`marca-visual-despapelize`).

*Alternativa descartada:* servir diretamente de `docs/images/` via rota customizada
do Next.js (`app/api/marca-origem/route.ts` lendo o arquivo do disco). Descartada
por desproporção — introduziria uma rota só para evitar copiar um arquivo estático,
e ainda criaria a mesma dependência de sincronização que a cópia tem, só que com
mais código.

### D2 — Sem chip, `next/image` com largura máxima 260px

A imagem é renderizada com `next/image`, não `<img>` cru: ganha otimização de
formato (AVIF/WebP quando o navegador suporta, mantendo o JPEG como fonte),
carregamento priorizado (`priority`, já que é conteúdo acima da dobra) e
`width`/`height` explícitos a partir das dimensões reais do arquivo (438×740),
controlada visualmente por `className="w-full max-w-[260px] h-auto"` para respeitar
o teto de 260px preservando a proporção original (~0,59).

Nenhum container circular, nenhum `overflow: hidden` recortando a imagem — ela
aparece "solta" sobre o fundo do card, como decidido na exploração.

*Alternativa descartada:* `<img>` estático simples. Perderia a otimização de
formato/tamanho do `next/image` sem ganhar nada em troca, já que o asset já vive em
`public/` e o componente está disponível.

### D3 — Imagem como heading acessível, sem `<h1>` de texto duplicado

Em vez de manter um `<h1>{NOME_PRODUTO}</h1>` textual ao lado da imagem (que
duplicaria "Despapelize®" já presente nos pixels), a imagem recebe `alt="Despapelize"`
e é envolvida por um `<h1>`:

```tsx
<h1>
  <Image src="/marca/login-hero.jpg" alt="Despapelize" width={438} height={740}
    priority className="mx-auto w-full max-w-[260px] h-auto" />
</h1>
```

O algoritmo de nome acessível (`accname`) que `@testing-library/react` usa para
`getByRole("heading", ...)` computa o nome de um heading a partir do texto
alternativo de imagens descendentes — então `screen.getByRole("heading", { name:
"Despapelize" })` (já usado em `page.test.tsx:41`) deve continuar passando sem
alteração de matcher. Isso é verificado como tarefa, não presumido: se o teste
falhar nessa forma, o matcher é ajustado para localizar a imagem por `alt`
diretamente.

*Alternativa descartada:* `<h1 className="sr-only">Despapelize</h1>` separado, com
a imagem `alt=""` decorativa. Rejeitada por duplicar a semântica de "nome do
produto" em dois lugares do DOM (um visualmente oculto, um visual) quando a imagem
já é perfeitamente capaz de carregar essa informação sozinha via `alt`.

### D4 — Sem tratamento de cor: a imagem é usada exatamente como fornecida

Nenhum filtro CSS, gradiente, sombra colorida ou `mix-blend-mode` é aplicado à
imagem. O "destaque" pedido vem inteiramente do tamanho (260px vs. os 28px atuais)
e da ausência de chip — não de um efeito visual novo. Isso mantém o resultado
dentro da paleta navy institucional que a capability `identidade-visual` exige como
token único de marca, sem abrir uma segunda linguagem de cor só para o Login.

### D5 — Exceção nas specs é textual e localizada, não uma reestruturação

Os quatro requisitos afetados (`Apresentação do Login sem SSO`, `Marca institucional
exibe o ícone do favicon`, `Símbolo derivado da marca fornecida pelo cliente`,
`Material de origem não é consumido pela aplicação`) recebem parágrafo de
"Exceção explícita — Login" dentro do próprio requisito, em vez de split em
sub-capabilities novas. Mantém a spec `identidade-visual` como fonte única da
identidade visual do produto, com o Login claramente marcado como o único desvio.

## Risks / Trade-offs

- **Peso do arquivo** (JPEG original, sem compressão adicional) pode pesar no
  carregamento do Login → `next/image` gera variantes otimizadas (AVIF/WebP) no
  build a partir do JPEG fonte; o arquivo fonte em si não é comprimido além do que
  já veio do cliente, para não alterar a fidelidade visual pedida.
- **Card fica bem mais alto** (imagem de até 260×440px aproximadamente, acima do
  formulário) → pode aproximar ou estourar o limite prático em viewport de 360px
  (requisito de spec "Largura mínima de viewport suportada"). Mitigação: tarefa de
  verificação explícita em 360px de largura, igual à que a spec já exige para
  outras telas; card e formulário devem continuar alcançáveis por rolagem vertical
  sem rolagem horizontal.
- **Duas cópias do arquivo podem divergir** (`docs/images/logo_despapelize.jpeg` e
  `apps/web/public/marca/login-hero.jpg`) se o cliente enviar uma arte revisada no
  futuro e só uma cópia for atualizada → mitigado pelo comentário cruzado (D1); é o
  mesmo modo de falha, com a mesma mitigação fraca por construção, que o `IconMarca`
  /`icon.svg` já assumem (D4 do change anterior).
- **`getByRole("heading")` pode não herdar o `alt` da imagem** dependendo da versão
  exata de `dom-accessibility-api` usada pelo projeto → verificado como tarefa (D3);
  se falhar, o teste é ajustado, não a decisão de design.

## Migration Plan

Sem migration de banco, contrato ou dado — mudança de apresentação estática do
frontend.

1. Copiar `docs/images/logo_despapelize.jpeg` para
   `apps/web/public/marca/login-hero.jpg`, sem edição.
2. `apps/web/app/login/page.tsx`: substituir o bloco do chip circular + `IconMarca`
   + `<h1>{NOME_PRODUTO}</h1>` pela imagem envolta em `<h1>` (D2/D3), com comentário
   apontando a origem (D1). Remover o import de `IconMarca` deste arquivo (não é
   mais usado no Login).
3. Rodar `pnpm --filter @setes/web test -- page.test.tsx` (Vitest, dentro de
   `apps/web`) e confirmar se `getByRole("heading", { name: "Despapelize" })`
   continua passando; ajustar o matcher só se necessário.
4. Verificar visualmente em 360px de largura (regra de viewport mínimo já vigente
   no produto) que o card do Login permanece operável.
5. `pnpm --filter @setes/web typecheck`.

**Rollback:** reverter o commit. Nenhum estado externo é criado — sem segredo, sem
bucket, sem recurso de infra, sem alteração de banco. O deploy anterior volta a
servir o chip circular anterior sem passo adicional.
