## Why

O SETES.DOCS tem infraestrutura provisionada (`bootstrap-infraestrutura`, arquivado) mas nenhuma tabela de negócio, nenhum usuário e nenhuma estrutura organizacional. Nenhum outro épico pode ser implementado sem isso: Processo (Épico 2) precisa de `usuario`, `unidade`, `tipo_processo` e `roteiro` para existir; toda tela do sistema exige login. Este change estabelece a base de identidade (quem pode entrar, com qual perfil) e a base organizacional (quais unidades existem, por qual caminho cada tipo de processo tramita) sobre a qual todo o restante do produto é construído.

## What Changes

- **US 8.0 — Inicialização do sistema**: rota de setup disponível apenas enquanto não existir nenhum Administrador; cria o Administrador root + a primeira unidade administrativa numa única transação; desabilita-se permanentemente após o primeiro uso.
- **US 1.1 / 1.2 — Cadastro de usuários**: Administrador cadastra usuários em qualquer unidade com qualquer perfil (Servidor/Gestor/Administrador); Gestor cadastra apenas Servidores nas unidades que gerencia (US 8.6b). Envio de e-mail com link de primeiro acesso (48h, reaproveita fila de e-mail assíncrono de `bootstrap-infraestrutura`).
- **US 1.6 — Primeiro acesso**: ativação de conta via link de validade configurável (padrão 48h, hardcoded neste change — parametrização fica para US 8.5, fora de escopo), com validação de complexidade de senha e tratamento de link expirado/já usado.
- **US 1.3 — Login**: autenticação por e-mail/senha, JWT assinado com HS256 reaproveitando o segredo `jwt-signing-key` (D4 do bootstrap), bloqueio temporário após 3 tentativas incorretas (30 min), recuperação de senha por link (2h) sem enumeração de e-mail cadastrado.
- **US 1.7 — Troca de senha**: troca autenticada com verificação de senha atual e histórico das últimas 6 senhas (hardcoded — parametrização é US 8.5).
- **US 1.8 / 1.9 — Sessão**: expiração por inatividade (padrão 30 min) com aviso prévio, logout manual, múltiplas sessões concorrentes independentes (sem invalidação cruzada).
- **US 1.10 — Reset de senha por Administrador**: invalida senha atual, envia link de redefinição, registra em log de auditoria.
- **US 1.4 / 1.5 — Controle de acesso por unidade e perfil**: estabelece as primitivas de autorização (perfil + unidade do usuário + unidades geridas) como dependências FastAPI reutilizáveis, incluindo o cenário de acesso negado com registro em log de segurança. **Escopo parcial**: como as tabelas `processo`/`documento` ainda não existem, a aplicação efetiva do filtro por unidade ao Kanban (US 1.4) e a listagem de processos/documentos assinados em "Meu Perfil" (US 1.5) ficam para o change do Épico 2/3, que consumirá essas primitivas. Neste change, "Meu Perfil" exibe dados cadastrais e os estados vazios ("Nenhum processo registrado", "Nenhum documento assinado" — US 1.5 Cenário 2).
- **US 8.1 — Unidades administrativas**: CRUD de unidade (nome, sigla, gestor responsável), com bloqueio de desativação enquanto houver processos em andamento (regra registrada agora; a contagem real de processos pendentes é aplicada quando `processo` existir — até lá, a validação considera zero processos em andamento).
- **US 8.6 — Vínculo servidor-unidade**: relação 1:1 obrigatória (um Servidor pertence a exatamente uma unidade por vez); transferência substitui o vínculo sem apagar o histórico de atuação.
- **US 8.6b — Unidades geridas por Gestor**: relação N:N entre Gestor e unidades geridas, distinta do vínculo 1:1 de Servidor.
- **US 8.2 — Tipos de processo e roteiros**: CRUD de tipo de processo com roteiro de tramitação (sequência ordenada de unidades), validação de roteiro não vazio, nome único, e versionamento (processos já criados mantêm o roteiro vigente no momento da criação — decisão de modelagem detalhada no design).

**Fora de escopo deste change** (US do Épico 8 não solicitadas): US 8.3 (permissão de Auditor), US 8.4 (desativação de usuário), US 8.5 (parâmetros operacionais configuráveis — os valores usados aqui são os defaults do PRD, hardcoded), US 8.7 (restauração de documentos). Ficam para changes futuros.

## Capabilities

### New Capabilities
- `inicializacao-sistema`: setup único do sistema (US 8.0) — Administrador root + primeira unidade, autodesabilitação.
- `autenticacao`: login, primeiro acesso, troca/recuperação/reset de senha, sessão e bloqueio por tentativas (US 1.3, 1.6, 1.7, 1.8, 1.9, 1.10).
- `gestao-usuarios`: cadastro de usuários por Administrador/Gestor, vínculo Servidor↔unidade (1:1) e Gestor↔unidades (N:N) (US 1.1, 1.2, 8.6, 8.6b).
- `controle-acesso-por-unidade`: primitivas de autorização por perfil/unidade, tela "Meu Perfil" e log de acesso negado (US 1.4, 1.5).
- `unidades-administrativas`: CRUD de unidade administrativa (US 8.1).
- `tipos-processo-e-roteiros`: CRUD de tipo de processo e definição/versionamento de roteiro de tramitação (US 8.2).

### Modified Capabilities
- (nenhuma — não há specs pré-existentes que mudem; `plataforma-gcp`, `conectividade-e-seguranca`, `rotinas-agendadas` e `fila-notificacoes` são infraestrutura consumida, não modificada)

## Impact

- **Dependência de change anterior:** requer `bootstrap-infraestrutura` arquivado — reutiliza o Cloud SQL privado + baseline Alembic (tasks 3.x, 9.1), o segredo `jwt-signing-key` (D4, HS256) e a `sa-api` já com `secretAccessor` sobre ele, e a fila de e-mail assíncrono (Cloud Tasks) para o envio de links de primeiro acesso/recuperação.
- **Tabelas PostgreSQL novas** (primeira migration Alembic de negócio do projeto):
  - `usuario` (nome, email único, senha_hash, perfil enum [servidor|gestor|administrador], status enum [pendente_primeiro_acesso|ativo|inativo], unidade_id FK → `unidade`, tentativas_login_falhas, bloqueado_até)
  - `unidade` (nome, sigla, gestor_responsavel_id FK → `usuario` nullable, ativo)
  - `unidade_gestor` (gestor_id FK → `usuario`, unidade_id FK → `unidade`) — N:N para US 8.6b
  - `tipo_processo` (nome único, ativo)
  - `roteiro` (tipo_processo_id FK → `tipo_processo`, versão/vigência — ver design)
  - `roteiro_etapa` (roteiro_id FK → `roteiro`, unidade_id FK → `unidade`, ordem)
  - `token_autenticacao` (usuario_id FK → `usuario`, tipo [primeiro_acesso|recuperacao_senha], token_hash, expira_em, usado_em)
  - `senha_historico` (usuario_id FK → `usuario`, senha_hash, criado_em)
  - `log_seguranca` (usuario_id FK nullable, tipo_evento, contexto, criado_em) — acesso negado, reset de senha por Admin, bloqueio por tentativas
- **Secret Manager:** nenhum segredo novo — reaproveita `jwt-signing-key` (assinatura/validação JWT HS256) e `sendgrid-api-key` (envio de e-mails transacionais), ambos já provisionados no bootstrap.
- **Cloud Storage:** nenhum bucket novo — este change não trata documentos.
- **LGPD:** `usuario` armazena dados pessoais funcionais (nome, e-mail) de servidores/gestores/administradores do próprio órgão. Base legal: execução de política pública / vínculo funcional, não consentimento do titular. Retenção: enquanto o vínculo funcional existir; desativação (US 8.4, change futuro) marca o registro como inativo sem apagar histórico, preservando a imutabilidade de tramitação já estabelecida como regra do projeto. `log_seguranca` registra IP/user-agent das tentativas de acesso negado — também dado pessoal, sujeito à mesma política de retenção que os demais logs de auditoria do sistema. Este change não introduz dados de interessados externos (CPF/CNPJ de partes de processo) — isso é escopo do Épico 2.
- **Código:** primeira migration de negócio em `apps/api` (SQLAlchemy 2.x + Alembic); novos routers/services de autenticação, usuários, unidades e tipos de processo/roteiro; dependências FastAPI de autorização (perfil + escopo de unidade) reutilizáveis pelos épicos seguintes; telas Next.js de login, primeiro acesso, recuperação de senha, "Meu Perfil", setup inicial, e CRUDs administrativos de usuário/unidade/tipo de processo.
