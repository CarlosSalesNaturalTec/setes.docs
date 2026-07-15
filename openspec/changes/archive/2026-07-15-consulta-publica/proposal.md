## Why

O cidadão (persona sem autenticação) não tem hoje nenhuma forma de acompanhar o
andamento de um processo — precisa se deslocar ou telefonar ao órgão. O Épico 7 do
PRD entrega a transparência pública que é uma das metas de sucesso do produto
("redução de 50% nas consultas presenciais/telefônicas"). Além disso, o change
anterior `sigilo-de-processo` (US 2.6) introduziu a flag `sigiloso` cuja **ocultação
efetiva foi explicitamente adiada para o Épico 7** — sem a consulta pública, essa
marcação ainda não protege nada observável. Este change fecha esse laço.

## What Changes

- Novo endpoint **público, sem autenticação** de consulta de processo por número
  (US 7.1), retornando número, assunto, tipo, status atual, unidade atual, data de
  criação e histórico simplificado de movimentações (datas + unidades percorridas),
  **sem expor nomes de servidores**.
- Novo endpoint **público** de pesquisa por assunto, tipo de processo e período,
  com resultados paginados (20 por página) (US 7.2).
- **Ocultação de processos sigilosos** em todos os resultados públicos: consulta pelo
  número exato de um processo sigiloso retorna a mesma mensagem de "não encontrado",
  para não revelar sua existência (US 7.1 Cen.4).
- **Proteção de dados pessoais (LGPD):** o nome do interessado é exibido, mas CPF/CNPJ
  **nunca** aparecem na consulta pública (US 7.1 Cen.3 / RF 36).
- **Rate limiting** de 60 req/min por IP nos endpoints públicos, reutilizando a infra
  `slowapi` já montada (`app/rate_limit.py`), com a mensagem de excesso do RNF de
  Segurança e liberação automática após 60s.
- Nova rota **pública** no frontend (`/consulta-publica`), fora do `protected-shell`/
  `auth-provider`, com formulário de busca, lista paginada e tela de detalhe do processo.
- Regeneração do contrato de tipos (`pnpm gen:types`), pois há rotas novas no OpenAPI.

## Capabilities

### New Capabilities
- `consulta-publica`: consulta e pesquisa pública de processos sem autenticação
  (por número, assunto, tipo e período), com ocultação de processos sigilosos e de
  dados pessoais (CPF/CNPJ), paginação e rate limiting por IP.

### Modified Capabilities
<!-- Nenhuma. A ocultação efetiva de processos sigilosos já estava prevista como
     responsabilidade do Épico 7 na spec `sigilo-processo` ("a ocultação efetiva é
     implementada no Épico 7"); portanto é um requisito NOVO desta capability, não uma
     alteração de requisito da capability de sigilo. Os endpoints apenas leem dados já
     modelados por `processos` e `workflow-tramitacao` — sem mudança de requisito neles. -->

## Impact

- **Depende de** (changes arquivados): `sigilo-de-processo` (flag `sigiloso`),
  `processos-e-workflow` (processo, interessados, histórico de tramitação).
- **Tabelas PostgreSQL:** nenhuma nova e nenhuma alterada. Leitura apenas de
  `processo`, `processo_interessado`, `tipo_processo` e do histórico imutável de
  tramitação já existentes.
- **Segredos / buckets:** nenhum segredo novo no Secret Manager; nenhum bucket novo
  no Cloud Storage.
- **Tratamento LGPD:** a consulta pública **não coleta** dados pessoais; ela apenas
  **restringe a exibição** — CPF/CNPJ dos interessados jamais são serializados na
  resposta pública (filtro na camada de schema, não só no frontend). Nome do
  interessado é exibido por já ser informação de andamento processual. Não há retenção
  nova nem anonimização adicional neste change.
- **Backend:** novo `app/routers/consulta_publica.py` (montado em `main.py`), novos
  schemas Pydantic públicos, uso de `app/rate_limit.py`. Sem migrations Alembic.
- **Frontend:** nova rota pública `app/consulta-publica/`; ajuste no roteamento para
  que ela não passe pelos guards de autenticação.
- **Contrato:** `packages/api-types` regenerado (`pnpm gen:types`); o CI de
  `types-drift` falha se o snapshot ficar defasado.
