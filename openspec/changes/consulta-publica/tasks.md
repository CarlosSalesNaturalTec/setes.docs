## 1. Backend — schemas públicos (contrato sem dado sensível)

- [x] 1.1 Criar `app/schemas/consulta_publica.py` com `InteressadoPublicoResponse` (apenas `nome`; **sem** `documento`/`tipo_documento`) e `MovimentacaoPublicaResponse` (data, unidade origem/destino como sigla/nome, status; **sem** `responsavel_id`). Aceite: schemas não possuem nenhum campo de CPF/CNPJ nem de servidor (D1).
- [x] 1.2 Adicionar `ProcessoPublicoResponse` (número, assunto, tipo, status, unidade atual, data de criação, lista de interessados públicos, histórico simplificado) e `PesquisaPublicaResponse` paginado (itens + página + total). Aceite: modelo paginado com no máximo 20 itens por página (D5, US 7.2).

## 2. Backend — serviço de consulta (queries que ocultam sigiloso e dado pessoal)

- [x] 2.1 Criar `app/services/consulta_publica.py` com `consultar_por_numero(db, numero)` aplicando `WHERE numero = :n AND sigiloso = false`, retornando `None` tanto para inexistente quanto para sigiloso (indistinguível). Aceite: sigiloso e inexistente produzem o mesmo retorno vazio (D2, US 7.1 Cen.4).
- [x] 2.2 Implementar `pesquisar(db, assunto?, tipo_id?, data_inicio?, data_fim?, pagina)` com `WHERE sigiloso = false`, `ILIKE` no assunto, filtro por tipo e intervalo de `criado_em`, paginando 20/página. Aceite: sigilosos nunca aparecem; retorno paginado (US 7.2).
- [x] 2.3 Implementar montagem do histórico simplificado a partir de `Tramitacao`, filtrando aos eventos de movimentação (`despacho`, `devolucao`, `conclusao`, `arquivamento_automatico`) e omitindo `marcar_sigilo`/`remover_sigilo` e o responsável. Aceite: histórico só com movimentações, sem servidor (D3, US 7.1 Cen.1).

## 3. Backend — router público + rate limiting

- [x] 3.1 Adicionar `RATE_LIMIT_CONSULTA_PUBLICA = "60/minute"` em `app/rate_limit.py`. Aceite: constante disponível e reutilizável (D4).
- [x] 3.2 Registrar handler customizado de `RateLimitExceeded` (ou resposta de rota) que devolve HTTP 429 com "Muitas consultas realizadas. Aguarde alguns instantes e tente novamente." para as rotas públicas. Aceite: excesso responde com a mensagem exata do PRD (D4, RNF Segurança).
- [x] 3.3 Criar `app/routers/consulta_publica.py` (sem dependência de sessão/JWT) com `GET /publico/processos/{numero}` (404 padronizado quando vazio) e `GET /publico/processos` (pesquisa paginada), ambos com `@limiter.limit(RATE_LIMIT_CONSULTA_PUBLICA)`. Aceite: rotas acessíveis sem autenticação; 404 usa mensagem única para sigiloso e inexistente.
- [x] 3.4 Montar o router em `app/main.py` (`app.include_router(consulta_publica.router)`). Aceite: rotas aparecem no OpenAPI (`/health` continua ok).

## 4. Testes automatizados de backend (pytest) — LGPD e sigilo obrigatórios

- [x] 4.1 Teste: consulta por número de processo não sigiloso retorna os campos de andamento esperados (US 7.1 Cen.1). Aceite: 200 com número/assunto/tipo/status/unidade/data/histórico.
- [x] 4.2 Teste (dado pessoal): processo com interessado com CPF/CNPJ — a resposta pública contém `nome` e **não** contém CPF/CNPJ em nenhum campo (US 7.1 Cen.3, RF 36). Aceite: asserção explícita de ausência do documento.
- [x] 4.3 Teste (sigilo): processo sigiloso consultado pelo número exato retorna 404 com a **mesma** mensagem de número inexistente (US 7.1 Cen.4). Aceite: corpo idêntico ao do caso inexistente.
- [x] 4.4 Teste (sigilo): pesquisa por assunto que casaria com processo sigiloso não o retorna (US 7.2). Aceite: sigiloso ausente dos resultados.
- [x] 4.5 Teste: histórico simplificado não expõe nome de servidor nem eventos de sigilo (US 7.1 Cen.1, D3). Aceite: asserção de ausência de responsável e de `marcar_sigilo`/`remover_sigilo`.
- [x] 4.6 Teste: pesquisa combinada por tipo + período e paginação de 20/página (US 7.2 Cen.2). Aceite: filtro correto e no máximo 20 itens por página.
- [x] 4.7 Teste: rate limiting — exceder 60 req/min no mesmo IP retorna 429 com a mensagem do PRD (RNF Segurança). Aceite: 429 + mensagem exata.

## 5. Frontend — rota pública

- [x] 5.1 Criar página `app/consulta-publica/page.tsx` **fora** do `protected-shell`/`auth-provider`, com formulário de busca (número | assunto + tipo + período). Aceite: rota acessível sem login, sem redirecionar para `/login`.
- [x] 5.2 Implementar exibição do resultado por número (dados de andamento + histórico simplificado) e da lista paginada de pesquisa, consumindo os endpoints públicos via `lib/api.ts` sem Bearer token. Aceite: telas renderizam número/assunto/status/unidade e histórico; paginação funcional.
- [x] 5.3 Tratar mensagens de vazio ("Nenhum processo encontrado com o número informado" / "Nenhum processo encontrado para os filtros informados") e de rate limit. Aceite: cada estado exibe a mensagem correta do PRD.
- [x] 5.4 Teste unit (Vitest + RTL): componente de resultado não renderiza CPF/CNPJ mesmo se presente em dados de teste; estados de vazio exibem as mensagens corretas. Aceite: asserções passam.

## 6. Contrato de tipos

- [x] 6.1 Rodar `pnpm gen:types` e commitar o snapshot atualizado (`packages/api-types`). Aceite: `pnpm gen:types:check` passa (sem drift no CI).

## 7. Testes E2E (Playwright) — obrigatório para consulta pública

- [x] 7.1 E2E: cidadão sem autenticação consulta um processo não sigiloso pelo número e vê os dados de andamento e o histórico simplificado (US 7.1 Cen.1). Aceite: fluxo verde ponta a ponta.
- [x] 7.2 E2E: consulta pelo número de um processo sigiloso retorna "Nenhum processo encontrado com o número informado" (US 7.1 Cen.4). Aceite: mensagem idêntica à de inexistente; existência não revelada.
- [x] 7.3 E2E: pesquisa por assunto/tipo/período lista processos não sigilosos paginados e exibe a mensagem de vazio quando não há resultados (US 7.2). Aceite: lista e estado vazio corretos.
