## Context

A estrutura organizacional hoje tem **um nível**: `unidade` (id, nome, sigla,
ativo, gestor_responsavel_id) e `usuario.unidade_id`. Toda autorização deriva
dessa coluna via `security/autorizacao.py::tem_acesso_a_unidade` e
`services/processo_consulta.py::unidades_visiveis`.

O cliente pediu um segundo nível (Setor) e novos campos de cadastro. O gatilho
real é a tramitação manual: a tela de tramitação precisa de
`unidade → setor → servidor` em cascata.

Fatos que enquadram o design:

- `usuario.unidade_id` já é **nullable** — Administrador pode não ter unidade.
  A obrigatoriedade nova é só do perfil **Servidor**, e é condicional ao perfil,
  portanto não cabe em `NOT NULL` de coluna.
- O padrão de "nunca excluir, só desativar" já existe em `unidades` e em
  `usuarios` (`StatusUsuario.INATIVO`) — Setor segue o mesmo.
- O banco em avaliação **pode ser refeito** (dados são de teste, decisão do
  cliente), o que dispensa backfill defensivo — mas as migrations continuam
  escritas para aplicar sobre a base existente, sem depender disso.
- Este change **não toca autorização**: o escopo de acesso continua sendo a
  Unidade. Setor é organização e roteamento, não uma nova fronteira de permissão.

## Goals / Non-Goals

**Goals:**

- Tabela `setor` com CRUD do Administrador, análoga a `unidade`.
- `usuario.setor_id` com validação de coerência (setor pertence à unidade do
  usuário) e obrigatoriedade para Servidor.
- Campos `telefone`, `cargo`, `chefia_direta` no cadastro e no perfil.
- Modal de cadastro + filtro por nome no índice de `/admin/usuarios`.

**Non-Goals:**

- **Nenhuma mudança em autorização.** `tem_acesso_a_unidade`,
  `unidades_visiveis`, `require_acesso_unidade` e as regras de sigilo ficam
  intocadas. Setor não vira fronteira de permissão neste change nem nos
  seguintes.
- Nenhuma hierarquia recursiva de setor (sub-setor). Um nível só.
- Nenhuma mudança em tramitação, Kanban, dashboard ou notificações — são os
  changes `tramitacao-manual` e `kanban-por-servidor`.
- `chefia_direta` **não** vira FK nem hierarquia navegável (decisão do cliente).

## Decisions

### D1 — `setor` como tabela própria, 1:N com `unidade`

```
unidade (1) ────< setor (N) ────< usuario (N)
```

`setor`: `id` uuid PK, `unidade_id` FK→`unidade` NOT NULL, `nome` varchar(200)
NOT NULL, `sigla` varchar(20) NOT NULL, `ativo` boolean NOT NULL default true.
Unicidade de `(unidade_id, sigla)` por `UniqueConstraint` — siglas podem repetir
entre unidades diferentes (duas unidades podem ter um "GAB"), mas não dentro da
mesma. Espelha o formato de `unidade` deliberadamente: mesmo CRUD, mesmo
vocabulário de tela, menor custo cognitivo.

Alternativa rejeitada: `setor` como campo texto em `usuario`. Não permitiria os
selects em cascata da tela de tramitação, nem listar "servidores do setor X".

### D2 — Obrigatoriedade de setor é do **perfil**, validada na aplicação

`usuario.setor_id` é **nullable no schema** e obrigatório **apenas para
`PerfilUsuario.SERVIDOR`**, validado em `services/usuarios` no cadastro e na
edição. Motivo: a regra depende de outra coluna (`perfil`), e um `CHECK`
condicional em Postgres travaria a transição de perfil de um usuário existente
numa ordem de UPDATE infeliz. Mesmo tratamento já dado a `unidade_id`.

Validação adicional em toda escrita: `setor.unidade_id == usuario.unidade_id`.
Um setor de outra unidade é rejeitado com 422 — não é acesso negado (não é
questão de permissão), é dado inconsistente.

### D3 — Desativação em cascata, com guarda de servidores ativos

Espelha a regra já existente de Unidade:

```
desativar Unidade  →  desativa todos os Setores dela (cascata)
desativar Setor    →  bloqueado se existir Servidor ATIVO com esse setor_id
                      (422, mensagem listando a contagem)
reativar Unidade   →  NÃO reativa setores automaticamente (reativação é explícita)
```

A assimetria (cascata desativa, reativação não) é intencional: desativar é
contenção — deve ser total; reativar é decisão administrativa item a item.
Setor **nunca** é excluído — histórico de tramitação futuro vai referenciá-lo
(change `tramitacao-manual`), e histórico é imutável.

### D4 — `chefia_direta` como texto livre

`varchar(200)` nullable, sem FK. Decisão do cliente: a chefia direta pode ser
alguém que não é usuário do sistema (chefia externa, cargo político, terceirizado).
Uma FK obrigaria cadastrar essas pessoas como usuários só para preencher o campo.
Custo aceito: não há hierarquia navegável nem validação de existência.

### D5 — Filtro por nome no backend, não no front

`GET /usuarios` ganha query param `nome: str | None`, aplicando
`Usuario.nome.ilike(f"%{nome}%")`. Filtrar no backend mantém o comportamento
correto quando a lista crescer além de uma página e evita baixar todos os
usuários para filtrar no cliente. O front faz *debounce* de 300 ms.

### D6 — Modal de cadastro reaproveita o formulário existente

O formulário inline de `/admin/usuarios` é extraído para um componente e
montado dentro de um modal acionado por botão "Novo usuário". Nenhuma mudança de
contrato de API — é reorganização de UI. O espaço liberado no índice recebe o
campo de filtro (D5).

### D7 — Migrations `0020` e `0021`

Duas revisions sequenciais escritas à mão (schema antes de endpoint):

- `0020_setor` — cria a tabela `setor` + índice em `unidade_id` + unique
  `(unidade_id, sigla)`. `down_revision = "0019_ix_unidade_origem"`.
- `0021_usuario_setor_e_campos` — adiciona `usuario.setor_id` (FK, nullable),
  `usuario.telefone`, `usuario.cargo`, `usuario.chefia_direta`.
  `down_revision = "0020_setor"`.

Separadas porque a FK de `usuario` depende da tabela criada em `0020` e porque
`downgrade` de uma não deve derrubar a outra. Ambas passam por `ruff check`.

### Fluxo principal

```
Administrador           web (/admin/unidades)          api
     │ abre a unidade         │                         │
     │────────────────────────▶ GET /unidades/{id}/setores
     │                        │─────────────────────────▶
     │                        │◀─────────────────────────
     │ "Novo setor"           │                         │
     │────────────────────────▶ POST /unidades/{id}/setores
     │                        │─────────────────────────▶ valida sigla única
     │                        │                          na unidade
     │                        │◀───────────────────────── 201
     │                        │                         │
     │ (/admin/usuarios)      │                         │
     │ "Novo usuário" → modal │                         │
     │────────────────────────▶ POST /usuarios          │
     │  perfil=servidor       │─────────────────────────▶ D2: setor obrigatório
     │  unidade + setor       │                          + setor.unidade == usuario.unidade
     │  telefone/cargo/chefia │◀───────────────────────── 201
```

## Risks / Trade-offs

- [Servidores já cadastrados ficam sem setor e violam a regra do D2] → a
  validação incide sobre **escritas** (cadastro/edição), não sobre linhas
  existentes; o banco de avaliação será refeito de qualquer forma. A tela de
  administração sinaliza servidores sem setor para regularização.
- [Setor sem fronteira de permissão pode surpreender o cliente] → decisão
  explícita e registrada: a visão do Kanban estreita para o indivíduo
  (change `kanban-por-servidor`), mas o **acesso** continua por unidade. Um
  colega da mesma unidade segue podendo abrir o processo. Cenário de acesso
  negado explícito nas specs para deixar a fronteira inequívoca.
- [`chefia_direta` em texto livre gera grafias divergentes da mesma pessoa] →
  aceito por decisão do cliente; o campo é informativo, não alimenta nenhuma
  regra de negócio nem roteamento.
- [Cascata de desativação de Unidade pode desativar setores em massa sem
  intenção] → a tela confirma exibindo a contagem de setores afetados antes de
  aplicar, e a operação é reversível (reativação item a item, D3).
- [Duas migrations para um change simples] → preferido a uma migration única que
  misture criação de tabela e alteração de outra: o `downgrade` fica limpo e a
  cadeia sequencial permanece legível.
