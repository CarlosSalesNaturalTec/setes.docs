## ADDED Requirements

### Requirement: Frontend alcança o backend pela origem do browser

O sistema SHALL garantir que o serviço `api` seja alcançável a partir da origem do browser do usuário e que o build do serviço `web` embuta a URL pública canônica da `api` em `NEXT_PUBLIC_API_URL`, de modo que o cliente HTTP do frontend (`apps/web/lib/api.ts`) resolva a `api` real em produção, e não o fallback local. A exposição da `api` ao tráfego público NÃO remove nenhuma camada de autenticação/autorização de aplicação — toda proteção continua no backend (sessão JWT, `require_perfil`/`require_acesso_unidade`, rate limiting e registro imutável de acesso negado).

Referência: fecha o gap de conectividade registrado na task 5.3 do change `correcao-pipeline-deploy-wif`.

#### Scenario: Browser alcança a api em produção
- **WHEN** o browser de um usuário carrega uma tela do `web` (ex.: `/setup`) e o bundle dispara uma requisição para a `api` (ex.: `GET /setup/status`)
- **THEN** a requisição chega ao serviço `api` (ingress público) e recebe resposta HTTP `200` com corpo válido, em vez de falhar por destino inalcançável (`localhost`) ou por ingress interno sem load balancer

#### Scenario: URL da api embutida em build-time no bundle do web
- **WHEN** a imagem do serviço `web` é buildada pelo pipeline de deploy
- **THEN** o `docker build` recebe `NEXT_PUBLIC_API_URL` apontando para a URL pública canônica da `api`, e o bundle JS servido ao browser contém essa URL — não o fallback `http://localhost:8000`

#### Scenario: Acesso negado — requisição sem credencial válida à api pública
- **WHEN** uma requisição chega à `api` publicamente exposta para um endpoint autenticado sem sessão JWT válida (ou com token expirado/insuficiente para o perfil/unidade)
- **THEN** a própria `api` rejeita a requisição na camada de aplicação (`401`/`403`) e registra o evento em `log_seguranca` quando for negação de acesso por perfil/unidade — a exposição pública do ingress não concede nenhum acesso que a autorização de aplicação não conceda

#### Scenario: Banco permanece sem exposição pública
- **WHEN** a `api` passa a aceitar tráfego público (ingress `INGRESS_TRAFFIC_ALL`)
- **THEN** o Cloud SQL continua sem IP público, acessível somente por IP privado a partir da `api` via Direct VPC egress, conforme a capability `conectividade-e-seguranca` — a mudança de ingress afeta apenas o serviço `api`, não o banco
