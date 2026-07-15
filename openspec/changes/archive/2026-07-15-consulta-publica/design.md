## Context

O Épico 7 do PRD entrega a consulta pública — a única superfície do sistema acessível
sem autenticação, voltada ao Cidadão. O terreno já está preparado por changes
anteriores: a flag `Processo.sigiloso` (change `sigilo-de-processo`), o histórico
imutável `Tramitacao` (INSERT-only), o model `ProcessoInteressado` (nome + documento
CPF/CNPJ) e a infra `slowapi` (`app/rate_limit.py`, hoje aplicada só às rotas de
autenticação a `10/minute`). Não há tabela nova; este é um change de **leitura** com
duas preocupações centrais: **não vazar** (sigilosos e dados pessoais) e **resistir a
abuso** (rate limiting por IP).

Restrições herdadas: histórico imutável, máquina de estados de status, código de
domínio em português, contrato OpenAPI gerado (`pnpm gen:types`).

## Goals / Non-Goals

**Goals:**
- Endpoints públicos, sem autenticação, para consulta por número (US 7.1) e pesquisa
  por assunto/tipo/período paginada (US 7.2).
- Supressão de CPF/CNPJ e de nomes de servidores **na camada de serialização do
  backend**, não apenas na UI.
- Ocultação total de processos sigilosos, incluindo a não-revelação de existência na
  consulta por número exato.
- Rate limiting de 60 req/min por IP com a mensagem exata do RNF de Segurança.
- Rota pública no frontend fora dos guards de autenticação.

**Non-Goals:**
- Exibição de documentos anexados na consulta pública (Épico 3 ainda não existe).
- Canal LGPD / solicitação de anonimização (Épico 10 — change futuro).
- Exportação de resultados (fora do escopo do MVP).
- Rate limiting distribuído entre réplicas (mantém-se a limitação conhecida do
  `slowapi` em memória — ver Riscos).

## Decisions

### D1 — Schemas Pydantic públicos dedicados (sem CPF/CNPJ, sem servidor)

Em vez de reusar os schemas internos de processo e filtrar campos, criam-se schemas
**públicos** específicos (`ProcessoPublicoResponse`, `InteressadoPublicoResponse`,
`MovimentacaoPublicaResponse`) que simplesmente **não possuem** os campos sensíveis.
Assim a supressão é estrutural — é impossível o CPF/CNPJ ou o `responsavel_id`
"vazarem" por engano, pois o campo não existe no contrato. Alternativa descartada:
reusar schema interno com `exclude` — frágil, um novo campo sensível vazaria por padrão.

### D2 — Ocultação de sigiloso por filtro de query, não por checagem pós-carregamento

Todas as queries públicas aplicam `WHERE sigiloso = false` diretamente no SQL. A
consulta por número faz `WHERE numero = :n AND sigiloso = false`; um sigiloso e um
inexistente caem no mesmo ramo "não encontrado" (404 com a mensagem padronizada),
garantindo indistinguibilidade (US 7.1 Cen.4). Não se carrega o processo para depois
decidir — evita timing/erro que revele existência.

### D3 — Histórico simplificado: apenas eventos de movimentação

O histórico público deriva de `Tramitacao`, mas expõe só data, unidade origem, unidade
destino e status, e filtra os `tipo_evento` a eventos de **movimentação** (`despacho`,
`devolucao`, `conclusao`, `arquivamento_automatico`). Os eventos `marcar_sigilo`/
`remover_sigilo` são internos e **não** aparecem na consulta pública. `responsavel_id`
nunca é serializado (D1).

### D4 — Rate limiting: novo limite e handler com a mensagem do PRD

Adiciona-se `RATE_LIMIT_CONSULTA_PUBLICA = "60/minute"` em `app/rate_limit.py` e o
decorator `@limiter.limit(...)` nas rotas públicas. O handler default do `slowapi`
retorna 429 genérico; para produzir a mensagem exata do PRD ("Muitas consultas
realizadas. Aguarde alguns instantes e tente novamente.") registra-se um handler
customizado de `RateLimitExceeded` que devolve esse corpo. A liberação após 60s é
consequência natural da janela do `slowapi` (não requer estado extra).

### D5 — Rota pública no frontend fora do `protected-shell`

A página `app/consulta-publica/` é renderizada fora do `auth-provider`/`protected-shell`
(que hoje guardam as rotas autenticadas), consumindo os endpoints públicos via
`lib/api.ts` sem Bearer token. Formulário de busca (número | assunto+tipo+período),
lista paginada e tela de detalhe com o histórico simplificado.

### Diagrama de sequência — consulta por número

```
Cidadão            Frontend (/consulta-publica)      API pública (sem auth)        Postgres
   |  informa nº e "Consultar"  |                             |                        |
   |--------------------------->|                             |                        |
   |                            | GET /publico/processos/{nº} |                        |
   |                            |---------------------------->|                        |
   |                            |            [slowapi checa IP: <=60/min?]             |
   |                            |                             | SELECT ... WHERE       |
   |                            |                             |  numero=:n AND         |
   |                            |                             |  sigiloso=false        |
   |                            |                             |----------------------->|
   |                            |                             |<-----------------------|
   |                            |   200 ProcessoPublico       | (sem CPF/CNPJ, sem     |
   |                            |   OU 404 "Nenhum processo   |  nome de servidor)     |
   |                            |<----------------------------|                        |
   |   resultado ou "não encontrado" (sigiloso e inexistente = mesma resposta)         |
   |<---------------------------|                             |                        |
```

## Migrations

**Nenhuma migration Alembic.** O change não cria nem altera tabelas, colunas,
constraints ou enums. Usa apenas leitura de `processo`, `processo_interessado`,
`tipo_processo`, `unidade` e `tramitacao` já existentes. Índices atuais (`processo.numero`
único, FKs) atendem os padrões de acesso; se a pesquisa por assunto revelar lentidão em
volume, um índice adicional é otimização de follow-up, não pré-requisito.

## Risks / Trade-offs

- **Rate limiting em memória por réplica** (limitação herdada do `slowapi`, D6 do change
  de auth) → em múltiplas réplicas Cloud Run o teto efetivo é 60×N. Mitigação: aceitável
  para o MVP como camada anti-scraping básica; um limitador distribuído (ex.: Redis) é
  evolução futura, registrada como dívida conhecida.
- **Vazamento de dado pessoal por novo campo** → mitigado por D1 (schema público não
  possui os campos); teste automatizado obrigatório assegura ausência de CPF/CNPJ na
  resposta.
- **Revelação de existência de sigiloso por diferença de resposta/latência** → mitigado
  por D2 (mesmo ramo de código e mesma mensagem para sigiloso e inexistente).
- **Enumeração de números de processo** (o formato `AAAA/NNNNNN` é previsível) → o rate
  limiting reduz varredura em massa; o conteúdo exposto é intencionalmente público e sem
  dado pessoal, então a superfície de risco é limitada ao que já é transparência legal.

## Migration Plan

Deploy junto ao serviço `api` (rotas novas) e ao `web` (rota pública nova). Sem
migration, o rollback é apenas reverter o deploy — nenhuma alteração de dados a desfazer.
Validação pré-produção via traffic splitting do Cloud Run.

## Open Questions

- A pesquisa por assunto deve casar acento/caixa de forma insensível (ILIKE + unaccent)?
  Assumido: `ILIKE` case-insensitive no MVP; `unaccent` fica como melhoria se necessário.
