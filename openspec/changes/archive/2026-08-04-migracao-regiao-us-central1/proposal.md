## Why

Toda a infraestrutura está em `southamerica-east1` (Osasco/SP), escolhida no
change de bootstrap para garantir **residência de dados em território
brasileiro**, sob a premissa de que o cliente era um órgão da administração
pública. Na avaliação da primeira entrega o cliente pediu a migração para
`us-central1` (`docs/Ajustes SETES DOCS.pdf`): *"diminuir custo final, pois está
em South América, é mais rápido nas respostas, porém mais caro"*.

Duas informações do cliente mudam materialmente a análise desse pedido:

1. **O sistema não será utilizado por órgão público, e sim por uma instituição
   privada.** A premissa que motivou a residência nacional — exigência de
   administração pública — não se aplica. A LGPD continua valendo integralmente,
   mas a transferência internacional por empresa privada é rotineira e admitida
   (Lei 13.709/2018, Art. 33), desde que documentada.
2. **Os dados existentes são de teste e podem ser integralmente descartados.**
   Isso transforma o que seria uma migração com *dump/restore*, cópia de bucket e
   janela de indisponibilidade em um **provisionamento novo** — as limitações que
   tornariam a operação cara (região de Cloud SQL e localização de bucket são
   imutáveis) deixam de importar.

O próprio texto do cliente reconhece que São Paulo responde mais rápido para
usuários brasileiros, e opta conscientemente pelo custo. A decisão é do cliente e
está registrada como tal.

Este é o **sexto e último** change dos ajustes pós-avaliação. É deliberadamente
o último: é **destrutivo** e deve ocorrer depois que todo o restante estiver
implementado e validado, para que a reconstrução do ambiente já contemple o
sistema completo.

## What Changes

- **Região única passa a ser `us-central1`**: `var.region` alterada, alcançando
  Cloud Run (web e api), Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Scheduler,
  Cloud Run Jobs, Artifact Registry e a replicação do Secret Manager.
- **Ambiente reconstruído, não migrado**: `terraform destroy` seguido de
  `terraform apply` na nova região. **Nenhum dado é preservado** — decisão
  explícita do cliente. As migrations Alembic reconstroem o schema vazio, e o
  primeiro acesso do Administrador é refeito pelo fluxo de inicialização já
  existente.
- **Comentários de residência revistos**: as justificativas de residência
  nacional em `variables.tf`, `storage.tf`, `secrets.tf` e `org_policies.tf`
  passam a refletir a decisão corrente — a residência deixa de ser requisito e a
  região passa a ser escolha de custo.
- **Contexto do projeto corrigido**: `openspec/config.yaml` descreve o cliente
  como "órgão da administração pública (Bahia)", o que se mostrou incorreto. É
  atualizado para instituição privada, com a nota de que a LGPD permanece
  obrigatória.
- **Base legal da transferência internacional registrada** em documentação, com
  identificação de quem autorizou a decisão pelo cliente.
- **Manual de instruções atualizado** com todas as alterações dos seis changes —
  último item pendente do documento de ajustes.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a plataforma já é coberta por `plataforma-gcp`. -->

### Modified Capabilities

- `plataforma-gcp`: a região única passa a ser `us-central1`; a residência em
  território brasileiro deixa de ser requisito, substituída por região única
  escolhida por custo, com a transferência internacional documentada sob a LGPD.
- `gestao-documental`: o requisito de armazenamento deixa de exigir bucket com
  residência no Brasil; todas as demais garantias do bucket
  (`public_access_prevention`, acesso mediado pela aplicação, hash de
  integridade) permanecem **inalteradas**.

## Impact

- **Dependências**: recomenda-se implementar **por último**, após
  `setores-e-cadastro-usuario`, `tramitacao-manual`, `kanban-por-servidor`,
  `modelos-de-documento` e `perfil-em-abas`, para que o ambiente reconstruído já
  contemple o sistema completo. Requer `bootstrap-infraestrutura` e
  `reducao-custo-cloudsql` (arquivados).
- **Tabelas PostgreSQL**: **nenhuma** tabela nova ou alterada. A instância é
  recriada vazia e as migrations existentes reconstroem o schema.
- **Migrations**: **nenhuma migration nova**. As existentes são aplicadas do zero
  no banco recriado.
- **Segredos**: `db-password`, `jwt-signing-key` e `sendgrid-api-key` são
  **recriados** na nova região (a replicação gerenciada pelo usuário não é
  alterável). Nenhum segredo **novo** é introduzido.
- **Buckets**: o bucket de documentos é **recriado** em `us-central1` — a
  localização de um bucket é imutável. **Todo o conteúdo é descartado**, conforme
  decisão do cliente.
- **Infra** (`infra/`): `variables.tf` (`region`), `terraform.tfvars.example`,
  `storage.tf`, `secrets.tf`, `org_policies.tf`, `providers.tf` — a maior parte
  já referencia `var.region`, de modo que a alteração é concentrada na variável e
  nos comentários de justificativa.
- **CI/CD**: `.github/workflows/deploy.yml` — conferir referências de região do
  Artifact Registry e do Cloud Run Job efêmero de migrations. Workload Identity
  Federation permanece sem chave JSON.
- **Backend / Frontend / Contrato**: **nenhuma alteração de código de aplicação**
  e **nenhuma regeneração de tipos**.
- **LGPD**: o tratamento passa a ocorrer **fora do território nacional**. Isso
  configura **transferência internacional de dados** (Lei 13.709/2018, Art. 33) e
  exige base legal documentada pelo controlador — o cliente. Como o controlador é
  instituição **privada** e os dados atualmente existentes são de teste, a
  transferência não recai nas restrições específicas do setor público. Ações
  obrigatórias deste change: registrar a base legal adotada, identificar quem
  autorizou a decisão pelo cliente, e atualizar a política de privacidade e o
  aviso de tratamento para informar o tratamento no exterior. As garantias
  técnicas de proteção — acesso restrito, ausência de leitura pública,
  anonimização LGPD, retenção e purga — permanecem **inalteradas**.
- **PRD**: `docs/PRD.md` — RNF de conformidade legal revisto para retirar a
  afirmação de residência nacional e registrar a transferência internacional.
- **Documentação**: `docs/manual-usuario.md` atualizado com **todas** as
  alterações dos seis changes (último item do documento de ajustes do cliente).
