## 1. Schema — migration Alembic `0002_identidade_estrutura_organizacional`

- [x] 1.1 Criar enums (`perfil_usuario`, `status_usuario`, `tipo_token_autenticacao`, `tipo_evento_log`) e tabela `unidade` (sem `gestor_responsavel_id` ainda) — aceite: `alembic upgrade head` roda limpo a partir de `0001_baseline`
- [x] 1.2 Criar tabela `usuario` (com `unidade_id` FK → `unidade`, `email` unique, contadores de bloqueio) — aceite: FK e unique constraint visíveis via `\d usuario` no psql
- [x] 1.3 `ALTER TABLE unidade ADD COLUMN gestor_responsavel_id` FK → `usuario` (nullable) — aceite: ciclo de criação `unidade`↔`usuario` resolvido sem erro de dependência circular
- [x] 1.4 Criar tabela `unidade_gestor` (PK composta `gestor_id`, `unidade_id`, ambas FK) — aceite: insere e rejeita duplicata de par (gestor, unidade)
- [x] 1.5 Criar tabelas `tipo_processo`, `roteiro` (com índice único parcial `WHERE vigente`) e `roteiro_etapa` (unique em `roteiro_id, ordem`) — aceite: tentar inserir dois `roteiro` vigentes para o mesmo `tipo_processo_id` viola a constraint
- [x] 1.6 Criar tabelas `token_autenticacao` (unique em `token_hash`) e `senha_historico` — aceite: FKs para `usuario` corretas, `downgrade()` remove as duas tabelas
- [x] 1.7 Criar tabela `log_seguranca` (usuario_id FK nullable, tipo_evento, contexto jsonb, criado_em) — aceite: insere linha com `usuario_id=NULL` sem erro (caso de e-mail não cadastrado)
- [x] 1.8 Criar tabela `sessao` (usuario_id FK, `jti` unique, criada_em, ultima_atividade, revogada_em nullable, ip, user_agent) — aceite: índice único em `jti` e índice simples em `usuario_id` presentes
- [x] 1.9 Criar tabela singleton `sistema_config` (id fixo=1, `inicializado boolean default false`) com seed `INSERT` na própria migration — aceite: `SELECT inicializado FROM sistema_config WHERE id=1` retorna `false` logo após a migration
- [x] 1.10 Escrever `downgrade()` completo (ordem reversa de todas as tabelas/enums de 1.1–1.9) e testar `alembic downgrade -1` seguido de `alembic upgrade head` — aceite: ciclo up/down/up roda sem erro em banco local

## 2. Segurança — primitivas base

- [x] 2.1 Implementar hashing de senha com `passlib[bcrypt]` (custo 12) em `app/security/senha.py` (`hash_senha`, `verificar_senha`) — aceite: hash de duas chamadas para a mesma senha difere (salt), `verificar_senha` confirma ambas
- [x] 2.2 Teste automatizado de `app/security/senha.py` (hash determinístico na verificação, senha errada rejeitada) — **obrigatório por tocar dado pessoal (senha)**
- [x] 2.3 Implementar emissão/validação de JWT HS256 em `app/security/jwt.py` reaproveitando `Settings.jwt_signing_key` (claims `sub`, `jti`, `exp`) — aceite: token expirado é rejeitado, assinatura inválida é rejeitada
- [x] 2.4 Implementar `app/security/sessao.py`: criar sessão (INSERT em `sessao` + emissão de JWT), validar sessão (`jti` não revogado e `ultima_atividade` dentro do timeout, sliding update), revogar sessão (logout) — aceite: sessão expirada por inatividade é rejeitada mesmo com JWT ainda não expirado por `exp`
- [x] 2.5 Teste automatizado de `app/security/sessao.py`: criação, sliding window, expiração por inatividade, revogação — **obrigatório por tocar dado pessoal (sessão vinculada a usuário)**
- [x] 2.6 Implementar dependências FastAPI `get_current_user`, `require_perfil(*perfis)`, `require_acesso_unidade(unidade_id)` em `app/security/autorizacao.py`, gravando `log_seguranca` (tipo_evento=`acesso_negado`) em toda rejeição — aceite: Servidor de unidade A é rejeitado ao tentar acessar recurso escopado à unidade B, e a rejeição gera uma linha em `log_seguranca`
- [x] 2.7 Teste automatizado de `app/security/autorizacao.py` cobrindo os três perfis (Servidor, Gestor, Administrador) e o cenário de acesso negado com log gravado — **obrigatório (regra de visibilidade por unidade/perfil)**
- [x] 2.8 Implementar `app/email/queue.py` (`enqueue_email`) usando `google-cloud-tasks`, criando task na fila `emails` com nome = `event_id` (dedup nativo) apontando para `POST /internal/tasks/email` com OIDC `sa-tasks-invoker` — aceite: chamada local com emulador/mocked client gera task com nome determinístico a partir do `event_id`
- [x] 2.9 Middleware/dependência de rate limiting (`slowapi`, 10 req/min/IP) aplicável a `/auth/login`, `/auth/recuperar-senha`, `/auth/primeiro-acesso` — aceite: 11ª requisição no mesmo minuto/IP recebe 429

## 3. Inicialização do sistema (US 8.0)

- [x] 3.1 Endpoint `POST /setup` — dentro de uma transação: `UPDATE sistema_config SET inicializado=true WHERE id=1 AND inicializado=false RETURNING id`; se não retornar linha, 409 "Sistema já inicializado"; se retornar, cria Administrador root (hash de senha, status Ativo) e a primeira `unidade` — aceite: chamada dupla concorrente resulta em exatamente um Administrador criado
- [x] 3.2 Envio de e-mail de confirmação ao Administrador root via `enqueue_email` (event_id=`setup-confirmacao:{usuario_id}`) — aceite: task enfileirada após commit da transação de setup
- [x] 3.3 Endpoint `GET /setup/status` (verifica se `sistema_config.inicializado`) para o frontend decidir se mostra a tela de setup ou login — aceite: retorna `false` em banco vazio, `true` após setup concluído
- [x] 3.4 Teste automatizado: setup em banco vazio cria Administrador+unidade; setup após já inicializado retorna 409; corrida de duas requisições simultâneas produz um único Administrador — **obrigatório por tocar dado pessoal (Administrador root)**

## 4. Autenticação — login, sessão e logout

- [x] 4.1 Endpoint `POST /auth/login` — valida credenciais, verifica `bloqueado_ate`, incrementa/reseta `tentativas_login_falhas`, bloqueia após 3 falhas (30 min), cria sessão (2.4) em caso de sucesso — aceite: 3 tentativas incorretas bloqueiam a conta e disparam e-mail de alerta (`enqueue_email`, event_id=`alerta-bloqueio:{usuario_id}:{timestamp}`)
- [x] 4.2 Rejeitar login de usuário com `status=inativo` sem incrementar contador nem enviar alerta — aceite: mensagem "Conta desativada" e nenhuma task de e-mail enfileirada
- [x] 4.3 Endpoint `POST /auth/logout` — marca `sessao.revogada_em=now()` para a sessão do token atual — aceite: chamada subsequente com o mesmo token é rejeitada por `get_current_user`
- [x] 4.4 Endpoint `GET /auth/me` (ou equivalente) usado pelo frontend para checagem de sessão viva e sliding refresh — aceite: resposta inclui `exp` atualizado a cada chamada válida
- [x] 4.5 Teste automatizado: login válido, bloqueio após 3 falhas, login durante bloqueio não reseta o timer, desbloqueio automático após 30 min (mock de tempo), login com conta inativa — **obrigatório por tocar dado pessoal (credenciais)**
- [x] 4.6 Teste automatizado: múltiplas sessões concorrentes (dois logins do mesmo usuário) permanecem independentes; logout de uma não afeta a outra — **obrigatório (US 1.9)**

## 5. Autenticação — primeiro acesso e recuperação de senha

- [x] 5.1 Serviço `app/services/tokens.py`: gerar token opaco (`secrets.token_urlsafe`), persistir apenas o hash sha256 em `token_autenticacao` com `tipo` e `expira_em` (48h primeiro acesso / 2h recuperação) — aceite: valor puro do token nunca é persistido, apenas retornado para uso no e-mail
- [x] 5.2 Endpoint `POST /auth/primeiro-acesso/{token}` — valida token (não expirado, não usado), valida complexidade de senha, seta `senha_hash`, `status=ativo`, `usado_em=now()` no token — aceite: reuso do mesmo token após sucesso retorna erro "Link já utilizado"
- [x] 5.3 Endpoint `POST /auth/recuperar-senha` — sempre responde com a mensagem genérica; se o e-mail existir, gera token (5.1, tipo=recuperacao_senha) e enfileira e-mail; se não existir, não enfileira nada — aceite: tempo de resposta não varia perceptivelmente entre e-mail existente/inexistente (evitar timing leak trivial)
- [x] 5.4 Endpoint `POST /auth/redefinir-senha/{token}` — valida token de recuperação, aplica nova senha, zera `tentativas_login_falhas`/`bloqueado_ate` na mesma transação (desbloqueio automático) — aceite: conta bloqueada é desbloqueada após redefinição bem-sucedida
- [x] 5.5 Integrar 3.2/4.1/5.2/5.4 ao `enqueue_email` com os `event_id` definidos no design (D10) — aceite: cada fluxo gera exatamente uma task por evento, idempotente por nome
- [x] 5.6 Teste automatizado: primeiro acesso com link válido/expirado/já usado/senha fraca; recuperação com e-mail cadastrado/não cadastrado; recuperação durante bloqueio desbloqueia a conta — **obrigatório por tocar dado pessoal (senha, e-mail)**

## 6. Autenticação — troca de senha e reset administrativo

- [x] 6.1 Endpoint `POST /auth/trocar-senha` (autenticado) — valida senha atual, valida complexidade da nova, valida contra `senha_historico` (últimas 6), grava a senha antiga em `senha_historico` antes de trocar — aceite: reuso de qualquer uma das últimas 6 senhas é rejeitado
- [x] 6.2 Endpoint `POST /admin/usuarios/{id}/resetar-senha` (Administrador) — rejeita se `status != ativo`; caso contrário invalida a senha atual (força redefinição via token de recuperação), envia link, grava `log_seguranca` (tipo_evento=`reset_senha_admin`, contexto com Administrador responsável) — aceite: usuário inativo retorna erro sem gerar token nem e-mail
- [x] 6.3 Teste automatizado: troca de senha com sucesso/senha atual incorreta/senha repetida do histórico; reset por Admin em usuário ativo/inativo, com verificação da linha em `log_seguranca` — **obrigatório por tocar dado pessoal e log de auditoria**

## 7. Gestão de usuários

- [x] 7.1 Endpoint `POST /usuarios` — Administrador cadastra em qualquer unidade/perfil; validações de e-mail único, formato de e-mail, nome não vazio, unidade ativa; dispara token de primeiro acesso (5.1) + e-mail — aceite: cobre PRD US 1.1 Cen.1–5
- [x] 7.2 Aplicar `require_perfil`/`require_acesso_unidade` (2.6) ao mesmo endpoint para o caso Gestor: só cria em unidade gerida, só perfil Servidor — aceite: cobre PRD US 1.2 Cen.1–3
- [x] 7.3 Endpoint `PATCH /usuarios/{id}/unidade` — transferência de Servidor (substitui vínculo 1:1), rejeita tentativa de vínculo duplo mantendo perfil Servidor — aceite: cobre PRD US 8.6 Cen.1–2
- [x] 7.4 Endpoint `PUT /usuarios/{id}/unidades-geridas` — define o conjunto de `unidade_gestor` para um Gestor (uma ou mais unidades) — aceite: cobre PRD US 8.6b Cen.1–2
- [x] 7.5 Endpoint `GET /usuarios` (listagem paginada, escopada por perfil/unidade via 2.6) — aceite: Gestor só lista usuários das unidades que gerencia; Administrador lista todos
- [x] 7.6 Teste automatizado: todos os cenários de 7.1–7.4 (cadastro Admin, cadastro Gestor restrito, transferência de unidade, vínculo duplo rejeitado, unidades geridas) — **obrigatório por tocar dado pessoal (nome, e-mail, vínculo organizacional)**

## 8. Unidades administrativas

- [x] 8.1 Endpoint `POST /unidades` (Administrador) — cadastro com nome, sigla, gestor responsável — aceite: cobre PRD US 8.1 Cen.1
- [x] 8.2 Endpoint `PATCH /unidades/{id}` (Administrador) — edição aplicada imediatamente — aceite: cobre PRD US 8.1 Cen.2
- [x] 8.3 Serviço `app/services/unidades.py::contar_processos_em_andamento(unidade_id) -> int` — stub retornando `0`, com `TODO(épico-2)` explícito no docstring — aceite: chamada isolada testável, documentada como seam
- [x] 8.4 Endpoint `POST /unidades/{id}/desativar` (Administrador) — bloqueia se `contar_processos_em_andamento > 0`; caso contrário marca inativa e desvincula usuários (`usuario.unidade_id = NULL`, `status` inalterado conforme design) — aceite: cobre PRD US 8.1 Cen.3–4 (Cen.3 validado estruturalmente com stub em 0)
- [x] 8.5 Aplicar `require_perfil("administrador")` (2.6) a todos os endpoints de 8.1–8.4 — aceite: Gestor e Servidor recebem 403 em qualquer um deles, com linha em `log_seguranca`
- [x] 8.6 Teste automatizado: cadastro, edição, desativação com/sem processos pendentes (stub), acesso negado para Gestor/Servidor — obrigatório por regra de visibilidade por perfil

## 9. Tipos de processo e roteiros

- [x] 9.1 Serviço `app/services/roteiros.py::obter_roteiro_vigente(tipo_processo_id)` — único ponto de leitura de roteiro vigente (`vigente=true`) — aceite: função é o único lugar do código que faz `SELECT ... FROM roteiro WHERE vigente`
- [x] 9.2 Endpoint `POST /tipos-processo` (Administrador) — cria tipo de processo + primeira versão de roteiro (`roteiro_etapa` ordenada), rejeita nome duplicado e roteiro vazio — aceite: cobre PRD US 8.2 Cen.1, 3, 4
- [x] 9.3 Endpoint `PUT /tipos-processo/{id}/roteiro` (Administrador) — cria nova versão de `roteiro` (`vigente=true`), marca a anterior `vigente=false`, sem alterar `roteiro_etapa` de versões antigas — aceite: cobre PRD US 8.2 Cen.2, usando 9.1 para leitura
- [x] 9.4 Aplicar `require_perfil("administrador")` (2.6) aos endpoints de 9.2–9.3 — aceite: Gestor e Servidor recebem 403, com linha em `log_seguranca`
- [x] 9.5 Teste automatizado: criação de tipo/roteiro, roteiro vazio rejeitado, nome duplicado rejeitado, alteração de roteiro preserva a versão vigente na criação de um "processo" simulado (mock, já que `processo` não existe), acesso negado para Gestor/Servidor

## 10. Controle de acesso por unidade — "Meu Perfil"

- [x] 10.1 Endpoint `GET /usuarios/me/perfil` — retorna dados cadastrais do usuário autenticado + seções de histórico com estado vazio (`processos: []`, `documentos_assinados: []`, mensagens "Nenhum processo registrado"/"Nenhum documento assinado") — aceite: cobre PRD US 1.5 Cen.2; documentado como preparado para popular quando `processo`/`documento` existirem (Épico 2/3)
- [x] 10.2 Garantir que o endpoint só retorna dados do próprio `usuario_id` do token (sem parâmetro de ID manipulável) — aceite: não há rota `GET /usuarios/{id}/perfil` de terceiros neste change; tentativa de acessar perfil alheio não tem endpoint que a permita
- [x] 10.3 Teste automatizado: perfil de usuário sem histórico retorna os estados vazios esperados — obrigatório por tocar dado pessoal

## 11. Frontend — Next.js

- [x] 11.1 Página `/setup` — formulário de inicialização (Administrador root + primeira unidade), oculta automaticamente se `GET /setup/status` retornar `true`
- [x] 11.2 Página `/login` — formulário de login, tratamento de bloqueio/conta desativada, link "Esqueci minha senha"
- [x] 11.3 Página `/primeiro-acesso/[token]` e `/redefinir-senha/[token]` — criação de senha com validação de complexidade no client, tratamento de link expirado/usado
- [x] 11.4 Componente de sessão: timer de inatividade com modal de aviso 2 min antes do timeout (US 1.8 Cen.2b), sliding refresh a cada requisição autenticada bem-sucedida
- [x] 11.5 Página `/perfil` ("Meu Perfil") — dados cadastrais + seções de histórico com estado vazio
- [x] 11.6 Páginas administrativas `/admin/usuarios` (listagem/cadastro/transferência/unidades geridas), `/admin/unidades` (CRUD), `/admin/tipos-processo` (CRUD + editor de roteiro) — visíveis conforme perfil do usuário logado
- [x] 11.7 Gerar tipos TS via `openapi-typescript` a partir do OpenAPI atualizado da API (`pnpm gen:types`) e consumir nas páginas acima — aceite: nenhum tipo `any` nos payloads de request/response dessas páginas
- [x] 11.8 Testes Vitest + React Testing Library dos formulários de login, primeiro acesso e troca de senha (validação client-side, mensagens de erro)

## 12. Testes end-to-end (Playwright)

- [x] 12.1 Fluxo crítico: setup inicial → login do Administrador root — aceite: roda contra ambiente local com banco limpo
- [x] 12.2 Fluxo crítico: Administrador cadastra usuário → e-mail de primeiro acesso (mock do provedor) → usuário ativa conta → login
- [x] 12.3 Fluxo crítico: 3 tentativas de login incorretas → bloqueio → recuperação de senha → desbloqueio automático
- [x] 12.4 Fluxo crítico: Administrador cadastra unidade e tipo de processo com roteiro; Gestor tenta as mesmas ações e recebe acesso negado

## 13. Documentação e fechamento

- [x] 13.1 Atualizar `apps/api/README.md` com as novas variáveis/rotas de autenticação e o comando de geração de tipos TS, se necessário
- [x] 13.2 Rodar `openspec verify` (ou `/opsx:verify`) comparando specs/design/tasks com a implementação antes de arquivar o change
