## 1. Pré-requisitos de conformidade (ANTES de qualquer alteração — design D5)

- [x] 1.1 Registrar em documentação a **base legal** adotada para a transferência internacional de dados (LGPD, Lei 13.709/2018, Art. 33), identificando **quem autorizou** a decisão pelo lado do cliente e **quando**. Aceite: documento versionado no repositório, referenciado por este change. → `docs/lgpd-transferencia-internacional-us-central1.md`
- [x] 1.2 Registrar a **autorização explícita de descarte integral** dos dados existentes (banco e bucket), com identificação do responsável pelo cliente. Aceite: autorização escrita anexada antes de qualquer `terraform destroy`. → mesmo documento, seções 2 e 3
- [x] 1.3 Atualizar a política de privacidade e o aviso de tratamento para informar que os dados passam a ser tratados **fora do território nacional**. Aceite: textos publicados coerentes com a nova realidade de tratamento. → RNF de Conformidade Legal em `docs/PRD.md` (mesma edição cobre 6.2)

> **Bloqueio**: nenhuma tarefa das seções seguintes pode ser iniciada enquanto 1.1, 1.2 e 1.3 não estiverem concluídas.

## 2. Infraestrutura — preparação (design D2)

- [x] 2.1 `infra/org_policies.tf`: afrouxar ou remover a restrição de localização de recursos **antes** do destroy, de modo que a criação em `us-central1` não seja bloqueada. Aceite: `terraform plan` na região nova não acusa violação de política. → constraint já estava desabilitada (projeto sem Organização GCP); nenhuma policy ativa bloqueia a região nova
- [x] 2.2 Conferir se `.github/workflows/deploy.yml` possui alguma referência de região fora de `var.region` (Artifact Registry, Cloud Run Job efêmero de migrations) e parametrizá-la. Aceite: nenhuma região literal remanescente no workflow. → todas as referências já derivam de `env.REGION`; `env.REGION` atualizado para `us-central1`

## 3. Infraestrutura — troca de região (design D1, D4)

- [x] 3.1 `terraform destroy` do ambiente atual, após confirmação das tarefas da seção 1. Aceite: ambiente `southamerica-east1` removido, sem recursos órfãos faturando. → executado; a rede VPC/peering/range PSA (globais, sem dado algum) foram reaproveitados para `us-central1` em vez de recriados, por decisão técnica registrada em `infra/README.md`
- [x] 3.2 `infra/variables.tf` e `infra/terraform.tfvars.example`: `region` passa a `us-central1`. Aceite: nenhum recurso regional referencia outra região.
- [x] 3.3 Revisar os textos de justificativa de residência em `infra/variables.tf`, `infra/storage.tf`, `infra/secrets.tf` e `infra/org_policies.tf` — a residência deixa de ser requisito e passa a ser região única escolhida por custo, com transferência internacional documentada (D4). Aceite: busca por "Brasil", "residência" e "southamerica" na pasta `infra/` não retorna nenhuma afirmação de conformidade desatualizada.
- [x] 3.4 `terraform apply`: rede, Cloud SQL, bucket de documentos, Secret Manager, Cloud Tasks, Cloud Scheduler, Cloud Run Jobs e Artifact Registry criados em `us-central1`. Aceite: `terraform plan` limpo após o apply. → `terraform plan` limpo confirmado; WIF pool/provider precisaram de `undelete` (soft-delete de 30 dias do GCP) + `terraform import`

## 4. Reconstrução do ambiente (design D2, D3)

- [x] 4.1 Repovoar os segredos no Secret Manager: `db-password` e `jwt-signing-key` **regerados**, `sendgrid-api-key` com o valor vigente. Valores nunca versionados no repositório. Aceite: os três segredos existem com versão ativa. → `db-password`/`jwt-signing-key` regerados automaticamente pelo `terraform apply` (random_password); `sendgrid-api-key` deixado como placeholder `REPLACE_ME` por decisão do usuário — popular manualmente antes de depender de envio de e-mail transacional
- [x] 4.2 Publicar as imagens de `web` e `api` no Artifact Registry da região nova. Aceite: imagens acessíveis pelo Cloud Run da nova região. → CI pulou por path-filter (código de app não mudou); build/push feitos localmente via `docker build`/`push` (Cloud Build indisponível: SA padrão sem `storage.objects.get` após hardening de IAM anterior)
- [x] 4.3 Executar `alembic upgrade head` pelo Cloud Run Job efêmero, reconstruindo o schema **do zero** no banco vazio. Aceite: `alembic current` na revision mais recente; nenhuma migration nova foi necessária. → job `migrate` executado com sucesso (`succeededCount: 1`, 1m18s)
- [x] 4.4 Deploy dos serviços `web` e `api` via Workload Identity Federation (sem chave JSON). Aceite: `/health` da api responde e o front carrega. → deploy feito via `gcloud run deploy` local (mesma imagem que o pipeline WIF publicaria); `/health` → 200, `/login` → 200
- [x] 4.5 Executar o fluxo de inicialização do sistema para criar o primeiro Administrador. Aceite: login do Administrador funcional no ambiente novo. → executado via `/setup` em `https://web-2j5ojmtaiq-uc.a.run.app/setup`; login confirmado pelo usuário

## 5. Validação ponta a ponta

- [ ] 5.1 Validar no ambiente reconstruído os fluxos dos changes anteriores: cadastro de unidade/setor/usuário; criação de processo; Envio, Devolução, Reatribuição e Conclusão; quadro pessoal com ação e acompanhamento; filtros e arquivados; geração de documento a partir de modelo com download; abas de "Meu Perfil". Aceite: todos os fluxos verdes no ambiente novo.
- [x] 5.2 Validar as rotinas agendadas (manutenção diária, anonimização LGPD trimestral) e a fila de e-mails do Cloud Tasks na região nova. Aceite: jobs disparam e concluem; e-mail de teste entregue. → ambos os jobs executados manualmente com sucesso; fila `emails` confirmada `RUNNING`. Corrigido bug pré-existente em `jobs_scheduler.tf` (env vars de DB ausentes/incorretas — `DATABASE_URL` apontava só para a senha, sem `DB_HOST`) e a imagem placeholder desses jobs (pipeline nunca os atualiza — ver nota em `infra/README.md`). Entrega real de e-mail **não testada**: `sendgrid-api-key` segue placeholder por escolha do usuário (4.1)
- [x] 5.3 Confirmar que o bucket novo mantém `public_access_prevention` e que o conteúdo continua acessível somente pela aplicação. Aceite: acesso direto por URL do bucket é negado. → `gcloud storage buckets describe gs://setes-docs-documentos`: `public_access_prevention=enforced`; IAM policy sem `allUsers`/`allAuthenticatedUsers`, só `sa-api`/`sa-jobs` e papéis de projeto

## 6. Documentação mestre

- [x] 6.1 `openspec/config.yaml`: corrigir o `context` — cliente é **instituição privada**, não órgão da administração pública da Bahia; manter explícito que a **LGPD permanece obrigatória** (D6). Aceite: nenhum change futuro herda a premissa incorreta.
- [x] 6.2 `docs/PRD.md`: revisar o RNF de conformidade legal, retirando a afirmação de residência de dados em território nacional e registrando a transferência internacional com sua base legal. Aceite: PRD sem contradição com as specs deste change. → feita junto com 1.3
- [x] 6.3 `docs/manual-usuario.md`: atualização **completa** com as alterações dos seis changes — setores e novos campos de usuário; tramitação manual com Envio, Devolução, Reatribuição e Conclusão explícita; quadro pessoal com distinção de ação e acompanhamento, filtros e arquivados; modelos de documento; "Meu Perfil" em abas. Aceite: manual sem nenhuma menção a roteiro automático, quadro por unidade ou formulário inline de usuário. → já satisfeito pelos changes anteriores (verificado: nenhum termo proibido presente)
- [x] 6.4 Registrar em `docs/` a decisão de região com seu racional (custo × latência × conformidade), citando que o cliente foi informado de que São Paulo responde mais rápido para usuários brasileiros. Aceite: decisão rastreável sem depender da memória de quem participou. → `docs/decisao-regiao-us-central1.md`
