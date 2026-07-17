# Primeiro acesso em produção — SETES.DOCS

Guia para o primeiro acesso ao ambiente de produção, **antes do Discovery Técnico de
assinaturas digitais (Épico 4)**. Cobre: link do sistema, inicialização (bootstrap),
cadastros iniciais obrigatórios e o que já pode/não pode ser testado.

## 1. Link do sistema

| Serviço | URL |
|---|---|
| **Web (o sistema, acesse por aqui)** | https://web-2j5ojmtaiq-rj.a.run.app |
| API (uso interno do frontend, não precisa acessar direto) | https://api-2j5ojmtaiq-rj.a.run.app |

> **Nota de manutenção**: essas URLs são fixas hoje (`infra/cloudrun.tf:20,28`) porque o
> Terraform não pode auto-referenciar a própria URL do serviço no momento da criação. Se
> algum dia o serviço `api` ou `web` for **recriado do zero** no GCP, a URL muda e esses
> dois valores (+ a variável de repositório `NEXT_PUBLIC_API_URL` no GitHub) precisam ser
> atualizados manualmente — do contrário o CORS e o login OIDC quebram. Confirme a URL
> vigente a qualquer momento com `terraform output api_url` / `terraform output web_url`
> em `infra/`.

Não há domínio customizado configurado — é a URL padrão `*.run.app` do Cloud Run.

## 2. Inicialização do sistema (só acontece uma vez)

O sistema começa "vazio": sem Administrador, sem Unidade. A primeira pessoa a acessar
`https://web-2j5ojmtaiq-rj.a.run.app/setup` faz o bootstrap.

1. Acesse a URL acima. Se o sistema **ainda não foi inicializado**, o formulário de setup
   aparece; se já foi, a página redireciona direto para `/login`.
2. Preencha:
   - **Administrador**: nome, e-mail, senha (a senha precisa atender aos critérios de
     complexidade exibidos no formulário) e confirmação de senha.
   - **Primeira Unidade**: nome e sigla (até 20 caracteres).
3. Ao enviar, o backend cria — numa única transação — a primeira Unidade e o usuário
   Administrador, e volta para a tela de login (`/login?motivo=setup-concluido`). **Não
   há login automático aqui** — diferente do fluxo de primeiro acesso de usuários comuns
   (seção 4).
4. Um e-mail de confirmação é enviado ao endereço cadastrado do Administrador.

**Isso só pode acontecer uma vez.** Depois de concluído, qualquer nova tentativa de
`POST /setup` recebe `409 Conflict` ("Sistema já inicializado") — não precisa se preocupar
em rodar duas vezes por engano, é protegido a nível de banco (`UPDATE ... WHERE
inicializado = false`, atômico mesmo sob concorrência).

Se por algum motivo você chegar em produção e o setup **já tiver sido feito por outra
pessoa do time**, peça as credenciais de Administrador a quem executou, ou peça para essa
pessoa cadastrar você como Administrador (via seção 3.2).

## 3. Cadastros iniciais — ordem obrigatória

Depois de logado como Administrador, cadastre nesta ordem (o backend rejeita fora dela):

### 3.1 Unidades (`Administração > Unidades`)

Cadastre todas as unidades organizacionais que vão participar dos fluxos de processo
(ex.: Protocolo, unidades técnicas, Gabinete). Campos: nome, sigla. O responsável
(Gestor) pode ficar em branco por enquanto e ser definido depois.

> A primeira unidade já foi criada no setup (seção 2) — aqui você cadastra as demais.

### 3.2 Usuários (`Administração > Usuários`)

Cadastre Gestores e Servidores. Campos: nome, e-mail, perfil (`servidor`, `gestor` ou
`administrador`).

- **Servidor**: exige vincular a uma Unidade já existente e ativa — por isso Unidades
  vêm primeiro.
- **Gestor**: o cadastro em si não pede unidade; depois de criado, vá em
  `Administração > Usuários > [gestor] > Unidades geridas` para vincular uma ou mais
  unidades a ele.
- Cada cadastro dispara automaticamente um e-mail de "primeiro acesso" para a pessoa
  (seção 4) — **não é preciso criar senha manualmente para ninguém**.

### 3.3 Tipos de Processo e Roteiros (`Administração > Tipos de Processo`)

Cadastre os tipos de processo que a instituição usa, e para cada um defina o **roteiro**:
a sequência ordenada de Unidades por onde o processo desse tipo tramita. Por isso as
Unidades precisam existir antes — o roteiro referencia os IDs delas.

Roteiros são versionados: alterar o roteiro de um tipo de processo depois não afeta
processos já criados com a versão anterior, só os novos.

### Resumo da ordem

```
Unidades  →  Usuários (Servidor vinculado / Gestor com unidades geridas)  →  Tipos de Processo (roteiro)
```

Só depois disso um Servidor consegue abrir o primeiro processo de teste.

## 4. Primeiro acesso de quem foi cadastrado (Servidor/Gestor)

Cada pessoa cadastrada na seção 3.2 recebe um e-mail com um link do tipo
`.../primeiro-acesso/{token}`, **válido por 48 horas**. Ao abrir o link:

1. A página pede só a senha (e confirmação) — sem precisar saber o e-mail de novo.
2. Ao definir a senha, o sistema já autentica automaticamente e leva direto para
   `/perfil` — não é preciso fazer login em seguida.

Se o link expirar (48h) ou já tiver sido usado, a pessoa pode:
- Usar **"Esqueci minha senha"** na tela de login (gera um novo link, válido por 2h); ou
- Pedir para um Administrador **resetar a senha** dela em
  `Administração > Usuários > [pessoa] > Resetar senha`, que reenvia um novo link de 2h.

## 5. Parâmetros do sistema (`Administração > Configurações`)

Hoje só estes três parâmetros são revisáveis por essa tela, sem precisar de deploy:

| Parâmetro | Default |
|---|---|
| Prazo de arquivamento automático (dias) | 30 |
| Antecedência do alerta de prazo (dias) | 2 |
| Dias para considerar um processo "parado" numa unidade | 7 |

Mudar o prazo de arquivamento **não é retroativo** — só afeta processos concluídos daqui
para frente.

> **Atenção**: outros parâmetros "operacionais" (timeout de sessão por inatividade — 30
> min, tentativas de login antes de bloquear — 3, validade dos links de primeiro
> acesso/recuperação de senha) ainda **não** estão nesta tela — são valores fixos no
> código-fonte hoje (parametrização completa é a US 8.5, entregue parcialmente). Se
> precisar mudar algum desses durante os testes, é necessário alterar o código e fazer
> novo deploy, não dá para ajustar pela interface.

## 6. O que já pode ser testado

Épicos com implementação completa e arquivada, prontos para teste de ponta a ponta:

- **Épico 1** — autenticação, perfis, controle de acesso por unidade.
- **Épico 2** — processos e workflow Kanban (criação, despacho, devolução, conclusão,
  arquivamento).
- **Épico 3** — gestão documental (upload/anexo de documentos, Cloud Storage).
- **Épico 5** — notificações internas e e-mail.
- **Épico 6** — dashboard de KPIs.
- **Épico 7** — consulta pública (`/consulta-publica`, sem login): busca por número
  exato e por assunto/tipo/período, processos sigilosos e dados pessoais
  (CPF/CNPJ, nomes) ficam ocultos, rate limit de 60 req/min por IP.
- **Épico 8** — administração do sistema (unidades, usuários, tipos de processo,
  roteiros, permissão de auditoria, desativação de usuário).
- **Épico 9** — auditoria e relatórios consolidados (perfil Auditor).
- **Épico 10** — canal público e rotinas LGPD (fila administrativa de solicitações,
  anonimização automática de processos arquivados).

## 7. O que NÃO testar ainda

- **Épico 4 — assinatura digital ICP-Brasil**: fora do sistema hoje, **de propósito**,
  não é bug. Está condicionado ao Discovery Técnico que vocês ainda vão iniciar. Não
  existe endpoint, tela ou fluxo de assinatura no ar. O único vestígio já preparado é que
  cada documento anexado já guarda um hash SHA-256 (preparação de integridade para
  quando a assinatura for implementada).

## 8. Problemas comuns

- **`409 Conflict` ao tentar acessar `/setup`**: o sistema já foi inicializado por
  alguém — vá para `/login` ou peça as credenciais de Administrador a quem fez o setup.
- **Link de primeiro acesso/recuperação de senha "expirado" ou "já utilizado"**: peça um
  reset (seção 4).
- **Bloqueio de login após tentativas erradas**: 3 tentativas erradas bloqueiam o login
  por 30 minutos (constante fixa, não configurável pela interface ainda).
- **Sessão expirando "sozinha"**: timeout de inatividade é de 30 minutos — comportamento
  esperado, não é bug.
- **Frontend carrega mas nada responde / erro de CORS no console do navegador**: indica
  que a URL da API não bate com a configurada em produção — reporte à equipe de infra
  antes de continuar os testes, não é algo que se resolve pela interface.
