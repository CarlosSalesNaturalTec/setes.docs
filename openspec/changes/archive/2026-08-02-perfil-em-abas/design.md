## Context

`apps/web/app/perfil/page.tsx` renderiza hoje, em sequência vertical:

```
<h1>Meu Perfil</h1>
   dados do usuário + edição do nome
   <h2>Processos em que atuei</h2>   → perfil.processos_atuados
   <h2>Documentos assinados</h2>     → perfil.documentos_assinados (sempre vazio)
   <TrocarSenhaForm />
```

Todos os dados vêm de **uma única** chamada ao endpoint de "Meu Perfil"
(`MeuPerfilResponse`), já carregada de uma vez. `documentos_assinados` é um
placeholder: o Épico 4 (assinatura digital) foi movido para a Fase 2 por decisão
formalizada em 2026-07-27, e `openspec/config.yaml` registra explicitamente que
não deve haver change de assinatura sem decisão de retomada.

Fatos que enquadram o design:

- **Não há trabalho de backend.** Os quatro conteúdos já chegam juntos; abas são
  puramente uma questão de qual fragmento renderizar.
- `TrocarSenhaForm` já é um componente isolado (`components/trocar-senha-form.tsx`)
  — vai para dentro de uma aba sem refatoração.
- O projeto não possui um componente de abas; será o primeiro.

## Goals / Non-Goals

**Goals:**

- Quatro abas, preservando integralmente o conteúdo atual.
- Aba ativa refletida na URL, sobrevivendo a recarga e a compartilhamento de link.
- Navegação acessível por teclado, com semântica ARIA correta.

**Non-Goals:**

- **Nenhuma alteração de backend, contrato ou banco.**
- **Nenhuma retomada do Épico 4.** A aba de documentos assinados continua um
  placeholder vazio; implementar assinatura exige decisão explícita de produto,
  fora deste change.
- Nenhuma mudança nas regras de edição do nome, de troca de senha ou de
  composição da lista de processos atuados.
- Sem carregamento sob demanda por aba (*lazy loading*) — ver D2.

## Decisions

### D1 — Abas controladas por query string

A aba ativa vive na URL como `?aba=perfil|senha|processos|assinados`, lida e
escrita com os utilitários de roteamento do App Router. Ausente ou inválida, o
padrão é `perfil`.

Motivos: recarregar a página não devolve o usuário à primeira aba; um link pode
apontar direto para "Processos em que atuei"; e o botão "voltar" do navegador
percorre as abas de forma previsível. Alternativa rejeitada: estado local
(`useState`) — perde tudo isso e é indistinguível em custo.

### D2 — Sem carregamento sob demanda por aba

Todo o conteúdo já vem numa única resposta do endpoint de "Meu Perfil", que é
pequena. As abas apenas escolhem o que renderizar. Introduzir uma chamada por
aba criaria quatro estados de carregamento e quatro tratamentos de erro para
resolver um problema que não existe.

Consequência: trocar de aba é instantâneo, sem *spinner*.

### D3 — Aba "Documentos assinados" permanece placeholder explícito

A aba existe (o cliente a pediu nominalmente) e exibe mensagem informando que a
assinatura digital de documentos será disponibilizada em fase futura do produto.
NÃO SHALL haver botão "Assinar", campo de certificado ou qualquer elemento que
sugira funcionalidade disponível — a interface não pode prometer o que o produto
não entrega.

Isso mantém a coerência com `openspec/config.yaml`, que declara o Épico 4 fora
de escopo e o placeholder vazio como estado corrente esperado.

### D4 — Semântica ARIA de abas

Estrutura com `role="tablist"`, `role="tab"` (com `aria-selected` e
`aria-controls`) e `role="tabpanel"` (com `aria-labelledby`). Navegação por setas
esquerda/direita entre as abas e ativação por Enter/Espaço, no padrão de widget
de abas. Cada aba é um `<button>`, não um link — a mudança de aba não navega
para outra página, apenas atualiza a query string.

### Fluxo principal

```
Usuário           web (/perfil)                     api
   │ acessa            │                             │
   │───────────────────▶ GET /usuarios/meu-perfil    │
   │                   │─────────────────────────────▶
   │                   │◀───────────────────────────── dados + processos
   │                   │                                + documentos_assinados
   │                   │   D2: uma resposta alimenta as quatro abas
   │ vê aba "Meu perfil"                             │
   │ clica "Processos em que atuei"                  │
   │───────────────────▶ (sem nova chamada à API)    │
   │                   │   D1: URL vira ?aba=processos
   │                   │   D2: renderiza fragmento já carregado
   │ recarrega a página│                             │
   │───────────────────▶ GET /usuarios/meu-perfil    │
   │                   │   D1: aba "processos" restaurada da URL
```

## Risks / Trade-offs

- [Abas escondem conteúdo que antes era alcançável por rolagem] → é o objetivo do
  pedido; a mitigação é a aba ativa na URL (D1), que torna cada seção endereçável
  diretamente.
- [Aba vazia de documentos assinados pode ser lida como defeito] → mensagem
  explícita informando que se trata de funcionalidade de fase futura (D3), em vez
  de um vazio silencioso.
- [Primeiro componente de abas do projeto pode divergir do padrão visual] →
  construído com os tokens de estilo já em uso, e colocado em `components/` para
  reuso, evitando uma segunda implementação divergente mais adiante.
- [Query string pode receber valor inválido por edição manual da URL] → valor
  desconhecido cai no padrão `perfil`, sem erro.
- [Implementar antes de `setores-e-cadastro-usuario` obrigaria revisitar a aba de
  perfil] → registrado na proposta como recomendação de ordem, não como
  dependência técnica.
